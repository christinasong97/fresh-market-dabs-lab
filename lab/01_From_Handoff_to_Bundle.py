# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "6"
# ///
# MAGIC %md
# MAGIC # Module 1 · From handoff to bundle (10 min)
# MAGIC
# MAGIC **Goal:** take a job built by hand, the way jobs are built today, and turn it into code you own.
# MAGIC
# MAGIC Today the flow is: a developer builds a job in INT → hands the definition to DevOps → DevOps rebuilds it as a
# MAGIC bundle. Every handoff is a chance for what's deployed to drift from what was tested. In this module you do the
# MAGIC first part of DevOps's job yourself, in about a minute.
# MAGIC
# MAGIC Run the cell below first. It loads small helper functions used throughout the lab.

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.1 · Look at the hand-built job
# MAGIC
# MAGIC `Job_02_PL_Store_KPI_Alerts` flags stores that are behind their sales target. It works, but look at how it's
# MAGIC built. Run the cell and spot the problems.

# COMMAND ----------

import base64

legacy = next(iter(w.jobs.list(name="Job_02_PL_Store_KPI_Alerts")))
settings = w.jobs.get(legacy.job_id).settings
print(f"Job name:        {settings.name}")
print(f"Task names:      {[t.task_key for t in settings.tasks]}")
print(f"On failure:      {settings.email_notifications.on_failure}")
notebook_path = settings.tasks[0].notebook_task.notebook_path
print(f"Notebook:        {notebook_path}")
source = base64.b64decode(w.workspace.export(notebook_path).content).decode()
print("\nHard-coded values in the notebook:")
for line in source.splitlines():
    if line.startswith(("CATALOG", "LANDING", "THRESHOLD")):
        print("   " + line)
link(f"/jobs/{legacy.job_id}", "Open the job in the UI")

# COMMAND ----------

# MAGIC %md
# MAGIC **What's wrong with it?**
# MAGIC - The **name is numbered** (`Job_02_...`, `Task_01_...`). Run order lives in people's heads, not in the job.
# MAGIC - **A person gets the failure emails.** When Jane is on vacation, nobody hears about failures.
# MAGIC - **The catalog is hard-coded** to INT. Someone has to edit the code to move it to CERT or PROD.
# MAGIC - It reads **raw landing files** directly instead of a governed table.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.2 · Bring the job into your bundle
# MAGIC
# MAGIC **First, see the job as code.** Every job you build in the UI already has a YAML version:
# MAGIC 1. Click **Open the job in the UI** (the link above). The job opens in a new tab.
# MAGIC 2. Open the **⋮** menu at the top right of the job page and choose **View as code**.
# MAGIC 3. Choose **YAML**. That's the job's definition, in the same format a bundle uses. Close the dialog.
# MAGIC
# MAGIC **Then save it into your bundle: run the next cell.** It writes two files into your Git folder, exactly as the
# MAGIC job is today, problems included:
# MAGIC - `resources/job_02_pl_store_kpi_alerts.job.yml`: the YAML you just looked at
# MAGIC - `src/Job_02_Store_KPI_Alerts.py`: the notebook the job runs, so the bundle carries its own code
# MAGIC
# MAGIC ✅ You should see both files marked ✅. In the left sidebar, open your Git folder to find them.

# COMMAND ----------

import yaml

job_yaml = {
    "resources": {
        "jobs": {
            "job_02_pl_store_kpi_alerts": {
                "name": settings.name,
                "description": settings.description,
                "email_notifications": {"on_failure": list(settings.email_notifications.on_failure)},
                "schedule": {
                    "quartz_cron_expression": settings.schedule.quartz_cron_expression,
                    "timezone_id": settings.schedule.timezone_id,
                    "pause_status": settings.schedule.pause_status.value,
                },
                "tasks": [
                    {"task_key": t.task_key, "notebook_task": {"notebook_path": "../src/Job_02_Store_KPI_Alerts.py"}}
                    for t in settings.tasks
                ],
            }
        }
    }
}
with open(f"{REPO_ROOT}/resources/job_02_pl_store_kpi_alerts.job.yml", "w") as f:
    yaml.safe_dump(job_yaml, f, sort_keys=False)
with open(f"{REPO_ROOT}/src/Job_02_Store_KPI_Alerts.py", "w") as f:
    f.write(source)
expect_files(["resources/job_02_pl_store_kpi_alerts.job.yml", "src/Job_02_Store_KPI_Alerts.py"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.3 · Ask Genie Code about it
# MAGIC
# MAGIC Open `resources/job_02_pl_store_kpi_alerts.job.yml`, open **Genie Code** (agent mode), and paste:
# MAGIC
# MAGIC ```
# MAGIC Explain this job YAML to me. What would break if we deployed it to cert and prod as-is?
# MAGIC ```
# MAGIC
# MAGIC It should point out the hard-coded catalog, the personal email, and the naming. Genie Code knows the team's
# MAGIC rules because DevOps published them as workspace instructions (you'll look at them in module 2).

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.4 · Deploy your copy
# MAGIC
# MAGIC 1. Open **`databricks.yml`** in your Git folder. The **Deployments** panel (rocket icon) opens on the side.
# MAGIC 2. Choose target **`dev`**, click **Validate**, then **Deploy**.
# MAGIC
# MAGIC Validation passes: the YAML is valid. That doesn't mean it follows the team's rules.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.5 · Run the team's checks
# MAGIC
# MAGIC These are the **same checks CI runs on every pull request**, packaged as a job in the bundle. Expect about five
# MAGIC failures. That's the point: the job deploys, but it doesn't meet the team's standards.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 1
# MAGIC
# MAGIC The job a developer would hand to DevOps is now a file in your bundle. Next: fix it with Genie Code.
# MAGIC
# MAGIC **Next:** open **`02_Guardrails_with_Genie_Code`** in this folder.
