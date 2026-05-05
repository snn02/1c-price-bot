# Пользовательские сценарии и операции с БД

## Общие правила

- Каждое входящее сообщение сохраняется в `messages` до выполнения действия.
- Для обычного текста сначала вызывается LLM tool/action selection.
- LLM не читает и не пишет SQLite напрямую. Код приложения получает выбранное
  действие и сам вызывает repository, MCP client или renderer.
- MCP используется только для продуктов, цен и сборки табличного расчёта.
- Прайс 1С не пишется в базу бота.
- В v1 статусы черновиков, роли и направления сообщений пишутся строковыми
  кодами прямо в основные таблицы. Корректность кодов защищается
  `CHECK`-ограничениями из `docs/database.md`.
- В примерах ниже `telegram_user_id = 1001`, `telegram_chat_id = 2001`.

## 1. Простой запрос и создание КП

### 1.1 Менеджер пишет `УТ, сервер, 10 лицензий`

Чтение:

```sql
SELECT * FROM telegram_users WHERE telegram_user_id = 1001;
SELECT * FROM conversations
WHERE telegram_chat_id = 2001 AND telegram_user_id = 1001;
```

Если пользователя или разговора нет, запись:

```sql
INSERT INTO telegram_users (...);
INSERT INTO conversations (..., active_quote_draft_id, ...)
VALUES (..., NULL, ...);
```

Запись входящего сообщения:

```sql
INSERT INTO messages (conversation_id, telegram_message_id, direction, role, text, created_at)
VALUES (:conversation_id, :message_id, 'in', 'manager', 'УТ, сервер, 10 лицензий', :now);
```

LLM action selection:

```json
{
  "action": "add_items",
  "arguments": {
    "items_text": "УТ, сервер, 10 лицензий"
  }
}
```

Если активного черновика нет, запись:

```sql
INSERT INTO quote_drafts (
    conversation_id, status, title, client_name, manager_note,
    clarification_question, created_at, updated_at
)
VALUES (
    :conversation_id, 'collecting', 'УТ, сервер, 10 лицензий',
    NULL, NULL, NULL, :now, :now
);

UPDATE conversations
SET active_quote_draft_id = :draft_id, updated_at = :now
WHERE id = :conversation_id;
```

LLM product extraction и MCP:

```text
LLM -> позиции: УТ, сервер x64, 10 пользовательских лицензий
MCP -> search_products/get_product/build_quote
```

Запись выбранных позиций:

```sql
INSERT INTO quote_items (
    quote_draft_id, source_query, qty,
    selected_product_code, selected_product_name,
    price_retail, vat, line_sum,
    status, ambiguity_reason, created_at, updated_at
)
VALUES
(:draft_id, 'УТ', 1, :code_ut, :name_ut, :price_ut, :vat_ut, :sum_ut, 'selected', NULL, :now, :now),
(:draft_id, 'сервер x64', 1, :code_server, :name_server, :price_server, :vat_server, :sum_server, 'selected', NULL, :now, :now),
(:draft_id, '10 пользовательских лицензий', 10, :code_license, :name_license, :price_license, :vat_license, :sum_license, 'selected', NULL, :now, :now);
```

Запись ответа бота:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', :positions_summary, :now);

UPDATE quote_drafts SET updated_at = :now WHERE id = :draft_id;
UPDATE conversations SET updated_at = :now WHERE id = :conversation_id;
```

### 1.2 Менеджер пишет `Создай КП`

Запись входящего сообщения:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'in', 'manager', 'Создай КП', :now);
```

LLM action selection:

```json
{
  "action": "create_quote_file",
  "arguments": {}
}
```

Чтение активного черновика:

```sql
SELECT qd.*
FROM conversations c
JOIN quote_drafts qd ON qd.id = c.active_quote_draft_id
WHERE c.id = :conversation_id;
```

Если `client_name IS NULL`, бот спрашивает клиента:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', 'Для какого клиента создать КП?', :now);
```

### 1.3 Менеджер пишет `ООО Ромашка`

LLM action selection с учётом ожидаемого ответа:

```json
{
  "action": "clarify_answer",
  "arguments": {
    "answer": "ООО Ромашка"
  }
}
```

Запись клиента:

```sql
UPDATE quote_drafts
SET client_name = 'ООО Ромашка', status = 'ready', updated_at = :now
WHERE id = :draft_id;
```

Чтение данных для renderer:

```sql
SELECT * FROM quote_drafts WHERE id = :draft_id;
SELECT * FROM quote_items WHERE quote_draft_id = :draft_id AND status = 'selected';
```

Renderer создаёт Markdown-файл. Запись результата:

```sql
INSERT INTO generated_quotes (
    quote_draft_id, file_path, file_format, total_sum, created_at
)
VALUES (:draft_id, :file_path, 'md', :total_sum, :now);

