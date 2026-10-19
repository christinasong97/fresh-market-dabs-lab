"""Silver (cleaned, normalized) rules. Rows that break these are dropped, the pipeline continues."""

SILVER_DROP_RULES = {
    "valid_store_id": "store_id IS NOT NULL",
    "valid_product_id": "product_id IS NOT NULL",
    "positive_quantity": "quantity > 0",
    "non_negative_amount": "total_amount IS NOT NULL AND total_amount >= 0",
    "valid_transaction_ts": "transaction_ts IS NOT NULL",
}

SILVER_STORE_RULES = {
    "valid_store_id": "store_id IS NOT NULL",
    "known_state": "state IN ('MI', 'OH', 'IN', 'IL', 'KY', 'WI')",
}

SILVER_PRODUCT_RULES = {
    "valid_product_id": "product_id IS NOT NULL",
    "has_department": "department IS NOT NULL",
}
