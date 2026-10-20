# Databricks notebook source
# MAGIC %md
# MAGIC # Module 4 · Your own development target (15 min)
# MAGIC
# MAGIC **Goal:** run the real thing, in your own isolated copy, without touching anyone else's work.
# MAGIC
# MAGIC Before Store Ops relies on your alert every morning, you want proof that it works: the pipeline cleans the
# MAGIC sales, the KPI job flags the right stores, and the dashboard shows them. Today that test happens in the shared
# MAGIC INT workspace, where your half-finished change can break a teammate's work, and theirs can break yours.
# MAGIC
# MAGIC `int`, `cert`, and `prod` are locked to the CI/CD service principal, so only CI can deploy them. The **`dev`**
# MAGIC target is what lets you test yourself. Many team templates don't have one; it's the piece that makes developer
# MAGIC ownership possible.
# MAGIC
# MAGIC | | `dev` (you, today) | `prod` (shared) |
# MAGIC |---|---|---|
# MAGIC | **Who deploys** | You, from the Deployments panel | CI, after a pull request is approved |
# MAGIC | **Runs as** | You | The CI/CD service principal |
# MAGIC | **Where the data goes** | Your own schema, `dev_<you>_store_ops` | The production schema |
# MAGIC | **Names** | Prefixed `[dev <you>]` | The standard names |
# MAGIC | **Schedules** | Paused, so nothing runs on its own | On: the orchestrator runs at 6am |

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
# MAGIC
# MAGIC **Why it matters:** this is the full morning run, the same one prod will do at 6am: first the pipeline turns the
# MAGIC register files into clean tables, then the KPI job flags stores that are behind. One click runs everything in
# MAGIC the right order, because the order is in the orchestrator, not in anyone's head.

# COMMAND ----------

run_job("so_orchestrator")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.2 · Look at what you built
# MAGIC
# MAGIC Your tables are in **your own schema**. Everything you deployed is prefixed with your name, and schedules are
# MAGIC paused, so nothing runs on its own and nobody else is affected.
# MAGIC
# MAGIC **What to look for:**
# MAGIC - **The tables:** the bronze, silver, and gold tables your pipeline built, plus `gold_store_alerts` from the KPI job.
# MAGIC - **`bad_rows_dropped`:** rows that were in the raw files but didn't make it to silver. Those are the data quality
# MAGIC   rules from module 3 at work: a register glitch never reaches a district manager's report.
# MAGIC - **The alerts:** the stores furthest behind their target are at the top. This is the list Store Ops follows up on.

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
# MAGIC **Why it matters:** district managers don't write SQL. A Genie space lets them ask "Which stores are behind
# MAGIC this week?" in plain English. Because it's in the bundle, its instructions and example questions are code:
# MAGIC reviewed in the same pull request as the tables they describe, and promoted to prod with them.
# MAGIC
# MAGIC Notice how it names its tables: the YAML uses the bundle's catalog variable and schema, not a fixed catalog. In
# MAGIC dev it reads your schema; in prod it reads prod's.

# COMMAND ----------

catch_up(4)
show_file("resources/genie_spaces/store_ops/so_store_ops_genie.genie_space.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.4 · Open your dashboard and ask your Genie space
# MAGIC
# MAGIC ✅ You should see links to both, and Genie should list about six underperforming stores.
# MAGIC
# MAGIC **Why it matters:** this is what Store Ops actually uses. The dashboard and the Genie space read the tables your
# MAGIC pipeline and KPI job just built, and they all came from one deploy of one bundle.

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
# MAGIC
# MAGIC **Why it matters:** these are the same checks the pull request runs in module 5. If they pass here, you already
# MAGIC know your change will clear CI, before anyone else has to look at it.

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
# MAGIC **Ask Genie Code** to add a chart to `src/store_ops/dashboards/store_performance.lvdash.json` (for example, "add a
# MAGIC bar chart of net sales by store format"), deploy `dev` again, and refresh your dashboard. That one-file diff is
# MAGIC exactly what you'd put in a pull request.
# MAGIC
# MAGIC **Next:** open **`05_Pull_Request_and_Checks`**.
