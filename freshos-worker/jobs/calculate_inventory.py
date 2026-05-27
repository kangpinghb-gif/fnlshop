from __future__ import annotations

from jobs._bootstrap import run_job
from freshos.db.inventory_age import calculate_inventory_age_batches
from freshos.db.inventory import calculate_inventory_positions


def _handler(args, settings) -> None:
    print(f"[calculate_inventory] business_date={args.business_date}")
    if not settings.database.enabled:
        print("[calculate_inventory] database disabled; skip")
        return
    position_count = calculate_inventory_positions(settings, business_date=args.business_date)
    age_count = calculate_inventory_age_batches(settings, business_date=args.business_date)
    print(f"[calculate_inventory] upserted {position_count} inventory_positions rows")
    print(f"[calculate_inventory] upserted {age_count} inventory_age_batches rows")


def main() -> None:
    run_job("calculate_inventory", "Calculate inventory positions and age batches.", _handler)


if __name__ == "__main__":
    main()
