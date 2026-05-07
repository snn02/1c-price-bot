from datetime import datetime, timezone

import aiosqlite

from price_bot.common.types import GeneratedQuote


class GeneratedQuoteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def save(
        self, draft_id: int, file_path: str, total_sum: float
    ) -> GeneratedQuote:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO generated_quotes (quote_draft_id, file_path, file_format, total_sum, created_at)
            VALUES (?, ?, 'md', ?, ?)
            """,
            (draft_id, file_path, total_sum, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        async with self._conn.execute(
            "SELECT * FROM generated_quotes WHERE id = ?", (row_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return GeneratedQuote(**dict(row))
