import aiosqlite

from price_bot.common.config import Settings


async def get_connection(settings: Settings) -> aiosqlite.Connection:
    import pathlib
    pathlib.Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(settings.db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("PRAGMA journal_mode = WAL")
    await conn.execute("PRAGMA busy_timeout = 5000")
    return conn


async def init_db(conn: aiosqlite.Connection) -> None:
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_chat_id INTEGER NOT NULL,
            telegram_user_pk INTEGER NOT NULL,
            active_quote_draft_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            UNIQUE (telegram_chat_id, telegram_user_pk),

            FOREIGN KEY (telegram_user_pk)
                REFERENCES telegram_users (id),
            FOREIGN KEY (active_quote_draft_id)
                REFERENCES quote_drafts (id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            telegram_message_id INTEGER,
            direction TEXT NOT NULL CHECK (direction IN ('in', 'out')),
            role TEXT NOT NULL CHECK (role IN ('manager', 'bot', 'system')),
            text TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
                REFERENCES conversations (id)
        );

        CREATE TABLE IF NOT EXISTS quote_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN (
                    'collecting',
                    'needs_clarification',
                    'ready',
                    'generated',
                    'cancelled',
                    'superseded'
                )
            ),
            title TEXT,
            client_name TEXT,
            manager_note TEXT,
            clarification_question TEXT,
            clarification_kind TEXT CHECK (
                clarification_kind IN (
                    'client_name',
                    'product_choice',
                    'bundle_choice',
                    'generic'
                )
                OR clarification_kind IS NULL
            ),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
                REFERENCES conversations (id)
        );

        CREATE TABLE IF NOT EXISTS quote_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_draft_id INTEGER NOT NULL,
            source_query TEXT NOT NULL,
            qty INTEGER NOT NULL DEFAULT 1,
            selected_product_code TEXT,
            selected_product_name TEXT,
            price_retail REAL,
            vat TEXT,
            line_sum REAL,
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'selected', 'ambiguous', 'not_found', 'removed')
            ),
            ambiguity_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (quote_draft_id)
                REFERENCES quote_drafts (id)
        );

        CREATE TABLE IF NOT EXISTS generated_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_draft_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_format TEXT NOT NULL CHECK (file_format IN ('md')),
            total_sum REAL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (quote_draft_id)
                REFERENCES quote_drafts (id)
        );

        CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations (telegram_user_pk);

        CREATE INDEX IF NOT EXISTS idx_conversations_chat_user
            ON conversations (telegram_chat_id, telegram_user_pk);

        CREATE INDEX IF NOT EXISTS idx_conversations_active_draft
            ON conversations (active_quote_draft_id);

        CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
            ON messages (conversation_id, created_at);

        CREATE INDEX IF NOT EXISTS idx_quote_drafts_conversation_status
            ON quote_drafts (conversation_id, status);

        CREATE INDEX IF NOT EXISTS idx_quote_drafts_updated
            ON quote_drafts (updated_at);

        CREATE INDEX IF NOT EXISTS idx_quote_items_draft
            ON quote_items (quote_draft_id);

        CREATE INDEX IF NOT EXISTS idx_generated_quotes_draft
            ON generated_quotes (quote_draft_id);
    """)
    await conn.commit()
