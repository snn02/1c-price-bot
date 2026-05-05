# Структура базы данных бота

## Назначение

База бота хранит только состояние Telegram-бота: пользователей, разговоры,
сообщения, черновики КП, выбранные позиции и созданные файлы КП.

Прайс 1С в эту базу не копируется. Распарсенный прайс хранит внешний
MCP-сервер `mcp-1c-price` в своей SQLite-базе, по умолчанию
`~/.mcp-1c-price/prices.db`.

Рекомендуемый путь базы бота для v1:

```text
data/bot.db
```

## Режим SQLite

При открытии соединения приложение должно включать:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

## Таблицы

### `telegram_users`

Пользователи Telegram, которые писали боту.

```sql
CREATE TABLE telegram_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### `conversations`

Разговоры с ботом. Один пользователь может иметь несколько разговоров.
`active_quote_draft_id` показывает, с каким черновиком связан текущий разговор.

```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_chat_id INTEGER NOT NULL,
    telegram_user_id INTEGER NOT NULL,
    active_quote_draft_id INTEGER,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (telegram_user_id)
        REFERENCES telegram_users (telegram_user_id),
    FOREIGN KEY (active_quote_draft_id)
        REFERENCES quote_drafts (id)
);
```

Статусы:

```text
active | completed | cancelled
```

Пояснения:

- `active` — разговор открыт и может принимать новые сообщения. У него может
  быть активный черновик в `active_quote_draft_id`.
- `completed` — разговор завершён штатно: например, КП создано и бот больше не
  держит активный черновик в этом разговоре.
- `cancelled` — разговор закрыт без завершения сценария: например, менеджер
  явно отменил работу или будущая housekeeping-логика закрыла устаревший
  разговор.

### `messages`

История входящих и исходящих сообщений. Нужна для аудита, восстановления
контекста и диагностики поведения LLM.

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    telegram_message_id INTEGER,
    direction TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (conversation_id)
        REFERENCES conversations (id)
);
```

Значения:

```text
direction: in | out
role: manager | bot | system
```

Пояснения:

- `direction = in` — входящее сообщение от Telegram в сторону приложения.
- `direction = out` — исходящее сообщение приложения в Telegram.
- `role = manager` — сообщение написал менеджер.
- `role = bot` — сообщение сформировал бот для менеджера.
- `role = system` — служебная запись приложения, например диагностическая
  заметка о выбранном действии или восстановлении черновика. В v1 такие записи
  необязательны, но значение зарезервировано.

### `quote_drafts`

Черновики КП. Черновик принадлежит пользователю через исходный `conversation_id`,
но может быть открыт в новом разговоре через `conversations.active_quote_draft_id`.

```sql
CREATE TABLE quote_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    title TEXT,
    client_name TEXT,
    manager_note TEXT,
    clarification_question TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (conversation_id)
        REFERENCES conversations (id)
);
```

Статусы:

```text
collecting | needs_clarification | ready | generated | cancelled | superseded
```

Пояснения:

- `collecting` — черновик собирается: в него можно добавлять, заменять и удалять
  позиции.
- `needs_clarification` — бот задал уточняющий вопрос и ждёт ответа менеджера.
  Текст вопроса хранится в `clarification_question`.
- `ready` — черновик достаточно полный для генерации КП: позиции выбраны, суммы
  рассчитаны, клиент известен или будет передан в команде генерации.
- `generated` — по черновику сформирован файл КП, запись о файле находится в
  `generated_quotes`.
- `cancelled` — менеджер явно отказался от черновика или отменил расчёт.
- `superseded` — черновик заменён новым расчётом. Это не ошибка и не ручная
  отмена: например, после `ERP, 150 лицензий` менеджер написал
  `теперь посчитай УХ на 500 пользователей`.

### `quote_items`

Позиции черновика КП. Поля `selected_product_*`, `price_retail`, `currency`,
`vat` и `line_sum` являются снимком выбранного продукта на момент расчёта, а не
копией прайса 1С.

```sql
CREATE TABLE quote_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_draft_id INTEGER NOT NULL,
    source_query TEXT NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,

    selected_product_code TEXT,
    selected_product_name TEXT,
    price_retail REAL,
    currency TEXT,
    vat TEXT,

    line_sum REAL,
    status TEXT NOT NULL,
    ambiguity_reason TEXT,

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (quote_draft_id)
        REFERENCES quote_drafts (id)
);
```

Статусы:

```text
pending | selected | ambiguous | not_found | removed
```

Пояснения:

- `pending` — позиция распознана, но продукт ещё не выбран окончательно:
  например, перед вызовом MCP или во время обработки.
- `selected` — позиция сопоставлена с конкретным продуктом MCP, цена и сумма
  сохранены как снимок расчёта.
- `ambiguous` — найдено несколько подходящих вариантов или не хватает
  предметного уточнения. Причина хранится в `ambiguity_reason`.
- `not_found` — по исходному запросу не удалось найти подходящий продукт через
  MCP.
- `removed` — позиция была в черновике, но менеджер попросил её убрать. Запись
  сохраняется для истории, но не участвует в итоговом КП.

### `generated_quotes`

Файлы КП, которые бот сформировал и отправил или подготовил к отправке.

```sql
CREATE TABLE generated_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_draft_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_format TEXT NOT NULL,
    total_sum REAL,
    currency TEXT,
    created_at TEXT NOT NULL,

    FOREIGN KEY (quote_draft_id)
        REFERENCES quote_drafts (id)
);
```

## Индексы

```sql
CREATE INDEX idx_conversations_user_status
ON conversations (telegram_user_id, status);

CREATE INDEX idx_conversations_chat_status
ON conversations (telegram_chat_id, status);

CREATE INDEX idx_conversations_active_draft
ON conversations (active_quote_draft_id);

CREATE INDEX idx_messages_conversation_created
ON messages (conversation_id, created_at);

CREATE INDEX idx_quote_drafts_conversation_status
ON quote_drafts (conversation_id, status);

CREATE INDEX idx_quote_drafts_updated
ON quote_drafts (updated_at);

CREATE INDEX idx_quote_items_draft
ON quote_items (quote_draft_id);

CREATE INDEX idx_generated_quotes_draft
ON generated_quotes (quote_draft_id);
```

## Типовые чтения

### Найти активный разговор

```sql
SELECT *
FROM conversations
WHERE telegram_chat_id = :telegram_chat_id
  AND telegram_user_id = :telegram_user_id
  AND status = 'active'
ORDER BY updated_at DESC
LIMIT 1;
```

### Получить активный черновик разговора

```sql
SELECT qd.*
FROM conversations c
JOIN quote_drafts qd ON qd.id = c.active_quote_draft_id
WHERE c.id = :conversation_id;
```

### Показать черновики пользователя

```sql
SELECT
    qd.id,
    qd.title,
    qd.status,
    qd.client_name,
    qd.updated_at,
    COUNT(qi.id) AS items_count,
    COALESCE(SUM(qi.line_sum), 0) AS total_sum
FROM quote_drafts qd
JOIN conversations c ON c.id = qd.conversation_id
LEFT JOIN quote_items qi ON qi.quote_draft_id = qd.id
WHERE c.telegram_user_id = :telegram_user_id
  AND qd.status IN ('collecting', 'needs_clarification', 'ready')
GROUP BY qd.id
ORDER BY qd.updated_at DESC
LIMIT 10;
```

### Проверить, что черновик принадлежит пользователю

```sql
SELECT qd.*
FROM quote_drafts qd
JOIN conversations c ON c.id = qd.conversation_id
WHERE qd.id = :draft_id
  AND c.telegram_user_id = :telegram_user_id;
```
