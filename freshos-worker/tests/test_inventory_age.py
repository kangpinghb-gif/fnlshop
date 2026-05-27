from datetime import date

from freshos.db.inventory_age import ArrivalBatch, allocate_fifo_batches


def test_allocate_fifo_batches_consumes_oldest_arrival_first():
    batches = [
        ArrivalBatch(
            store_id="store-1",
            product_id="product-1",
            arrival_date=date(2026, 5, 24),
            batch_quantity=5,
            sellable_days=3,
            unit="kg",
        ),
        ArrivalBatch(
            store_id="store-1",
            product_id="product-1",
            arrival_date=date(2026, 5, 25),
            batch_quantity=8,
            sellable_days=3,
            unit="kg",
        ),
    ]

    rows = allocate_fifo_batches(
        batches,
        sales_by_key={("store-1", "product-1"): 7},
        business_date=date(2026, 5, 26),
    )

    assert len(rows) == 2
    assert rows[0].consumed_quantity == 5
    assert rows[0].remaining_quantity == 0
    assert rows[0].remaining_sellable_days == 1
    assert rows[0].batch_status == "near_expiry"
    assert rows[1].consumed_quantity == 2
    assert rows[1].remaining_quantity == 6
    assert rows[1].remaining_sellable_days == 2
    assert rows[1].batch_status == "sellable"


def test_allocate_fifo_batches_marks_expired():
    rows = allocate_fifo_batches(
        [
            ArrivalBatch(
                store_id="store-1",
                product_id="product-1",
                arrival_date=date(2026, 5, 20),
                batch_quantity=5,
                sellable_days=3,
                unit="kg",
            )
        ],
        sales_by_key={},
        business_date=date(2026, 5, 26),
    )

    assert rows[0].remaining_quantity == 5
    assert rows[0].remaining_sellable_days == -3
    assert rows[0].batch_status == "expired"
