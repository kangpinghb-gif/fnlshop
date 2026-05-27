from __future__ import annotations

from dataclasses import dataclass

from freshos.config import Settings
from freshos.db.connection import connect


@dataclass(frozen=True)
class DailySummary:
    order_item_count: int = 0
    suggested_order_total_qty: float = 0.0
    high_risk_count: int = 0
    stockout_risk_count: int = 0
    expiry_risk_count: int = 0
    open_exception_count: int = 0


def fetch_daily_summary(settings: Settings, *, business_date: str) -> DailySummary:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            return _fetch_daily_summary(cur, business_date=business_date)


def _fetch_daily_summary(cur, *, business_date: str) -> DailySummary:
    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE suggested_order_qty > 0),
            COALESCE(SUM(suggested_order_qty) FILTER (WHERE suggested_order_qty > 0), 0)
        FROM order_suggestions
        WHERE suggestion_date = %s
        """,
        (business_date,),
    )
    order_row = cur.fetchone()

    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE risk_level = 'high'),
            COUNT(*) FILTER (WHERE risk_type = 'stockout'),
            COUNT(*) FILTER (WHERE risk_type IN ('near_expiry', 'expired'))
        FROM inventory_risks
        WHERE business_date = %s
          AND status = 'open'
        """,
        (business_date,),
    )
    risk_row = cur.fetchone()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM import_exceptions
        WHERE status = 'open'
        """
    )
    exception_row = cur.fetchone()

    return DailySummary(
        order_item_count=int(order_row[0] or 0),
        suggested_order_total_qty=float(order_row[1] or 0),
        high_risk_count=int(risk_row[0] or 0),
        stockout_risk_count=int(risk_row[1] or 0),
        expiry_risk_count=int(risk_row[2] or 0),
        open_exception_count=int(exception_row[0] or 0),
    )
