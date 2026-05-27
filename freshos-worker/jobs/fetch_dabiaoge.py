from __future__ import annotations

from jobs._bootstrap import run_job


def _handler(args, settings) -> None:
    print(f"[fetch_dabiaoge] business_date={args.business_date}")
    print("[fetch_dabiaoge] placeholder: browser/Hermes integration will be added after export route is stable.")


def main() -> None:
    run_job("fetch_dabiaoge", "Fetch dBiaoGe data for FreshOS V1.", _handler)


if __name__ == "__main__":
    main()
