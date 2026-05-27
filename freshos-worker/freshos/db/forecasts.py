from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from freshos.calculators.forecast import calculate_sales_forecast
from freshos.config import Settings
from freshos.db.connection import connect


def generate_sales_forecasts(settings: Settings, *, forecast_date: str) -> int:
    target_date = date.fromisoformat(forecast_date)
    start_14d = target_date - timedelta(days=14)
    start_7d = target_date - timedelta(days=7)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            candidates = _fetch_candidate_store_products(cur)
            sales = _fetch_recent_sales(cur, start_14d, target_date)
            rows = []
            for candidate in candidates:
                key = (candidate["store_id"], candidate["product_id"])
                recent_14d_sales = [item["sales_quantity"] for item in sales.get(key, [])]
                recent_7d_sales = [
                    item["sales_quantity"]
                    for item in sales.get(key, [])
                    if item["business_date"] >= start_7d
                ]
                forecast = calculate_sales_forecast(
                    recent_14d_sales=recent_14d_sales,
                    recent_7d_sales=recent_7d_sales,
                    fallback_recent_daily_sales=candidate["recent_daily_sales"],
                )
                rows.append(
                    (
                        candidate["store_id"],
                        candidate["product_id"],
                        forecast_date,
                        forecast.forecast_quantity,
                        forecast.forecast_method,
                        forecast.sales_days_used,
                        candidate["recent_daily_sales"],
                        forecast.sales_stddev,
                        candidate["unit"],
                    )
                )
            _upsert_sales_forecasts(cur, rows)
            return len(rows)


def _fetch_candidate_store_products(cur) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            sp.store_id::text,
            sp.product_id::text,
            sp.recent_daily_sales,
            p.sale_unit
        FROM store_products sp
        JOIN products p ON p.id = sp.product_id
        WHERE sp.is_active = true
          AND sp.is_sellable = true
        """
    )
    return [
        {
            "store_id": row[0],
            "product_id": row[1],
            "recent_daily_sales": float(row[2]) if row[2] is not None else None,
            "unit": row[3] or "kg",
        }
        for row in cur.fetchall()
    ]


def _fetch_recent_sales(cur, start_date: date, end_date: date):
    cur.execute(
        """
        SELECT store_id::text, product_id::text, business_date, sales_quantity
        FROM sales_daily
        WHERE business_date >= %s
          AND business_date < %s
        ORDER BY business_date
        """,
        (start_date, end_date),
    )
    grouped = defaultdict(list)
    for row in cur.fetchall():
        grouped[(row[0], row[1])].append(
            {
                "business_date": row[2],
                "sales_quantity": float(row[3] or 0),
            }
        )
    return grouped


def _upsert_sales_forecasts(cur, rows) -> None:
    sql = """
        INSERT INTO sales_forecasts (
            store_id,
            product_id,
            forecast_date,
            forecast_quantity,
            forecast_method,
            sales_days_used,
            recent_daily_sales,
            sales_stddev,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, forecast_date)
        DO UPDATE SET
            forecast_quantity = EXCLUDED.forecast_quantity,
            forecast_method = EXCLUDED.forecast_method,
            sales_days_used = EXCLUDED.sales_days_used,
            recent_daily_sales = EXCLUDED.recent_daily_sales,
            sales_stddev = EXCLUDED.sales_stddev,
            unit = EXCLUDED.unit,
            calculated_at = now()
    """
    cur.executemany(sql, rows)

