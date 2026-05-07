from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    code: str
    name: str
    price_retail: float
    vat: str


@dataclass
class QuoteItem:
    id: int
    quote_draft_id: int
    source_query: str
    qty: int
    status: str
    selected_product_code: Optional[str] = None
    selected_product_name: Optional[str] = None
    price_retail: Optional[float] = None
    vat: Optional[str] = None
    line_sum: Optional[float] = None
    ambiguity_reason: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class QuoteDraft:
    id: int
    conversation_id: int
    status: str
    title: Optional[str] = None
    client_name: Optional[str] = None
    manager_note: Optional[str] = None
    clarification_question: Optional[str] = None
    clarification_kind: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class QuoteResult:
    items: list
    total_sum: float


@dataclass
class Message:
    id: int
    conversation_id: int
    direction: str
    role: str
    text: str
    created_at: Optional[str] = None
    telegram_message_id: Optional[int] = None


@dataclass
class Conversation:
    id: int
    telegram_chat_id: int
    telegram_user_pk: int
    active_quote_draft_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class GeneratedQuote:
    id: int
    quote_draft_id: int
    file_path: str
    file_format: str
    total_sum: Optional[float] = None
    created_at: Optional[str] = None
