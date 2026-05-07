from datetime import datetime, timezone
from typing import Any

import aiosqlite

from price_bot.common.types import QuoteDraft


class QuoteDraftRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, conversation_id: int, title: str) -> QuoteDraft:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO quote_drafts (conversation_id, status, title, created_at, updated_at)
            VALUES (?, 'collecting', ?, ?, ?)
            """,
            (conversation_id, title, now, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        return await self._fetch(row_id)  # type: ignore[return-value]

    async def get_by_id(
        self, draft_id: int, telegram_user_id: int
    ) -> QuoteDraft | None:
        async with self._conn.execute(
            """
            SELECT qd.* FROM quote_drafts qd
            JOIN conversations c ON c.id = qd.conversation_id
            JOIN telegram_users u ON u.id = c.telegram_user_pk
            WHERE qd.id = ? AND u.telegram_user_id = ?
            """,
            (draft_id, telegram_user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return QuoteDraft(**dict(row)) if row else None

    async def get_active(self, conversation_id: int) -> QuoteDraft | None:
        async with self._conn.execute(
            """
            SELECT qd.* FROM quote_drafts qd
            JOIN conversations c ON c.id = qd.conversation_id
            WHERE c.id = ? AND c.active_quote_draft_id = qd.id
            """,
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return QuoteDraft(**dict(row)) if row else None

    async def update_status(self, draft_id: int, status: str, **kwargs: Any) -> None:
        now = datetime.now(timezone.utc).isoformat()
        set_clauses = ["status = ?", "updated_at = ?"]
        params: list[Any] = [status, now]
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        params.append(draft_id)
        await self._conn.execute(
            f"UPDATE quote_drafts SET {', '.join(set_clauses)} WHERE id = ?",
            params,
        )
        await self._conn.commit()

    async def list_active(
        self, telegram_user_id: int, limit: int = 10
    ) -> list[QuoteDraft]:
        async with self._conn.execute(
            """
            SELECT qd.* FROM quote_drafts qd
            JOIN conversations c ON c.id = qd.conversation_id
            JOIN telegram_users u ON u.id = c.telegram_user_pk
            WHERE u.telegram_user_id = ?
              AND qd.status IN ('collecting', 'needs_clarification', 'ready')
            ORDER BY qd.updated_at DESC
            LIMIT ?
            """,
            (telegram_user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [QuoteDraft(**dict(r)) for r in rows]

    async def find_by_query(
        self, telegram_user_id: int, query: str
    ) -> list[QuoteDraft]:
        like = f"%{query}%"
        async with self._conn.execute(
            """
            SELECT qd.* FROM quote_drafts qd
            JOIN conversations c ON c.id = qd.conversation_id
            JOIN telegram_users u ON u.id = c.telegram_user_pk
            WHERE u.telegram_user_id = ?
              AND qd.status IN ('collecting', 'needs_clarification', 'ready')
              AND (qd.title LIKE ? OR qd.client_name LIKE ? OR qd.manager_note LIKE ?)
            ORDER BY qd.updated_at DESC
            """,
            (telegram_user_id, like, like, like),
        ) as cursor:
            rows = await cursor.fetchall()
            return [QuoteDraft(**dict(r)) for r in rows]

    async def _fetch(self, draft_id: int) -> QuoteDraft | None:
        async with self._conn.execute(
            "SELECT * FROM quote_drafts WHERE id = ?", (draft_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return QuoteDraft(**dict(row)) if row else None
