from __future__ import annotations

from datetime import date

from freshos.calculators.risks import identify_inventory_risks
from freshos.config import Settings
from freshos.db.connection import connect


def generate_inventory_risks(settings: Settings, *, business_date: str) -> int:
    target_date = date.fromisoformat(business_date)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            candidates = _fetch_candidates(cur, target_date)
            _clear_existing_risks(cur, target_date)
            rows = []
            for candidate in candidates:
                safety_stock_qty = candidate["forecast_quantity"] * candidate["safety_stock_days"]
                risks = identify_inventory_risks(
                    corrected_inventory_qty=candidate["corrected_inventory_qty"],
                    forecast_quantity=candidate["forecast_quantity"],
                    safety_stock_qty=safety_stock_qty,
                    remaining_sellable_days=candidate["remaining_sellable_days"],
                    aged_remaining_qty=candidate["aged_remaining_qty"],
                    loss_quantity=candidate["loss_quantity"],
                    recent_daily_sales=candidate["recent_daily_sales"],
                )
                rows.extend(
                    (
                        candidate["store_id"],
                        candidate["product_id"],
                        business_date,
                        risk.risk_type,
                        risk.risk_level,
                        risk.message,
                        risk.related_quantity,
                    )
                    for risk in risks
                )
            _insert_inventory_risks(cur, rows)
            return len(rows)


def _fetch_candidates(cur, target_date: date) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            sp.store_id::text,
            sp.product_id::text,
            sp.safety_stock_days,
            sp.recent_daily_sales,
            ip.corrected_inventory_qty,
            sf.forecast_quantity,
            ib.remaining_sellable_days,
            ib.remaining_quantity,
            ild.loss_quantity
        FROM store_products sp
        JOIN inventory_positions ip
          ON ip.store_id = sp.store_id
         AND ip.product_id = sp.product_id
         AND ip.business_date = %s
        LEFT JOIN sales_forecasts sf
          ON sf.store_id = sp.store_id
         AND sf.product_id = sp.product_id
         AND sf.forecast_date = %s
        LEFT JOIN LATERAL (
            SELECT remaining_sellable_days, remaining_quantity
            FROM inventory_age_batches ib
            WHERE ib.store_id = sp.store_id
              AND ib.product_id = sp.product_id
              AND ib.remaining_quantity > 0
            ORDER BY remaining_sellable_days ASC
            LIMIT 1
        ) ib ON true
        LEFT JOIN inventory_loss_daily ild
          ON ild.store_id = sp.store_id
         AND ild.product_id = sp.product_id
         AND ild.business_date = %s
        WHERE sp.is_active = true
          AND sp.is_sellable = true
        """,
        (target_date, target_date, target_date),
    )
    return [
        {
            "store_id": row[0],
            "product_id": row[1],
            "safety_stock_days": float(row[2] or 1),
            "recent_daily_sales": float(row[3]) if row[3] is not None else None,
            "corrected_inventory_qty": float(row[4] or 0),
            "forecast_quantity": float(row[5] or 0),
            "remaining_sellable_days": float(row[6]) if row[6] is not None else None,
            "aged_remaining_qty": float(row[7]) if row[7] is not None else None,
            "loss_quantity": float(row[8]) if row[8] is not None else None,
        }
        for row in cur.fetchall()
    ]


def _clear_existing_risks(cur, target_date: date) -> None:
    cur.execute(
        """
        DELETE FROM inventory_risks
        WHERE business_date = %s
          AND status = 'open'
        """,
        (target_date,),
    )


def _insert_inventory_risks(cur, rows) -> None:
    if not rows:
        return
    sql = """
        INSERT INTO inventory_risks (
            store_id,
            product_id,
            business_date,
            risk_type,
            risk_level,
            risk_message,
            related_quantity
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.executemany(sql, rows)
