from __future__ import annotations

from freshos.config import Settings
from freshos.db.connection import connect


def fetch_order_suggestion_report_rows(settings: Settings, *, suggestion_date: str) -> list[dict[str, object]]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            return _fetch_order_suggestion_report_rows(cur, suggestion_date=suggestion_date)


def fetch_inventory_risk_report_rows(settings: Settings, *, business_date: str) -> list[dict[str, object]]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            return _fetch_inventory_risk_report_rows(cur, business_date=business_date)


def fetch_import_exception_report_rows(settings: Settings) -> list[dict[str, object]]:
    with connect(settings.database.dsn) as conn:
        with conn.cursor() as cur:
            return _fetch_import_exception_report_rows(cur)


def _fetch_order_suggestion_report_rows(cur, *, suggestion_date: str) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            s.store_name,
            p.product_name,
            os.corrected_inventory_qty,
            os.forecast_quantity,
            os.safety_stock_qty,
            os.pending_arrival_qty,
            os.suggested_order_qty,
            os.suggestion_reason,
            COALESCE(r.high_risk_count, 0)
        FROM order_suggestions os
        JOIN stores s ON s.id = os.store_id
        JOIN products p ON p.id = os.product_id
        LEFT JOIN (
            SELECT store_id, product_id, COUNT(*) AS high_risk_count
            FROM inventory_risks
            WHERE business_date = %s
              AND risk_level = 'high'
              AND status = 'open'
            GROUP BY store_id, product_id
        ) r ON r.store_id = os.store_id AND r.product_id = os.product_id
        WHERE os.suggestion_date = %s
        ORDER BY s.store_name, p.product_name
        """,
        (suggestion_date, suggestion_date),
    )
    return [
        {
            "门店": row[0],
            "商品": row[1],
            "当前库存": row[2],
            "预测销量": row[3],
            "安全库存": row[4],
            "已订未到": row[5],
            "建议订货量": row[6],
            "订货原因": row[7],
            "风险标记": "高风险" if row[8] else "",
        }
        for row in cur.fetchall()
    ]


def _fetch_import_exception_report_rows(cur) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            source_file_name,
            source_table,
            raw_row_number,
            exception_type,
            exception_message,
            status,
            created_at
        FROM import_exceptions
        WHERE status = 'open'
        ORDER BY created_at DESC, source_file_name, raw_row_number
        """
    )
    return [
        {
            "来源文件": row[0],
            "来源表": row[1],
            "原始行号": row[2],
            "异常类型": row[3],
            "异常说明": row[4],
            "处理状态": row[5],
            "创建时间": row[6],
        }
        for row in cur.fetchall()
    ]


def _fetch_inventory_risk_report_rows(cur, *, business_date: str) -> list[dict[str, object]]:
    cur.execute(
        """
        SELECT
            s.store_name,
            p.product_name,
            ir.risk_type,
            ir.risk_level,
            ir.risk_message,
            ir.related_quantity,
            ir.status
        FROM inventory_risks ir
        JOIN stores s ON s.id = ir.store_id
        JOIN products p ON p.id = ir.product_id
        WHERE ir.business_date = %s
        ORDER BY
            CASE ir.risk_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            s.store_name,
            p.product_name,
            ir.risk_type
        """,
        (business_date,),
    )
    return [
        {
            "门店": row[0],
            "商品": row[1],
            "风险类型": row[2],
            "风险等级": row[3],
            "风险说明": row[4],
            "相关数量": row[5],
            "处理状态": row[6],
        }
        for row in cur.fetchall()
    ]
