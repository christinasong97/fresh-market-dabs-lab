# Databricks notebook source
# MAGIC %md
# MAGIC # Welcome: CI/CD with Declarative Automation Bundles
# MAGIC
# MAGIC In the next 90 minutes you'll take a job built by hand in the workspace, turn it into code you own,
# MAGIC test your own copy, and see how it gets to production through a pull request, automated checks, and an
# MAGIC approval. Everything happens here in the workspace, with Genie Code. No terminal, no IDE.
# MAGIC
# MAGIC **Before you start:** you should be reading this from **your own Git folder** (created from
# MAGIC `https://github.com/christinasong97/fresh-market-dabs-lab`), on the **`lab/start`** branch. If you're
# MAGIC not, create the Git folder first: **Workspace → Create → Git folder**, paste the URL, then switch the
# MAGIC branch to `lab/start`.
# MAGIC
# MAGIC **Then run this notebook top to bottom.** It explains bundles, sets up the lab environment, and checks it.
# MAGIC
# MAGIC | Module | What you'll do | Time |
# MAGIC |---|---|---|
# MAGIC | 0 · Today vs. target | Why bundles, and who owns what | 10 min |
# MAGIC | 1 · From handoff to bundle | Turn a hand-built job into code, deploy it, run the team's checks | 10 min |
# MAGIC | 2 · The guardrails DevOps owns | Genie Code fixes the job using the team's rules | 10 min |
# MAGIC | 3 · Build the bundle with Genie Code | Add a pipeline and an orchestrator job | 20 min |
# MAGIC | 4 · Your own development target | Deploy and run your copy; open your dashboard and Genie space | 15 min |
# MAGIC | 5 · Pull request and checks | *Instructor:* PR → checks → approval → production | 20 min |
# MAGIC | 6 · Production is locked | *Instructor:* why hand edits in production don't stick | 5 min |

# COMMAND ----------

# MAGIC %md
# MAGIC ## What is a Declarative Automation Bundle (DAB)?
# MAGIC
# MAGIC > **Same thing, new name.** Declarative Automation Bundles (DABs) were formerly called **Databricks Asset
# MAGIC > Bundles**. Only the name changed: same `databricks.yml`, same features, same "DABs" acronym. If your team's
# MAGIC > docs or older articles say "Asset Bundles," they mean exactly this.
# MAGIC
# MAGIC A **bundle** is a folder in Git that describes your Databricks work as files: the jobs, pipelines,
# MAGIC dashboards, and Genie spaces, plus the code they run. You don't click resources into existence; you
# MAGIC **deploy** the folder, and Databricks creates or updates everything it describes.
# MAGIC
# MAGIC ```
# MAGIC  fresh-market-dabs-lab/  (a Git folder)
# MAGIC  ├── databricks.yml        ← the bundle: name + targets (dev, int, cert, prod)
# MAGIC  ├── resources/            ← YAML describing each job, pipeline, dashboard, Genie space
# MAGIC  └── src/                  ← the notebooks, pipeline code, and dashboard they use
# MAGIC
# MAGIC        Deploy (target: dev)  ──►  your own copy, in your own schema
# MAGIC        Deploy (target: prod) ──►  production, run by a service principal
# MAGIC ```
# MAGIC
# MAGIC **Why bother?** Compare getting a dashboard and its job from development to production:
# MAGIC
# MAGIC | | Built by hand ("click-ops") | Bundle |
# MAGIC |---|---|---|
# MAGIC | Moving to prod | Someone rebuilds it, re-pointing catalogs and permissions | The same files deploy to every target |
# MAGIC | Reviewing a change | Screenshots, or trust | A diff in a pull request |
# MAGIC | Enforcing team rules | Someone remembers to check | Automated checks on every change |
# MAGIC | Who runs prod | Whoever built it | A service principal, so nothing breaks when people change roles |
# MAGIC | Undoing a bad change | Rebuild from memory | Redeploy the previous version |
# MAGIC
# MAGIC **Words you'll hear today**
# MAGIC
# MAGIC | Term | Meaning |
# MAGIC |---|---|
# MAGIC | **Resource** | One thing the bundle creates: a job, pipeline, dashboard, Genie space, schema |
# MAGIC | **Target** | Where and how to deploy: `dev` (you), `int`, `cert`, `prod` (shared) |
# MAGIC | **Variable** | A value that changes per target, like `${var.catalog}`, so nothing is hard-coded |
# MAGIC | **Development mode** | The `dev` target: your own copy, names prefixed `[dev <you>]`, schedules paused |
# MAGIC | **Service principal** | A non-human identity. Shared targets deploy and run as it, never as a person |
# MAGIC | **Deployments panel** | The rocket icon next to `databricks.yml`: Validate and Deploy from the UI |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 · Set up the lab environment
# MAGIC
# MAGIC This runs `devops/lab_setup/00_lab_setup` from your Git folder. It creates everything the lab needs that
# MAGIC lives **outside** the bundle, and it's safe to run again:
# MAGIC
# MAGIC | Creates | Used for |
# MAGIC |---|---|
# MAGIC | Catalogs `fresh_market_lab_int`, `_cert`, `_prod` | One catalog per target |
# MAGIC | `landing.raw` volume with synthetic POS data | The "source system" your pipeline reads |
# MAGIC | SQL warehouse `fresh_market_lab_warehouse` | Your dashboard and Genie space |
# MAGIC | Job `Job_02_PL_Store_KPI_Alerts` | The hand-built job you start with in module 1 |
# MAGIC | `/Workspace/.assistant_workspace_instructions.md` | The DevOps team's rules for Genie Code |
# MAGIC
# MAGIC Takes about 3 minutes the first time.

