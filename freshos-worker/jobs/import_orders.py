from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.orders import upsert_fresh_order_imports
from freshos.importers.order_importer import parse_order_workbook, rows_to_dicts
from freshos.reports.csv_report import write_csv_report


ORDER_IMPORT_FIELDS = [
    "source_file_name",
    "source_sheet_name",
    "source_format",
    "supplier_code",
    "supplier_name",
    "store_name_raw",
    "product_name_raw",
    "order_date",
    "arrival_date",
    "ordered_quantity",
    "arrival_quantity",
    "gross_quantity",
    "tare_quantity",
    "received_quantity",
    "unit",
    "match_status",
    "remark",
    "raw_row_number",
]


def _handler(args, settings) -> None:
    print(f"[import_orders] business_date={args.business_date}")
    if not args.input:
        print("[import_orders] no --input files provided; skip")
        return

    parsed_rows = []
    for input_path in args.input:
        rows = parse_order_workbook(input_path)
        parsed_rows.extend(rows_to_dicts(rows))
        print(f"[import_orders] parsed {len(rows)} rows from {input_path}")

    if settings.database.enabled:
        written = upsert_fresh_order_imports(settings, parsed_rows)
        print(f"[import_orders] upserted {written} rows into fresh_order_imports")

    if args.output or not settings.database.enabled:
        output = Path(args.output) if args.output else settings.paths.data_dir / f"fresh_order_imports_{args.business_date}.csv"
        write_csv_report(output, parsed_rows, ORDER_IMPORT_FIELDS)
        print(f"[import_orders] wrote {len(parsed_rows)} rows to {output}")


def main() -> None:
    run_job("import_orders", "Import fresh order files.", _handler)


if __name__ == "__main__":
    main()
