from freshos.matching.order_matching import EntityRecord, match_order_row


def test_match_order_row_by_store_and_cleaned_product_name():
    stores = [EntityRecord(id="store-1", code="10008", name="宝信润山店")]
    products = [EntityRecord(id="product-1", code="2014691", name="海南香蕉")]

    result = match_order_row(
        store_name_raw="宝信润山店",
        product_name_raw="JPZ-海南香蕉",
        stores=stores,
        products=products,
    )

    assert result.match_status == "matched"
    assert result.store_id == "store-1"
    assert result.product_id == "product-1"
    assert result.exception_types == ()


def test_match_order_row_reports_unmatched_product():
    stores = [EntityRecord(id="store-1", code="10008", name="宝信润山店")]
    products = [EntityRecord(id="product-1", code="2014691", name="海南香蕉")]

    result = match_order_row(
        store_name_raw="宝信润山店",
        product_name_raw="不存在商品",
        stores=stores,
        products=products,
    )

    assert result.match_status == "failed"
    assert result.store_id == "store-1"
    assert result.product_id is None
    assert result.exception_types == ("unmatched_product",)

