# Databricks notebook source
# MAGIC %md
# MAGIC # Module 3 · Build the bundle with Genie Code (20 min)
# MAGIC
# MAGIC **Goal:** add the sales pipeline that feeds your KPI job, plus an orchestrator job that runs everything in order.
# MAGIC By the end, one bundle holds jobs, a pipeline, and a dashboard. (The Genie space joins in module 4.)

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.1 · The pipeline
# MAGIC
# MAGIC Ask Genie Code (agent mode):
# MAGIC
# MAGIC ```
# MAGIC Create a Spark Declarative Pipeline for store_ops called so_sales_medallion
# MAGIC (resources/pipelines/store_ops/so_sales_medallion.pipeline.yml, code in
# MAGIC src/store_ops/pipelines/sales_medallion/transformations/). Serverless. Catalog ${var.catalog}, schema
# MAGIC ${resources.schemas.so_store_ops.name}. Pass ${var.landing_path} to the code as the so.landing_path setting.
# MAGIC Bronze: Auto Loader over the POS CSVs in <landing_path>/pos_transactions.
# MAGIC Silver: clean transactions (drop rows with no store_id or product_id, non-positive quantity, or missing
# MAGIC total_amount), plus silver_stores, silver_products, and silver_store_targets from the stores, products, and
# MAGIC store_targets CSV folders.
# MAGIC Gold: gold_daily_store_sales (net sales, transaction count, and target attainment per store per day, with store
# MAGIC name, city, state, region, and store_format) and gold_department_sales (net sales per department per day).
# MAGIC Put the data quality rules in expectations/ dictionaries: bronze expect, silver expect_or_drop, gold
# MAGIC expect_or_fail.
# MAGIC ```
# MAGIC
# MAGIC Notice the severity convention: **drop** bad rows in silver, **fail** the run if gold breaks a rule, so nobody
# MAGIC downstream ever sees bad data.

# COMMAND ----------

expect_files(
    [
        "resources/pipelines/store_ops/so_sales_medallion.pipeline.yml",
        "src/store_ops/pipelines/sales_medallion/transformations",
        "src/store_ops/pipelines/sales_medallion/expectations",
    ]
)
for root, dirs, files in os.walk(f"{REPO_ROOT}/src/store_ops/pipelines/sales_medallion"):
    for name in sorted(files + [d for d in dirs if not d.startswith((".", "_"))]):
        print("   " + os.path.relpath(os.path.join(root, name), REPO_ROOT))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.2 · The orchestrator
# MAGIC
# MAGIC The old way encodes run order in file names (`Job_00`, `Job_01`, `Job_02`). The team's standard puts it in one
# MAGIC orchestrator per domain. Ask Genie Code:
# MAGIC
# MAGIC ```
# MAGIC Create resources/jobs/store_ops/orchestrator.job.yml with a job called so_orchestrator: first refresh the
# MAGIC so_sales_medallion pipeline, then run the so_store_kpis job. Schedule it daily at 6am America/Detroit.
# MAGIC ```

# COMMAND ----------

expect_files(["resources/jobs/store_ops/orchestrator.job.yml"])
show_file("resources/jobs/store_ops/orchestrator.job.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.3 · The dashboard was already code
# MAGIC
# MAGIC It came with the starter repo and points at the tables your pipeline just defined. Its queries use bare table
# MAGIC names; `dataset_catalog` and `dataset_schema` point them at `${var.catalog}` and your schema, so the same file
# MAGIC shows your data in dev and production data in prod. (The Genie space joins the bundle in module 4, once its
# MAGIC tables exist.)

# COMMAND ----------

show_file("resources/dashboards/store_ops/so_store_performance.dashboard.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.4 · Validate, then deploy
# MAGIC
# MAGIC Deployments panel: target **`dev`** → **Validate** → **Deploy**. Then run the checks.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 3
# MAGIC
# MAGIC **Next:** open **`04_Run_Your_Own_Copy`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Catch up (only if you need to)
# MAGIC
# MAGIC Behind, or Genie Code's pipeline won't validate? Remove the `#` and run this cell. It puts the finished module 3
# MAGIC files in your Git folder (and module 2's, if you skipped it). Then redeploy `dev` and continue.

# COMMAND ----------

# catch_up(2)
# catch_up(3)
