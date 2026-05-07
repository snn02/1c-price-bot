from datetime import datetime, timezone

import aiosqlite

from price_bot.common.types import Message


class MessageRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save(
        self,
        conversation_id: int,
        telegram_message_id: int | None,
        direction: str,
        role: str,
        text: str,
    ) -> Message:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO messages (conversation_id, telegram_message_id, direction, role, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (conversation_id, telegram_message_id, direction, role, text, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT * FROM messages WHERE id = ?", (row_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return Message(**dict(row))

    async def get_last_n(self, conversation_id: int, n: int) -> list[Message]:
        async with self._conn.execute(
            """
            SELECT * FROM (
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ) ORDER BY created_at ASC
            """,
            (conversation_id, n),
        ) as cursor:
            rows = await cursor.fetchall()
            return [Message(**dict(r)) for r in rows]
