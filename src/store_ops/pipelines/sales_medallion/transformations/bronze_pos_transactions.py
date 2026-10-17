from pyspark import pipelines as dp
from pyspark.sql import functions as F

from expectations.bronze_expectations import BRONZE_RULES

LANDING_PATH = spark.conf.get("so.landing_path")

POS_SCHEMA = """
    transaction_id STRING, store_id INT, product_id INT, transaction_ts TIMESTAMP,
    quantity INT, unit_price DECIMAL(10,2), discount_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2), payment_type STRING, rewards_member BOOLEAN
"""


@dp.table(comment="Raw POS line items, incrementally ingested from the landing volume with Auto Loader.")
@dp.expect_all(BRONZE_RULES)
def bronze_pos_transactions():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(POS_SCHEMA)
        .load(f"{LANDING_PATH}/pos_transactions/")
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_ingested_at", F.current_timestamp())
    )
