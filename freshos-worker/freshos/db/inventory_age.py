from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from freshos.config import Settings
from freshos.db.connection import connect


@dataclass(frozen=True)
class ArrivalBatch:
    store_id: str
    product_id: str
    arrival_date: date
    batch_quantity: float
    sellable_days: float
    unit: str


@dataclass(frozen=True)
class InventoryAgeBatch:
    store_id: str
    product_id: str
    arrival_date: date
    batch_quantity: float
    consumed_quantity: float
    remaining_quantity: float
    sellable_days: float
    expiry_date: date
    remaining_sellable_days: float
    batch_status: str
    unit: str


def calculate_inventory_age_batches(settings: Settings, *, business_date: str) -> int:
    target_date = date.fromisoformat(business_date)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            arrival_batches = _fetch_arrival_batches(cur, target_date)
            sales_by_key = _fetch_sales_since_first_arrival(cur, arrival_batches, target_date)
            calculated = allocate_fifo_batches(
                arrival_batches,
                sales_by_key=sales_by_key,
                business_date=target_date,
            )
            _upsert_inventory_age_batches(cur, calculated)
            return len(calculated)


def allocate_fifo_batches(
    batches: list[ArrivalBatch],
    *,
    sales_by_key: dict[tuple[str, str], float],
    business_date: date,
) -> list[InventoryAgeBatch]:
    grouped: dict[tuple[str, str], list[ArrivalBatch]] = defaultdict(list)
    for batch in batches:
        grouped[(batch.store_id, batch.product_id)].append(batch)

    results: list[InventoryAgeBatch] = []
    for key, key_batches in grouped.items():
        remaining_sales = sales_by_key.get(key, 0.0)
        for batch in sorted(key_batches, key=lambda item: item.arrival_date):
            consumed = min(batch.batch_quantity, max(remaining_sales, 0.0))
            remaining_sales -= consumed
            remaining_quantity = max(batch.batch_quantity - consumed, 0.0)
            expiry_date = batch.arrival_date + timedelta(days=int(batch.sellable_days))
            remaining_sellable_days = (expiry_date - business_date).days
            results.append(
                InventoryAgeBatch(
                    store_id=batch.store_id,
                    product_id=batch.product_id,
                    arrival_date=batch.arrival_date,
                    batch_quantity=round(batch.batch_quantity, 3),
                    consumed_quantity=round(consumed, 3),
                    remaining_quantity=round(remaining_quantity, 3),
                    sellable_days=batch.sellable_days,
                    expiry_date=expiry_date,
                    remaining_sellable_days=remaining_sellable_days,
                    batch_status=_batch_status(remaining_sellable_days),
                    unit=batch.unit,
                )
            )
    return results


def _fetch_arrival_batches(cur, business_date: date) -> list[ArrivalBatch]:
    cur.execute(
        """
        SELECT
            foi.store_id::text,
            foi.product_id::text,
            foi.arrival_date,
            SUM(foi.arrival_quantity) AS batch_quantity,
            COALESCE(sp.sellable_days_override, p.sellable_days, p.shelf_life_days, 1) AS sellable_days,
            p.sale_unit
        FROM fresh_order_imports foi
        JOIN products p ON p.id = foi.product_id
        LEFT JOIN store_products sp
          ON sp.store_id = foi.store_id
         AND sp.product_id = foi.product_id
        WHERE foi.arrival_date <= %s
          AND foi.store_id IS NOT NULL
          AND foi.product_id IS NOT NULL
          AND foi.match_status = 'matched'
        GROUP BY
            foi.store_id,
            foi.product_id,
            foi.arrival_date,
            COALESCE(sp.sellable_days_override, p.sellable_days, p.shelf_life_days, 1),
            p.sale_unit
        ORDER BY foi.store_id, foi.product_id, foi.arrival_date
        """,
        (business_date,),
    )
    return [
        ArrivalBatch(
            store_id=row[0],
            product_id=row[1],
            arrival_date=row[2],
            batch_quantity=float(row[3] or 0),
            sellable_days=float(row[4] or 1),
            unit=row[5] or "kg",
        )
        for row in cur.fetchall()
        if row[3] is not None and float(row[3]) > 0
    ]


def _fetch_sales_since_first_arrival(
    cur,
    batches: list[ArrivalBatch],
    business_date: date,
) -> dict[tuple[str, str], float]:
    if not batches:
        return {}
    first_arrival = min(batch.arrival_date for batch in batches)
    cur.execute(
        """
        SELECT store_id::text, product_id::text, COALESCE(SUM(sales_quantity), 0)
        FROM sales_daily
        WHERE business_date >= %s
          AND business_date <= %s
        GROUP BY store_id, product_id
        """,
        (first_arrival, business_date),
    )
    return {
        (row[0], row[1]): float(row[2] or 0)
        for row in cur.fetchall()
    }


def _upsert_inventory_age_batches(cur, rows: list[InventoryAgeBatch]) -> None:
    if not rows:
        return
    sql = """
        INSERT INTO inventory_age_batches (
            store_id,
            product_id,
            arrival_date,
            batch_quantity,
            consumed_quantity,
            remaining_quantity,
            sellable_days,
            expiry_date,
            remaining_sellable_days,
            batch_status,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, arrival_date)
        DO UPDATE SET
            batch_quantity = EXCLUDED.batch_quantity,
            consumed_quantity = EXCLUDED.consumed_quantity,
            remaining_quantity = EXCLUDED.remaining_quantity,
            sellable_days = EXCLUDED.sellable_days,
            expiry_date = EXCLUDED.expiry_date,
            remaining_sellable_days = EXCLUDED.remaining_sellable_days,
            batch_status = EXCLUDED.batch_status,
            unit = EXCLUDED.unit,
            calculated_at = now()
    """
    cur.executemany(
        sql,
        [
            (
                row.store_id,
                row.product_id,
                row.arrival_date,
                row.batch_quantity,
                row.consumed_quantity,
                row.remaining_quantity,
                row.sellable_days,
                row.expiry_date,
                row.remaining_sellable_days,
                row.batch_status,
                row.unit,
            )
            for row in rows
        ],
    )


def _batch_status(remaining_sellable_days: float) -> str:
    if remaining_sellable_days <= 0:
        return "expired"
    if remaining_sellable_days <= 1:
        return "near_expiry"
    return "sellable"
