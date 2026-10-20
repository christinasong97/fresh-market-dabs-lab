# Databricks notebook source
# MAGIC %md
# MAGIC # Module 3 · Build the bundle with Genie Code (20 min)
# MAGIC
# MAGIC **Goal:** put the whole store sales data product in one bundle: the data, the job that uses it, the run order,
# MAGIC and the dashboard.
# MAGIC
# MAGIC Your KPI job from module 2 reads `gold_daily_store_sales`, but nothing creates that table yet. Today, a table
# MAGIC like this comes from another job, the run order lives in job names (`Job_00` → `Job_01` → `Job_02`), and each
# MAGIC piece is rebuilt by hand in every environment. If one piece reaches production without the other, it breaks.
# MAGIC
# MAGIC In this module, every piece goes into the same bundle:
# MAGIC
# MAGIC | Piece | What it does |
# MAGIC |---|---|
# MAGIC | Pipeline `so_sales_medallion` | Turns raw sales files into clean tables, like `gold_daily_store_sales` |
# MAGIC | Job `so_store_kpis` | Flags stores that are behind their sales target |
# MAGIC | Orchestrator `so_orchestrator` | Runs the pipeline first, then the KPI job |
# MAGIC | Dashboard `so_store_performance` | Shows the results |
# MAGIC
# MAGIC **One bundle means:** reviewed together in one pull request, deployed together with one click, and promoted
# MAGIC together to cert and prod. Nothing reaches production without the pieces it depends on.

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.1 · The pipeline
# MAGIC
# MAGIC The pipeline builds three layers of tables, often called a **medallion**:
# MAGIC
# MAGIC | Layer | What it holds |
# MAGIC |---|---|
# MAGIC | **Bronze** | The raw sales files, loaded as they arrive |
# MAGIC | **Silver** | Cleaned data, with bad rows dropped |
# MAGIC | **Gold** | Business-ready totals, like daily sales per store, that the KPI job and dashboard read |
# MAGIC
# MAGIC **Ask Genie Code** (agent mode):
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
# MAGIC **Why it matters:** a pipeline is a bundle resource just like a job. It uses the same variables (no hard-coded
# MAGIC catalog), the same naming rules, and the same rule checks. Its data quality rules (**expectations**: what counts
# MAGIC as a bad row) are code files too, so changing them goes through a pull request like any other change.
# MAGIC
# MAGIC Notice the severity convention: **drop** bad rows in silver, **fail** the run if gold breaks a rule, so nobody
# MAGIC downstream ever sees bad data.
# MAGIC
# MAGIC ✅ When it's done, run the cell. You should see the pipeline's YAML file, its code in `transformations/`, and its
# MAGIC data quality rules in `expectations/`, all inside your Git folder.

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
# MAGIC **Ask Genie Code:**
# MAGIC
# MAGIC ```
# MAGIC Create resources/jobs/store_ops/orchestrator.job.yml with a job called so_orchestrator: first refresh the
# MAGIC so_sales_medallion pipeline, then run the so_store_kpis job. Schedule it daily at 6am America/Detroit.
# MAGIC ```
# MAGIC
# MAGIC **Why it matters:** today, run order is encoded in names (`Job_00`, `Job_01`, `Job_02`) and in people's heads.
# MAGIC The team's standard puts it in one **orchestrator** job per domain, so the order is written down, reviewed, and
# MAGIC the same in every environment.

# COMMAND ----------

expect_files(["resources/jobs/store_ops/orchestrator.job.yml"])
show_file("resources/jobs/store_ops/orchestrator.job.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC **Read these lines in the YAML above:**
# MAGIC
# MAGIC ```
# MAGIC tasks:
# MAGIC   - task_key: refresh_sales
# MAGIC     pipeline_task:
# MAGIC       pipeline_id: ${resources.pipelines.so_sales_medallion.id}   ← run the pipeline from this bundle
# MAGIC
# MAGIC   - task_key: publish_store_kpis
# MAGIC     depends_on:
# MAGIC       - task_key: refresh_sales                                    ← only after the pipeline finishes
# MAGIC     run_job_task:
# MAGIC       job_id: ${resources.jobs.so_store_kpis.id}                   ← then run the KPI job from this bundle
# MAGIC ```
# MAGIC
# MAGIC The orchestrator points at the pipeline and the job by their **resource keys**, not by ID. Every environment
# MAGIC gives them different IDs, so a hard-coded ID would only work in one place. These lines work in dev, int, cert,
# MAGIC and prod, and on deploy the bundle creates the pipeline and the job before the orchestrator that needs them.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3.3 · The dashboard was already code
# MAGIC
# MAGIC **Why it matters:** a dashboard has the same problem as the job in module 1. If its queries say
# MAGIC `fresh_market_lab_int.store_ops.gold_daily_store_sales`, it only ever shows INT data, and someone has to edit every
# MAGIC query to move it to prod.
# MAGIC
# MAGIC In a bundle, a dashboard is two files:
# MAGIC
# MAGIC | File | What it holds |
# MAGIC |---|---|
# MAGIC | `src/store_ops/dashboards/store_performance.lvdash.json` | The dashboard itself: pages, charts, queries |
# MAGIC | `resources/dashboards/store_ops/so_store_performance.dashboard.yml` | Where it deploys and which data it reads |
# MAGIC
# MAGIC The queries use bare table names (`FROM gold_daily_store_sales`). Two lines in the YAML fill in the rest:
# MAGIC
# MAGIC | Line | What it means |
# MAGIC |---|---|
# MAGIC | `dataset_catalog: ${var.catalog}` | Read from this target's catalog |
# MAGIC | `dataset_schema: ${resources.schemas.so_store_ops.name}` | ...and this target's schema |
# MAGIC
# MAGIC Same dashboard file: your data in dev, production data in prod. It deploys with the pipeline that feeds it, so
# MAGIC the charts and the tables they read always move to production together.

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