UPDATE quote_drafts
SET status = 'generated', updated_at = :now
WHERE id = :draft_id;

UPDATE conversations
SET active_quote_draft_id = NULL, updated_at = :now
WHERE id = :conversation_id;

INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', :file_sent_message, :now);
```

## 2. Запрос и брошенный черновик

### 2.1 Менеджер пишет `ERP, 150 лицензий`

Операции такие же, как в сценарии 1:

```text
messages <- входящее сообщение
LLM -> add_items
quote_drafts <- новый collecting-черновик
conversations.active_quote_draft_id <- draft_id
MCP -> продукты и цены
quote_items <- выбранные позиции
messages <- ответ со списком позиций
```

Итоговое состояние:

```text
conversations.active_quote_draft_id = draft_id
quote_drafts.status = collecting
generated_quotes: записей нет
```

### 2.2 Менеджер больше ничего не пишет

Бот не создаёт КП сам и не меняет статус черновика на `generated`.

Черновик остаётся доступным:

```sql
SELECT qd.*
FROM quote_drafts qd
JOIN conversations c ON c.id = qd.conversation_id
WHERE c.telegram_user_id = 1001
  AND qd.status IN ('collecting', 'needs_clarification', 'ready');
```

Опциональная будущая housekeeping-задача может помечать старые черновики как
`cancelled`, но в v1 без отдельной команды менеджера черновик не удаляется.

## 3. Без активного черновика подняли старый черновик, сделали новый запрос, создали КП

### 3.1 Разговор без активного черновика, менеджер пишет `покажи мои черновики`

Находится существующий `conversation` для пары `telegram_chat_id` +
`telegram_user_id`. Если такой записи ещё нет, она создаётся.

Запись входящего сообщения:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'in', 'manager', 'покажи мои черновики', :now);
```

LLM action selection:

```json
{
  "action": "list_drafts",
  "arguments": {}
}
```

Чтение черновиков пользователя:

```sql
SELECT
    qd.id, qd.title, qd.status, qd.client_name, qd.updated_at,
    COUNT(CASE WHEN qi.status = 'selected' THEN qi.id END) AS selected_items_count,
    COUNT(CASE WHEN qi.status = 'ambiguous' THEN qi.id END) AS ambiguous_items_count,
    COUNT(CASE WHEN qi.status = 'not_found' THEN qi.id END) AS not_found_items_count,
    COALESCE(SUM(CASE WHEN qi.status = 'selected' THEN qi.line_sum ELSE 0 END), 0) AS total_sum
FROM quote_drafts qd
JOIN conversations c ON c.id = qd.conversation_id
LEFT JOIN quote_items qi ON qi.quote_draft_id = qd.id
WHERE c.telegram_user_id = 1001
  AND qd.status IN ('collecting', 'needs_clarification', 'ready')
GROUP BY qd.id
ORDER BY qd.updated_at DESC
LIMIT 10;
```

Запись ответа:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', :drafts_list, :now);
```

MCP не вызывается.

### 3.2 Менеджер пишет `открой 12`

LLM action selection:

```json
{
  "action": "open_draft",
  "arguments": {
    "draft_id": 12
  }
}
```

Проверка владения черновиком:

```sql
SELECT qd.*
FROM quote_drafts qd
JOIN conversations c ON c.id = qd.conversation_id
WHERE qd.id = 12
  AND c.telegram_user_id = 1001;
```

Связать текущий разговор с черновиком:

```sql
UPDATE conversations
SET active_quote_draft_id = 12, updated_at = :now
WHERE id = :conversation_id;
```

Прочитать позиции и ответить:

```sql
SELECT * FROM quote_items WHERE quote_draft_id = 12 AND status != 'removed';
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', :opened_draft_summary, :now);
```

### 3.3 Менеджер пишет `добавь еще ДО КОРП`

LLM action selection:

```json
{
  "action": "add_items",
  "arguments": {
    "items_text": "ДО КОРП"
  }
}
```

Чтение активного черновика:

```sql
SELECT active_quote_draft_id
FROM conversations
WHERE id = :conversation_id;
```

LLM product extraction и MCP:

```text
LLM -> позиция ДО КОРП
MCP -> search_products/build_quote
```

Запись новой позиции:

```sql
INSERT INTO quote_items (...)
VALUES (12, 'ДО КОРП', 1, :code_do, :name_do, :price_do, :vat_do, :sum_do, 'selected', NULL, :now, :now);

UPDATE quote_drafts
SET status = 'collecting', updated_at = :now
WHERE id = 12;
```

### 3.4 Менеджер пишет `сделай КП для ООО Ромашка`

LLM action selection:

```json
{
  "action": "create_quote_file",
  "arguments": {
    "client_name": "ООО Ромашка"
  }
}
```

Запись клиента, чтение позиций, генерация файла:

```sql
UPDATE quote_drafts
SET client_name = 'ООО Ромашка', status = 'ready', updated_at = :now
WHERE id = 12;

