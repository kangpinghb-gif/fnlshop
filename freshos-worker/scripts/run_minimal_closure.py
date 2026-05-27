from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from freshos.config import load_settings
from freshos.db.forecasts import generate_sales_forecasts
from freshos.db.inventory import calculate_inventory_positions
from freshos.db.inventory_risks import generate_inventory_risks
from freshos.db.migrations import apply_migrations
from freshos.db.order_suggestions import generate_order_suggestions
from freshos.db.reports import fetch_inventory_risk_report_rows, fetch_order_suggestion_report_rows
from freshos.reports.csv_report import write_csv_report
from jobs.export_reports import ORDER_REPORT_FIELDS, RISK_REPORT_FIELDS
from scripts.apply_seed_data import apply_seed_file


def run_minimal_closure(
    *,
    config_path: str,
    business_date: str,
    migrations_dir: str,
    seed_path: str,
) -> None:
    settings = load_settings(config_path)
    if not settings.database.enabled:
        raise SystemExit("database.enabled must be true for minimal closure verification.")
    if not settings.database.dsn:
        raise SystemExit("Database DSN is required.")

    print("[minimal_closure] applying migrations")
    applied = apply_migrations(settings.database.dsn, migrations_dir)
    for path in applied:
        print(f"[minimal_closure] applied migration {path}")

    print("[minimal_closure] applying seed data")
    applied_seed = apply_seed_file(settings.database.dsn, seed_path)
    print(f"[minimal_closure] applied seed {applied_seed}")

    print("[minimal_closure] calculating inventory positions")
    inventory_count = calculate_inventory_positions(settings, business_date=business_date)
    print(f"[minimal_closure] inventory_positions rows={inventory_count}")

    print("[minimal_closure] forecasting sales")
    forecast_count = generate_sales_forecasts(settings, forecast_date=business_date)
    print(f"[minimal_closure] sales_forecasts rows={forecast_count}")

    print("[minimal_closure] generating order suggestions")
    suggestion_count = generate_order_suggestions(settings, suggestion_date=business_date)
    print(f"[minimal_closure] order_suggestions rows={suggestion_count}")

    print("[minimal_closure] generating inventory risks")
    risk_count = generate_inventory_risks(settings, business_date=business_date)
    print(f"[minimal_closure] inventory_risks rows={risk_count}")

    print("[minimal_closure] exporting reports")
    order_rows = fetch_order_suggestion_report_rows(settings, suggestion_date=business_date)
    risk_rows = fetch_inventory_risk_report_rows(settings, business_date=business_date)
    order_path = settings.paths.report_dir / f"order_suggestions_{business_date}.csv"
    risk_path = settings.paths.report_dir / f"inventory_risks_{business_date}.csv"
    write_csv_report(order_path, order_rows, ORDER_REPORT_FIELDS)
    write_csv_report(risk_path, risk_rows, RISK_REPORT_FIELDS)
    print(f"[minimal_closure] wrote {order_path} rows={len(order_rows)}")
    print(f"[minimal_closure] wrote {risk_path} rows={len(risk_rows)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FreshOS V1 minimal closure verification.")
    parser.add_argument("--config", default="config/settings.toml")
    parser.add_argument("--business-date", default="2026-05-26")
    parser.add_argument("--migrations-dir", default="migrations")
    parser.add_argument("--seed", default="seeds/001_minimal_closure.sql")
    args = parser.parse_args()

    run_minimal_closure(
        config_path=args.config,
        business_date=args.business_date,
        migrations_dir=args.migrations_dir,
        seed_path=args.seed,
    )


if __name__ == "__main__":
    main()
