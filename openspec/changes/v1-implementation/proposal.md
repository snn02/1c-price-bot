## Why

Каркас проекта и проектная документация готовы, реализация отсутствует. Нужно
написать первую рабочую версию бота — от запуска до получения Markdown КП
менеджером в Telegram.

## What Changes

- Реализовать пакет `common` — конфигурация, общие типы данных, исключения.
- Реализовать пакет `storage` — aiosqlite-репозитории для всех таблиц, миграции SQLite.
- Реализовать пакет `llm` — OpenRouter client, сборка промпта, парсинг JSON action response.
- Реализовать пакет `mcp` — запуск MCP subprocess, adapter для четырёх инструментов, обработка ошибок.
- Реализовать пакет `quotes` — Quote service: оркестрация 10 LLM actions, жизненный цикл черновика.
- Реализовать пакет `bot` — Telegram handlers, long polling, команды `/start` и `/refresh_prices`.
- Добавить renderer в пакет `quotes` — загрузка Jinja2-шаблона, генерация Markdown КП.
- Добавить `pyproject.toml` с зависимостями и точкой входа.

## Capabilities

### New Capabilities

- `common-config`: конфигурация из переменных окружения, общие типы данных
  (Product, QuoteDraft, QuoteItem и др.), иерархия исключений проекта.
- `storage`: aiosqlite-репозитории для `telegram_users`, `conversations`,
  `messages`, `quote_drafts`, `quote_items`, `generated_quotes`; инициализация
  схемы и PRAGMA при старте.
- `llm-client`: клиент OpenRouter, сборка LLM input context (system + rules +
  draft state + history + message), парсинг и валидация JSON action response,
  поведение при malformed ответе.
- `mcp-adapter`: управление MCP subprocess (`stdio`), адаптер для
  `search_products`, `get_product`, `build_quote`, `refresh_prices`; reconnect
  стратегия; атомарность при ошибке MCP.
- `quote-service`: оркестрация всех 10 LLM actions (`add_items`, `remove_item`,
  `replace_item`, `new_calculation`, `create_quote_file`, `open_draft`,
  `list_drafts`, `find_drafts`, `clarify_answer`, `refresh_prices`), управление
  статусами черновика, логика `clarification_kind`.
- `renderer`: загрузка `templates/quote.md.j2`, рендеринг Markdown КП через
  Jinja2, запись файла в `OUTPUT_DIR`, форматирование денежных значений.
- `telegram-bot`: aiogram long polling, handler текстовых сообщений, команды
  `/start` и `/refresh_prices`, отправка сформированного Markdown-файла.

### Modified Capabilities

—

## Impact

- Создаются файлы во всех пакетах `src/price_bot/`.
- Добавляется `pyproject.toml` (aiogram, aiosqlite, jinja2, httpx или openai-compatible client).
- Заполняется `templates/quote.md.j2` (уже существует как заготовка).
- Runtime-правила в `rules/*.md` остаются без изменений — это не код.
