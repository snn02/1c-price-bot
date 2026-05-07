# План закрытия `techlead_review_active.md`

## Summary

Закрыть ревью одним документационным проходом в 5 группах: LLM contract, состояние черновиков, MCP contract, renderer/config/storage, DB/module cleanups. Цель — сделать документацию decision-complete для последующего OpenSpec: без скрытых выборов для implementer.

## Key Changes

- **LLM contract (`R01`, `R02`)**
  - Добавить в архитектуру раздел про prompt/input contract: system instructions, `rules/*.md`, активный черновик, последние 10 сообщений, текущее сообщение.
  - Зафиксировать action selection как JSON response, не tool calling.
  - JSON envelope: `action`, `arguments`, `reason`.
  - Неизвестный action или невалидный JSON: не выполнять side effects, сохранить сообщение, попросить уточнение.

- **Dialog / draft state (`R03`, `R07`, `R14`)**
  - Добавить `quote_drafts.clarification_kind TEXT`.
  - Использовать `clarification_kind` для `client_name`, `product_choice`, `bundle_choice`, `generic`.
  - Описать `clarify_answer`: интерпретируется только через сохранённый `clarification_kind`.
  - Добавить допустимые переходы `quote_drafts.status`.
  - Зафиксировать `quote_drafts.title`: `trim(items_text)` и обрезка до 120 символов, без LLM summary в v1.

- **MCP contract (`R04`, `R05`)**
  - Добавить `docs/mcp-contract.md`.
  - Описать bot-side adapter contract для `search_products`, `get_product`, `build_quote`, `refresh_prices`.
  - Зафиксировать ожидаемые поля: код, название, цена, НДС display text, суммы.
  - Lifecycle: бот стартует `mcp-1c-price` как subprocess через `MCP_SERVER_PATH` при запуске; transport `stdio`.
  - При MCP ошибке: не менять черновик частично, сообщить менеджеру, reconnect/restart на следующем запросе.

- **Renderer, config, storage (`R08`, `R09`, `R10`)**
  - Добавить `docs/configuration.md`.
  - Переменные: `TELEGRAM_TOKEN`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `MCP_SERVER_PATH`, `DATA_DIR`, `OUTPUT_DIR`, `RULES_DIR`, `TEMPLATES_DIR`.
  - Storage runtime: `aiosqlite`; PRAGMA из `docs/database.md` включать на каждом соединении.
  - Добавить описание Markdown КП: клиент, дата, таблица код/название/кол-во/цена/сумма/НДС, итог, примечание.

- **DB / scenarios / code structure (`R06`, `R11`, `R12`, `R13`, `R15`)**
  - Добавить сценарии БД для `find_drafts`, `remove_item`, `replace_item`.
  - Перевести `conversations` на FK к `telegram_users.id`; Telegram id оставить unique external id.
  - `quote_items.vat`: display text из MCP, приложение не парсит и не считает НДС.
  - `generated_quotes.file_format`: `CHECK (file_format IN ('md'))`.
  - Добавить описание пакетов: `bot`, `quotes`, `llm`, `mcp`, `storage`, `common`.

## Test / Verification Plan

- Поиск по документации:
  - нет старых `telegram_user_id` FK на `telegram_users.telegram_user_id`;
  - нет неописанных LLM actions;
  - есть `clarification_kind`;
  - есть `CHECK file_format`;
  - есть docs для MCP, config, template, status transitions.
- Перечитать `docs/review/techlead_review_active.md` и отметить, какие R закрываются каждым изменением.
- Сверить SQL-примеры с актуальной схемой таблиц.
- Сверить `docs/database-scenarios.md` с `Supported LLM actions`.

## Assumptions

- `rules/*.md` остаются human-readable prompt context, не DSL.
- Реальный MCP response может отличаться; бот документирует bot-side adapter contract.
- В v1 нет tool calling, только JSON response от LLM.
- В v1 всё локально: Telegram long polling, SQLite, `aiosqlite`, MCP subprocess over stdio.
- Конкретные OpenSpec capability specs будут писаться после закрытия этого документационного ревью.
