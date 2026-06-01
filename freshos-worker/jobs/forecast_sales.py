from __future__ import annotations

from datetime import date, timedelta

from jobs._bootstrap import run_job
from freshos.db.forecasts import generate_sales_forecasts


def _handler(args, settings) -> None:
    print(f"[forecast_sales] business_date={args.business_date}")
    if not settings.database.enabled:
        print("[forecast_sales] database disabled; skip")
        return
    order_date = date.fromisoformat(args.business_date)
    forecast_date = (order_date + timedelta(days=1)).isoformat()
    count = generate_sales_forecasts(settings, forecast_date=forecast_date, order_date=args.business_date)
    print(f"[forecast_sales] upserted {count} sales_forecasts rows forecast_date={forecast_date}")


def main() -> None:
    run_job("forecast_sales", "Forecast sales.", _handler)


if __name__ == "__main__":
    main()
