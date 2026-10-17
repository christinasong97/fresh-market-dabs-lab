# Databricks notebook source
# MAGIC %md
# MAGIC # Welcome: CI/CD with Declarative Automation Bundles
# MAGIC
# MAGIC In the next 90 minutes you'll take a job built by hand in the workspace, turn it into code you own,
# MAGIC test your own copy, and see how it gets to production through a pull request, automated checks, and an
# MAGIC approval. Everything happens here in the workspace, with Genie Code. No terminal, no IDE.
# MAGIC
# MAGIC **Run this notebook top to bottom.** It explains bundles, checks your environment, and creates your
# MAGIC working copy of the lab.
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
# MAGIC ## What is a Declarative Automation Bundle?
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
# MAGIC ## Step 1 · Check your environment
# MAGIC
# MAGIC Your instructor's setup already created the shared pieces. This cell only **reads**; it changes nothing.

# COMMAND ----------

import os

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
me = w.current_user.me().user_name
PREFIX = "fresh_market_lab"
WAREHOUSE = f"{PREFIX}_warehouse"
LEGACY_JOB = "Job_02_PL_Store_KPI_Alerts"
INSTRUCTIONS = "/Workspace/.assistant_workspace_instructions.md"


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
]
print()
print(
    "Ready to go."
    if all(results)
    else "Something is missing. Ask your instructor, or see the next cell if you're on Free Edition."
)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Free Edition only: run the setup yourself
# MAGIC
# MAGIC In Vocareum this is done for you. On Free Edition (where you're the workspace admin), set the
# MAGIC **run_setup** widget at the top of the notebook to `true` and run this cell. It takes about 2 minutes,
# MAGIC then re-run Step 1. This cell needs the lab repo, so run Step 2 first if you opened this notebook on its own.

# COMMAND ----------

dbutils.widgets.dropdown("run_setup", "false", ["false", "true"], "Free Edition: run setup")

if dbutils.widgets.get("run_setup") == "true":
    here = os.getcwd()
    candidates = [
        f"{here}/devops/lab_setup/00_lab_setup",
        f"/Workspace/Users/{me}/fresh-market-dabs-lab/devops/lab_setup/00_lab_setup",
    ]
    setup = next((p for p in candidates if os.path.exists(p) or os.path.exists(p + ".py")), candidates[-1])
    print(dbutils.notebook.run(setup, 1800, {"catalog_prefix": PREFIX, "warehouse_name": WAREHOUSE, "attendee_principal": ""}))
else:
    print("Skipped (run_setup is false).")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 · Create your working copy (Git folder)
# MAGIC
# MAGIC This creates a **Git folder** in your home folder from the public lab repo, on the `lab/start` branch.
# MAGIC It's your copy: you can edit and deploy it. It can't push back to GitHub, and it doesn't need to.

# COMMAND ----------

REPO_URL = "https://github.com/christinasong97/fresh-market-dabs-lab"
REPO_PATH = f"/Workspace/Users/{me}/fresh-market-dabs-lab"
START_BRANCH = "lab/start"

existing = next((r for r in w.repos.list(path_prefix=REPO_PATH) if r.path.rstrip("/").endswith("fresh-market-dabs-lab")), None)
if existing:
    print(f"Your Git folder already exists (branch: {existing.branch}). Leaving it as is.")
    repo_id = existing.id
else:
    repo_id = w.repos.create(url=REPO_URL, provider="gitHub", path=REPO_PATH).id
    w.repos.update(repo_id, branch=START_BRANCH)
    print(f"Created your Git folder on branch {START_BRANCH}.")

host = w.config.host.rstrip("/")
displayHTML(
    f'<p style="font-size:16px">Open your Git folder: '
    f'<a href="{host}/browse/folders/{w.workspace.get_status(REPO_PATH).object_id}" target="_blank">{REPO_PATH}</a></p>'
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 · Start module 1
# MAGIC
# MAGIC 1. Open your Git folder (link above) and open **`databricks.yml`**. The **Deployments** panel (rocket icon)
# MAGIC    appears on the side. That's where you'll validate and deploy all day.
# MAGIC 2. Open **`lab/LAB_GUIDE.md`** in the same folder. It has every step and every Genie Code prompt.
# MAGIC 3. Go to **Jobs & Pipelines** and open **`Job_02_PL_Store_KPI_Alerts`**: the hand-built job you'll start with.
# MAGIC
# MAGIC **Fell behind?** In your Git folder's branch picker, switch to the catch-up branch for the module you're on:
# MAGIC `lab/01-imported`, `lab/02-restructured`, `lab/03-pipeline`, or `main` (complete).
