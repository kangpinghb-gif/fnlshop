from __future__ import annotations

from collections.abc import Sequence

from freshos.config import Settings
from freshos.db.connection import connect


FRESH_ORDER_COLUMNS = [
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


def upsert_fresh_order_imports(settings: Settings, rows: Sequence[dict[str, object]]) -> int:
    if not rows:
        return 0

    placeholders = ", ".join(["%s"] * len(FRESH_ORDER_COLUMNS))
    columns = ", ".join(FRESH_ORDER_COLUMNS)
    updates = ", ".join(
        f"{column} = EXCLUDED.{column}"
        for column in FRESH_ORDER_COLUMNS
        if column not in {"source_file_name", "source_sheet_name", "raw_row_number"}
    )
    sql = f"""
        INSERT INTO fresh_order_imports ({columns})
        VALUES ({placeholders})
        ON CONFLICT (source_file_name, source_sheet_name, raw_row_number)
        DO UPDATE SET
            {updates},
            imported_at = now()
    """

    values = [tuple(row.get(column) for column in FRESH_ORDER_COLUMNS) for row in rows]
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, values)
    return len(values)

