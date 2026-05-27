from __future__ import annotations

from datetime import date, timedelta

from freshos.calculators.orders import calculate_order_suggestion
from freshos.config import Settings
from freshos.db.connection import connect


def generate_order_suggestions(settings: Settings, *, suggestion_date: str) -> int:
    target_date = date.fromisoformat(suggestion_date)
    arrival_date = target_date + timedelta(days=1)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            candidates = _fetch_candidates(cur, target_date)
            pending_arrivals = _fetch_pending_arrivals(cur, target_date, arrival_date)
            rows = []
            for candidate in candidates:
                key = (candidate["store_id"], candidate["product_id"])
                forecast_quantity = candidate["forecast_quantity"]
                safety_stock_qty = max(
                    forecast_quantity * candidate["safety_stock_days"],
                    candidate["sales_stddev"],
                )
                pending_arrival_qty = pending_arrivals.get(key, 0.0)
                suggestion = calculate_order_suggestion(
                    is_orderable=candidate["is_orderable"],
                    is_sellable=candidate["is_sellable"],
                    forecast_quantity=forecast_quantity,
                    corrected_inventory_qty=candidate["corrected_inventory_qty"],
                    safety_stock_days=candidate["safety_stock_days"],
                    sales_stddev=candidate["sales_stddev"],
                    pending_arrival_qty=pending_arrival_qty,
                    min_order_qty=candidate["min_order_qty"],
                    order_batch_qty=candidate["order_batch_qty"],
                )
                rows.append(
                    (
                        candidate["store_id"],
                        candidate["product_id"],
                        suggestion_date,
                        arrival_date.isoformat(),
                        forecast_quantity,
                        candidate["corrected_inventory_qty"],
                        None,
                        None,
                        safety_stock_qty,
                        pending_arrival_qty,
                        suggestion.raw_suggested_qty,
                        suggestion.suggested_order_qty,
                        candidate["order_batch_qty"],
                        candidate["min_order_qty"],
                        suggestion.reason,
                        candidate["unit"],
                    )
                )
            _upsert_order_suggestions(cur, rows)
            return len(rows)


def _fetch_candidates(cur, target_date: date) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            sp.store_id::text,
            sp.product_id::text,
            sp.is_orderable,
            sp.is_sellable,
            sp.safety_stock_days,
            sp.order_batch_qty,
            sp.min_order_qty,
            sf.forecast_quantity,
            sf.sales_stddev,
            ip.corrected_inventory_qty,
            p.sale_unit
        FROM store_products sp
        JOIN sales_forecasts sf
          ON sf.store_id = sp.store_id
         AND sf.product_id = sp.product_id
         AND sf.forecast_date = %s
        JOIN inventory_positions ip
          ON ip.store_id = sp.store_id
         AND ip.product_id = sp.product_id
         AND ip.business_date = %s
        JOIN products p ON p.id = sp.product_id
        WHERE sp.is_active = true
        """,
        (target_date, target_date),
    )
    return [
        {
            "store_id": row[0],
            "product_id": row[1],
            "is_orderable": bool(row[2]),
            "is_sellable": bool(row[3]),
            "safety_stock_days": float(row[4] or 1),
            "order_batch_qty": float(row[5]) if row[5] is not None else None,
            "min_order_qty": float(row[6]) if row[6] is not None else None,
            "forecast_quantity": float(row[7] or 0),
            "sales_stddev": float(row[8] or 0),
            "corrected_inventory_qty": float(row[9] or 0),
            "unit": row[10] or "kg",
        }
        for row in cur.fetchall()
    ]


def _fetch_pending_arrivals(cur, suggestion_date: date, arrival_date: date) -> dict[tuple[str, str], float]:
    cur.execute(
        """
        SELECT store_id::text, product_id::text, COALESCE(SUM(arrival_quantity), 0)
        FROM fresh_order_imports
        WHERE arrival_date > %s
          AND arrival_date <= %s
          AND store_id IS NOT NULL
          AND product_id IS NOT NULL
        GROUP BY store_id, product_id
        """,
        (suggestion_date, arrival_date),
    )
    return {
        (row[0], row[1]): float(row[2] or 0)
        for row in cur.fetchall()
    }


def _upsert_order_suggestions(cur, rows) -> None:
    sql = """
        INSERT INTO order_suggestions (
            store_id,
            product_id,
            suggestion_date,
            arrival_date,
            forecast_quantity,
            corrected_inventory_qty,
            sellable_inventory_qty,
            overstock_qty,
            safety_stock_qty,
            pending_arrival_qty,
            raw_suggested_qty,
            suggested_order_qty,
            order_batch_qty,
            min_order_qty,
            suggestion_reason,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, suggestion_date, arrival_date)
        DO UPDATE SET
            forecast_quantity = EXCLUDED.forecast_quantity,
            corrected_inventory_qty = EXCLUDED.corrected_inventory_qty,
            sellable_inventory_qty = EXCLUDED.sellable_inventory_qty,
            overstock_qty = EXCLUDED.overstock_qty,
            safety_stock_qty = EXCLUDED.safety_stock_qty,
            pending_arrival_qty = EXCLUDED.pending_arrival_qty,
            raw_suggested_qty = EXCLUDED.raw_suggested_qty,
            suggested_order_qty = EXCLUDED.suggested_order_qty,
            order_batch_qty = EXCLUDED.order_batch_qty,
            min_order_qty = EXCLUDED.min_order_qty,
            suggestion_reason = EXCLUDED.suggestion_reason,
            unit = EXCLUDED.unit,
            calculated_at = now()
    """
    cur.executemany(sql, rows)
