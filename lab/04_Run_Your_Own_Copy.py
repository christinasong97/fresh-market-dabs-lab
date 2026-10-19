# Databricks notebook source
# MAGIC %md
# MAGIC # Module 4 · Your own development target (15 min)
# MAGIC
# MAGIC **Goal:** run the real thing, in your own isolated copy, without touching anyone else's work.
# MAGIC
# MAGIC `int`, `cert`, and `prod` are locked to the CI/CD service principal, so only CI can deploy them. The **`dev`**
# MAGIC target is what lets you test yourself. Many team templates don't have one; it's the piece that makes developer
# MAGIC ownership possible.

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.1 · Deploy, then run the orchestrator
# MAGIC
# MAGIC Deployments panel: target **`dev`** → **Deploy**. Then run the cell. It runs the pipeline and the KPI job in
# MAGIC order and takes about 3 to 5 minutes. Open the run link to watch it.
# MAGIC
# MAGIC ✅ You should see `so_orchestrator: SUCCESS`, with `refresh_sales` and `publish_store_kpis` both succeeding.

# COMMAND ----------

run_job("so_orchestrator")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.2 · Look at what you built
# MAGIC
# MAGIC Your tables are in **your own schema**. Everything you deployed is prefixed with your name, and schedules are
# MAGIC paused, so nothing runs on its own and nobody else is affected.

# COMMAND ----------

schema = dev_schema()
print(f"Your schema: {CATALOG}.{schema}  (deployed as {dev_prefix()})\n")
display(spark.sql(f"SHOW TABLES IN `{CATALOG}`.`{schema}`"))
display(
    spark.sql(f"""
    SELECT
      (SELECT COUNT(*) FROM `{CATALOG}`.`{schema}`.bronze_pos_transactions) AS bronze_rows,
      (SELECT COUNT(*) FROM `{CATALOG}`.`{schema}`.silver_pos_transactions) AS silver_rows,
      (SELECT COUNT(*) FROM `{CATALOG}`.`{schema}`.bronze_pos_transactions)
        - (SELECT COUNT(*) FROM `{CATALOG}`.`{schema}`.silver_pos_transactions) AS bad_rows_dropped
""")
)
display(spark.sql(f"SELECT * FROM `{CATALOG}`.`{schema}`.gold_store_alerts ORDER BY attainment_pct"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.3 · Add an agent to your bundle: the Genie space
# MAGIC
# MAGIC A Genie space is an agent that answers questions about specific tables, and it can't be created until those
# MAGIC tables exist. Now that your orchestrator has built them, add **Store Ops Genie** to the bundle. Run the cell,
# MAGIC look at the YAML, then **deploy again** (Deployments panel → `dev` → **Deploy**).
# MAGIC
# MAGIC Notice how it names its tables: `${var.catalog}.${resources.schemas.so_store_ops.name}`. In dev it reads your
# MAGIC schema; in prod it reads prod's. Its instructions and example SQL are code, reviewed in the same pull request
# MAGIC as the tables they describe.

# COMMAND ----------

catch_up(4)
show_file("resources/genie_spaces/store_ops/so_store_ops_genie.genie_space.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.4 · Open your dashboard and ask your Genie space
# MAGIC
# MAGIC ✅ You should see links to both, and Genie should list about six underperforming stores.

# COMMAND ----------

dash = find_dev_dashboard()
space = find_dev_genie_space()
if dash:
    link(f"/dashboardsv3/{dash['id']}/published", f"📊 {dash['name']}")
if space:
    link(f"/genie/rooms/{space['id']}", f"💬 {space['name']}")
if not space:
    print("No Genie space yet: run the cell in 4.3, then deploy again.")

# COMMAND ----------

ask_genie("Which stores are underperforming right now?")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.5 · Final check
# MAGIC
# MAGIC Everything should pass now.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.6 · Same files, different targets
# MAGIC
# MAGIC Compare `dev` with `prod`: same resources, but a different catalog, a different identity, and locked
# MAGIC permissions. Nobody edits a file to promote; the target does the work.

# COMMAND ----------

import yaml

targets = yaml.safe_load(open(f"{REPO_ROOT}/databricks.yml"))["targets"]
for name in ("dev", "prod"):
    print(f"--- {name} ---")
    print(yaml.safe_dump(targets[name], sort_keys=False))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optional · Change something and redeploy
# MAGIC
# MAGIC Ask Genie Code to add a chart to `src/store_ops/dashboards/store_performance.lvdash.json` (for example, "add a
# MAGIC bar chart of net sales by store format"), deploy `dev` again, and refresh your dashboard. That one-file diff is
# MAGIC exactly what you'd put in a pull request.
# MAGIC
# MAGIC **Next:** open **`05_Pull_Request_and_Checks`**.
