## ADDED Requirements

### Requirement: Инициализация базы данных
Функция `init_db(conn)` SHALL создавать все таблицы по DDL из `docs/database.md`
если они не существуют (`CREATE TABLE IF NOT EXISTS`). При каждом открытии
соединения MUST применяться PRAGMA: `foreign_keys = ON`, `journal_mode = WAL`,
`busy_timeout = 5000`.

#### Scenario: Первый запуск
- **WHEN** вызывается `init_db(conn)` на пустой БД
- **THEN** все таблицы создаются без ошибок

#### Scenario: Повторный запуск
- **WHEN** вызывается `init_db(conn)` на уже инициализированной БД
- **THEN** функция завершается без ошибок и без потери данных

---

### Requirement: UserRepository
`UserRepository` SHALL предоставлять метод `get_or_create(telegram_user_id, username,
first_name, last_name) → QuoteDraft`. Если пользователь с таким `telegram_user_id`
не найден, MUST создаваться новая запись. Метод MUST быть идемпотентным.

#### Scenario: Новый пользователь
- **WHEN** вызывается `get_or_create` с новым `telegram_user_id`
- **THEN** создаётся запись в `telegram_users` и возвращается объект с `id`

#### Scenario: Существующий пользователь
- **WHEN** вызывается `get_or_create` с уже существующим `telegram_user_id`
- **THEN** возвращается существующая запись без создания дубля

---

### Requirement: ConversationRepository
`ConversationRepository` SHALL предоставлять:
- `get_or_create(telegram_chat_id, telegram_user_pk) → Conversation`
- `set_active_draft(conversation_id, draft_id | None)`
- `get_active_draft_id(conversation_id) → int | None`

#### Scenario: Создание разговора
- **WHEN** вызывается `get_or_create` с новой парой `chat_id + user_pk`
- **THEN** создаётся запись в `conversations` с `active_quote_draft_id = NULL`

#### Scenario: Обновление активного черновика
- **WHEN** вызывается `set_active_draft(conversation_id, draft_id)`
- **THEN** `conversations.active_quote_draft_id` обновляется до `draft_id`

#### Scenario: Сброс активного черновика
- **WHEN** вызывается `set_active_draft(conversation_id, None)`
- **THEN** `conversations.active_quote_draft_id` становится `NULL`

---

### Requirement: MessageRepository
`MessageRepository` SHALL предоставлять `save(conversation_id, telegram_message_id,
direction, role, text) → Message` и `get_last_n(conversation_id, n) → list[Message]`
отсортированные по `created_at` ASC.

#### Scenario: Сохранение входящего сообщения
- **WHEN** вызывается `save(..., direction="in", role="manager", text="...")`
- **THEN** запись создаётся в `messages` с корректными полями

#### Scenario: Получение последних сообщений
- **WHEN** вызывается `get_last_n(conversation_id, 10)`
- **THEN** возвращаются до 10 последних сообщений в хронологическом порядке

---

### Requirement: QuoteDraftRepository
`QuoteDraftRepository` SHALL предоставлять:
- `create(conversation_id, title, items_text) → QuoteDraft` — создаёт черновик со статусом `collecting`
- `get_by_id(draft_id, telegram_user_id) → QuoteDraft | None` — с проверкой владения
- `get_active(conversation_id) → QuoteDraft | None`
- `update_status(draft_id, status, **kwargs)` — обновляет статус и связанные поля
- `list_active(telegram_user_id, limit=10) → list[QuoteDraft]`
- `find_by_query(telegram_user_id, query) → list[QuoteDraft]` — поиск по title/client_name/manager_note через LIKE

#### Scenario: Создание черновика
- **WHEN** вызывается `create(conversation_id, title="ERP, 10 лицензий")`
- **THEN** создаётся запись со `status="collecting"` и `title="ERP, 10 лицензий"`

#### Scenario: Проверка владения
- **WHEN** вызывается `get_by_id(draft_id, telegram_user_id)` для чужого черновика
- **THEN** возвращается `None`

#### Scenario: Поиск черновиков
- **WHEN** вызывается `find_by_query(user_id, "ERP")`
- **THEN** возвращаются незавершённые черновики, в title/client_name/manager_note которых есть подстрока "ERP"

---

### Requirement: QuoteItemRepository
`QuoteItemRepository` SHALL предоставлять:
- `insert_items(items: list[dict]) → list[QuoteItem]`
- `get_by_draft(draft_id, exclude_removed=True) → list[QuoteItem]`
- `set_removed(draft_id, target_like)` — помечает совпадающие позиции как `removed`
- `insert_selected(draft_id, source_query, qty, product, line_sum) → QuoteItem`

#### Scenario: Вставка выбранных позиций
- **WHEN** вызывается `insert_selected` с корректными данными продукта
- **THEN** создаётся запись со `status="selected"` и заполненными product-полями

#### Scenario: Удаление позиции
- **WHEN** вызывается `set_removed(draft_id, "ЗУП")`
- **THEN** позиция с совпадающим `source_query` или `selected_product_name` переходит в `status="removed"`

---

### Requirement: GeneratedQuoteRepository
`GeneratedQuoteRepository` SHALL предоставлять `save(draft_id, file_path, total_sum)
→ GeneratedQuote`.

#### Scenario: Сохранение записи о КП
- **WHEN** вызывается `save(draft_id, "/outputs/quote_123.md", 250000.0)`
- **THEN** создаётся запись в `generated_quotes` с `file_format="md"`
