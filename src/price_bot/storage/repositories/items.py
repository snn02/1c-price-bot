from datetime import datetime, timezone

import aiosqlite

from price_bot.common.types import Product, QuoteItem


class QuoteItemRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def insert_selected(
        self,
        draft_id: int,
        source_query: str,
        qty: int,
        product: Product,
        line_sum: float,
    ) -> QuoteItem:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO quote_items (
                quote_draft_id, source_query, qty,
                selected_product_code, selected_product_name,
                price_retail, vat, line_sum,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'selected', ?, ?)
            """,
            (
                draft_id,
                source_query,
                qty,
                product.code,
                product.name,
                product.price_retail,
                product.vat,
                line_sum,
                now,
                now,
            ),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        return await self._fetch(row_id)  # type: ignore[return-value]

    async def insert_ambiguous(
        self,
        draft_id: int,
        source_query: str,
        qty: int,
        ambiguity_reason: str,
    ) -> QuoteItem:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO quote_items (
                quote_draft_id, source_query, qty,
                status, ambiguity_reason, created_at, updated_at
            ) VALUES (?, ?, ?, 'ambiguous', ?, ?, ?)
            """,
            (draft_id, source_query, qty, ambiguity_reason, now, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        return await self._fetch(row_id)  # type: ignore[return-value]

    async def insert_not_found(
        self, draft_id: int, source_query: str, qty: int
    ) -> QuoteItem:
        now = datetime.now(timezone.utc).isoformat()
        async with self._conn.execute(
            """
            INSERT INTO quote_items (
                quote_draft_id, source_query, qty,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, 'not_found', ?, ?)
            """,
            (draft_id, source_query, qty, now, now),
        ) as cursor:
            row_id = cursor.lastrowid
        await self._conn.commit()
        return await self._fetch(row_id)  # type: ignore[return-value]

    async def get_by_draft(
        self, draft_id: int, exclude_removed: bool = True
    ) -> list[QuoteItem]:
        if exclude_removed:
            query = "SELECT * FROM quote_items WHERE quote_draft_id = ? AND status != 'removed' ORDER BY id"
        else:
            query = "SELECT * FROM quote_items WHERE quote_draft_id = ? ORDER BY id"
        async with self._conn.execute(query, (draft_id,)) as cursor:
            rows = await cursor.fetchall()
            return [QuoteItem(**dict(r)) for r in rows]

    async def set_removed(self, draft_id: int, target_like: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        like = f"%{target_like}%"
        async with self._conn.execute(
            """
            UPDATE quote_items SET status = 'removed', updated_at = ?
            WHERE quote_draft_id = ?
              AND status != 'removed'
              AND (source_query LIKE ? OR selected_product_name LIKE ? OR selected_product_code LIKE ?)
            """,
            (now, draft_id, like, like, like),
        ) as cursor:
            count = cursor.rowcount
        await self._conn.commit()
        return count

    async def find_matching(self, draft_id: int, target_like: str) -> list[QuoteItem]:
        like = f"%{target_like}%"
        async with self._conn.execute(
            """
            SELECT * FROM quote_items
            WHERE quote_draft_id = ?
              AND status != 'removed'
              AND (source_query LIKE ? OR selected_product_name LIKE ? OR selected_product_code LIKE ?)
            ORDER BY id
            """,
            (draft_id, like, like, like),
        ) as cursor:
            rows = await cursor.fetchall()
            return [QuoteItem(**dict(r)) for r in rows]

    async def update_to_selected(
        self, item_id: int, product: Product, line_sum: float
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            """
            UPDATE quote_items SET
                status = 'selected',
                selected_product_code = ?,
                selected_product_name = ?,
                price_retail = ?,
                vat = ?,
                line_sum = ?,
                ambiguity_reason = NULL,
                updated_at = ?
            WHERE id = ?
            """,
            (product.code, product.name, product.price_retail, product.vat, line_sum, now, item_id),
        )
        await self._conn.commit()

    async def _fetch(self, item_id: int) -> QuoteItem | None:
        async with self._conn.execute(
            "SELECT * FROM quote_items WHERE id = ?", (item_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return QuoteItem(**dict(row)) if row else None
