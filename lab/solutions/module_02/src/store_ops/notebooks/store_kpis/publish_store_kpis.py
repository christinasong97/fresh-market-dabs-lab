# Databricks notebook source
# MAGIC %md
# MAGIC # Publish store KPIs
# MAGIC Thin entrypoint: reads widgets, delegates to `lib/store_kpi_logic.py`, writes the alert table,
# MAGIC and sets `flagged_count` for the downstream condition task.

# COMMAND ----------

import os
import sys

sys.path.append(os.path.abspath("../../lib"))

from store_kpi_logic import StorePerformance, flag_underperformers  # noqa: E402

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
dbutils.widgets.text("lookback_days", "14")
dbutils.widgets.text("threshold_pct", "85")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
lookback_days = int(dbutils.widgets.get("lookback_days"))
threshold_pct = float(dbutils.widgets.get("threshold_pct"))

# COMMAND ----------

recent = spark.sql(f"""
    SELECT store_id, store_name, region,
           SUM(net_sales) AS net_sales,
           SUM(daily_sales_target) AS target_sales
    FROM `{catalog}`.`{schema}`.gold_daily_store_sales
    WHERE sales_date > (SELECT MAX(sales_date) FROM `{catalog}`.`{schema}`.gold_daily_store_sales) - INTERVAL {lookback_days} DAYS
    GROUP BY store_id, store_name, region
""").collect()

stores = [StorePerformance(r.store_id, r.store_name, r.region, float(r.net_sales), float(r.target_sales or 0)) for r in recent]
rows = flag_underperformers(stores, threshold_pct)

(
    spark.createDataFrame(rows)
    .selectExpr("*", "current_timestamp() AS evaluated_at", f"{lookback_days} AS lookback_days")
    .write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable(f"`{catalog}`.`{schema}`.gold_store_alerts")
)

flagged = [r for r in rows if r["status"] == "UNDERPERFORMING"]
dbutils.jobs.taskValues.set(key="flagged_count", value=len(flagged))
print(f"{len(flagged)} of {len(rows)} stores below {threshold_pct}% of target over the last {lookback_days} days")
