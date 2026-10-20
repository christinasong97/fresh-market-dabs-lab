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
# MAGIC **Step 1 · Deploy first.** The cell below runs your *deployed* copy of the orchestrator, so deploy before you run
# MAGIC it. Even if you deployed at the end of module 3, deploying again is quick and makes sure your dev copy matches
# MAGIC your files.
# MAGIC 1. In your Git folder in Databricks, open **`databricks.yml`**. The **Deployments** panel (rocket icon) opens.
# MAGIC 2. Choose target **`dev`** and click **Deploy**. Wait until the panel says the deployment finished.
# MAGIC
# MAGIC **Step 2 · Run the cell.** It runs the pipeline, then the KPI job, and waits for both. It takes about 3 to 5
# MAGIC minutes. Click the run link it prints to watch it.
# MAGIC
# MAGIC ✅ You should see `so_orchestrator: SUCCESS`, with `refresh_sales` and `publish_store_kpis` both succeeding.
# MAGIC
# MAGIC If you see *"No dev copy of 'so_orchestrator' yet"*, Step 1 didn't finish. Deploy again, then rerun the cell.
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
# MAGIC tables exist. Now that your orchestrator has built them, add **Store Ops Genie** to the bundle.
# MAGIC
# MAGIC **Why it matters:** district managers don't write SQL. A Genie space lets them ask "Which stores are behind
# MAGIC this week?" in plain English. Because it's in the bundle, its instructions and example questions are code:
# MAGIC reviewed in the same pull request as the tables they describe, and promoted to prod with them.
# MAGIC
# MAGIC **Pick one of the two options.**
# MAGIC
# MAGIC ### Option A · Build it in the UI, then bring it into your bundle
# MAGIC The Deployments panel's **Add existing** doesn't offer Genie spaces yet, so you build the space in the UI and a
# MAGIC cell turns it into bundle YAML.
# MAGIC 1. In the left sidebar, click **Genie**, then **New**.
# MAGIC 2. Add your tables: catalog **`fresh_market_lab_int`** → **your schema** (the cell below prints its name) →
# MAGIC    select `gold_daily_store_sales`, `gold_department_sales`, and `gold_store_alerts`.
# MAGIC 3. Name the space **`My Store Ops Genie`** and choose the **Serverless Starter Warehouse**. Save it.
# MAGIC 4. Optional: in its **Instructions**, add *"'Right now' means the last 14 days of sales_date."* Then ask it
# MAGIC    *"Which stores are underperforming right now?"*
# MAGIC 5. Run the Option A cell. It saves the space as a bundle file and swaps your schema's name for the bundle's
# MAGIC    variables, so the same file works in every target.
# MAGIC
# MAGIC ### Option B · Add the finished file
# MAGIC Run the Option B cell. It adds a ready-made Genie space file, with instructions and example SQL, to your bundle.
# MAGIC
# MAGIC ### Then, either option: deploy again
# MAGIC The cell only adds a file; the Genie space doesn't exist yet. **Deploy:** Deployments panel → target **`dev`** →
# MAGIC **Deploy**. That's what creates the Genie space. Wait until the deployment finishes, then go to 4.4.

# COMMAND ----------

print(f"Your schema: {dev_schema()}")

# COMMAND ----------

# Option A only: you built "My Store Ops Genie" in the UI.
import_genie_space("My Store Ops Genie")

# COMMAND ----------

# Option B only: add the finished file.
add_genie_space()

# COMMAND ----------

# MAGIC %md
# MAGIC **Read the Genie space's YAML.** Run the cell, then look for these parts:
# MAGIC
# MAGIC ```
# MAGIC title: Store Ops Genie (${var.environment})       ← its own name in every target
# MAGIC warehouse_id: ${var.warehouse_id}                 ← looked up by name, so no IDs in the file
# MAGIC serialized_space:
# MAGIC   data_sources:
# MAGIC     tables:
# MAGIC       - identifier: ${var.catalog}.${resources.schemas.so_store_ops.name}.gold_store_alerts
# MAGIC                                                   ← your schema in dev, prod's schema in prod
# MAGIC   instructions:
# MAGIC     text_instructions: ...                        ← what Genie should know about the data
# MAGIC     example_question_sqls: ...                    ← known-good SQL for common questions (Option B)
# MAGIC ```
# MAGIC
# MAGIC Change an instruction here, and the change goes through a pull request like any other code.

# COMMAND ----------

show_file(GENIE_FILE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4.4 · Open your dashboard and ask your Genie space
# MAGIC
# MAGIC The dashboard is the one from module 3 (3.3), now showing your data. Open both links, then run the next cell to
# MAGIC ask Genie a question from the notebook.
# MAGIC
# MAGIC ✅ You should see links to both, and Genie should list about six underperforming stores. No Genie space link?
# MAGIC You haven't deployed since 4.3: deploy `dev` again, then rerun the cell.
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
    print("No Genie space yet: do Option A or B in 4.3, then deploy again.")

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
# MAGIC ## Optional · Change the dashboard and redeploy
# MAGIC
# MAGIC In 3.3 you saw that the dashboard is a file in your bundle, `src/store_ops/dashboards/store_performance.lvdash.json`.
# MAGIC Now that it shows real data, change it the way you'd change any code:
# MAGIC
# MAGIC 1. **Ask Genie Code:**
# MAGIC    ```
# MAGIC    Add a bar chart of net sales by store_format to src/store_ops/dashboards/store_performance.lvdash.json.
# MAGIC    ```
# MAGIC 2. **See the change:** click the branch name at the top of your Git folder in Databricks. The Git dialog lists the
# MAGIC    changed file; click it to see the diff.
# MAGIC 3. **Deploy:** Deployments panel → target **`dev`** → **Deploy**.
# MAGIC 4. **Refresh your dashboard** (the link in 4.4). ✅ You should see the new chart.
# MAGIC
# MAGIC **Why it matters:** that one-file diff is exactly what you'd put in a pull request. A reviewer sees the change, the
# MAGIC checks run, and the same file goes to prod.
# MAGIC
# MAGIC **Next:** open **`05_Pull_Request_and_Checks`**.
