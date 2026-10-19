from pyspark import pipelines as dp

from expectations.silver_expectations import SILVER_PRODUCT_RULES, SILVER_STORE_RULES

LANDING_PATH = spark.conf.get("so.landing_path")


def _read_csv(folder):
    return spark.read.option("header", "true").option("inferSchema", "true").csv(f"{LANDING_PATH}/{folder}/")


@dp.materialized_view(comment="Store master data.")
@dp.expect_all_or_drop(SILVER_STORE_RULES)
def silver_stores():
    return _read_csv("stores")


@dp.materialized_view(comment="Product master data.")
@dp.expect_all_or_drop(SILVER_PRODUCT_RULES)
def silver_products():
    return _read_csv("products")


@dp.materialized_view(comment="Daily sales target per store, set by store operations.")
def silver_store_targets():
    return _read_csv("store_targets")
