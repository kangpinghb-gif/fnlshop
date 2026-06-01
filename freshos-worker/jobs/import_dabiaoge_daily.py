from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.dabiaoge_daily import upsert_dabiaoge_daily
from freshos.importers.dabiaoge_daily import REPORT_TYPES, merge_dabiaoge_daily_rows, parse_dabiaoge_daily_file
from freshos.reports.csv_report import write_csv_report


DAILY_FIELDS = [
    "report_type",
    "store_code",
    "product_code",
    "business_date",
    "unit",
    "sales_quantity",
    "sales_amount",
    "closing_stock_qty",
    "loss_quantity",
    "loss_amount",
    "inventory_difference_qty",
    "order_quantity",
    "receive_quantity",
    "total_receive_quantity",
    "total_return_quantity",
    "inventory_quantity",
    "cutoff_sales_quantity",
    "current_inventory_qty",
    "in_transit_qty",
    "cutoff_time",
    "snapshot_time",
    "inventory_source",
    "source_file",
]


def _handler(args, settings) -> None:
    report_type = getattr(args, "report_type", "")
    print(f"[import_dabiaoge_daily] business_date={args.business_date} report_type={report_type}")
    if report_type not in REPORT_TYPES:
        raise ValueError(f"--report-type must be one of: {', '.join(sorted(REPORT_TYPES))}")
    if not args.input:
        print("[import_dabiaoge_daily] no --input files provided; skip")
        return

    parsed_rows = []
    for input_path in args.input:
        rows = parse_dabiaoge_daily_file(
            input_path,
            report_type=report_type,
            default_business_date=args.business_date,
        )
        parsed_rows.extend(rows)
        print(f"[import_dabiaoge_daily] parsed {len(rows)} rows from {input_path}")
    parsed_rows = merge_dabiaoge_daily_rows(parsed_rows)
    print(f"[import_dabiaoge_daily] merged rows={len(parsed_rows)}")

    if settings.database.enabled:
        written = upsert_dabiaoge_daily(settings, parsed_rows, report_type=report_type)
        print(f"[import_dabiaoge_daily] upserted {written} rows into {report_type}")

    if args.output or not settings.database.enabled:
        output = Path(args.output) if args.output else settings.paths.data_dir / f"dabiaoge_{report_type}_{args.business_date}.csv"
        write_csv_report(output, [row.to_dict() for row in parsed_rows], DAILY_FIELDS)
        print(f"[import_dabiaoge_daily] wrote {len(parsed_rows)} rows to {output}")


def main() -> None:
    run_job("import_dabiaoge_daily", "Import dBiaoGe daily report data.", _handler)


if __name__ == "__main__":
    main()
