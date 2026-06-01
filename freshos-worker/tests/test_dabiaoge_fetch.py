from freshos.importers.dabiaoge_fetch import check_required_dabiaoge_exports, find_dabiaoge_exports


def test_check_required_dabiaoge_exports_finds_expected_files(tmp_path):
    business_date = "2026-06-02"
    for name in [
        "dabiaoge_base_40_42_2026-06-02.xlsx",
        "dabiaoge_sales_40_42_2026-06-02.xlsx",
        "dabiaoge_inventory_loss_40_42_2026-06-02.xlsx",
        "dabiaoge_purchase_receipts_40_42_2026-06-02.xlsx",
        "dabiaoge_cutoff_sales_40_42_2026-06-02.xlsx",
    ]:
        (tmp_path / name).write_text("placeholder", encoding="utf-8")

    results = check_required_dabiaoge_exports(tmp_path, business_date)

    assert all(result.is_present for result in results)
    assert {result.report_type for result in results} == {
        "base",
        "sales",
        "inventory_loss",
        "purchase_receipts",
        "cutoff_sales",
    }


def test_check_required_dabiaoge_exports_reports_missing_files(tmp_path):
    (tmp_path / "dabiaoge_base_40_42_2026-06-02.xlsx").write_text("placeholder", encoding="utf-8")

    results = check_required_dabiaoge_exports(tmp_path, "2026-06-02")
    missing = [result.report_type for result in results if not result.is_present]

    assert missing == ["sales", "inventory_loss", "purchase_receipts", "cutoff_sales"]


def test_find_dabiaoge_exports_includes_optional_inventory_snapshot(tmp_path):
    (tmp_path / "dabiaoge_inventory_snapshot_40_42_2026-06-02.xlsx").write_text("placeholder", encoding="utf-8")

    exports = find_dabiaoge_exports(tmp_path, "2026-06-02")

    assert exports["inventory_snapshot"] == [tmp_path / "dabiaoge_inventory_snapshot_40_42_2026-06-02.xlsx"]
