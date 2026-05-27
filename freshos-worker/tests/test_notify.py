from pathlib import Path

from freshos.db.summary import DailySummary, _fetch_daily_summary
from jobs.notify import build_notification_text


class FakeCursor:
    def __init__(self, fetchone_rows):
        self.fetchone_rows = list(fetchone_rows)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.fetchone_rows.pop(0)


def test_fetch_daily_summary_counts_order_risk_and_exceptions():
    cur = FakeCursor(
        [
            (3, 25.5),
            (2, 1, 1),
            (4,),
        ]
    )

    summary = _fetch_daily_summary(cur, business_date="2026-05-26")

    assert cur.executed[0][1] == ("2026-05-26",)
    assert cur.executed[1][1] == ("2026-05-26",)
    assert cur.executed[2][1] is None
    assert summary == DailySummary(
        order_item_count=3,
        suggested_order_total_qty=25.5,
        high_risk_count=2,
        stockout_risk_count=1,
        expiry_risk_count=1,
        open_exception_count=4,
    )


def test_build_notification_text_includes_summary_and_report_paths():
    text = build_notification_text(
        business_date="2026-05-26",
        summary=DailySummary(
            order_item_count=3,
            suggested_order_total_qty=25.5,
            high_risk_count=2,
            stockout_risk_count=1,
            expiry_risk_count=1,
            open_exception_count=4,
        ),
        report_dir=Path("/var/lib/freshos/reports"),
        database_enabled=True,
    )

    assert "FreshOS 订货建议 - 2026-05-26" in text
    assert "需订商品：3 个" in text
    assert "建议订货总量：25.5" in text
    assert "高风险商品：2 个" in text
    assert "待处理导入异常：4 个" in text
    assert "/var/lib/freshos/reports/order_suggestions_2026-05-26.csv" in text
