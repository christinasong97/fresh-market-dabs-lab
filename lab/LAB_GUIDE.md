# Lab Guide: CI/CD with Declarative Automation Bundles

> **Declarative Automation Bundles (DABs)** were formerly called **Databricks Asset Bundles**. Same feature,
> new name.

**Time:** 90 minutes · **Where:** the Databricks workspace (no IDE, no terminal) · **Tools:** Git folders, Deployments panel, Genie Code

You'll take a job built by hand the way jobs are built today, turn it into code you own, test your own
copy, and see how it gets to production without anyone rebuilding it by hand.

| Part | Module | Time |
|---|---|---|
| Hands-on | 0 · Today vs. target | 10 min |
| | 1 · From handoff to bundle | 10 min |
| | 2 · The guardrails DevOps owns | 10 min |
| | 3 · Build the bundle with Genie Code | 20 min |
| | 4 · Your own development target | 15 min |
| Instructor-led | 5 · Pull request and checks | 20 min |
| | 6 · Production is locked | 5 min |

If you fall behind, switch your Git folder to the catch-up branch listed at the end of each module.

---

## Before you start: create your Git folder and run START_HERE

1. **Workspace → Create → Git folder.**
2. URL: `https://github.com/christinasong97/fresh-market-dabs-lab`, provider **GitHub**. Click **Create Git folder**.
3. In the Git folder, open the branch picker and switch to **`lab/start`**. Optionally create your own local
   branch, e.g. `feature/<your-name>`.
4. Open **`00_START_HERE`** in the Git folder and run it top to bottom. It explains bundles, sets up the lab
   environment (catalogs, data, warehouse, the legacy job, Genie Code instructions), and checks that it's ready.
5. Open `databricks.yml`. The editor recognizes the bundle and shows the **Deployments** panel (rocket icon).

> The repo is public and read-only for you: you can branch, edit, and deploy your own copy, but you can't push.
> That's on purpose. Module 5 shows the push → pull request → production path.

---

## Module 0 · Today vs. target (instructor, 10 min)

**Today:** a developer builds a job in INT → hands the definition to DevOps → DevOps rebuilds it as a bundle
and deploys it. Every handoff is a chance for the deployed job to drift from what was tested.

**Target:** DevOps writes the rules once (the template, the Genie Code instructions, the CI checks). Developers
own their files under `resources/` and `src/`, test their own copy, and open a pull request. The pipeline
promotes the same files to every environment.

Look around `lab/start`:
- `databricks.yml` — targets `int`, `cert`, `prod`. All production mode, all run as the CI/CD service principal.
- `resources/variables/common.vars.yml` — `catalog`, `notification_email`, `warehouse_id` (looked up by name).
- `resources/dashboards/` and `resources/genie_spaces/` — a dashboard and Genie space that are **already code**.
- `tests/bundle/test_rules.py` — the team rules as tests.

---

## Module 1 · From handoff to bundle (10 min)

The job **`Job_02_PL_Store_KPI_Alerts`** was built by hand in INT. Open it from **Jobs & Pipelines** and look at:
the numbered name, the personal email on failure, and the notebook with `fresh_market_lab_int` hard-coded.

**Bring it into your bundle:**
1. In the Deployments panel, choose **Add existing resource → Job**, pick `Job_02_PL_Store_KPI_Alerts`.
   (Alternative: on the job page, **⋮ → View as code → YAML**, copy it into a new file under `resources/`.)
2. The YAML lands in `resources/` and the notebook in `src/`.
3. Ask Genie Code:

> **Prompt card 1:** *Explain this job YAML to me. What would break if we deployed it to cert and prod as-is?*

**Run the team's checks:** in the Deployments panel, pick target **dev** and click **Deploy**. Then run the
**`admin_rule_checks`** job. These are the same checks CI runs on every pull request. The imported job deploys
fine, but the checks fail on five rules. That's the gap between "valid" and "follows our standards."

Catch-up: `lab/01-imported`

---

## Module 2 · The guardrails DevOps owns (10 min)

Open `.assistant_workspace_instructions.md`. This is the team's standard written for Genie Code. DevOps keeps it
in the repo and publishes it to the workspace, so every developer's Genie Code follows the same rules.

