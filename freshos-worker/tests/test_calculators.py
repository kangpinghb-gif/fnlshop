from freshos.calculators.forecast import calculate_sales_forecast
from freshos.calculators.inventory import calculate_inventory_position
from freshos.calculators.orders import calculate_order_suggestion
from freshos.calculators.risks import identify_inventory_risks


def test_forecast_prefers_7d_when_enough_data():
    result = calculate_sales_forecast(
        recent_14d_sales=[1, 2, 3, 4, 5, 6, 7],
        recent_7d_sales=[10, 11, 12],
    )
    assert result.forecast_quantity == 11
    assert result.forecast_method == "moving_average_7d"


def test_forecast_uses_14d_when_7d_insufficient():
    result = calculate_sales_forecast(
        recent_14d_sales=[1, 2, 3, 4],
        recent_7d_sales=[10, 11],
    )
    assert result.forecast_quantity == 2.5
    assert result.forecast_method == "moving_average_14d"


def test_inventory_uses_realtime_and_manual_adjustment():
    result = calculate_inventory_position(
        realtime_inventory_qty=10,
        closing_inventory_qty=8,
        theoretical_inventory_qty=9,
        manual_adjustment_qty=-2,
    )
    assert result.corrected_inventory_qty == 8
    assert result.inventory_source == "realtime"


def test_order_suggestion_applies_min_and_batch():
    result = calculate_order_suggestion(
        is_orderable=True,
        is_sellable=True,
        forecast_quantity=10,
        corrected_inventory_qty=5,
        safety_stock_days=1,
        min_order_qty=8,
        order_batch_qty=5,
    )
    assert result.raw_suggested_qty == 15
    assert result.suggested_order_qty == 15


def test_risk_detects_stockout_and_near_expiry():
    risks = identify_inventory_risks(
        corrected_inventory_qty=3,
        forecast_quantity=5,
        safety_stock_qty=2,
        remaining_sellable_days=1,
        aged_remaining_qty=4,
    )
    assert {risk.risk_type for risk in risks} == {"stockout", "near_expiry"}
