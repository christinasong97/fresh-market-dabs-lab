# Databricks notebook source
# MAGIC %md
# MAGIC # Publish weekly department report
# MAGIC Week-over-week net sales by department for the merchandising team.

# COMMAND ----------

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")

spark.sql(f"""
    CREATE OR REPLACE TABLE `{catalog}`.`{schema}`.gold_weekly_department_report AS
    SELECT DATE_TRUNC('WEEK', sales_date) AS week_start, department,
           SUM(net_sales) AS net_sales,
           SUM(net_sales) - LAG(SUM(net_sales))
               OVER (PARTITION BY department ORDER BY DATE_TRUNC('WEEK', sales_date)) AS wow_change
    FROM `{catalog}`.`{schema}`.gold_department_sales
    GROUP BY 1, 2
""")
display(spark.table(f"`{catalog}`.`{schema}`.gold_weekly_department_report").orderBy("week_start", "department"))
