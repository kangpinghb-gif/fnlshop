from __future__ import annotations

from collections.abc import Sequence

from freshos.config import Settings
from freshos.db.connection import connect
from freshos.importers.dabiaoge_daily import DabiaogeDailyRow


def upsert_dabiaoge_daily(settings: Settings, rows: Sequence[DabiaogeDailyRow], *, report_type: str) -> int:
    if not rows:
        return 0
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            store_ids = _fetch_store_ids(cur, sorted({row.store_code for row in rows}))
            product_ids = _fetch_product_ids(cur, sorted({row.product_code for row in rows}))
            values = [
                (row, store_ids.get(row.store_code), product_ids.get(row.product_code))
                for row in rows
                if store_ids.get(row.store_code) and product_ids.get(row.product_code)
            ]
            if report_type == "sales":
                _upsert_sales(cur, values)
            elif report_type == "inventory_loss":
                _upsert_inventory_loss(cur, values)
            elif report_type == "purchase_receipts":
                _upsert_purchase_receipts(cur, values)
            elif report_type == "inventory_snapshot":
                _upsert_inventory_snapshots(cur, values)
            else:
                raise ValueError(f"Unsupported report_type: {report_type}")
            return len(values)


def _fetch_store_ids(cur, store_codes: list[str]) -> dict[str, str]:
    if not store_codes:
        return {}
    cur.execute("SELECT store_code, id::text FROM stores WHERE store_code = ANY(%s)", (store_codes,))
    return {row[0]: row[1] for row in cur.fetchall()}


def _fetch_product_ids(cur, product_codes: list[str]) -> dict[str, str]:
    if not product_codes:
        return {}
    cur.execute("SELECT product_code, id::text FROM products WHERE product_code = ANY(%s)", (product_codes,))
    return {row[0]: row[1] for row in cur.fetchall()}


def _upsert_sales(cur, values) -> None:
    sql = """
        INSERT INTO sales_daily (
            store_id, product_id, business_date, sales_quantity, sales_amount, unit, source_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, business_date)
        DO UPDATE SET
            sales_quantity = EXCLUDED.sales_quantity,
            sales_amount = EXCLUDED.sales_amount,
            unit = EXCLUDED.unit,
            source_file = EXCLUDED.source_file,
            imported_at = now()
    """
    cur.executemany(
        sql,
        [
            (store_id, product_id, row.business_date, row.sales_quantity or 0, row.sales_amount or 0, row.unit, row.source_file)
            for row, store_id, product_id in values
        ],
    )


def _upsert_inventory_loss(cur, values) -> None:
    sql = """
        INSERT INTO inventory_loss_daily (
            store_id, product_id, business_date, closing_stock_qty, loss_quantity,
            loss_amount, inventory_difference_qty, unit, source_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, business_date)
        DO UPDATE SET
            closing_stock_qty = EXCLUDED.closing_stock_qty,
            loss_quantity = EXCLUDED.loss_quantity,
            loss_amount = EXCLUDED.loss_amount,
            inventory_difference_qty = EXCLUDED.inventory_difference_qty,
            unit = EXCLUDED.unit,
            source_file = EXCLUDED.source_file,
            imported_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                store_id,
                product_id,
                row.business_date,
                row.closing_stock_qty,
                row.loss_quantity,
                row.loss_amount,
                row.inventory_difference_qty,
                row.unit,
                row.source_file,
            )
            for row, store_id, product_id in values
        ],
    )


def _upsert_purchase_receipts(cur, values) -> None:
    sql = """
        INSERT INTO purchase_receipts_daily (
            store_id, product_id, business_date, order_quantity, receive_quantity,
            total_receive_quantity, total_return_quantity, unit, source_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, business_date)
        DO UPDATE SET
            order_quantity = EXCLUDED.order_quantity,
            receive_quantity = EXCLUDED.receive_quantity,
            total_receive_quantity = EXCLUDED.total_receive_quantity,
            total_return_quantity = EXCLUDED.total_return_quantity,
            unit = EXCLUDED.unit,
            source_file = EXCLUDED.source_file,
            imported_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                store_id,
                product_id,
                row.business_date,
                row.order_quantity,
                row.receive_quantity,
                row.total_receive_quantity,
                row.total_return_quantity,
                row.unit,
                row.source_file,
            )
            for row, store_id, product_id in values
        ],
    )


def _upsert_inventory_snapshots(cur, values) -> None:
    sql = """
        INSERT INTO inventory_snapshots (
            store_id, product_id, snapshot_time, business_date, inventory_quantity,
            inventory_source, unit, source_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, snapshot_time, inventory_source)
        DO UPDATE SET
            inventory_quantity = EXCLUDED.inventory_quantity,
            unit = EXCLUDED.unit,
            source_file = EXCLUDED.source_file,
            imported_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                store_id,
                product_id,
                row.snapshot_time,
                row.business_date,
                row.inventory_quantity or 0,
                row.inventory_source or "realtime",
                row.unit,
                row.source_file,
            )
            for row, store_id, product_id in values
        ],
    )

