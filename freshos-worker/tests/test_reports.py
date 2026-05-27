from freshos.db.reports import (
    _fetch_import_exception_report_rows,
    _fetch_inventory_risk_report_rows,
    _fetch_order_suggestion_report_rows,
)


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows


def test_fetch_order_suggestion_report_rows_maps_fields_and_risk_flag():
    cur = FakeCursor(
        [
            (
                "宝信润山店",
                "海南香蕉",
                8,
                10,
                10,
                0,
                15,
                "rule_based_v1",
                1,
            )
        ]
    )

    rows = _fetch_order_suggestion_report_rows(cur, suggestion_date="2026-05-26")

    assert cur.executed[0][1] == ("2026-05-26", "2026-05-26")
    assert rows == [
        {
            "门店": "宝信润山店",
            "商品": "海南香蕉",
            "当前库存": 8,
            "预测销量": 10,
            "安全库存": 10,
            "已订未到": 0,
            "建议订货量": 15,
            "订货原因": "rule_based_v1",
            "风险标记": "高风险",
        }
    ]


def test_fetch_inventory_risk_report_rows_maps_fields():
    cur = FakeCursor(
        [
            (
                "宝信润山店",
                "海南香蕉",
                "stockout",
                "high",
                "库存低于预测销量",
                3,
                "open",
            )
        ]
    )

    rows = _fetch_inventory_risk_report_rows(cur, business_date="2026-05-26")

    assert cur.executed[0][1] == ("2026-05-26",)
    assert rows == [
        {
            "门店": "宝信润山店",
            "商品": "海南香蕉",
            "风险类型": "stockout",
            "风险等级": "high",
            "风险说明": "库存低于预测销量",
            "相关数量": 3,
            "处理状态": "open",
        }
    ]


def test_fetch_import_exception_report_rows_maps_fields():
    cur = FakeCursor(
        [
            (
                "stock.xlsx",
                "stock_count_adjustments",
                2,
                "unmatched_product",
                "盘点修正商品无法匹配: 2014691",
                "open",
                "2026-05-26 08:00:00",
            )
        ]
    )

    rows = _fetch_import_exception_report_rows(cur)

    assert cur.executed[0][1] is None
    assert rows == [
        {
            "来源文件": "stock.xlsx",
            "来源表": "stock_count_adjustments",
            "原始行号": 2,
            "异常类型": "unmatched_product",
            "异常说明": "盘点修正商品无法匹配: 2014691",
            "处理状态": "open",
            "创建时间": "2026-05-26 08:00:00",
        }
    ]
