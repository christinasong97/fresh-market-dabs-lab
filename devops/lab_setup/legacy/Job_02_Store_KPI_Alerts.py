# Databricks notebook source
# MAGIC %md
# MAGIC # Job_02 Store KPI Alerts
# MAGIC Built by hand in the workspace, the way jobs are built today. Run after Job_01 finishes.
# MAGIC (Lab starting point: attendees bring this job into the bundle in module 1.)

# COMMAND ----------

# Hard-coded for INT. Change these before handing the job to DevOps for CERT and PROD.
CATALOG = "fresh_market_lab_int"
LANDING = "/Volumes/fresh_market_lab_int/landing/raw"
THRESHOLD = 85

# COMMAND ----------

from pyspark.sql import functions as F

txns = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{LANDING}/pos_transactions/")
stores = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{LANDING}/stores/")
targets = spark.read.option("header", "true").option("inferSchema", "true").csv(f"{LANDING}/store_targets/")

recent = txns.where(F.to_date("transaction_ts") > F.date_sub(F.current_date(), 15)).where("store_id IS NOT NULL AND quantity > 0")
days = recent.select(F.countDistinct(F.to_date("transaction_ts"))).first()[0]

kpis = (
    recent.groupBy("store_id").agg(F.sum("total_amount").alias("net_sales"))
    .join(stores, "store_id").join(targets, "store_id")
    .withColumn("attainment_pct", F.round(100 * F.col("net_sales") / (F.col("daily_sales_target") * days), 1))
    .withColumn("status", F.when(F.col("attainment_pct") < THRESHOLD, "UNDERPERFORMING").otherwise("OK"))
)
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.legacy_store_ops")
kpis.write.mode("overwrite").saveAsTable(f"{CATALOG}.legacy_store_ops.store_alerts")
display(kpis.where("status = 'UNDERPERFORMING'").orderBy("attainment_pct"))
