from __future__ import annotations

from jobs._bootstrap import run_job
from freshos.db.inventory_risks import generate_inventory_risks


def _handler(args, settings) -> None:
    print(f"[generate_inventory_risks] business_date={args.business_date}")
    if not settings.database.enabled:
        print("[generate_inventory_risks] database disabled; skip")
        return
    count = generate_inventory_risks(settings, business_date=args.business_date)
    print(f"[generate_inventory_risks] inserted {count} inventory_risks rows")


def main() -> None:
    run_job("generate_inventory_risks", "Generate inventory risks.", _handler)


if __name__ == "__main__":
    main()
