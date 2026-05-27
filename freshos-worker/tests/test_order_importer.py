from pathlib import Path

from freshos.importers.order_importer import parse_order_workbook


ROOT = Path(__file__).resolve().parents[2]


def test_parse_fruit_order_sample():
    rows = parse_order_workbook(ROOT / "样表" / "5.25水果订单(2).xlsx")

    assert len(rows) == 29
    first = rows[0]
    assert first.source_format == "fruit_standard"
    assert first.supplier_code == "900339"
    assert first.supplier_name == "R-生鲜自采（水果孙江波）"
    assert first.store_name_raw == "宝信润山店"
    assert first.product_name_raw == "C-富士苹果（小仅订货）"
    assert first.arrival_date.endswith("-05-25")
    assert first.arrival_quantity == 15.15


def test_parse_vegetable_supplier_sample():
    rows = parse_order_workbook(ROOT / "样表" / "宝信润山店.xlsx")

    assert len(rows) == 22
    first = rows[0]
    assert first.source_format == "vegetable_supplier"
    assert first.supplier_code == "200477"
    assert first.supplier_name == "徐州喜果供应链管理有限公司（蔬菜）"
    assert first.store_name_raw == "宝信润山店"
    assert first.product_name_raw == "瓠子"
    assert first.arrival_date.endswith("-05-24")
    assert first.arrival_quantity == 3.15

