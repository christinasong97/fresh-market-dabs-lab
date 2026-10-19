from pyspark import pipelines as dp
from pyspark.sql import functions as F

from expectations.silver_expectations import SILVER_DROP_RULES


@dp.table(comment="Cleaned POS line items. Rows failing SILVER_DROP_RULES are dropped and counted.")
@dp.expect_all_or_drop(SILVER_DROP_RULES)
def silver_pos_transactions():
    return (
        spark.readStream.table("bronze_pos_transactions")
        .withColumn("sales_date", F.to_date("transaction_ts"))
        .drop("_source_file")
    )
