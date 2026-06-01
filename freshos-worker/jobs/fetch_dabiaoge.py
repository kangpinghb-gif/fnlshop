from __future__ import annotations

from jobs._bootstrap import run_job
from freshos.importers.dabiaoge_fetch import check_required_dabiaoge_exports


def _handler(args, settings) -> None:
    print(f"[fetch_dabiaoge] business_date={args.business_date}")
    print(f"[fetch_dabiaoge] checking data_dir={settings.paths.data_dir}")
    results = check_required_dabiaoge_exports(settings.paths.data_dir, args.business_date)
    missing = [result for result in results if not result.is_present]
    for result in results:
        if result.is_present:
            files = ", ".join(str(path) for path in result.matched_files)
            print(f"[fetch_dabiaoge] found {result.report_type}: {files}")
        else:
            patterns = ", ".join(result.patterns)
            print(f"[fetch_dabiaoge] missing {result.report_type}: expected one of {patterns}")
    if missing:
        missing_types = ", ".join(result.report_type for result in missing)
        raise FileNotFoundError(
            f"Hermes exports are missing for {args.business_date}: {missing_types}. "
            "Export files to settings.paths.data_dir before running FreshOS jobs."
        )


def main() -> None:
    run_job("fetch_dabiaoge", "Check dBiaoGe export files for FreshOS V1.1.", _handler)


if __name__ == "__main__":
    main()
