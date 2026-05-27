from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryRisk:
    risk_type: str
    risk_level: str
    message: str
    related_quantity: float | None = None


def identify_inventory_risks(
    *,
    corrected_inventory_qty: float,
    forecast_quantity: float,
    safety_stock_qty: float,
    remaining_sellable_days: float | None = None,
    aged_remaining_qty: float | None = None,
    loss_quantity: float | None = None,
    recent_daily_sales: float | None = None,
) -> list[InventoryRisk]:
    risks: list[InventoryRisk] = []

    if corrected_inventory_qty < 0:
        risks.append(InventoryRisk("negative_inventory", "high", "修正库存为负", corrected_inventory_qty))
    if corrected_inventory_qty < forecast_quantity:
        risks.append(InventoryRisk("stockout", "high", "库存低于预测销量", corrected_inventory_qty))
    elif corrected_inventory_qty < forecast_quantity + safety_stock_qty:
        risks.append(InventoryRisk("stockout", "medium", "库存低于预测销量加安全库存", corrected_inventory_qty))
    if forecast_quantity > 0 and corrected_inventory_qty > forecast_quantity * 3:
        risks.append(InventoryRisk("overstock", "medium", "库存超过预测销量3倍", corrected_inventory_qty))
    if aged_remaining_qty and remaining_sellable_days is not None:
        if remaining_sellable_days <= 0:
            risks.append(InventoryRisk("expired", "high", "计算批次已超过可售天数", aged_remaining_qty))
        elif remaining_sellable_days <= 1:
            risks.append(InventoryRisk("near_expiry", "medium", "计算批次临期", aged_remaining_qty))
    if loss_quantity and recent_daily_sales and loss_quantity > recent_daily_sales:
        risks.append(InventoryRisk("high_loss", "medium", "报损数量高于近期日均销量", loss_quantity))

    return risks

