from pyspark import pipelines as dp
from pyspark.sql import functions as F

from expectations.gold_expectations import GOLD_FAIL_RULES


@dp.materialized_view(comment="Daily net sales per store, with target attainment. Feeds the dashboard and Genie space.")
@dp.expect_all_or_fail(GOLD_FAIL_RULES)
def gold_daily_store_sales():
    txns = spark.read.table("silver_pos_transactions")
    stores = spark.read.table("silver_stores")
    targets = spark.read.table("silver_store_targets")
    daily = txns.groupBy("store_id", "sales_date").agg(
        F.sum("total_amount").alias("net_sales"),
        F.sum("discount_amount").alias("discounts"),
        F.countDistinct("transaction_id").alias("transaction_count"),
        F.sum("quantity").alias("units_sold"),
        F.avg(F.col("rewards_member").cast("int")).alias("rewards_share"),
    )
    return (
        daily.join(stores, "store_id", "left")
        .join(targets, "store_id", "left")
        .withColumn("target_attainment_pct", F.round(100 * F.col("net_sales") / F.col("daily_sales_target"), 1))
        .select(
            "sales_date",
            "store_id",
            "store_name",
            "city",
            "state",
            "region",
            "store_format",
            "net_sales",
            "discounts",
            "transaction_count",
            "units_sold",
            "rewards_share",
            "daily_sales_target",
            "target_attainment_pct",
        )
    )


@dp.materialized_view(comment="Daily net sales per department across all stores.")
def gold_department_sales():
    txns = spark.read.table("silver_pos_transactions")
    products = spark.read.table("silver_products")
    return (
        txns.join(products, "product_id", "left")
        .groupBy("sales_date", "department", "category")
        .agg(F.sum("total_amount").alias("net_sales"), F.sum("quantity").alias("units_sold"))
    )
