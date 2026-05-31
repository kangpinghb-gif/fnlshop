from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OrderSuggestion:
    raw_suggested_qty: float
    suggested_order_qty: float
    reason: str


def calculate_order_suggestion(
    *,
    is_orderable: bool,
    is_sellable: bool,
    forecast_quantity: float,
    corrected_inventory_qty: float,
    safety_stock_days: float = 1.0,
    sales_stddev: float = 0.0,
    loss_rate: float = 0.0,
    pending_arrival_qty: float = 0.0,
    min_order_qty: float | None = None,
    order_batch_qty: float | None = None,
) -> OrderSuggestion:
    if not is_orderable:
        return OrderSuggestion(0.0, 0.0, "not_orderable")
    if not is_sellable:
        return OrderSuggestion(0.0, 0.0, "not_sellable")

    order_inventory_qty = max(corrected_inventory_qty, 0.0)
    safety_stock_qty = max(forecast_quantity * safety_stock_days, sales_stddev)
    loss_compensation_qty = forecast_quantity * max(loss_rate, 0.0)
    raw = forecast_quantity + safety_stock_qty + loss_compensation_qty - order_inventory_qty - pending_arrival_qty
    raw = max(raw, 0.0)

    suggested = raw
    if suggested > 0 and min_order_qty and suggested < min_order_qty:
        suggested = min_order_qty
    if suggested > 0 and order_batch_qty and order_batch_qty > 0:
        suggested = math.ceil(suggested / order_batch_qty) * order_batch_qty

    return OrderSuggestion(round(raw, 3), round(suggested, 3), "rule_based_v1")
