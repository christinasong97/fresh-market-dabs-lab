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
# MAGIC **About this job.** `Job_02_PL_Store_KPI_Alerts` is the Store Operations team's daily alert. A developer built it
# MAGIC by hand in INT so district managers know each morning which stores are falling behind.
# MAGIC
# MAGIC | | |
# MAGIC |---|---|
# MAGIC | **What kind of job** | A scheduled job with one notebook task, 6:30 every morning, after `Job_01` loads the sales |
# MAGIC | **What it reads** | The last 15 days of register sales, the store list, and each store's daily sales target |
# MAGIC | **What it does** | Compares each store's sales with its target and marks any store under 85% `UNDERPERFORMING` |
# MAGIC | **What it writes** | A `store_alerts` table that Store Ops uses to follow up with those stores |
# MAGIC | **Who hears about failures** | Jane, the developer who built it, by email |
# MAGIC
# MAGIC It works, but look at how it's built. Run the cell and spot the problems.

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
# MAGIC Every job you build in the UI can be written as YAML, the same format a bundle uses. Turn this one into a YAML
# MAGIC file in your bundle, exactly as it is today, problems included. **Pick one of the two options.**
# MAGIC
# MAGIC ### Option A · In the UI, no code
# MAGIC 1. In the left sidebar, click **Workspace** and open your Git folder (`fresh-market-dabs-lab`).
# MAGIC 2. Click **Open in editor** next to the bundle name, at the top.
# MAGIC 3. Click the **Deployments** icon (rocket) on the left of the editor. The Deployments panel opens.
# MAGIC 4. In the **Bundle resources** section, click **Add**, then **Add existing job**.
# MAGIC 5. In the job dropdown, choose **`Job_02_PL_Store_KPI_Alerts`**.
# MAGIC 6. Choose **(Advanced) Don't update**. Your bundle gets its own copy, and the original hand-built job stays
# MAGIC    untouched. (The other two options link the original job to your bundle, so your deploys would overwrite it.)
# MAGIC 7. Click **Add**. Databricks writes the job's YAML file into your bundle.
# MAGIC 8. Skip the next cell and go to **1.3**.
# MAGIC
# MAGIC ### Option B · Run the cell
# MAGIC Run the next cell. It does the same thing with code, and also copies the job's notebook into `src/`, so the
# MAGIC bundle carries its own code. It writes:
# MAGIC - `resources/job_02_pl_store_kpi_alerts.job.yml`: the job's YAML
# MAGIC - `src/Job_02_Store_KPI_Alerts.py`: the notebook the job runs
# MAGIC
# MAGIC With Option A, the notebook stays in `/Workspace/Shared` for now. Genie Code moves it into the bundle in module 2.

# COMMAND ----------

# Option B only. Skip this cell if you used Option A.
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
# MAGIC ## 1.3 · Break down the job YAML
# MAGIC
# MAGIC Run the cell. It finds the job's YAML file in your Git folder, whichever option you used, and prints it.
# MAGIC
# MAGIC ✅ You should see `✅` next to the file, then the YAML.

# COMMAND ----------

job_file = show_imported_job()

# COMMAND ----------

# MAGIC %md
# MAGIC **How the file is built.** Every resource file in a bundle has the same shape:
# MAGIC
# MAGIC ```
# MAGIC resources:                        ← everything the bundle creates is listed under "resources"
# MAGIC   jobs:                           ← the resource type: jobs, pipelines, dashboards, schemas, genie_spaces, ...
# MAGIC     job_02_pl_store_kpi_alerts:   ← the resource key: the bundle's own name for this job (yours may differ)
# MAGIC       name: ...                   ← the display name you see in the Jobs UI
# MAGIC       email_notifications: ...    ← who hears about failures
# MAGIC       schedule: ...               ← when it runs
# MAGIC       tasks:                      ← the steps, in order
# MAGIC         - task_key: ...           ← the step's name
# MAGIC           notebook_task:
# MAGIC             notebook_path: ...    ← the code the step runs
# MAGIC ```
# MAGIC
# MAGIC | Part | What it does |
# MAGIC |---|---|
# MAGIC | **Resource key** | How other files refer to the job: `${resources.jobs.<key>.id}`. Same in every target. |
# MAGIC | **`name`** | What people see in the UI. Module 2 makes it `${bundle.name}_${var.environment}_...` |
# MAGIC | **Settings** (`email_notifications`, `schedule`, `tasks`) | What you'd click through on the job page |
# MAGIC | **How it joins the bundle** | `databricks.yml` includes every `resources/*.yml` file |
# MAGIC
# MAGIC The problems from 1.1 are all visible here: the numbered name and task key, Jane's email, and (inside the
# MAGIC notebook) the hard-coded catalog.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.4 · Ask Genie Code about it
# MAGIC
# MAGIC Open the job's YAML file from 1.3, open **Genie Code** (agent mode), and paste:
# MAGIC
# MAGIC ```
# MAGIC Explain this job YAML to me. What would break if we deployed it to cert and prod as-is?
# MAGIC ```
# MAGIC
# MAGIC It should point out the hard-coded catalog, the personal email, and the naming. Genie Code knows the team's
# MAGIC rules because DevOps published them as workspace instructions (you'll look at them in module 2).

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.5 · Deploy your copy
# MAGIC
# MAGIC 1. Open **`databricks.yml`** in your Git folder. The **Deployments** panel (rocket icon) opens on the side.
# MAGIC 2. Choose target **`dev`**, click **Validate**, then **Deploy**.
# MAGIC
# MAGIC Validation passes: the YAML is valid. That doesn't mean it follows the team's rules.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1.6 · Run the team's checks
# MAGIC
# MAGIC These are the **same checks CI runs on every pull request** (`tests/bundle/` in your Git folder). They read your
# MAGIC bundle's files and check them against the team's rules: who gets failure emails, tags, naming, no hard-coded
# MAGIC catalogs, and how the shared targets are locked down. They take a few seconds.
# MAGIC
# MAGIC **Why it matters:** **Validate** only checks that the YAML is valid. These check that it follows the team's
# MAGIC rules. Running them here, you find out in seconds, not after you open a pull request and wait for CI, and
# MAGIC nobody in DevOps has to catch it in review.
# MAGIC
# MAGIC Expect about five failures. That's the point: the job deploys, but it doesn't meet the team's standards.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 1
# MAGIC
# MAGIC The job a developer would hand to DevOps is now a file in your bundle. Next: fix it with Genie Code.
# MAGIC
# MAGIC **Next:** open **`02_Guardrails_with_Genie_Code`** in this folder.
