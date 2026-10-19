# Databricks notebook source
# MAGIC %md
# MAGIC # Module 2 · The guardrails DevOps owns (10 min)
# MAGIC
# MAGIC **Goal:** fix the imported job with Genie Code, using rules the DevOps team wrote once for everybody.
# MAGIC
# MAGIC | DevOps owns (set once, enforced everywhere) | You own (every change) |
# MAGIC |---|---|
# MAGIC | `databricks.yml`: targets, run-as identity, permissions | Your files under `resources/` and `src/` |
# MAGIC | Genie Code workspace instructions | Deploying your own copy to `dev` |
# MAGIC | The rule checks and the production approval gate | Opening the pull request and fixing what checks flag |

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.1 · Read the rules Genie Code follows
# MAGIC
# MAGIC DevOps keeps this file in the repo and publishes it to the workspace, so every developer's Genie Code follows
# MAGIC the same standard.

# COMMAND ----------

show_file(".assistant_workspace_instructions.md")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.2 · Ask Genie Code to restructure the job
# MAGIC
# MAGIC Open Genie Code (agent mode) from your Git folder and paste:
# MAGIC
# MAGIC ```
# MAGIC Restructure the imported Job_02 job (resources/job_02_pl_store_kpi_alerts.job.yml and
# MAGIC src/Job_02_Store_KPI_Alerts.py) to follow our workspace bundle standards. It belongs to the store_ops domain.
# MAGIC Name the job so_store_kpis and put it in resources/jobs/store_ops/so_store_kpis.job.yml.
# MAGIC Read from the gold_daily_store_sales table in ${var.catalog} and the bundle's store_ops schema instead of the
# MAGIC landing CSVs, and write the results to a gold_store_alerts table there.
# MAGIC Put the KPI logic in src/store_ops/lib/store_kpi_logic.py as pure functions, keep the notebook thin in
# MAGIC src/store_ops/notebooks/store_kpis/, and add a condition task so a notify step only runs when stores are
# MAGIC flagged. Put the lookback days and threshold in resources/jobs/store_ops/_domain.vars.yml.
# MAGIC Delete the imported files when you're done.
# MAGIC ```
# MAGIC
# MAGIC **While it works:** Genie Code isn't guessing your conventions; it's reading them. Watch for the name pattern,
# MAGIC the `so_` prefix, `${var.notification_email}`, tags, and no hard-coded catalog.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.3 · Check the files Genie Code created

# COMMAND ----------

expect_files(
    [
        "resources/jobs/store_ops/so_store_kpis.job.yml",
        "resources/jobs/store_ops/_domain.vars.yml",
        "src/store_ops/lib/store_kpi_logic.py",
    ]
)
for old in ["resources/job_02_pl_store_kpi_alerts.job.yml", "src/Job_02_Store_KPI_Alerts.py"]:
    if _exists(old):
        print(f"⚠️  {old} still exists. Ask Genie Code to delete it (or delete it yourself).")
print()
show_file("resources/jobs/store_ops/so_store_kpis.job.yml")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2.4 · Redeploy and rerun the checks
# MAGIC
# MAGIC In the Deployments panel: target **`dev`** → **Validate** → **Deploy**. Then run the checks. If anything
# MAGIC still fails, paste the failure into Genie Code and ask it to fix it.
# MAGIC
# MAGIC Don't run `so_store_kpis` yet: the table it reads (`gold_daily_store_sales`) is built in module 3.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 2
# MAGIC
# MAGIC Rules written once, followed by every developer and by Genie Code, and checked automatically.
# MAGIC
# MAGIC **Next:** open **`03_Build_the_Bundle`**.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Catch up (only if you need to)
# MAGIC
# MAGIC Behind, or Genie Code's version won't pass? Remove the `#` and run this cell. It puts the finished module 2
# MAGIC files in your Git folder (and removes the imported Job_02 files). Then redeploy `dev` and continue.

# COMMAND ----------

# catch_up(2)
