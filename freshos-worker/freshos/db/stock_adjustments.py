from __future__ import annotations

import json
from collections.abc import Sequence

from freshos.config import Settings
from freshos.db.connection import connect
from freshos.importers.stock_adjustments import StockAdjustmentRow


def upsert_stock_count_adjustments(settings: Settings, rows: Sequence[StockAdjustmentRow]) -> dict[str, int]:
    if not rows:
        return {"inserted": 0, "exceptions": 0}

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            stores = _fetch_stores(cur)
            products = _fetch_products(cur)
            values = []
            exceptions = []
            for row in rows:
                store_id = _match_entity(row.store_code, row.store_name, stores)
                product_id = _match_entity(row.product_code, row.product_name, products)
                if store_id and product_id:
                    values.append(
                        (
                            store_id,
                            product_id,
                            row.count_time,
                            row.business_date,
                            row.adjusted_quantity,
                            row.unit,
                            row.count_type,
                            row.remark,
                        )
                    )
                else:
                    exception_type = "unmatched_store" if not store_id else "unmatched_product"
                    exceptions.append((row, exception_type))

            _upsert_adjustments(cur, values)
            _upsert_exceptions(cur, exceptions)
            return {"inserted": len(values), "exceptions": len(exceptions)}


def _fetch_stores(cur) -> dict[str, dict[str, str]]:
    cur.execute("SELECT id::text, store_code, store_name FROM stores WHERE is_active = true")
    return _entity_maps(cur.fetchall())


def _fetch_products(cur) -> dict[str, dict[str, str]]:
    cur.execute("SELECT id::text, product_code, product_name FROM products WHERE is_active = true")
    return _entity_maps(cur.fetchall())


def _entity_maps(rows) -> dict[str, dict[str, str]]:
    by_code = {}
    by_name = {}
    for row in rows:
        entity_id, code, name = row
        if code:
            by_code[str(code)] = entity_id
        if name:
            by_name[str(name).strip()] = entity_id
    return {"by_code": by_code, "by_name": by_name}


def _match_entity(code: str, name: str, maps: dict[str, dict[str, str]]) -> str | None:
    if code and code in maps["by_code"]:
        return maps["by_code"][code]
    if name and name in maps["by_name"]:
        return maps["by_name"][name]
    return None


def _upsert_adjustments(cur, values) -> None:
    if not values:
        return
    sql = """
        INSERT INTO stock_count_adjustments (
            store_id,
            product_id,
            count_time,
            business_date,
            adjusted_quantity,
            unit,
            count_type,
            remark
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, count_time)
        DO UPDATE SET
            business_date = EXCLUDED.business_date,
            adjusted_quantity = EXCLUDED.adjusted_quantity,
            unit = EXCLUDED.unit,
            count_type = EXCLUDED.count_type,
            remark = EXCLUDED.remark
    """
    cur.executemany(sql, values)


def _upsert_exceptions(cur, exceptions) -> None:
    if not exceptions:
        return
    sql = """
        INSERT INTO import_exceptions (
            source_file_name,
            source_table,
            raw_row_number,
            exception_type,
            exception_message,
            raw_payload
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (source_file_name, source_table, raw_row_number, exception_type)
        DO UPDATE SET
            exception_message = EXCLUDED.exception_message,
            raw_payload = EXCLUDED.raw_payload,
            status = 'open',
            created_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                row.source_file_name,
                "stock_count_adjustments",
                row.raw_row_number,
                exception_type,
                _exception_message(row, exception_type),
                json.dumps(row.to_dict(), ensure_ascii=False),
            )
            for row, exception_type in exceptions
        ],
    )


def _exception_message(row: StockAdjustmentRow, exception_type: str) -> str:
    if exception_type == "unmatched_store":
        return f"盘点修正门店无法匹配: {row.store_code or row.store_name}"
    return f"盘点修正商品无法匹配: {row.product_code or row.product_name}"
