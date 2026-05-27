from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class SalesForecast:
    forecast_quantity: float
    forecast_method: str
    sales_days_used: int
    sales_stddev: float


def calculate_sales_forecast(
    recent_14d_sales: list[float],
    recent_7d_sales: list[float] | None = None,
    fallback_recent_daily_sales: float | None = None,
) -> SalesForecast:
    seven = [x for x in (recent_7d_sales or []) if x is not None]
    fourteen = [x for x in recent_14d_sales if x is not None]

    if len(seven) >= 3:
        return SalesForecast(round(mean(seven), 3), "moving_average_7d", len(seven), round(pstdev(seven), 3))

    if len(fourteen) >= 3:
        return SalesForecast(
            round(mean(fourteen), 3),
            "moving_average_14d",
            len(fourteen),
            round(pstdev(fourteen), 3),
        )

    if fallback_recent_daily_sales is not None:
        return SalesForecast(float(fallback_recent_daily_sales), "fallback_recent_daily_sales", 0, 0.0)

    return SalesForecast(0.0, "no_sales_data", 0, 0.0)

