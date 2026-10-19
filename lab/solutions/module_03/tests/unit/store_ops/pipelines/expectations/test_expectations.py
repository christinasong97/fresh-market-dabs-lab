"""Expectation dictionaries are plain Python, so we can check them without a pipeline."""

import re

import pytest
import sqlglot

from expectations import bronze_expectations, gold_expectations, silver_expectations

RULE_SETS = {
    "BRONZE_RULES": bronze_expectations.BRONZE_RULES,
    "SILVER_DROP_RULES": silver_expectations.SILVER_DROP_RULES,
    "SILVER_STORE_RULES": silver_expectations.SILVER_STORE_RULES,
    "SILVER_PRODUCT_RULES": silver_expectations.SILVER_PRODUCT_RULES,
    "GOLD_FAIL_RULES": gold_expectations.GOLD_FAIL_RULES,
}


@pytest.mark.parametrize("set_name", RULE_SETS)
def test_rules_parse_as_sql(set_name):
    for name, expr in RULE_SETS[set_name].items():
        sqlglot.parse_one(expr, read="databricks")  # raises on a typo


@pytest.mark.parametrize("set_name", RULE_SETS)
def test_rule_names_are_snake_case(set_name):
    for name in RULE_SETS[set_name]:
        assert re.fullmatch(r"[a-z][a-z0-9_]*", name), f"{set_name}.{name} is not snake_case"


def test_silver_has_required_invariants():
    required = {"valid_store_id", "valid_product_id", "positive_quantity", "non_negative_amount"}
    assert required <= set(silver_expectations.SILVER_DROP_RULES)


def test_gold_has_required_invariants():
    assert {"store_matched", "non_negative_sales"} <= set(gold_expectations.GOLD_FAIL_RULES)
