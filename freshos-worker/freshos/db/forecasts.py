from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from freshos.calculators.forecast import calculate_sales_forecast
from freshos.config import Settings
from freshos.db.connection import connect


def generate_sales_forecasts(settings: Settings, *, forecast_date: str, order_date: str | None = None) -> int:
    target_date = date.fromisoformat(forecast_date)
    order_day = date.fromisoformat(order_date) if order_date else target_date
    start_14d = target_date - timedelta(days=14)
    start_7d = target_date - timedelta(days=7)

    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            candidates = _fetch_candidate_store_products(cur)
            sales = _fetch_recent_sales(cur, start_14d, target_date)
            cutoff_history = _fetch_cutoff_sales(cur, start_14d, order_day)
            today_cutoff = _fetch_today_cutoff_sales(cur, order_day)
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
                    historical_noon_sales=[
                        item["cutoff_sales_quantity"]
                        for item in cutoff_history.get(key, [])
                        if item["business_date"] in {sale["business_date"] for sale in sales.get(key, [])}
                    ],
                    historical_full_day_sales=[
                        sale["sales_quantity"]
                        for sale in sales.get(key, [])
                        if sale["business_date"] in {item["business_date"] for item in cutoff_history.get(key, [])}
                    ],
                    today_noon_sales_qty=today_cutoff.get(key, {}).get("cutoff_sales_quantity"),
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
                        forecast.base_forecast_quantity,
                        forecast.historical_noon_ratio,
                        forecast.projected_today_sales_qty,
                        forecast.today_trend_factor,
                        forecast.forecast_adjustment_factor,
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


def _fetch_cutoff_sales(cur, start_date: date, end_date: date):
    cur.execute(
        """
        SELECT store_id::text, product_id::text, business_date, cutoff_sales_quantity
        FROM sales_cutoff_snapshots
        WHERE business_date >= %s
          AND business_date < %s
          AND cutoff_time = '12:00'
        ORDER BY business_date
        """,
        (start_date, end_date),
    )
    grouped = defaultdict(list)
    for row in cur.fetchall():
        grouped[(row[0], row[1])].append(
            {
                "business_date": row[2],
                "cutoff_sales_quantity": float(row[3] or 0),
            }
        )
    return grouped


def _fetch_today_cutoff_sales(cur, order_date: date):
    cur.execute(
        """
        SELECT store_id::text, product_id::text, cutoff_sales_quantity
        FROM sales_cutoff_snapshots
        WHERE business_date = %s
          AND cutoff_time = '12:00'
        """,
        (order_date,),
    )
    return {
        (row[0], row[1]): {"cutoff_sales_quantity": float(row[2] or 0)}
        for row in cur.fetchall()
    }


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
            base_forecast_quantity,
            historical_noon_ratio,
            projected_today_sales_qty,
            today_trend_factor,
            forecast_adjustment_factor,
            unit
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (store_id, product_id, forecast_date)
        DO UPDATE SET
            forecast_quantity = EXCLUDED.forecast_quantity,
            forecast_method = EXCLUDED.forecast_method,
            sales_days_used = EXCLUDED.sales_days_used,
            recent_daily_sales = EXCLUDED.recent_daily_sales,
            sales_stddev = EXCLUDED.sales_stddev,
            base_forecast_quantity = EXCLUDED.base_forecast_quantity,
            historical_noon_ratio = EXCLUDED.historical_noon_ratio,
            projected_today_sales_qty = EXCLUDED.projected_today_sales_qty,
            today_trend_factor = EXCLUDED.today_trend_factor,
            forecast_adjustment_factor = EXCLUDED.forecast_adjustment_factor,
            unit = EXCLUDED.unit,
            calculated_at = now()
    """
    cur.executemany(sql, rows)