SELECT * FROM quote_drafts WHERE id = 12;
SELECT * FROM quote_items WHERE quote_draft_id = 12 AND status = 'selected';

INSERT INTO generated_quotes (...)
VALUES (12, :file_path, 'md', :total_sum, :now);

UPDATE quote_drafts SET status = 'generated', updated_at = :now WHERE id = 12;
UPDATE conversations SET active_quote_draft_id = NULL, updated_at = :now WHERE id = :conversation_id;
```

## 4. Запрос, уточнение, совсем новый запрос, создание КП

### 4.1 Менеджер пишет `ERP, 150 лицензий`

Создаётся черновик `draft_a`, добавляются выбранные позиции, бот отвечает
расчётом. Операции совпадают со сценарием 1.

### 4.2 Менеджер пишет `Добавь еще ДО`

Запись сообщения:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'in', 'manager', 'Добавь еще ДО', :now);
```

LLM action selection:

```json
{
  "action": "add_items",
  "arguments": {
    "items_text": "ДО"
  }
}
```

MCP или LLM выявляет неоднозначность: ДО ПРОФ или ДО КОРП.

Запись ambiguous-позиции:

```sql
INSERT INTO quote_items (
    quote_draft_id, source_query, qty,
    selected_product_code, selected_product_name,
    price_retail, vat, line_sum,
    status, ambiguity_reason, created_at, updated_at
)
VALUES (
    :draft_a, 'ДО', 1,
    NULL, NULL,
    NULL, NULL, NULL,
    'ambiguous', 'Нужно выбрать редакцию: ПРОФ или КОРП', :now, :now
);

UPDATE quote_drafts
SET status = 'needs_clarification',
    clarification_question = 'Какой ДО: ПРОФ или КОРП?',
    updated_at = :now
WHERE id = :draft_a;

INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'out', 'bot', 'Какой ДО: ПРОФ или КОРП?', :now);
```

### 4.3 Менеджер пишет `Теперь посчитай УХ на 500 пользователей`

Так как фраза явно указывает на новый расчёт, бот не применяет её как ответ на
уточнение по ДО.

LLM action selection:

```json
{
  "action": "new_calculation",
  "arguments": {
    "items_text": "УХ на 500 пользователей"
  }
}
```

Старый черновик помечается заменённым:

```sql
UPDATE quote_drafts
SET status = 'superseded',
    manager_note = 'Заменён новым расчётом: УХ на 500 пользователей',
    updated_at = :now
WHERE id = :draft_a;
```

Создаётся новый черновик `draft_b`:

```sql
INSERT INTO quote_drafts (
    conversation_id, status, title, client_name, manager_note,
    clarification_question, created_at, updated_at
)
VALUES (
    :conversation_id, 'collecting', 'УХ на 500 пользователей',
    NULL, NULL, NULL, :now, :now
);

UPDATE conversations
SET active_quote_draft_id = :draft_b, updated_at = :now
WHERE id = :conversation_id;
```

LLM product extraction и MCP:

```text
LLM -> УХ, сервер x64, 500 пользовательских лицензий
MCP -> search_products/get_product/build_quote
```

Запись позиций нового черновика:

```sql
INSERT INTO quote_items (...)
VALUES
(:draft_b, 'УХ', 1, :code_uh, :name_uh, :price_uh, :vat_uh, :sum_uh, 'selected', NULL, :now, :now),
(:draft_b, 'сервер x64', 1, :code_server, :name_server, :price_server, :vat_server, :sum_server, 'selected', NULL, :now, :now),
(:draft_b, '500 пользовательских лицензий', 500, :code_license, :name_license, :price_license, :vat_license, :sum_license, 'selected', NULL, :now, :now);
```

### 4.4 Менеджер пишет `Создай КП для ООО Вектор`

LLM action selection:

```json
{
  "action": "create_quote_file",
  "arguments": {
    "client_name": "ООО Вектор"
  }
}
```

Генерация выполняется только по активному `draft_b`:

```sql
UPDATE quote_drafts
SET client_name = 'ООО Вектор', status = 'ready', updated_at = :now
WHERE id = :draft_b;

SELECT * FROM quote_items
WHERE quote_draft_id = :draft_b AND status = 'selected';

INSERT INTO generated_quotes (...)
VALUES (:draft_b, :file_path, 'md', :total_sum, :now);

UPDATE quote_drafts
SET status = 'generated', updated_at = :now
WHERE id = :draft_b;

UPDATE conversations
SET active_quote_draft_id = NULL, updated_at = :now
WHERE id = :conversation_id;
```

Итог:

