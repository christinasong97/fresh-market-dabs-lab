# Fresh Market Lab: CI/CD with Declarative Automation Bundles

Declarative Automation Bundles (DABs) were formerly called Databricks Asset Bundles; same feature, new name.

A 90-minute hands-on lab, plus a reference bundle for a DevOps team's repository layout. You take a job built by
hand in the workspace, bring it into a bundle, test your own copy, and see it promoted to production through a pull
request, automated checks, and an approval gate. All of it happens in the Databricks workspace with Genie Code.

## Before you start (attendees)

You do everything in your **Databricks workspace**. You never need to open or change this GitHub repo.

1. **Sign in to your Databricks workspace.** For this lab, that's
   [Databricks Free Edition](https://www.databricks.com/learn/free-edition): sign up with your email, Google, or
   Microsoft account.
2. **Create your Git folder in Databricks.** A Git folder is a copy of this repo inside your workspace.
   - In the left sidebar, click **Workspace**, then **Create → Git folder**.
   - Paste `https://github.com/christinasong97/fresh-market-dabs-lab` and click **Create**. No GitHub account needed.
   - It opens on the `lab/start` branch, which is all you need for the whole lab.
3. **Open `00_START_HERE` in your Git folder**, set compute to **Serverless**, and click **Run all**. It explains
   bundles, sets up the lab environment (about 5 minutes), and checks it. Every check should show ✅.
4. **Then follow the notebooks in the `lab` folder**, in order: `01_From_Handoff_to_Bundle` through
   `05_Ship_It`. Each one has numbered steps, the Genie Code prompts to paste, and a "✅ you should see"
   after each step.

**Instructors:** `devops/instructor/reset_demo` resets a demo workspace between rehearsals, and
`devops/instructor/reset_github_demo.sh` resets the module 5 pull request demo on GitHub.

---

The rest of this README is reference: what's in the bundle and how it's built. You don't need it for the lab.

## What's in the bundle

| Resource | Key | What it does |
|---|---|---|
| Schema | `so_store_ops` | Output schema per target (`dev_<you>_store_ops` in dev) |
| Pipeline | `so_sales_medallion` | POS landing CSVs → bronze → silver → gold, with expectations |
| Job | `so_store_kpis` | Flags stores behind target, notifies only when there are any |
| Job | `so_orchestrator` | Daily DAG: refresh sales → publish KPIs |
| Dashboard | `so_store_performance` | Store performance overview |
| Genie space | `so_store_ops_genie` | "Store Ops Genie" — ask questions about store sales |
| Job | `admin_rule_checks` | The same rule checks CI runs, runnable as a job (the lab runs them in the notebook) |

## Targets

| Target | Mode | Catalog | Deployed by | When |
|---|---|---|---|---|
| `dev` | development | `fresh_market_lab_int` (your own schema) | You, from the Deployments panel | Any time |
| `int` | production | `fresh_market_lab_int` | CI/CD service principal | Merge to `develop` |
| `cert` | production | `fresh_market_lab_cert` | CI/CD service principal | Merge to `main` |
| `prod` | production | `fresh_market_lab_prod` | CI/CD service principal | After cert passes **and** an approver signs off |

## Layout

```
00_START_HERE.py                   # Entry notebook: DABs overview, runs lab setup, checks the environment
databricks.yml                     # Targets, includes (DevOps-owned)
resources/
  variables/common.vars.yml        # Bundle-wide variables (DevOps-owned)
  schemas/store_ops.schema.yml
  jobs/store_ops/                  # _domain.vars.yml, so_store_kpis.job.yml, orchestrator.job.yml
  jobs/admin/admin_rule_checks.job.yml
  pipelines/store_ops/so_sales_medallion.pipeline.yml
  dashboards/store_ops/so_store_performance.dashboard.yml
  genie_spaces/store_ops/so_store_ops_genie.genie_space.yml
src/store_ops/
  notebooks/store_kpis/            # Thin job entrypoints
  pipelines/sales_medallion/
    transformations/               # bronze / silver / gold tables
    expectations/                  # <LAYER>_RULES dictionaries
  lib/                             # Pure, unit-tested logic
  dashboards/store_performance.lvdash.json
tests/
  unit/                            # Logic + expectation tests (no Spark)
  bundle/                          # Team rules + target guardrails (no credentials)
devops/
  checks/run_rule_checks.py        # Runs tests/bundle inside the workspace
  lab_setup/00_lab_setup.py        # Admin-only, run once per workspace: everything outside the bundle
  instructor/                      # Instructor reset tools (workspace and GitHub demo)
lab/                               # Module notebooks, shared helpers, and solutions/ for catching up
.github/                           # CI, deploy, CODEOWNERS
.assistant_workspace_instructions.md  # Genie Code instructions (the team's rules)
```

## Branches

| Branch | Use |
|---|---|
| `lab/start` (default) | **Attendees use only this branch.** Template, tests, CI, dashboard, Genie space, and the lab notebooks. Each module's catch-up files are in `lab/solutions/` |
| `main` / `develop` | Complete solution; the instructor's pull request demo merges here and CI promotes it |
| `feature/weekly-department-report` | The instructor's example pull request (with a planted rule violation) |

## Quick setup without the lab (for your own workspace)

A short summary for setting up this bundle and its CI/CD in a workspace of your own, without the lab notebooks.
**If you're doing the lab, skip this:** `00_START_HERE` does steps 2 and 3 for you, and the lab notebooks walk
through everything else.

1. **Fork the repo** and create a Git folder in Databricks from your fork.
2. **Set two variables** in `resources/variables/common.vars.yml`: `cicd_service_principal` (the application ID of
   the service principal that deploys int, cert, and prod) and `warehouse_name` (an existing SQL warehouse). No host
   is pinned: the workspace UI deploys to the workspace you're in, and CI uses `DATABRICKS_HOST`.
3. **Run `devops/lab_setup/00_lab_setup`** from your Git folder as a workspace admin. It creates the catalogs, landing
   data, SQL warehouse, legacy job, and Genie Code instructions.
4. **Connect GitHub Actions:** create GitHub environments `ci`, `int`, `cert`, `prod` with secrets
   `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`, plus repository variables `DATABRICKS_HOST` and
   `DATABRICKS_CI_ENABLED=true`. Add a required reviewer to `prod`. Prefer
   [workload identity federation](https://docs.databricks.com/dev-tools/auth/provider-github) over secrets when you
   have account admin access.
5. **Deploy `dev`** from the Deployments panel to test, and merge to `develop` / `main` to promote.

## Run the checks locally

```bash
pip install -r requirements-dev.txt
ruff check . && pytest
```
