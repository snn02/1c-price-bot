from datetime import datetime, timezone

import aiosqlite

from price_bot.common.types import Conversation


class ConversationRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get_or_create(
        self, telegram_chat_id: int, telegram_user_pk: int
    ) -> Conversation:
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            """
            INSERT INTO conversations (telegram_chat_id, telegram_user_pk, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_chat_id, telegram_user_pk) DO NOTHING
            """,
            (telegram_chat_id, telegram_user_pk, now, now),
        )
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT * FROM conversations WHERE telegram_chat_id = ? AND telegram_user_pk = ?",
            (telegram_chat_id, telegram_user_pk),
        ) as cursor:
            row = await cursor.fetchone()
            return Conversation(**dict(row))

    async def set_active_draft(
        self, conversation_id: int, draft_id: int | None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "UPDATE conversations SET active_quote_draft_id = ?, updated_at = ? WHERE id = ?",
            (draft_id, now, conversation_id),
        )
        await self._conn.commit()

    async def get_active_draft_id(self, conversation_id: int) -> int | None:
        async with self._conn.execute(
            "SELECT active_quote_draft_id FROM conversations WHERE id = ?",
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row["active_quote_draft_id"] if row else None
