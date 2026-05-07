import logging
from typing import Optional

import aiosqlite

from price_bot.common.config import Settings
from price_bot.common.exceptions import LLMError, MCPError
from price_bot.common.types import QuoteDraft, QuoteItem
from price_bot.llm.client import LLMClient
from price_bot.llm.context import build_context
from price_bot.llm.rules import RulesLoader
from price_bot.mcp.client import McpClient
from price_bot.quotes.renderer import Renderer
from price_bot.storage.repositories.conversations import ConversationRepository
from price_bot.storage.repositories.drafts import QuoteDraftRepository
from price_bot.storage.repositories.generated_quotes import GeneratedQuoteRepository
from price_bot.storage.repositories.items import QuoteItemRepository
from price_bot.storage.repositories.messages import MessageRepository
from price_bot.storage.repositories.users import UserRepository

logger = logging.getLogger(__name__)


class QuoteService:
    def __init__(
        self,
        conn: aiosqlite.Connection,
        llm_client: LLMClient,
        mcp_client: McpClient,
        renderer: Renderer,
        settings: Settings,
    ) -> None:
        self._conn = conn
        self._llm = llm_client
        self._mcp = mcp_client
        self._renderer = renderer
        self._settings = settings

        self._users = UserRepository(conn)
        self._convs = ConversationRepository(conn)
        self._msgs = MessageRepository(conn)
        self._drafts = QuoteDraftRepository(conn)
        self._items = QuoteItemRepository(conn)
        self._gquotes = GeneratedQuoteRepository(conn)

    async def handle_message(
        self,
        telegram_chat_id: int,
        telegram_user_id: int,
        telegram_message_id: int | None,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        text: str,
    ) -> str:
        user = await self._users.get_or_create(telegram_user_id, username, first_name, last_name)
        conv = await self._convs.get_or_create(telegram_chat_id, user["id"])

        await self._msgs.save(conv.id, telegram_message_id, "in", "manager", text)

        draft: Optional[QuoteDraft] = None
        draft_items: list[QuoteItem] = []
        active_draft_id = await self._convs.get_active_draft_id(conv.id)
        if active_draft_id:
            draft = await self._drafts.get_active(conv.id)
            if draft:
                draft_items = await self._items.get_by_draft(draft.id)

        history = await self._msgs.get_last_n(conv.id, 10)
        rules_text = RulesLoader.load(self._settings.rules_dir)
        context = build_context(draft, draft_items, history[:-1], text, rules_text)

        try:
            action_response = await self._llm.select_action(context)
        except LLMError as exc:
            reply = "Не удалось разобрать запрос, попробуйте переформулировать."
            logger.warning("LLM error: %s", exc)
            await self._msgs.save(conv.id, None, "out", "bot", reply)
            return reply

        action = action_response.action
        args = action_response.arguments

        try:
            if action == "add_items":
                reply = await self._action_add_items(conv.id, draft, args["items_text"])
            elif action == "remove_item":
                reply = await self._action_remove_item(conv.id, draft, args["target"])
            elif action == "replace_item":
                reply = await self._action_replace_item(conv.id, draft, args["target"], args["replacement_text"])
            elif action == "new_calculation":
                reply = await self._action_new_calculation(conv.id, draft, args["items_text"])
            elif action == "create_quote_file":
                reply = await self._action_create_quote_file(conv.id, draft, args.get("client_name"))
            elif action == "clarify_answer":
                reply = await self._action_clarify_answer(conv.id, draft, args["answer"])
            elif action == "list_drafts":
                reply = await self._action_list_drafts(telegram_user_id)
            elif action == "find_drafts":
                reply = await self._action_find_drafts(telegram_user_id, args["query"])
            elif action == "open_draft":
                reply = await self._action_open_draft(conv.id, telegram_user_id, int(args["draft_id"]))
            elif action == "refresh_prices":
                reply = await self._action_refresh_prices()
            else:
                reply = "Неизвестное действие. Попробуйте переформулировать."
        except MCPError as exc:
            logger.error("MCP error during action %s: %s", action, exc)
            reply = "Сервис цен временно недоступен. Попробуйте позже."
        except Exception as exc:
            logger.exception("Unexpected error during action %s: %s", action, exc)
            reply = "Что-то пошло не так, попробуйте ещё раз."

        await self._msgs.save(conv.id, None, "out", "bot", reply)
        return reply

    async def handle_refresh_prices(
        self,
        telegram_chat_id: int,
        telegram_user_id: int,
    ) -> str:
        user = await self._users.get_or_create(telegram_user_id, None, None, None)
        conv = await self._convs.get_or_create(telegram_chat_id, user["id"])
        try:
            result = await self._mcp.refresh_prices()
        except MCPError as exc:
            logger.error("refresh_prices MCP error: %s", exc)
            result = "Не удалось обновить цены. MCP-сервер недоступен."
        await self._msgs.save(conv.id, None, "out", "bot", result)
        return result

    # ─── actions ─────────────────────────────────────────────────────────────

    async def _action_add_items(
        self, conv_id: int, draft: Optional[QuoteDraft], items_text: str
    ) -> str:
        if draft is None:
            title = items_text.strip()[:120]
            draft = await self._drafts.create(conv_id, title)
            await self._convs.set_active_draft(conv_id, draft.id)

        products = await self._mcp.search_products(items_text)

        if not products:
            await self._items.insert_not_found(draft.id, items_text, 1)
            return f"Продукты по запросу «{items_text}» не найдены."

        if len(products) == 1:
            product = products[0]
            qty = _extract_qty(items_text)
            line_sum = product.price_retail * qty
            await self._items.insert_selected(draft.id, items_text, qty, product, line_sum)
            return (
                f"Добавлено: {product.name} × {qty} = {round(line_sum):,} руб. (НДС: {product.vat})"
            )

        ambiguity = "; ".join(f"{p.name} ({p.code})" for p in products[:5])
        await self._items.insert_ambiguous(draft.id, items_text, 1, ambiguity)
        await self._drafts.update_status(
            draft.id,
            "needs_clarification",
            clarification_question=f"Уточните, какой вариант: {ambiguity}",
            clarification_kind="product_choice",
        )
        return f"Найдено несколько вариантов: {ambiguity}\nКакой именно вас интересует?"

    async def _action_remove_item(
        self, conv_id: int, draft: Optional[QuoteDraft], target: str
    ) -> str:
        if draft is None:
            return "Нет активного черновика."
        matches = await self._items.find_matching(draft.id, target)
        if not matches:
            return f"Позиция «{target}» не найдена в черновике."
        if len(matches) > 1:
            names = ", ".join(i.selected_product_name or i.source_query for i in matches)
            return f"Найдено несколько позиций: {names}. Уточните, какую удалить."
        await self._items.set_removed(draft.id, target)
        await self._drafts.update_status(draft.id, "collecting")
        name = matches[0].selected_product_name or matches[0].source_query
        return f"Позиция «{name}» удалена из черновика."

    async def _action_replace_item(
        self, conv_id: int, draft: Optional[QuoteDraft], target: str, replacement_text: str
    ) -> str:
        if draft is None:
            return "Нет активного черновика."
        removed = await self._action_remove_item(conv_id, draft, target)
        added = await self._action_add_items(conv_id, draft, replacement_text)
        return f"{removed}\n{added}"

    async def _action_new_calculation(
        self, conv_id: int, draft: Optional[QuoteDraft], items_text: str
    ) -> str:
        if draft is not None:
            await self._drafts.update_status(draft.id, "superseded")
            await self._convs.set_active_draft(conv_id, None)
        return await self._action_add_items(conv_id, None, items_text)

    async def _action_create_quote_file(
        self, conv_id: int, draft: Optional[QuoteDraft], client_name: Optional[str]
    ) -> str:
        if draft is None:
            return "Нет активного черновика для формирования КП."

        effective_client = client_name or draft.client_name
        if not effective_client:
            await self._drafts.update_status(
                draft.id,
                "needs_clarification",
                clarification_question="Укажите название клиента для КП.",
                clarification_kind="client_name",
            )
            return "Укажите название клиента для КП."

        if client_name:
            await self._drafts.update_status(
                draft.id, "ready", client_name=effective_client
            )
        else:
            await self._drafts.update_status(draft.id, "ready")

        draft.client_name = effective_client
        items = await self._items.get_by_draft(draft.id)
        content = self._renderer.render(draft, items)
        file_path = self._renderer.save(content, draft.id)

        selected = [i for i in items if i.status == "selected"]
        total_sum = sum(i.line_sum or 0 for i in selected)
        await self._gquotes.save(draft.id, file_path, total_sum)
        await self._drafts.update_status(draft.id, "generated")
        await self._convs.set_active_draft(conv_id, None)
        return file_path

    async def _action_clarify_answer(
        self, conv_id: int, draft: Optional[QuoteDraft], answer: str
    ) -> str:
        if draft is None:
            return "Нет активного черновика."

        kind = draft.clarification_kind
        if kind == "client_name":
            await self._drafts.update_status(
                draft.id,
                "ready",
                client_name=answer,
                clarification_question=None,
                clarification_kind=None,
            )
            return f"Клиент сохранён: {answer}. Черновик готов к формированию КП."

        if kind in ("product_choice", "bundle_choice"):
            all_items = await self._items.get_by_draft(draft.id, exclude_removed=False)
            ambiguous = [i for i in all_items if i.status == "ambiguous"]
            if not ambiguous:
                return "Не найдено позиций для уточнения."
            item = ambiguous[0]
            products = await self._mcp.search_products(answer, limit=1)
            if not products:
                return f"Продукт «{answer}» не найден."
            product = products[0]
            line_sum = product.price_retail * item.qty
            await self._items.update_to_selected(item.id, product, line_sum)
            await self._drafts.update_status(
                draft.id,
                "collecting",
                clarification_question=None,
                clarification_kind=None,
            )
            return f"Выбран: {product.name} × {item.qty} = {round(line_sum):,} руб."

        await self._drafts.update_status(
            draft.id,
            "collecting",
            clarification_question=None,
            clarification_kind=None,
        )
        return await self._action_add_items(conv_id, draft, answer)

    async def _action_list_drafts(self, telegram_user_id: int) -> str:
        drafts = await self._drafts.list_active(telegram_user_id)
        if not drafts:
            return "Незавершённых черновиков нет."
        lines = ["Ваши черновики:"]
        for d in drafts:
            client = f" | {d.client_name}" if d.client_name else ""
            lines.append(f"  #{d.id} [{d.status}] {d.title or '—'}{client}")
        return "\n".join(lines)

    async def _action_find_drafts(self, telegram_user_id: int, query: str) -> str:
        drafts = await self._drafts.find_by_query(telegram_user_id, query)
        if not drafts:
            return f"Черновики по запросу «{query}» не найдены."
        lines = [f"Найдены черновики по «{query}»:"]
        for d in drafts:
            client = f" | {d.client_name}" if d.client_name else ""
            lines.append(f"  #{d.id} [{d.status}] {d.title or '—'}{client}")
        return "\n".join(lines)

    async def _action_open_draft(
        self, conv_id: int, telegram_user_id: int, draft_id: int
    ) -> str:
        draft = await self._drafts.get_by_id(draft_id, telegram_user_id)
        if draft is None:
            return f"Черновик #{draft_id} не найден или не принадлежит вам."
        await self._convs.set_active_draft(conv_id, draft_id)
        items = await self._items.get_by_draft(draft_id)
        selected = [i for i in items if i.status == "selected"]
        total = sum(i.line_sum or 0 for i in selected)
        summary = f"Открыт черновик #{draft.id}: {draft.title or '—'}\n"
        summary += f"Позиций: {len(selected)} selected, итого {round(total):,} руб."
        return summary

    async def _action_refresh_prices(self) -> str:
        return await self._mcp.refresh_prices()


def _extract_qty(text: str) -> int:
    import re
    match = re.search(r"(\d+)\s*(лиц|шт|пользовател|user)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 1
