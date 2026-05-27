from __future__ import annotations

import subprocess
import sys

from jobs._bootstrap import parse_job_args


JOB_MODULES = [
    "jobs.fetch_dabiaoge",
    "jobs.import_dabiaoge_base",
    "jobs.import_orders",
    "jobs.match_order_imports",
    "jobs.import_stock_adjustments",
    "jobs.calculate_inventory",
    "jobs.forecast_sales",
    "jobs.generate_order_suggestions",
    "jobs.generate_inventory_risks",
    "jobs.export_reports",
    "jobs.notify",
]


def main() -> None:
    args = parse_job_args("Run FreshOS daily job chain.")
    for module in JOB_MODULES:
        cmd = [
            sys.executable,
            "-m",
            module,
            "--config",
            args.config,
            "--business-date",
            args.business_date,
        ]
        print(f"[run_daily] running {' '.join(cmd)}")
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
