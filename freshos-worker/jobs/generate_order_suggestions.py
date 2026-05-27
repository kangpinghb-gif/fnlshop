from __future__ import annotations

from jobs._bootstrap import run_job
from freshos.db.order_suggestions import generate_order_suggestions


def _handler(args, settings) -> None:
    print(f"[generate_order_suggestions] business_date={args.business_date}")
    if not settings.database.enabled:
        print("[generate_order_suggestions] database disabled; skip")
        return
    count = generate_order_suggestions(settings, suggestion_date=args.business_date)
    print(f"[generate_order_suggestions] upserted {count} order_suggestions rows")


def main() -> None:
    run_job("generate_order_suggestions", "Generate order suggestions.", _handler)


if __name__ == "__main__":
    main()
