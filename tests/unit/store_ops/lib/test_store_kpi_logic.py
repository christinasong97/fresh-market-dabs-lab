from store_kpi_logic import StorePerformance, classify, flag_underperformers


def test_attainment_handles_missing_target():
    assert StorePerformance(1, "Fresh Market Holland", "West Michigan", 500.0, 0).attainment_pct == 0.0


def test_classify_boundaries():
    assert classify(84.9, 85) == "UNDERPERFORMING"
    assert classify(85.0, 85) == "WATCH"
    assert classify(100.0, 85) == "ON_TARGET"


def test_flag_underperformers_sorted_worst_first():
    rows = flag_underperformers(
        [
            StorePerformance(1, "A", "Ohio", 1000, 1000),
            StorePerformance(2, "B", "Ohio", 700, 1000),
            StorePerformance(3, "C", "Ohio", 900, 1000),
        ],
        threshold_pct=85,
    )
    assert [r["store_id"] for r in rows] == [2, 3, 1]
    assert [r["status"] for r in rows] == ["UNDERPERFORMING", "WATCH", "ON_TARGET"]
