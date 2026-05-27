from __future__ import annotations

from datetime import date, timedelta

from freshos.calculators.inventory import calculate_inventory_position
from freshos.config import Settings
from freshos.db.connection import connect


def calculate_inventory_positions(settings: Settings, *, business_date: str) -> int:
    target_date = date.fromisoformat(business_date)
    previous_date = target_date - timedelta(days=1)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            candidates = _fetch_candidate_store_products(cur)
            realtime = _fetch_realtime_inventory(cur, target_date)
            closing = _fetch_closing_inventory(cur, target_date)
            previous_positions = _fetch_previous_positions(cur, previous_date)
            receipts = _fetch_receipts(cur, target_date)
            sales = _fetch_sales(cur, target_date)
            losses = _fetch_losses(cur, target_date)
            manual_adjustments = _fetch_manual_adjustments(cur, target_date)

            rows = []
            for candidate in candidates:
                key = (candidate["store_id"], candidate["product_id"])
                theoretical = _calculate_theoretical_inventory(
                    previous_positions.get(key),
                    receipts.get(key),
                    sales.get(key),
                    losses.get(key),
                )
                position = calculate_inventory_position(
                    realtime_inventory_qty=realtime.get(key),
                    closing_inventory_qty=closing.get(key),
                    theoretical_inventory_qty=theoretical,
                    manual_adjustment_qty=manual_adjustments.get(key),
                )
                rows.append(
                    (
                        candidate["store_id"],
                        candidate["product_id"],
                        business_date,
                        realtime.get(key),
                        closing.get(key),
                        theoretical,
                        manual_adjustments.get(key),
                        position.corrected_inventory_qty,
                        position.inventory_confidence,
                        position.inventory_source,
                        candidate["unit"],
                    )
                )
            _upsert_inventory_positions(cur, rows)
            return len(rows)


def _fetch_candidate_store_products(cur) -> list[dict[str, str]]:
    cur.execute(
        """
        SELECT sp.store_id::text, sp.product_id::text, p.sale_unit
        FROM store_products sp
        JOIN products p ON p.id = sp.product_id
        WHERE sp.is_active = true
          AND sp.is_sellable = true
        """
    )
    return [
        {"store_id": row[0], "product_id": row[1], "unit": row[2] or "kg"}
        for row in cur.fetchall()
    ]


def _fetch_realtime_inventory(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT DISTINCT ON (store_id, product_id)
            store_id::text,
            product_id::text,
            inventory_quantity
        FROM inventory_snapshots
        WHERE business_date = %s
        ORDER BY store_id, product_id, snapshot_time DESC
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_closing_inventory(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, closing_stock_qty
        FROM inventory_loss_daily
        WHERE business_date = %s
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_previous_positions(cur, previous_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, corrected_inventory_qty
        FROM inventory_positions
        WHERE business_date = %s
        """,
        (previous_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_receipts(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, COALESCE(SUM(arrival_quantity), 0)
        FROM fresh_order_imports
        WHERE arrival_date = %s
          AND store_id IS NOT NULL
          AND product_id IS NOT NULL
        GROUP BY store_id, product_id
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_sales(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, sales_quantity
        FROM sales_daily
        WHERE business_date = %s
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_losses(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, loss_quantity
        FROM inventory_loss_daily
        WHERE business_date = %s
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _fetch_manual_adjustments(cur, business_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, COALESCE(SUM(adjusted_quantity), 0)
        FROM stock_count_adjustments
        WHERE business_date = %s
        GROUP BY store_id, product_id
        """,
        (business_date,),
    )
    return _quantity_map(cur.fetchall())


def _quantity_map(rows) -> dict[tuple[str, str], float]:
    result: dict[tuple[str, str], float] = {}
    for row in rows:
        if row[2] is not None:
            result[(row[0], row[1])] = float(row[2])
    return result


def _calculate_theoretical_inventory(
    previous_inventory: float | None,
    receipt_qty: float | None,
    sales_qty: float | None,
    loss_qty: float | None,
) -> float | None:
    if previous_inventory is None:
        return None
    return previous_inventory + (receipt_qty or 0.0) - (sales_qty or 0.0) - (loss_qty or 0.0)


def _upsert_inventory_positions(cur, rows) -> None:
    sql = """
        INSERT INTO inventory_positions (
            store_id,
            product_id,
            business_date,
            realtime_inventory_qty,
            closing_inventory_qty,
            theoretical_inventory_qty,
            manual_adjustment_qty,
            corrected_inventory_qty,
            inventory_confidence,
            inventory_source,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, business_date)
        DO UPDATE SET
            realtime_inventory_qty = EXCLUDED.realtime_inventory_qty,
            closing_inventory_qty = EXCLUDED.closing_inventory_qty,
            theoretical_inventory_qty = EXCLUDED.theoretical_inventory_qty,
            manual_adjustment_qty = EXCLUDED.manual_adjustment_qty,
            corrected_inventory_qty = EXCLUDED.corrected_inventory_qty,
            inventory_confidence = EXCLUDED.inventory_confidence,
            inventory_source = EXCLUDED.inventory_source,
            unit = EXCLUDED.unit,
            calculated_at = now()
    """
    cur.executemany(sql, rows)
