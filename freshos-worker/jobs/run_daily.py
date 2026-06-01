from __future__ import annotations

import subprocess
import sys

from jobs._bootstrap import parse_job_args
from freshos.config import load_settings
from freshos.importers.dabiaoge_fetch import find_dabiaoge_exports


DAILY_REPORT_TYPES = ["sales", "inventory_loss", "purchase_receipts", "inventory_snapshot", "cutoff_sales"]


def main() -> None:
    args = parse_job_args("Run FreshOS daily job chain.")
    settings = load_settings(args.config)
    exports = find_dabiaoge_exports(settings.paths.data_dir, args.business_date)

    _run_module(args, "jobs.fetch_dabiaoge")
    _run_module(args, "jobs.import_dabiaoge_base", _input_args(exports.get("base", [])))
    for report_type in DAILY_REPORT_TYPES:
        _run_module(
            args,
            "jobs.import_dabiaoge_daily",
            ["--report-type", report_type] + _input_args(exports.get(report_type, [])),
        )
    _run_module(args, "jobs.import_orders")
    _run_module(args, "jobs.match_order_imports")
    _run_module(args, "jobs.import_stock_adjustments")
    _run_module(args, "jobs.calculate_inventory")
    _run_module(args, "jobs.forecast_sales")
    _run_module(args, "jobs.generate_order_suggestions")
    _run_module(args, "jobs.generate_inventory_risks")
    _run_module(args, "jobs.export_reports")
    _run_module(args, "jobs.notify")


def _run_module(args, module: str, extra_args: list[str] | None = None) -> None:
    cmd = [
        sys.executable,
        "-m",
        module,
        "--config",
        args.config,
        "--business-date",
        args.business_date,
    ]
    if extra_args:
        cmd.extend(extra_args)
    print(f"[run_daily] running {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def _input_args(paths) -> list[str]:
    args = []
    for path in paths:
        args.extend(["--input", str(path)])
    return args


if __name__ == "__main__":
    main()