> **Prompt card 2:** *Restructure the imported Job_02 job to follow our workspace bundle standards. It belongs to
> the store_ops domain. Name it so_store_kpis. Read from the gold_daily_store_sales table instead of the landing
> CSVs. Put the KPI logic in src/store_ops/lib/store_kpi_logic.py as pure functions, keep the notebook thin, and
> add a condition task so the notify step only runs when stores are flagged.*

Check what Genie Code did against the rules: name pattern, `so_` key, tags, `${var.notification_email}`,
no hard-coded catalog, folder split. Then validate in the Deployments panel.

Catch-up: `lab/02-restructured`

---

## Module 3 · Build the bundle with Genie Code (20 min)

> **Prompt card 3a:** *Create a Spark Declarative Pipeline for store_ops called so_sales_medallion. Bronze: Auto
> Loader over the POS CSVs in ${var.landing_path}/pos_transactions. Silver: clean transactions (drop rows with no
> store_id or product_id, non-positive quantity, or missing amount), plus stores, products, and store targets.
> Gold: gold_daily_store_sales (net sales and target attainment per store per day) and gold_department_sales. Put
> the rules in expectations/ dictionaries. Serverless.*

**Start it early:** as soon as the pipeline YAML validates, move on. You'll deploy and run it in module 4.

> **Prompt card 3b:** *Create orchestrator.job.yml for store_ops: refresh so_sales_medallion, then run the
> so_store_kpis job. Schedule it daily at 6am Eastern.*

Validate after each step. Notice the dashboard and Genie space already reference `gold_daily_store_sales`,
`gold_department_sales`, and `gold_store_alerts`. Jobs, pipelines, dashboards, and the agent are all one bundle.

Catch-up: `lab/03-pipeline`

---

## Module 4 · Your own development target (15 min)

`int`, `cert`, and `prod` are locked to the CI/CD service principal, so only CI can deploy them. The `dev`
target is what lets you test the real thing yourself. Your team's current template doesn't have one; this is the
piece the lab adds.

```yaml
targets:
  dev:
    mode: development
    default: true
    variables:
      environment: dev
      catalog: fresh_market_lab_int
```

1. **Deploy** from the Deployments panel (target `dev`).
2. Look at what you got: every job is prefixed `[dev <you>]`, schedules are paused, and your tables land in
   `fresh_market_lab_int.dev_<you>_store_ops`, so nobody else's work is touched.
3. Run **`so_orchestrator`**. While it runs, run **`admin_rule_checks`** again. Everything should pass now.
4. When the orchestrator finishes, open **Store Performance (dev)** and ask **Store Ops Genie (dev)**:
   *Which stores are underperforming right now?*
5. Open `databricks.yml` and compare `dev` with `prod`: same resources, different catalog, run-as identity,
   and permissions.

Catch-up: `main` (complete solution)

---

## Module 5 · Pull request and checks (instructor, 20 min)

Watch on screen, then explore the same things yourself in the repo's **Pull requests** and **Actions** tabs:
1. A developer pushes a branch that adds a job notifying `jane.doe@...` instead of the team list.
2. They open a pull request. **CI** runs lint, unit tests, the rule checks, and `bundle validate` for int, cert,
   and prod. The rule check fails; the merge button is blocked.
3. The fix is pushed; CI goes green. **CODEOWNERS** requires DevOps approval because the change touched a
   guarded path.
4. Merge to `main` → deploy to **cert** as the service principal → the orchestrator runs as an integration test.
5. The **prod** deployment waits for an approver. The instructor approves; the same files deploy to prod.

## Module 6 · Production is locked (instructor, 5 min)

1. The instructor edits the prod orchestrator in the UI (changes the schedule). The UI warns that the job is
   managed by a bundle.
2. The next deploy puts it back. Git is the source of truth.
3. Production resources show **Can View** for everyone except the service principal.

---

## Take it home

- Fork the repo and follow the README to run the whole flow in your own workspace.
- In your team's bundle: add a `dev` target, move hard-coded IDs to lookups, and add `tests/bundle/test_rules.py`.