```text
draft_a.status = superseded
draft_b.status = generated
generated_quotes содержит файл КП по УХ на 500 пользователей
```

## 5. Два КП в одном разговоре

### 5.1 Менеджер создаёт первое КП

Менеджер пишет:

```text
УТ, сервер, 10 лицензий
```

Бот выполняет те же операции, что в сценарии 1:

```text
messages <- входящее сообщение
LLM -> add_items
quote_drafts <- draft_1 со status = collecting
conversations.active_quote_draft_id <- draft_1
MCP -> продукты и цены
quote_items <- выбранные позиции первого КП
messages <- ответ со списком позиций
```

Менеджер пишет:

```text
создай КП для ООО Ромашка
```

LLM action selection:

```json
{
  "action": "create_quote_file",
  "arguments": {
    "client_name": "ООО Ромашка"
  }
}
```

Запись результата:

```sql
UPDATE quote_drafts
SET client_name = 'ООО Ромашка', status = 'ready', updated_at = :now
WHERE id = :draft_1;

SELECT * FROM quote_items
WHERE quote_draft_id = :draft_1 AND status = 'selected';

INSERT INTO generated_quotes (...)
VALUES (:draft_1, :file_path_1, 'md', :total_sum_1, :now);

UPDATE quote_drafts
SET status = 'generated', updated_at = :now
WHERE id = :draft_1;

UPDATE conversations
SET active_quote_draft_id = NULL, updated_at = :now
WHERE id = :conversation_id;
```

Ключевое состояние после первого КП:

```text
quote_drafts[draft_1].status = generated
conversations.active_quote_draft_id = NULL
generated_quotes содержит file_path_1
```

### 5.2 Менеджер в том же разговоре делает новый запрос

Менеджер пишет:

```text
ERP, сервер, 150 лицензий
```

Запись входящего сообщения:

```sql
INSERT INTO messages (..., direction, role, text, ...)
VALUES (:conversation_id, ..., 'in', 'manager', 'ERP, сервер, 150 лицензий', :now);
```

LLM action selection:

```json
{
  "action": "add_items",
  "arguments": {
    "items_text": "ERP, сервер, 150 лицензий"
  }
}
```

Так как `conversations.active_quote_draft_id IS NULL`, бот создаёт новый
черновик, а не изменяет `draft_1`:

```sql
INSERT INTO quote_drafts (
    conversation_id, status, title, client_name, manager_note,
    clarification_question, created_at, updated_at
)
VALUES (
    :conversation_id, 'collecting', 'ERP, сервер, 150 лицензий',
    NULL, NULL, NULL, :now, :now
);

UPDATE conversations
SET active_quote_draft_id = :draft_2, updated_at = :now
WHERE id = :conversation_id;
```

LLM product extraction и MCP:

```text
LLM -> ERP, сервер x64, 150 пользовательских лицензий
MCP -> search_products/get_product/build_quote
```

Запись позиций второго КП:

```sql
INSERT INTO quote_items (...)
VALUES
(:draft_2, 'ERP', 1, :code_erp, :name_erp, :price_erp, :vat_erp, :sum_erp, 'selected', NULL, :now, :now),
(:draft_2, 'сервер x64', 1, :code_server, :name_server, :price_server, :vat_server, :sum_server, 'selected', NULL, :now, :now),
(:draft_2, '150 пользовательских лицензий', 150, :code_license, :name_license, :price_license, :vat_license, :sum_license, 'selected', NULL, :now, :now);
```

### 5.3 Менеджер создаёт второе КП

Менеджер пишет:

```text
создай КП для ООО Вектор
```

Запись результата:

```sql
UPDATE quote_drafts
SET client_name = 'ООО Вектор', status = 'ready', updated_at = :now
WHERE id = :draft_2;

SELECT * FROM quote_items
WHERE quote_draft_id = :draft_2 AND status = 'selected';

INSERT INTO generated_quotes (...)
VALUES (:draft_2, :file_path_2, 'md', :total_sum_2, :now);

UPDATE quote_drafts
SET status = 'generated', updated_at = :now
WHERE id = :draft_2;

UPDATE conversations
SET active_quote_draft_id = NULL, updated_at = :now
WHERE id = :conversation_id;
```

Итог:

```text
draft_1.status = generated
draft_2.status = generated
generated_quotes содержит две записи: file_path_1 и file_path_2
conversations.active_quote_draft_id = NULL
```

### 5.4 Защита от изменения уже созданного КП

Если после генерации КП `active_quote_draft_id = NULL`, а менеджер пишет
неполную команду изменения вроде:

```text
добавь еще ДО
```

бот не должен автоматически менять последний `generated`-черновик. Он должен
создать новый расчёт только при достаточном продуктовом запросе или уточнить:

```text
Создать новый расчёт с ДО или открыть один из прошлых черновиков как основу?
```
