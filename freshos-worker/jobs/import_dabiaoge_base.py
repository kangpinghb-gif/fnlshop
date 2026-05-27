from __future__ import annotations

from pathlib import Path

from jobs._bootstrap import run_job
from freshos.db.dabiaoge_base import upsert_dabiaoge_base
from freshos.importers.dabiaoge_base import parse_dabiaoge_base_file
from freshos.reports.csv_report import write_csv_report


STORE_FIELDS = ["store_code", "store_name", "store_status"]
PRODUCT_FIELDS = [
    "product_code",
    "product_name",
    "barcode",
    "cat_id_01",
    "cat_name_01",
    "cat_id_02",
    "cat_name_02",
    "sale_unit",
    "fresh_attribute",
    "shelf_life_days",
]
STORE_PRODUCT_FIELDS = [
    "store_code",
    "product_code",
    "store_order_status",
    "store_sale_status",
    "is_orderable",
    "is_sellable",
    "package_size",
    "order_batch_qty",
    "safety_stock_days",
    "recent_daily_sales",
    "store_stock_qty_yesterday",
]


def _handler(args, settings) -> None:
    print(f"[import_dabiaoge_base] business_date={args.business_date}")
    if not args.input:
        print("[import_dabiaoge_base] no --input files provided; skip")
        return

    merged_stores = {}
    merged_products = {}
    merged_store_products = {}
    for input_path in args.input:
        result = parse_dabiaoge_base_file(input_path)
        merged_stores.update((row.store_code, row.to_dict()) for row in result.stores)
        merged_products.update((row.product_code, row.to_dict()) for row in result.products)
        merged_store_products.update(((row.store_code, row.product_code), row.to_dict()) for row in result.store_products)
        print(
            f"[import_dabiaoge_base] parsed {input_path}: "
            f"stores={len(result.stores)} products={len(result.products)} "
            f"store_products={len(result.store_products)}"
        )
        if settings.database.enabled:
            written = upsert_dabiaoge_base(settings, result)
            print(f"[import_dabiaoge_base] upserted {written}")

    if args.output or not settings.database.enabled:
        output_dir = Path(args.output) if args.output else settings.paths.data_dir / f"dabiaoge_base_{args.business_date}"
        write_csv_report(output_dir / "stores.csv", merged_stores.values(), STORE_FIELDS)
        write_csv_report(output_dir / "products.csv", merged_products.values(), PRODUCT_FIELDS)
        write_csv_report(output_dir / "store_products.csv", merged_store_products.values(), STORE_PRODUCT_FIELDS)
        print(f"[import_dabiaoge_base] wrote CSV outputs to {output_dir}")


def main() -> None:
    run_job("import_dabiaoge_base", "Import dBiaoGe stores/products/store-products base data.", _handler)


if __name__ == "__main__":
    main()
