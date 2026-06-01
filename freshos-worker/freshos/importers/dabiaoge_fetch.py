from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_DABIAOGE_EXPORTS = {
    "base": ["dabiaoge_base_40_42_{date}.*", "dabiaoge_stores_products_base_{date}.*"],
    "sales": ["dabiaoge_sales_40_42_{date}.*", "dabiaoge_sales_daily_{date}.*"],
    "inventory_loss": ["dabiaoge_inventory_loss_40_42_{date}.*", "dabiaoge_inventory_loss_daily_{date}.*"],
    "purchase_receipts": ["dabiaoge_purchase_receipts_40_42_{date}.*", "dabiaoge_purchase_receipts_daily_{date}.*"],
    "cutoff_sales": ["dabiaoge_cutoff_sales_40_42_{date}.*", "dabiaoge_realtime_sales_12_{date}.*"],
}

OPTIONAL_DABIAOGE_EXPORTS = {
    "inventory_snapshot": ["dabiaoge_inventory_snapshot_40_42_{date}.*", "dabiaoge_realtime_inventory_{date}.*"],
}


@dataclass(frozen=True)
class ExportCheckResult:
    report_type: str
    matched_files: list[Path]
    patterns: list[str]

    @property
    def is_present(self) -> bool:
        return bool(self.matched_files)


def check_required_dabiaoge_exports(data_dir: Path, business_date: str) -> list[ExportCheckResult]:
    return [
        check_dabiaoge_export(data_dir, report_type=report_type, business_date=business_date, patterns=patterns)
        for report_type, patterns in REQUIRED_DABIAOGE_EXPORTS.items()
    ]


def find_dabiaoge_exports(data_dir: Path, business_date: str) -> dict[str, list[Path]]:
    patterns_by_type = REQUIRED_DABIAOGE_EXPORTS | OPTIONAL_DABIAOGE_EXPORTS
    return {
        report_type: check_dabiaoge_export(
            data_dir,
            report_type=report_type,
            business_date=business_date,
            patterns=patterns,
        ).matched_files
        for report_type, patterns in patterns_by_type.items()
    }


def check_dabiaoge_export(
    data_dir: Path,
    *,
    report_type: str,
    business_date: str,
    patterns: list[str],
) -> ExportCheckResult:
    matched_files: list[Path] = []
    for pattern in patterns:
        matched_files.extend(sorted(data_dir.glob(pattern.format(date=business_date))))
    return ExportCheckResult(
        report_type=report_type,
        matched_files=matched_files,
        patterns=[pattern.format(date=business_date) for pattern in patterns],
    )
