from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.reports import (
    fetch_import_exception_report_rows,
    fetch_inventory_risk_report_rows,
    fetch_order_suggestion_report_rows,
)
from freshos.reports.csv_report import write_csv_report


ORDER_REPORT_FIELDS = ["门店", "商品", "当前库存", "预测销量", "安全库存", "已订未到", "建议订货量", "订货原因", "风险标记"]
RISK_REPORT_FIELDS = ["门店", "商品", "风险类型", "风险等级", "风险说明", "相关数量", "处理状态"]
EXCEPTION_REPORT_FIELDS = ["来源文件", "来源表", "原始行号", "异常类型", "异常说明", "处理状态", "创建时间"]


def _handler(args, settings) -> None:
    report_dir = settings.paths.report_dir

    order_path = Path(report_dir) / f"order_suggestions_{args.business_date}.csv"
    risk_path = Path(report_dir) / f"inventory_risks_{args.business_date}.csv"
    exception_path = Path(report_dir) / f"import_exceptions_{args.business_date}.csv"

    order_rows = []
    risk_rows = []
    exception_rows = []
    if settings.database.enabled:
        order_rows = fetch_order_suggestion_report_rows(settings, suggestion_date=args.business_date)
        risk_rows = fetch_inventory_risk_report_rows(settings, business_date=args.business_date)
        exception_rows = fetch_import_exception_report_rows(settings)
        print(
            "[export_reports] fetched "
            f"order_rows={len(order_rows)} risk_rows={len(risk_rows)} "
            f"exception_rows={len(exception_rows)}"
        )
    else:
        print("[export_reports] database disabled; write empty report templates")

    write_csv_report(order_path, order_rows, ORDER_REPORT_FIELDS)
    write_csv_report(risk_path, risk_rows, RISK_REPORT_FIELDS)
    write_csv_report(exception_path, exception_rows, EXCEPTION_REPORT_FIELDS)
    print(f"[export_reports] wrote {order_path}")
    print(f"[export_reports] wrote {risk_path}")
    print(f"[export_reports] wrote {exception_path}")


def main() -> None:
    run_job("export_reports", "Export FreshOS report files.", _handler)


if __name__ == "__main__":
    main()
