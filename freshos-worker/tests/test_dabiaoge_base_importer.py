import csv

from openpyxl import Workbook

from freshos.importers.dabiaoge_base import DABIAOGE_BASE_COLUMNS, parse_dabiaoge_base_csv


def test_parse_dabiaoge_base_filters_40_42(tmp_path):
    path = tmp_path / "base.csv"
    row_42 = {column: "" for column in DABIAOGE_BASE_COLUMNS}
    row_42.update(
        {
            "店铺编号": "10008",
            "店铺名称": "宝信润山店",
            "店铺状态": "正常",
            "大分类编码": "42",
            "大分类名称": "日配生鲜",
            "中分类编码": "4201",
            "中分类名称": "水果",
            "商品编码": "2014691",
            "商品名称": "海南香蕉",
            "商品条码": "barcode-1",
            "销售单位": "kg",
            "商品属性": "普通水果",
            "保质期限(天)": "3",
            "店铺订货标识": "门店可订",
            "店铺销售标识": "门店可销售",
            "箱装数": "1",
            "订货批量": "5",
            "近期日均销量": "10.5",
            "门店库存数量(昨日)": "8",
        }
    )
    row_01 = dict(row_42)
    row_01["大分类编码"] = "01"
    row_01["商品编码"] = "ignore-me"

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=DABIAOGE_BASE_COLUMNS)
        writer.writeheader()
        writer.writerow(row_42)
        writer.writerow(row_01)

    result = parse_dabiaoge_base_csv(path)

    assert len(result.stores) == 1
    assert len(result.products) == 1
    assert len(result.store_products) == 1
    assert result.products[0].product_name == "海南香蕉"
    assert result.products[0].cat_id_01 == "42"
    assert result.store_products[0].is_orderable is True
    assert result.store_products[0].order_batch_qty == 5


def test_parse_dabiaoge_base_accepts_header_aliases(tmp_path):
    path = tmp_path / "base_alias.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "门店编号",
                "门店名称",
                "大类编码",
                "大类名称",
                "产品编码",
                "品名",
                "单位",
                "保质期",
                "可订标识",
                "可销标识",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "门店编号": "10008.0",
                "门店名称": "宝信润山店",
                "大类编码": "40",
                "大类名称": "生鲜",
                "产品编码": "2014691.0",
                "品名": "海南香蕉",
                "单位": "kg",
                "保质期": "3",
                "可订标识": "门店不可订",
                "可销标识": "门店可销售",
            }
        )

    result = parse_dabiaoge_base_csv(path)

    assert result.stores[0].store_code == "10008"
    assert result.products[0].product_code == "2014691"
    assert result.products[0].shelf_life_days == 3
    assert result.store_products[0].is_orderable is False
    assert result.store_products[0].is_sellable is True


def test_parse_dabiaoge_base_treats_numeric_status_one_as_enabled(tmp_path):
    path = tmp_path / "numeric_status.csv"
    row = {column: "" for column in DABIAOGE_BASE_COLUMNS}
    row.update(
        {
            "店铺编号": "10008",
            "店铺名称": "宝信润山店",
            "大分类编码": "42",
            "大分类名称": "日配生鲜",
            "商品编码": "2014691",
            "商品名称": "海南香蕉",
            "店铺订货标识": "1",
            "店铺销售标识": "1",
        }
    )

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=DABIAOGE_BASE_COLUMNS)
        writer.writeheader()
        writer.writerow(row)

    result = parse_dabiaoge_base_csv(path)

    assert result.store_products[0].is_orderable is True
    assert result.store_products[0].is_sellable is True


def test_parse_dabiaoge_base_marks_clearance_products_not_orderable(tmp_path):
    path = tmp_path / "clearance.csv"
    rows = []
    for code, name in [
        ("2014691", "折-海南香蕉"),
        ("2014692", "ZJP-精品香蕉"),
        ("2014693", "精品zjp香蕉"),
    ]:
        row = {column: "" for column in DABIAOGE_BASE_COLUMNS}
        row.update(
            {
                "店铺编号": "10008",
                "店铺名称": "宝信润山店",
                "大分类编码": "42",
                "大分类名称": "日配生鲜",
                "商品编码": code,
                "商品名称": name,
                "店铺订货标识": "门店可订",
                "店铺销售标识": "门店可销售",
            }
        )
        rows.append(row)

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=DABIAOGE_BASE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result = parse_dabiaoge_base_csv(path)

    assert len(result.store_products) == 3
    assert all(row.is_orderable is False for row in result.store_products)
    assert all(row.is_sellable is True for row in result.store_products)


def test_parse_dabiaoge_base_overrides_grape_shelf_life(tmp_path):
    path = tmp_path / "grapes.csv"
    rows = []
    for code, name, shelf_life in [
        ("2014691", "巨峰葡萄", "5"),
        ("2014692", "葡萄柚", "15"),
    ]:
        row = {column: "" for column in DABIAOGE_BASE_COLUMNS}
        row.update(
            {
                "店铺编号": "10008",
                "店铺名称": "宝信润山店",
                "大分类编码": "42",
                "大分类名称": "日配生鲜",
                "商品编码": code,
                "商品名称": name,
                "保质期限(天)": shelf_life,
            }
        )
        rows.append(row)

    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=DABIAOGE_BASE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    result = parse_dabiaoge_base_csv(path)
    shelf_life_by_name = {row.product_name: row.shelf_life_days for row in result.products}

    assert shelf_life_by_name["巨峰葡萄"] == 1
    assert shelf_life_by_name["葡萄柚"] == 15


def test_parse_dabiaoge_base_accepts_xlsx(tmp_path):
    path = tmp_path / "base.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["门店编号", "门店名称", "大类编码", "大类名称", "商品编码", "商品名称"])
    sheet.append(["10008", "宝信润山店", "42", "日配生鲜", "2014691", "海南香蕉"])
    workbook.save(path)

    result = parse_dabiaoge_base_csv(path)

    assert len(result.stores) == 1
    assert result.stores[0].store_name == "宝信润山店"
    assert result.products[0].cat_id_01 == "42"
