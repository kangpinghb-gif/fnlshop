from __future__ import annotations

from dataclasses import dataclass
import json

from freshos.config import Settings
from freshos.db.connection import connect
from freshos.matching.order_matching import EntityRecord, match_order_row


@dataclass(frozen=True)
class PendingOrderRow:
    id: str
    source_file_name: str
    raw_row_number: int
    store_name_raw: str
    product_name_raw: str


def match_pending_order_imports(settings: Settings, *, limit: int = 1000) -> dict[str, int]:
    stores = _fetch_stores(settings)
    products = _fetch_products(settings)
    pending_rows = _fetch_pending_order_rows(settings, limit=limit)

    matched = 0
    failed = 0
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            for row in pending_rows:
                result = match_order_row(
                    store_name_raw=row.store_name_raw,
                    product_name_raw=row.product_name_raw,
                    stores=stores,
                    products=products,
                )
                cur.execute(
                    """
                    UPDATE fresh_order_imports
                    SET store_id = %s,
                        product_id = %s,
                        match_status = %s
                    WHERE id = %s
                    """,
                    (result.store_id, result.product_id, result.match_status, row.id),
                )
                if result.match_status == "matched":
                    matched += 1
                else:
                    failed += 1
                    for exception_type in result.exception_types:
                        _insert_import_exception(cur, row, exception_type)

    return {"total": len(pending_rows), "matched": matched, "failed": failed}


def _fetch_stores(settings: Settings) -> list[EntityRecord]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id::text, store_code, store_name FROM stores WHERE is_active = true")
            return [EntityRecord(id=row[0], code=row[1] or "", name=row[2] or "") for row in cur.fetchall()]


def _fetch_products(settings: Settings) -> list[EntityRecord]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id::text, product_code, product_name FROM products WHERE is_active = true")
            return [EntityRecord(id=row[0], code=row[1] or "", name=row[2] or "") for row in cur.fetchall()]


def _fetch_pending_order_rows(settings: Settings, *, limit: int) -> list[PendingOrderRow]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id::text, source_file_name, raw_row_number, store_name_raw, product_name_raw
                FROM fresh_order_imports
                WHERE match_status IN ('pending', 'failed')
                ORDER BY imported_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [
                PendingOrderRow(
                    id=row[0],
                    source_file_name=row[1],
                    raw_row_number=row[2],
                    store_name_raw=row[3] or "",
                    product_name_raw=row[4] or "",
                )
                for row in cur.fetchall()
            ]


def _insert_import_exception(cur, row: PendingOrderRow, exception_type: str) -> None:
    message = {
        "unmatched_store": f"门店无法匹配：{row.store_name_raw}",
        "unmatched_product": f"商品无法匹配：{row.product_name_raw}",
    }.get(exception_type, exception_type)
    payload = {
        "fresh_order_import_id": row.id,
        "store_name_raw": row.store_name_raw,
        "product_name_raw": row.product_name_raw,
    }
    cur.execute(
        """
        INSERT INTO import_exceptions (
            source_file_name,
            source_table,
            raw_row_number,
            exception_type,
            exception_message,
            raw_payload,
            status
        )
        VALUES (%s, 'fresh_order_imports', %s, %s, %s, %s::jsonb, 'open')
        ON CONFLICT (source_file_name, source_table, raw_row_number, exception_type)
        DO UPDATE SET
            exception_message = EXCLUDED.exception_message,
            raw_payload = EXCLUDED.raw_payload,
            status = 'open'
        """,
        (
            row.source_file_name,
            row.raw_row_number,
            exception_type,
            message,
            json.dumps(payload, ensure_ascii=False),
        ),
    )
