# Fresh Market Lab: CI/CD with Declarative Automation Bundles

A reference bundle for the DevOps team's repository layout, plus a 90-minute hands-on lab. You take a job
built by hand in the workspace, bring it into a bundle, test your own copy, and see it promoted to
production through a pull request, automated checks, and an approval gate. All of it happens in the
Databricks workspace UI with Genie Code.

- **Lab guide:** [lab/LAB_GUIDE.md](lab/LAB_GUIDE.md)
- **Instructor talk track:** [lab/TALK_TRACK.md](lab/TALK_TRACK.md)

## What's in the bundle

| Resource | Key | What it does |
|---|---|---|
| Schema | `so_store_ops` | Output schema per target (`dev_<you>_store_ops` in dev) |
| Pipeline | `so_sales_medallion` | POS landing CSVs → bronze → silver → gold, with expectations |
| Job | `so_store_kpis` | Flags stores behind target, notifies only when there are any |
| Job | `so_orchestrator` | Daily DAG: refresh sales → publish KPIs |
| Dashboard | `so_store_performance` | Store performance overview |
| Genie space | `so_store_ops_genie` | "Store Ops Genie" — ask questions about store sales |
| Job | `admin_rule_checks` | The same rule checks CI runs, runnable from the workspace |

## Targets

| Target | Mode | Catalog | Deployed by | When |
|---|---|---|---|---|
| `dev` | development | `fresh_market_lab_int` (your own schema) | You, from the Deployments panel | Any time |
| `int` | production | `fresh_market_lab_int` | CI/CD service principal | Merge to `develop` |
| `cert` | production | `fresh_market_lab_cert` | CI/CD service principal | Merge to `main` |
| `prod` | production | `fresh_market_lab_prod` | CI/CD service principal | After cert passes **and** an approver signs off |

## Layout

```
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
.github/                           # CI, deploy, CODEOWNERS
.assistant_workspace_instructions.md  # Genie Code instructions (the team's rules)
```

## Branches

| Branch | Use |
|---|---|
| `lab/start` | Where attendees begin: template (with a `dev` target), tests, CI, dashboard, and Genie space only |
| `lab/01-imported` | Catch-up: legacy job imported as-is (fails the rule checks on purpose) |
| `lab/02-restructured` | Catch-up: job restructured to the team standard |
| `lab/03-pipeline` | Catch-up: pipeline and orchestrator added |
| `main` / `develop` | Complete solution, promoted by CI |

## Try the full flow yourself

Fork the repo, then:
1. Set `cicd_service_principal` and `warehouse_name` in `resources/variables/common.vars.yml`. No host is pinned:
   the workspace UI deploys to the workspace you're in, and CI uses `DATABRICKS_HOST`.
2. Open `devops/lab_setup/00_lab_setup` from your Git folder and click **Run all** (as a workspace admin). It creates
   the catalogs, landing data, SQL warehouse, legacy job, and Genie Code instructions.
3. Create GitHub environments `ci`, `int`, `cert`, `prod` with secrets `DATABRICKS_CLIENT_ID` and
   `DATABRICKS_CLIENT_SECRET`, plus a repository variable `DATABRICKS_HOST`. Add a required reviewer to `prod`.
   Prefer [workload identity federation](https://docs.databricks.com/dev-tools/auth/provider-github) over secrets
   when you have account admin access.

## Run the checks locally

```bash
pip install -r requirements-dev.txt
ruff check . && pytest
```
