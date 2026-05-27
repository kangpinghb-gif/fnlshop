from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryPosition:
    corrected_inventory_qty: float
    inventory_source: str
    inventory_confidence: str


def choose_main_inventory(
    realtime_inventory_qty: float | None,
    closing_inventory_qty: float | None,
    theoretical_inventory_qty: float | None,
) -> tuple[float, str]:
    if realtime_inventory_qty is not None:
        return realtime_inventory_qty, "realtime"
    if closing_inventory_qty is not None:
        return closing_inventory_qty, "closing"
    if theoretical_inventory_qty is not None:
        return theoretical_inventory_qty, "theoretical"
    return 0.0, "missing"


def calculate_inventory_position(
    *,
    realtime_inventory_qty: float | None,
    closing_inventory_qty: float | None,
    theoretical_inventory_qty: float | None,
    manual_adjustment_qty: float | None = None,
) -> InventoryPosition:
    main_qty, source = choose_main_inventory(
        realtime_inventory_qty, closing_inventory_qty, theoretical_inventory_qty
    )
    corrected = main_qty + (manual_adjustment_qty or 0.0)
    confidence = classify_inventory_confidence(source, corrected, theoretical_inventory_qty)
    return InventoryPosition(corrected, source, confidence)


def classify_inventory_confidence(
    source: str,
    corrected_inventory_qty: float,
    theoretical_inventory_qty: float | None,
) -> str:
    if corrected_inventory_qty < 0 or source == "missing":
        return "low"
    if source == "realtime" and theoretical_inventory_qty is not None:
        diff = abs(corrected_inventory_qty - theoretical_inventory_qty)
        base = max(abs(theoretical_inventory_qty), 1.0)
        return "high" if diff / base <= 0.2 else "medium"
    if source in {"realtime", "closing"}:
        return "medium"
    return "low"

