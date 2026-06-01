from freshos.calculators.forecast import calculate_sales_forecast
from freshos.calculators.inventory import calculate_inventory_position
from freshos.calculators.orders import calculate_order_suggestion, estimate_inventory_at_arrival
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


def test_forecast_applies_noon_trend_adjustment_when_ratio_is_reliable():
    result = calculate_sales_forecast(
        recent_14d_sales=[20, 20, 20, 20],
        recent_7d_sales=[20, 20, 20],
        historical_noon_sales=[6, 6, 6, 6],
        historical_full_day_sales=[20, 20, 20, 20],
        today_noon_sales_qty=9,
    )
    assert result.base_forecast_quantity == 20
    assert result.historical_noon_ratio == 0.3
    assert result.projected_today_sales_qty == 30
    assert result.forecast_adjustment_factor == 1.1
    assert result.forecast_quantity == 22
    assert result.forecast_method == "moving_average_7d_noon_adjusted"


def test_forecast_skips_noon_trend_when_ratio_is_too_low():
    result = calculate_sales_forecast(
        recent_14d_sales=[20, 20, 20, 20],
        recent_7d_sales=[20, 20, 20],
        historical_noon_sales=[1, 1, 1],
        historical_full_day_sales=[20, 20, 20],
        today_noon_sales_qty=3,
    )
    assert result.forecast_quantity == 20
    assert result.forecast_method == "moving_average_7d"
    assert result.historical_noon_ratio == 0.05


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


def test_order_suggestion_truncates_negative_inventory_for_ordering():
    result = calculate_order_suggestion(
        is_orderable=True,
        is_sellable=True,
        forecast_quantity=10,
        corrected_inventory_qty=-100,
        safety_stock_days=1,
    )

    assert result.raw_suggested_qty == 20
    assert result.suggested_order_qty == 20


def test_order_suggestion_can_use_expected_inventory_at_arrival():
    expected_inventory = estimate_inventory_at_arrival(
        current_inventory_qty=20,
        projected_today_sales_qty=30,
        today_noon_sales_qty=9,
        loss_rate=0.1,
        pending_arrival_qty=5,
    )
    assert expected_inventory == 1

    result = calculate_order_suggestion(
        is_orderable=True,
        is_sellable=True,
        forecast_quantity=22,
        corrected_inventory_qty=20,
        expected_inventory_at_arrival=expected_inventory,
        safety_stock_days=1,
    )
    assert result.raw_suggested_qty == 43


def test_risk_detects_stockout_and_near_expiry():
    risks = identify_inventory_risks(
        corrected_inventory_qty=3,
        forecast_quantity=5,
        safety_stock_qty=2,
        remaining_sellable_days=1,
        aged_remaining_qty=4,
    )
    assert {risk.risk_type for risk in risks} == {"stockout", "near_expiry"}
