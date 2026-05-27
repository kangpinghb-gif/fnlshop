import csv
from pathlib import Path

from openpyxl import Workbook

from freshos.importers.stock_adjustments import parse_stock_adjustment_file


ROOT = Path(__file__).resolve().parents[2]


def test_parse_stock_adjustment_template_sample():
    rows = parse_stock_adjustment_file(ROOT / "data_templates" / "人工盘点修正模板.xlsx")

    assert len(rows) == 1
    assert rows[0].store_code == "10008"
    assert rows[0].store_name == "宝信润山店"
    assert rows[0].product_code == "2904834"
    assert rows[0].product_name == "Z-油桃"
    assert rows[0].count_time == "2026-05-25 21:30:00"
    assert rows[0].business_date == "2026-05-25"
    assert rows[0].adjusted_quantity == 8.5
    assert rows[0].count_type == "risk_triggered"


def test_parse_stock_adjustment_csv_aliases_and_default_date(tmp_path):
    path = tmp_path / "stock_adjustments.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["门店编码", "门店名称", "商品编码", "商品名称", "盘点修正值", "单位", "盘点类型"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "门店编码": "10008.0",
                "门店名称": "宝信润山店",
                "商品编码": "2014691.0",
                "商品名称": "海南香蕉",
                "盘点修正值": "-2",
                "单位": "kg",
                "盘点类型": "random",
            }
        )

    rows = parse_stock_adjustment_file(path, default_business_date="2026-05-26")

    assert len(rows) == 1
    assert rows[0].store_code == "10008"
    assert rows[0].product_code == "2014691"
    assert rows[0].count_time == "2026-05-26 00:00:00"
    assert rows[0].business_date == "2026-05-26"
    assert rows[0].adjusted_quantity == -2


def test_parse_stock_adjustment_xlsx_aliases(tmp_path):
    path = tmp_path / "stock_adjustments.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "盘点"
    sheet.append(["门店编码", "门店名称", "商品编码", "商品名称", "盘点时间", "人工盘点修正值"])
    sheet.append(["10008", "宝信润山店", "2014691", "海南香蕉", "2026/05/26 20:00:00", "3"])
    workbook.save(path)

    rows = parse_stock_adjustment_file(path)

    assert len(rows) == 1
    assert rows[0].source_sheet_name == "盘点"
    assert rows[0].count_time == "2026-05-26 20:00:00"
    assert rows[0].adjusted_quantity == 3
