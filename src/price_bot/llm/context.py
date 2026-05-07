from typing import Optional

from price_bot.common.types import Message, QuoteDraft, QuoteItem


SYSTEM_PROMPT = """Ты — ассистент менеджера по продажам программного обеспечения 1С.
Твоя задача — помочь менеджеру составить коммерческое предложение (КП).

Правила:
- Никогда не придумывай продукты, цены и коды — всё берётся только из MCP.
- Всегда возвращай ответ строго в формате JSON.
- Не добавляй текст вне JSON.

Формат ответа:
{
  "action": "<action_name>",
  "arguments": { ... },
  "reason": "<короткое пояснение>"
}

Доступные действия:
- list_drafts — показать незавершённые черновики. Аргументы: {}
- find_drafts — найти черновики по тексту. Аргументы: {"query": "..."}
- open_draft — открыть черновик. Аргументы: {"draft_id": 12}
- add_items — добавить позиции. Аргументы: {"items_text": "..."}
- replace_item — заменить позицию. Аргументы: {"target": "...", "replacement_text": "..."}
- remove_item — убрать позицию. Аргументы: {"target": "..."}
- new_calculation — начать новый расчёт. Аргументы: {"items_text": "..."}
- create_quote_file — сформировать КП. Аргументы: {} или {"client_name": "..."}
- refresh_prices — обновить цены. Аргументы: {}
- clarify_answer — ответить на уточнение. Аргументы: {"answer": "..."}
"""


def _serialize_draft(draft: QuoteDraft, items: list[QuoteItem]) -> str:
    lines = [
        f"Активный черновик #{draft.id}:",
        f"  Статус: {draft.status}",
        f"  Заголовок: {draft.title or '—'}",
        f"  Клиент: {draft.client_name or 'не указан'}",
    ]
    if draft.clarification_question:
        lines.append(f"  Ожидается уточнение ({draft.clarification_kind}): {draft.clarification_question}")
    if items:
        lines.append("  Позиции:")
        for item in items:
            status_mark = {"selected": "✓", "ambiguous": "?", "not_found": "✗", "removed": "—", "pending": "…"}.get(item.status, item.status)
            product_info = ""
            if item.selected_product_name:
                product_info = f" → {item.selected_product_name}"
                if item.line_sum is not None:
                    product_info += f" ({item.qty} шт., {item.line_sum:.0f} руб.)"
            elif item.ambiguity_reason:
                product_info = f" [неоднозначно: {item.ambiguity_reason}]"
            lines.append(f"    [{status_mark}] {item.source_query}{product_info}")
    return "\n".join(lines)


def build_context(
    draft: Optional[QuoteDraft],
    draft_items: list[QuoteItem],
    messages: list[Message],
    current_message: str,
    rules_text: str,
) -> list[dict]:
    system_content = SYSTEM_PROMPT
    if rules_text:
        system_content += f"\n\n# Правила и политики\n\n{rules_text}"
    if draft is not None:
        system_content += f"\n\n# Текущее состояние\n\n{_serialize_draft(draft, draft_items)}"

    context: list[dict] = [{"role": "system", "content": system_content}]

    for msg in messages[-10:]:
        role = "user" if msg.role == "manager" else "assistant"
        context.append({"role": role, "content": msg.text})

    context.append({"role": "user", "content": current_message})
    return context
