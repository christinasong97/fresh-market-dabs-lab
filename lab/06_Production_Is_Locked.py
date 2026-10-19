# Databricks notebook source
# MAGIC %md
# MAGIC # Module 6 · Production is locked (5 min)
# MAGIC
# MAGIC **Goal:** see why hand edits in production don't stick, and why that's a good thing.

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.1 · Watch (instructor)
# MAGIC
# MAGIC 1. The instructor opens the **prod** orchestrator job and changes its schedule by hand. The UI warns that the job
# MAGIC    is managed by a bundle.
# MAGIC 2. The next deploy from `main` puts the schedule back. **Git is the source of truth.**
# MAGIC 3. Everyone except the service principal has **Can View** on production. You can look, not change.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6.2 · Check who can change production
# MAGIC
# MAGIC This lists the production jobs (if they've been deployed in this workspace) and who can manage them.

# COMMAND ----------

prod_jobs = [j for j in w.jobs.list() if j.settings and j.settings.name.startswith(f"{BUNDLE}_prod_")]
if not prod_jobs:
    print("Production isn't deployed in this workspace. Your instructor will show it on screen.")
for job in prod_jobs:
    acl = w.permissions.get("jobs", str(job.job_id)).access_control_list or []
    print(job.settings.name)
    for entry in acl:
        who = entry.user_name or entry.group_name or entry.service_principal_name
        levels = ", ".join(p.permission_level.value for p in entry.all_permissions or [])
        print(f"   {who}: {levels}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wrap-up
# MAGIC
# MAGIC | You did | Why it matters |
# MAGIC |---|---|
# MAGIC | Turned a hand-built job into bundle files | No more rebuilding by hand for each environment |
# MAGIC | Had Genie Code follow the DevOps team's rules | Standards set once, followed by everyone |
# MAGIC | Ran the same checks CI runs | You know a change passes before you open a PR |
# MAGIC | Deployed your own `dev` copy | Test the real thing without touching shared environments |
# MAGIC | Saw a change go PR → cert → approval → prod | Every production change is reviewed and recorded |
# MAGIC
# MAGIC **Take it home:** the repo's README explains how to run the whole flow in your own workspace. In your team's
# MAGIC bundle, start with three things: a `dev` target, lookups instead of hard-coded IDs, and `tests/bundle/test_rules.py`.
# MAGIC
# MAGIC **Clean up (optional):** Deployments panel → target `dev` → **Destroy** removes everything you deployed today.
