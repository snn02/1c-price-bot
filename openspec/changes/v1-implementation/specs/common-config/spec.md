## ADDED Requirements

### Requirement: Загрузка конфигурации из переменных окружения
Модуль `price_bot.common.config` SHALL читать конфигурацию из переменных окружения
при импорте и предоставлять объект `Settings` с полями: `telegram_token`,
`openrouter_api_key`, `openrouter_model`, `mcp_server_path`, `data_dir`,
`output_dir`, `rules_dir`, `templates_dir`. Производные пути `db_path`,
`quote_template_path` MUST вычисляться из базовых директорий. При отсутствии
обязательной переменной (`TELEGRAM_TOKEN`, `OPENROUTER_API_KEY`, `MCP_SERVER_PATH`)
SHALL выбрасываться `ConfigError` при старте.

#### Scenario: Все переменные заданы
- **WHEN** все обязательные переменные окружения заданы
- **THEN** `Settings` создаётся без ошибок и поля содержат корректные значения

#### Scenario: Отсутствует обязательная переменная
- **WHEN** переменная `TELEGRAM_TOKEN` не задана
- **THEN** при импорте или создании `Settings` выбрасывается `ConfigError`

#### Scenario: Дефолтные пути
- **WHEN** `DATA_DIR` не задан
- **THEN** `settings.data_dir` равен `"data"` и `settings.db_path` равен `"data/bot.db"`

---

### Requirement: Общие типы данных
Модуль `price_bot.common.types` SHALL определять dataclass-типы для межпакетного
обмена: `Product` (code, name, price_retail, vat), `QuoteItem` (id, quote_draft_id,
source_query, qty, selected_product_code, selected_product_name, price_retail, vat,
line_sum, status, ambiguity_reason), `QuoteDraft` (id, conversation_id, status,
title, client_name, clarification_question, clarification_kind, created_at,
updated_at), `QuoteResult` (items, total_sum), `Message` (id, conversation_id,
direction, role, text, created_at).

#### Scenario: Создание Product
- **WHEN** создаётся `Product(code="123", name="ERP", price_retail=100000.0, vat="НДС 20%")`
- **THEN** объект создаётся без ошибок и все поля доступны

#### Scenario: QuoteDraft содержит опциональные поля
- **WHEN** создаётся `QuoteDraft` без `client_name` и `clarification_kind`
- **THEN** эти поля равны `None`

---

### Requirement: Иерархия исключений
Модуль `price_bot.common.exceptions` SHALL определять базовый класс `BotError` и
подклассы: `ConfigError`, `StorageError`, `LLMError`, `MCPError`, `ValidationError`.
Все пакеты MUST использовать эти исключения для межпакетной передачи ошибок.

#### Scenario: Перехват базового класса
- **WHEN** код перехватывает `BotError`
- **THEN** он перехватывает и `MCPError`, и `LLMError`, и `StorageError`
