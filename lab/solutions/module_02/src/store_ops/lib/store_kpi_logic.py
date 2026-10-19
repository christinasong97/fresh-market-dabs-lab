"""Pure store KPI logic. No Spark, no widgets, so it is unit-tested in seconds."""

from dataclasses import dataclass


@dataclass(frozen=True)
class StorePerformance:
    store_id: int
    store_name: str
    region: str
    net_sales: float
    target_sales: float

    @property
    def attainment_pct(self) -> float:
        if not self.target_sales:
            return 0.0
        return round(100.0 * self.net_sales / self.target_sales, 1)


def classify(attainment_pct: float, threshold_pct: float) -> str:
    """Return the store's status for the review list."""
    if attainment_pct < threshold_pct:
        return "UNDERPERFORMING"
    if attainment_pct < 100:
        return "WATCH"
    return "ON_TARGET"


def flag_underperformers(stores: list[StorePerformance], threshold_pct: float) -> list[dict]:
    """Rows for the store alert table, worst attainment first."""
    rows = [
        {
            "store_id": s.store_id,
            "store_name": s.store_name,
            "region": s.region,
            "net_sales": round(s.net_sales, 2),
            "target_sales": round(s.target_sales, 2),
            "attainment_pct": s.attainment_pct,
            "status": classify(s.attainment_pct, threshold_pct),
        }
        for s in stores
    ]
    return sorted(rows, key=lambda r: r["attainment_pct"])
