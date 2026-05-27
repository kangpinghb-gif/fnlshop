from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_job_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", default="config/settings.example.toml")
    parser.add_argument("--business-date", default=date.today().isoformat())
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output", default="")
    parser.add_argument("--report-type", default="")
    return parser.parse_args()


def run_job(job_name: str, description: str, handler: Callable[[argparse.Namespace, object], None]) -> None:
    from freshos.config import load_settings
    from freshos.db.job_runs import job_run

    args = parse_job_args(description)
    settings = load_settings(args.config)
    with job_run(settings, job_name=job_name, business_date=args.business_date):
        handler(args, settings)
