import pytest

from price_bot.common.types import Message, QuoteDraft, QuoteItem
from price_bot.llm.context import build_context


def make_message(i: int, role: str = "manager") -> Message:
    direction = "in" if role == "manager" else "out"
    return Message(
        id=i,
        conversation_id=1,
        direction=direction,
        role=role,
        text=f"сообщение {i}",
    )


class TestBuildContext:
    def test_without_draft_has_system_and_user(self):
        ctx = build_context(None, [], [], "привет", "")
        assert ctx[0]["role"] == "system"
        assert ctx[-1]["role"] == "user"
        assert ctx[-1]["content"] == "привет"

    def test_with_draft_state_appears_in_system(self):
        draft = QuoteDraft(id=7, conversation_id=1, status="collecting", title="ERP")
        ctx = build_context(draft, [], [], "добавь ЗУП", "")
        system_content = ctx[0]["content"]
        assert "Активный черновик #7" in system_content
        assert "ERP" in system_content

    def test_without_draft_no_draft_state_in_system(self):
        ctx = build_context(None, [], [], "привет", "")
        system_content = ctx[0]["content"]
        assert "Активный черновик" not in system_content

    def test_rules_text_included_in_system(self):
        ctx = build_context(None, [], [], "запрос", "ПРАВИЛО: всегда КОРП")
        assert "ПРАВИЛО: всегда КОРП" in ctx[0]["content"]

    def test_manager_messages_become_user_role(self):
        msgs = [make_message(1, "manager")]
        ctx = build_context(None, [], msgs, "новое", "")
        user_messages = [m for m in ctx if m["role"] == "user"]
        assert any("сообщение 1" in m["content"] for m in user_messages)

    def test_bot_messages_become_assistant_role(self):
        msgs = [make_message(2, "bot")]
        ctx = build_context(None, [], msgs, "новое", "")
        assert any(m["role"] == "assistant" and "сообщение 2" in m["content"] for m in ctx)

    def test_history_limited_to_10_messages(self):
        msgs = [make_message(i) for i in range(25)]
        ctx = build_context(None, [], msgs, "текущее", "")
        history_messages = [m for m in ctx[1:] if m["content"] != "текущее"]
        assert len(history_messages) <= 10

    def test_current_message_is_last(self):
        msgs = [make_message(i) for i in range(3)]
        ctx = build_context(None, [], msgs, "финальное", "")
        assert ctx[-1]["content"] == "финальное"

    def test_clarification_question_in_system_when_draft_has_it(self):
        draft = QuoteDraft(
            id=1,
            conversation_id=1,
            status="needs_clarification",
            clarification_question="ПРОФ или КОРП?",
            clarification_kind="product_choice",
        )
        ctx = build_context(draft, [], [], "КОРП", "")
        assert "ПРОФ или КОРП?" in ctx[0]["content"]

    def test_draft_items_appear_in_system(self):
        draft = QuoteDraft(id=5, conversation_id=1, status="collecting")
        items = [
            QuoteItem(
                id=1,
                quote_draft_id=5,
                source_query="ERP",
                qty=3,
                status="selected",
                selected_product_name="1С:ERP Корп",
                line_sum=300000.0,
            )
        ]
        ctx = build_context(draft, items, [], "запрос", "")
        assert "1С:ERP Корп" in ctx[0]["content"]
