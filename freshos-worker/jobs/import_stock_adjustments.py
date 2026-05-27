from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.stock_adjustments import upsert_stock_count_adjustments
from freshos.importers.stock_adjustments import parse_stock_adjustment_file
from freshos.reports.csv_report import write_csv_report


STOCK_ADJUSTMENT_FIELDS = [
    "source_file_name",
    "source_sheet_name",
    "raw_row_number",
    "store_code",
    "store_name",
    "product_code",
    "product_name",
    "count_time",
    "business_date",
    "adjusted_quantity",
    "unit",
    "count_type",
    "remark",
]


def _handler(args, settings) -> None:
    print(f"[import_stock_adjustments] business_date={args.business_date}")
    if not args.input:
        print("[import_stock_adjustments] no --input files provided; skip")
        return

    parsed_rows = []
    for input_path in args.input:
        rows = parse_stock_adjustment_file(input_path, default_business_date=args.business_date)
        parsed_rows.extend(rows)
        print(f"[import_stock_adjustments] parsed {len(rows)} rows from {input_path}")

    if settings.database.enabled:
        written = upsert_stock_count_adjustments(settings, parsed_rows)
        print(
            "[import_stock_adjustments] "
            f"inserted={written['inserted']} exceptions={written['exceptions']}"
        )

    if args.output or not settings.database.enabled:
        output = Path(args.output) if args.output else settings.paths.data_dir / f"stock_count_adjustments_{args.business_date}.csv"
        write_csv_report(output, [row.to_dict() for row in parsed_rows], STOCK_ADJUSTMENT_FIELDS)
        print(f"[import_stock_adjustments] wrote {len(parsed_rows)} rows to {output}")


def main() -> None:
    run_job("import_stock_adjustments", "Import manual stock count adjustments.", _handler)


if __name__ == "__main__":
    main()
