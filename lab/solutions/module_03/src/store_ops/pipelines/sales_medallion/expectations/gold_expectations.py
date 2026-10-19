"""Gold (business-facing) invariants. A violation fails the update so consumers never see bad data."""

GOLD_FAIL_RULES = {
    "store_matched": "store_name IS NOT NULL",
    "non_negative_sales": "net_sales >= 0",
    "positive_transactions": "transaction_count > 0",
}
