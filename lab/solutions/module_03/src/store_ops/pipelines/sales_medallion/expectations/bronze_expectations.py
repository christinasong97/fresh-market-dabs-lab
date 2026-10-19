"""Bronze (raw landing) rules. Soft checks only: record the metric, keep the row."""

BRONZE_RULES = {
    "has_transaction_id": "transaction_id IS NOT NULL",
    "has_source_file": "_source_file IS NOT NULL",
}
