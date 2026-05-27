from __future__ import annotations

from freshos.config import Settings
from freshos.db.connection import connect
from freshos.importers.dabiaoge_base import DabiaogeBaseImportResult


def upsert_dabiaoge_base(settings: Settings, result: DabiaogeBaseImportResult) -> dict[str, int]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            _upsert_stores(cur, result)
            _upsert_products(cur, result)
            store_ids = _fetch_store_ids(cur, [row.store_code for row in result.stores])
            product_ids = _fetch_product_ids(cur, [row.product_code for row in result.products])
            _upsert_store_products(cur, result, store_ids, product_ids)
    return {
        "stores": len(result.stores),
        "products": len(result.products),
        "store_products": len(result.store_products),
    }


def _upsert_stores(cur, result: DabiaogeBaseImportResult) -> None:
    sql = """
        INSERT INTO stores (store_code, store_name, store_status)
        VALUES (%s, %s, %s)
        ON CONFLICT (store_code)
        DO UPDATE SET
            store_name = EXCLUDED.store_name,
            store_status = EXCLUDED.store_status,
            updated_at = now()
    """
    cur.executemany(sql, [(row.store_code, row.store_name, row.store_status) for row in result.stores])


def _upsert_products(cur, result: DabiaogeBaseImportResult) -> None:
    sql = """
        INSERT INTO products (
            product_code,
            product_name,
            barcode,
            cat_id_01,
            cat_name_01,
            cat_id_02,
            cat_name_02,
            sale_unit,
            fresh_attribute,
            shelf_life_days
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_code)
        DO UPDATE SET
            product_name = EXCLUDED.product_name,
            barcode = EXCLUDED.barcode,
            cat_id_01 = EXCLUDED.cat_id_01,
            cat_name_01 = EXCLUDED.cat_name_01,
            cat_id_02 = EXCLUDED.cat_id_02,
            cat_name_02 = EXCLUDED.cat_name_02,
            sale_unit = EXCLUDED.sale_unit,
            fresh_attribute = EXCLUDED.fresh_attribute,
            shelf_life_days = EXCLUDED.shelf_life_days,
            updated_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                row.product_code,
                row.product_name,
                row.barcode,
                row.cat_id_01,
                row.cat_name_01,
                row.cat_id_02,
                row.cat_name_02,
                row.sale_unit,
                row.fresh_attribute,
                row.shelf_life_days,
            )
            for row in result.products
        ],
    )


def _fetch_store_ids(cur, store_codes: list[str]) -> dict[str, str]:
    if not store_codes:
        return {}
    cur.execute(
        "SELECT store_code, id::text FROM stores WHERE store_code = ANY(%s)",
        (store_codes,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def _fetch_product_ids(cur, product_codes: list[str]) -> dict[str, str]:
    if not product_codes:
        return {}
    cur.execute(
        "SELECT product_code, id::text FROM products WHERE product_code = ANY(%s)",
        (product_codes,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def _upsert_store_products(
    cur,
    result: DabiaogeBaseImportResult,
    store_ids: dict[str, str],
    product_ids: dict[str, str],
) -> None:
    sql = """
        INSERT INTO store_products (
            store_id,
            product_id,
            store_order_status,
            store_sale_status,
            is_orderable,
            is_sellable,
            package_size,
            order_batch_qty,
            safety_stock_days,
            recent_daily_sales,
            store_stock_qty_yesterday
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id)
        DO UPDATE SET
            store_order_status = EXCLUDED.store_order_status,
            store_sale_status = EXCLUDED.store_sale_status,
            is_orderable = EXCLUDED.is_orderable,
            is_sellable = EXCLUDED.is_sellable,
            package_size = EXCLUDED.package_size,
            order_batch_qty = EXCLUDED.order_batch_qty,
            safety_stock_days = EXCLUDED.safety_stock_days,
            recent_daily_sales = EXCLUDED.recent_daily_sales,
            store_stock_qty_yesterday = EXCLUDED.store_stock_qty_yesterday,
            updated_at = now()
    """
    values = []
    for row in result.store_products:
        store_id = store_ids.get(row.store_code)
        product_id = product_ids.get(row.product_code)
        if not store_id or not product_id:
            continue
        values.append(
            (
                store_id,
                product_id,
                row.store_order_status,
                row.store_sale_status,
                row.is_orderable,
                row.is_sellable,
                row.package_size,
                row.order_batch_qty,
                row.safety_stock_days,
                row.recent_daily_sales,
                row.store_stock_qty_yesterday,
            )
        )
    cur.executemany(sql, values)

