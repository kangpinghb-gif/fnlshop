from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.summary import DailySummary, fetch_daily_summary
from freshos.notifiers.webhook import send_webhook_text


def build_notification_text(
    *,
    business_date: str,
    summary: DailySummary,
    report_dir: Path,
    database_enabled: bool,
) -> str:
    data_status = "数据库已启用" if database_enabled else "数据库未启用，当前为本地模板模式"
    return (
        f"FreshOS 订货建议 - {business_date}\n\n"
        f"状态：{data_status}\n"
        f"需订商品：{summary.order_item_count} 个\n"
        f"建议订货总量：{summary.suggested_order_total_qty:g}\n"
        f"高风险商品：{summary.high_risk_count} 个\n"
        f"缺货风险：{summary.stockout_risk_count} 个\n"
        f"临期/过期：{summary.expiry_risk_count} 个\n"
        f"待处理导入异常：{summary.open_exception_count} 个\n\n"
        "附件/报表：\n"
        f"1. {report_dir / f'order_suggestions_{business_date}.csv'}\n"
        f"2. {report_dir / f'inventory_risks_{business_date}.csv'}\n"
        f"3. {report_dir / f'import_exceptions_{business_date}.csv'}"
    )


def _handler(args, settings) -> None:
    summary = DailySummary()
    if settings.database.enabled:
        summary = fetch_daily_summary(settings, business_date=args.business_date)
    text = build_notification_text(
        business_date=args.business_date,
        summary=summary,
        report_dir=settings.paths.report_dir,
        database_enabled=settings.database.enabled,
    )

    if settings.notify.provider == "none":
        print("[notify] provider=none, skip webhook")
        print(text)
        return

    send_webhook_text(settings.notify.webhook_url, text)
    print("[notify] webhook sent")


def main() -> None:
    run_job("notify", "Notify WeCom or Feishu.", _handler)


if __name__ == "__main__":
    main()
