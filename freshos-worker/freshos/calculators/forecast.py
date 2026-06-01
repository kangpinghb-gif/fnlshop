from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class SalesForecast:
    forecast_quantity: float
    forecast_method: str
    sales_days_used: int
    sales_stddev: float
    base_forecast_quantity: float = 0.0
    historical_noon_ratio: float | None = None
    projected_today_sales_qty: float | None = None
    today_trend_factor: float = 1.0
    forecast_adjustment_factor: float = 1.0


def calculate_sales_forecast(
    recent_14d_sales: list[float],
    recent_7d_sales: list[float] | None = None,
    fallback_recent_daily_sales: float | None = None,
    historical_noon_sales: list[float] | None = None,
    historical_full_day_sales: list[float] | None = None,
    today_noon_sales_qty: float | None = None,
    noon_ratio_min: float = 0.2,
    noon_trend_weight: float = 0.2,
    adjustment_min: float = 0.9,
    adjustment_max: float = 1.1,
) -> SalesForecast:
    seven = [x for x in (recent_7d_sales or []) if x is not None]
    fourteen = [x for x in recent_14d_sales if x is not None]

    if len(seven) >= 3:
        base = SalesForecast(round(mean(seven), 3), "moving_average_7d", len(seven), round(pstdev(seven), 3))
    elif len(fourteen) >= 3:
        base = SalesForecast(
            round(mean(fourteen), 3),
            "moving_average_14d",
            len(fourteen),
            round(pstdev(fourteen), 3),
        )
    elif fallback_recent_daily_sales is not None:
        base = SalesForecast(float(fallback_recent_daily_sales), "fallback_recent_daily_sales", 0, 0.0)
    else:
        base = SalesForecast(0.0, "no_sales_data", 0, 0.0)

    return apply_noon_trend_adjustment(
        base,
        historical_noon_sales=historical_noon_sales,
        historical_full_day_sales=historical_full_day_sales,
        today_noon_sales_qty=today_noon_sales_qty,
        noon_ratio_min=noon_ratio_min,
        noon_trend_weight=noon_trend_weight,
        adjustment_min=adjustment_min,
        adjustment_max=adjustment_max,
    )


def apply_noon_trend_adjustment(
    base: SalesForecast,
    *,
    historical_noon_sales: list[float] | None,
    historical_full_day_sales: list[float] | None,
    today_noon_sales_qty: float | None,
    noon_ratio_min: float = 0.2,
    noon_trend_weight: float = 0.2,
    adjustment_min: float = 0.9,
    adjustment_max: float = 1.1,
) -> SalesForecast:
    if base.forecast_quantity <= 0 or today_noon_sales_qty is None:
        return _with_base(base)

    historical_noon_sales = historical_noon_sales or []
    historical_full_day_sales = historical_full_day_sales or []
    paired = [
        (noon, full)
        for noon, full in zip(historical_noon_sales, historical_full_day_sales)
        if noon is not None and full and full > 0
    ]
    if len(paired) < 3:
        return _with_base(base)

    historical_noon_ratio = sum(noon for noon, _ in paired) / sum(full for _, full in paired)
    if historical_noon_ratio < noon_ratio_min:
        return _with_base(base, historical_noon_ratio=round(historical_noon_ratio, 4))

    projected_today_sales_qty = today_noon_sales_qty / historical_noon_ratio
    today_trend_factor = projected_today_sales_qty / base.forecast_quantity
    adjustment = 1 + (today_trend_factor - 1) * noon_trend_weight
    adjustment = min(max(adjustment, adjustment_min), adjustment_max)
    adjusted_forecast = round(base.forecast_quantity * adjustment, 3)

    return SalesForecast(
        forecast_quantity=adjusted_forecast,
        forecast_method=f"{base.forecast_method}_noon_adjusted",
        sales_days_used=base.sales_days_used,
        sales_stddev=base.sales_stddev,
        base_forecast_quantity=base.forecast_quantity,
        historical_noon_ratio=round(historical_noon_ratio, 4),
        projected_today_sales_qty=round(projected_today_sales_qty, 3),
        today_trend_factor=round(today_trend_factor, 3),
        forecast_adjustment_factor=round(adjustment, 3),
    )


def _with_base(base: SalesForecast, historical_noon_ratio: float | None = None) -> SalesForecast:
    return SalesForecast(
        forecast_quantity=base.forecast_quantity,
        forecast_method=base.forecast_method,
        sales_days_used=base.sales_days_used,
        sales_stddev=base.sales_stddev,
        base_forecast_quantity=base.forecast_quantity,
        historical_noon_ratio=historical_noon_ratio,
    )