# COMMAND ----------

import os

from databricks.sdk import WorkspaceClient

PREFIX = "fresh_market_lab"
WAREHOUSE = f"{PREFIX}_warehouse"
LEGACY_JOB = "Job_02_PL_Store_KPI_Alerts"
INSTRUCTIONS = "/Workspace/.assistant_workspace_instructions.md"

dbutils.notebook.run(
    "./devops/lab_setup/00_lab_setup",
    3600,
    {
        "catalog_prefix": PREFIX,
        "attendee_principal": "",
        "cicd_service_principal": "",
        "warehouse_name": WAREHOUSE,
        "stage_data": "auto",
    },
)
print("Setup finished. Run the next cell to check it.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Check your environment
# MAGIC
# MAGIC Read-only: confirms each piece from Step 1 is there.

# COMMAND ----------

w = WorkspaceClient()


def check(label, fn):
    try:
        detail = fn()
        print(f"✅ {label}{f'  ({detail})' if detail else ''}")
        return True
    except Exception as e:  # noqa: BLE001 - report any failure as "not ready"
        print(f"❌ {label}  ->  {str(e).splitlines()[0][:120]}")
        return False


results = [
    check("Catalogs", lambda: ", ".join(w.catalogs.get(f"{PREFIX}_{t}").name for t in ("int", "cert", "prod"))),
    check("POS landing data", lambda: f"{len(dbutils.fs.ls(f'/Volumes/{PREFIX}_int/landing/raw/pos_transactions'))} files"),
    check("SQL warehouse", lambda: next(x.name for x in w.warehouses.list() if x.name == WAREHOUSE)),
    check("Legacy job for module 1", lambda: next(iter(w.jobs.list(name=LEGACY_JOB))).settings.name),
    check("Genie Code team instructions", lambda: w.workspace.get_status(INSTRUCTIONS).path),
    check("This notebook is in a Git folder", lambda: os.getcwd()),
]
print()
print("Ready to go." if all(results) else "Something is missing. Re-run Step 1, or ask your instructor.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Start module 1
# MAGIC
# MAGIC 1. In this same Git folder, open **`databricks.yml`**. The **Deployments** panel (rocket icon) appears on
# MAGIC    the side. That's where you'll validate and deploy all day.
# MAGIC 2. Open **`lab/LAB_GUIDE.md`**. It has every step and every Genie Code prompt.
# MAGIC 3. Go to **Jobs & Pipelines** and open **`Job_02_PL_Store_KPI_Alerts`**: the hand-built job you'll start with.
# MAGIC
# MAGIC **Fell behind?** In your Git folder's branch picker, switch to the catch-up branch for the module you're on:
# MAGIC `lab/01-imported`, `lab/02-restructured`, `lab/03-pipeline`, or `main` (complete).
