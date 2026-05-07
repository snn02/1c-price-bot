import pytest

from price_bot.common.types import (
    Conversation,
    GeneratedQuote,
    Message,
    Product,
    QuoteDraft,
    QuoteItem,
    QuoteResult,
)


class TestProduct:
    def test_create_with_all_fields(self):
        p = Product(code="123", name="ERP", price_retail=100000.0, vat="НДС 20%")
        assert p.code == "123"
        assert p.name == "ERP"
        assert p.price_retail == 100000.0
        assert p.vat == "НДС 20%"


class TestQuoteDraft:
    def test_optional_fields_default_to_none(self):
        d = QuoteDraft(id=1, conversation_id=2, status="collecting")
        assert d.client_name is None
        assert d.clarification_kind is None
        assert d.clarification_question is None
        assert d.title is None

    def test_all_fields_settable(self):
        d = QuoteDraft(
            id=1,
            conversation_id=2,
            status="needs_clarification",
            client_name="ООО Ромашка",
            clarification_kind="client_name",
            clarification_question="Укажите клиента",
        )
        assert d.client_name == "ООО Ромашка"
        assert d.clarification_kind == "client_name"


class TestQuoteItem:
    def test_minimal_creation(self):
        item = QuoteItem(id=1, quote_draft_id=10, source_query="ERP", qty=1, status="selected")
        assert item.selected_product_code is None
        assert item.line_sum is None
        assert item.ambiguity_reason is None

    def test_selected_item_with_product_fields(self):
        item = QuoteItem(
            id=2,
            quote_draft_id=10,
            source_query="ERP",
            qty=5,
            status="selected",
            selected_product_code="290",
            selected_product_name="1С:ERP",
            price_retail=100000.0,
            vat="НДС 20%",
            line_sum=500000.0,
        )
        assert item.line_sum == 500000.0
        assert item.selected_product_name == "1С:ERP"


class TestQuoteResult:
    def test_creation(self):
        qr = QuoteResult(items=[], total_sum=0.0)
        assert qr.total_sum == 0.0
        assert qr.items == []


class TestMessage:
    def test_minimal_creation(self):
        m = Message(id=1, conversation_id=2, direction="in", role="manager", text="привет")
        assert m.telegram_message_id is None
        assert m.created_at is None


class TestConversation:
    def test_optional_active_draft(self):
        c = Conversation(id=1, telegram_chat_id=100, telegram_user_pk=5)
        assert c.active_quote_draft_id is None
