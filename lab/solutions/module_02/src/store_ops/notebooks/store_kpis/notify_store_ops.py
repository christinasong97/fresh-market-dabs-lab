# Databricks notebook source
# MAGIC %md
# MAGIC # Notify store operations
# MAGIC Runs only when the condition task finds underperforming stores. In the lab this logs the
# MAGIC review request; in production it would open work items for the regional managers.

# COMMAND ----------

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

flagged = spark.sql(f"""
    SELECT store_name, region, attainment_pct
    FROM `{catalog}`.`{schema}`.gold_store_alerts
    WHERE status = 'UNDERPERFORMING'
    ORDER BY attainment_pct
""")
display(flagged)
for r in flagged.collect():
    print(f"Review requested: {r.store_name} ({r.region}) at {r.attainment_pct}% of target")
