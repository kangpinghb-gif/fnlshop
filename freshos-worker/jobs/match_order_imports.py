from __future__ import annotations

from jobs._bootstrap import run_job
from freshos.db.order_matching import match_pending_order_imports


def _handler(args, settings) -> None:
    print(f"[match_order_imports] business_date={args.business_date}")
    if not settings.database.enabled:
        print("[match_order_imports] database disabled; skip")
        return
    result = match_pending_order_imports(settings)
    print(
        "[match_order_imports] "
        f"total={result['total']} matched={result['matched']} failed={result['failed']}"
    )


def main() -> None:
    run_job("match_order_imports", "Match fresh order imports to stores and products.", _handler)


if __name__ == "__main__":
    main()

