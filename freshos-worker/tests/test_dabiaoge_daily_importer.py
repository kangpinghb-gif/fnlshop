import csv

from openpyxl import Workbook

from freshos.importers.dabiaoge_daily import merge_dabiaoge_daily_rows, parse_dabiaoge_daily_csv


def test_parse_sales_daily_csv(tmp_path):
    path = tmp_path / "sales.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["店铺编号", "商品编码", "日期", "销售数量", "销售金额", "单位"])
        writer.writeheader()
        writer.writerow(
            {
                "店铺编号": "10008",
                "商品编码": "2014691",
                "日期": "2026-05-25",
                "销售数量": "12.5",
                "销售金额": "88",
                "单位": "kg",
            }
        )

    rows = parse_dabiaoge_daily_csv(path, report_type="sales")

    assert len(rows) == 1
    assert rows[0].store_code == "10008"
    assert rows[0].product_code == "2014691"
    assert rows[0].business_date == "2026-05-25"
    assert rows[0].sales_quantity == 12.5
    assert rows[0].sales_amount == 88


def test_parse_inventory_loss_csv(tmp_path):
    path = tmp_path / "inventory_loss.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["店铺编号", "商品编码", "营业日期", "库存数量", "报损数量", "报损金额", "盘盈盘亏数量"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "店铺编号": "10008",
                "商品编码": "2014691",
                "营业日期": "2026/05/25",
                "库存数量": "8",
                "报损数量": "1",
                "报损金额": "6",
                "盘盈盘亏数量": "-0.5",
            }
        )

    rows = parse_dabiaoge_daily_csv(path, report_type="inventory_loss")

    assert len(rows) == 1
    assert rows[0].business_date == "2026-05-25"
    assert rows[0].closing_stock_qty == 8
    assert rows[0].loss_quantity == 1
    assert rows[0].inventory_difference_qty == -0.5


def test_parse_cutoff_sales_csv(tmp_path):
    path = tmp_path / "cutoff.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["店铺编号", "商品编码", "日期", "0-12点销量", "12点库存", "在途数量", "截止时间"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "店铺编号": "10008",
                "商品编码": "2014691",
                "日期": "2026-05-25",
                "0-12点销量": "9",
                "12点库存": "20",
                "在途数量": "5",
                "截止时间": "12:00",
            }
        )

    rows = parse_dabiaoge_daily_csv(path, report_type="cutoff_sales")

    assert len(rows) == 1
    assert rows[0].cutoff_sales_quantity == 9
    assert rows[0].current_inventory_qty == 20
    assert rows[0].in_transit_qty == 5
    assert rows[0].cutoff_time == "12:00"


def test_parse_daily_csv_uses_default_business_date(tmp_path):
    path = tmp_path / "sales_without_date.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["门店编号", "产品编码", "销量", "销售额"])
        writer.writeheader()
        writer.writerow(
            {
                "门店编号": "10008.0",
                "产品编码": "2014691.0",
                "销量": "5",
                "销售额": "35",
            }
        )

    rows = parse_dabiaoge_daily_csv(path, report_type="sales", default_business_date="2026-05-26")

    assert len(rows) == 1
    assert rows[0].store_code == "10008"
    assert rows[0].product_code == "2014691"
    assert rows[0].business_date == "2026-05-26"
    assert rows[0].sales_quantity == 5


def test_parse_daily_xlsx(tmp_path):
    path = tmp_path / "inventory.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "库存"
    sheet.append(["门店编号", "商品编码", "库存时间", "实时库存数量", "单位"])
    sheet.append(["10008", "2014691", "2026/05/26 08:30:00", "8.5", "kg"])
    workbook.save(path)

    rows = parse_dabiaoge_daily_csv(path, report_type="inventory_snapshot", default_business_date="2026-05-26")

    assert len(rows) == 1
    assert rows[0].business_date == "2026-05-26"
    assert rows[0].snapshot_time == "2026-05-26 08:30:00"
    assert rows[0].inventory_quantity == 8.5
    assert rows[0].inventory_source == "realtime"
    assert rows[0].source_file == "inventory.xlsx:库存"


def test_merge_dabiaoge_daily_rows_sums_daily_sales(tmp_path):
    path = tmp_path / "sales.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["店铺编号", "商品编码", "日期", "销售数量", "销售金额"])
        writer.writeheader()
        writer.writerow({"店铺编号": "10008", "商品编码": "2014691", "日期": "2026-05-25", "销售数量": "4", "销售金额": "20"})
        writer.writerow({"店铺编号": "10008", "商品编码": "2014691", "日期": "2026-05-25", "销售数量": "6", "销售金额": "30"})

    rows = merge_dabiaoge_daily_rows(parse_dabiaoge_daily_csv(path, report_type="sales"))

    assert len(rows) == 1
    assert rows[0].sales_quantity == 10
    assert rows[0].sales_amount == 50
