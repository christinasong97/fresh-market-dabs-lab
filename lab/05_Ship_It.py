# Databricks notebook source
# MAGIC %md
# MAGIC # Module 5 · Ship it: from dev to production (25 min)
# MAGIC
# MAGIC **Goal:** get a change to production the way your team will: through guardrails and policies, not by hand.
# MAGIC
# MAGIC ![The CI/CD cycle, from Develop to Deploy to Production](./images/cicd_cycle.png)
# MAGIC
# MAGIC | | Part of the cycle | In this lab |
# MAGIC |---|---|---|
# MAGIC | **CI** | **Develop, Build, Test** | Modules 1 to 4: you built the bundle, ran the checks, and deployed your `dev` copy |
# MAGIC | **CI** | **Version Control** | 5.2: the change goes into Git as a pull request, and the CI checks run on it |
# MAGIC | **CD** | **Deploy to Stage** | 5.4: the CD pipeline deploys to **cert** and runs the orchestrator as a test |
# MAGIC | **CD** | **Deploy to Production** | 5.4: after approval, the CD pipeline deploys the same files to **prod** |
# MAGIC
# MAGIC The right half is the part DevOps used to do by hand. Every step in it is a **policy written as code**:
# MAGIC
# MAGIC | Question | The policy | Step |
# MAGIC |---|---|---|
# MAGIC | Who can deploy to prod? | Only the CI/CD service principal | 5.1 |
# MAGIC | What has to pass first? | The team's rule checks, on every pull request | 5.2, 5.3 |
# MAGIC | Who has to approve? | A reviewer for the pull request, and an approver for prod | 5.4 |
# MAGIC | Can anyone change prod by hand? | No: the next deploy puts it back | 5.5 |

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.1 · Try to ship it yourself
# MAGIC
# MAGIC Your alert works in dev. Why not deploy it straight to prod? Try it:
# MAGIC 1. In your Git folder in Databricks, open **`databricks.yml`**. The **Deployments** panel (rocket icon) opens.
# MAGIC 2. In the target dropdown, choose **`prod`**.
# MAGIC 3. Click **Validate**.
# MAGIC
# MAGIC ✅ You should see an error, and nothing is created. In plain English:
# MAGIC
# MAGIC | The panel says | What it means |
# MAGIC |---|---|
# MAGIC | `Path: /Workspace/Users/fed96b3b-.../.bundle/.../prod` | Prod's files live in the CI/CD service principal's own folder |
# MAGIC | `Folder Users is protected` | Only that service principal can write there, so you can't deploy prod |
# MAGIC | `Recommendation: permissions ... should include` you | On purpose: only the service principal can manage prod |
# MAGIC
# MAGIC **Why it matters:** nobody deploys production from their own login, not even an admin by accident. A **service
# MAGIC principal** is a non-human identity that only the CI/CD pipeline uses. Production doesn't depend on who built
# MAGIC it, and every prod deploy goes through the same path.
# MAGIC
# MAGIC Run the cell to see where that policy lives: four lines in `databricks.yml`, owned by DevOps.

# COMMAND ----------

import yaml

prod = yaml.safe_load(open(f"{REPO_ROOT}/databricks.yml"))["targets"]["prod"]
print(yaml.safe_dump({"prod": {k: prod[k] for k in ("mode", "workspace", "run_as", "permissions")}}, sort_keys=False))

# COMMAND ----------

# MAGIC %md
# MAGIC **Read it:**
# MAGIC
# MAGIC ```
# MAGIC mode: production                         ← no name prefixes, schedules run, stricter checks
# MAGIC workspace:
# MAGIC   root_path: /Workspace/Users/${var.cicd_service_principal}/...   ← prod's files: only the service principal can write
# MAGIC run_as:
# MAGIC   service_principal_name: ...            ← prod jobs run as the service principal, never as a person
# MAGIC permissions:
# MAGIC   - level: CAN_MANAGE  (service principal)   ← only the CI/CD pipeline can change prod
# MAGIC   - level: CAN_VIEW    (users)               ← everyone else can look
# MAGIC ```
# MAGIC
# MAGIC So how *does* a change get to production? Through a pull request.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.2 · Watch: a pull request (instructor's screen)
# MAGIC
# MAGIC **Watch the instructor's screen for this step.** A teammate added a new job, a weekly department sales report for
# MAGIC merchandising, on their own branch. The instructor opens their pull request live.
# MAGIC
# MAGIC | Word | What it means |
# MAGIC |---|---|
# MAGIC | **Branch** | Your own copy of the code in Git, where you make changes without affecting anyone else |
# MAGIC | **Pull request (PR)** | A request to merge your branch into `main`. It shows the change and needs approval |
# MAGIC | **Checks** | Automated tests that run on every pull request. If one fails, the merge is blocked |
# MAGIC
# MAGIC **Be the reviewer.** Run the cell to see the teammate's change, the same file the pull request shows. Can you spot
# MAGIC the problem before the checks do?

# COMMAND ----------

show_teammates_change()

# COMMAND ----------

# MAGIC %md
# MAGIC Found it? The job sends failure emails to `jane.doe@example.com`, a person, not the team list. When Jane is on
# MAGIC vacation, nobody hears about failures. Easy to miss in a review, and on the instructor's screen the **rule checks
# MAGIC fail**, so the merge button is blocked.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.3 · Your turn: run the same check
# MAGIC
# MAGIC You can't open a pull request on the shared repo, but you can run exactly what CI just ran.
# MAGIC
# MAGIC 1. **Run the first cell.** It adds the teammate's job to your Git folder and runs the checks.
# MAGIC    ✅ One failure: *Failure emails go to the team list, not a person*. That's what blocked the merge.
# MAGIC 2. **Fix it:** ask Genie Code *"The rule checks say so_weekly_department_report sends failure emails to a person.
# MAGIC    Fix it."*, or run the second cell.
# MAGIC    ✅ Every rule passes.
# MAGIC
# MAGIC **Why it matters:** the check that blocks a pull request is one you can run yourself, in seconds. The person who
# MAGIC made the change fixes it before anyone else has to review it.

# COMMAND ----------

add_teammates_change()
rule_checks()

# COMMAND ----------

fix_teammates_change()
rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.4 · Watch: merge, cert, approval, prod (instructor's screen)
# MAGIC
# MAGIC The teammate pushes the same fix. On the instructor's screen:
# MAGIC 1. The checks go green, and a reviewer approves the pull request.
# MAGIC 2. **Merge.** GitHub Actions deploys to **cert** as the service principal.
# MAGIC 3. The orchestrator runs end to end on cert data, as an integration test.
# MAGIC 4. **Prod waits for an approver.** The room votes: ship it? The instructor approves.
# MAGIC 5. The same files deploy to **prod**. The new job is live as `fresh_market_dabs_lab_prod_so_weekly_department_report`,
# MAGIC    run by the service principal. Nobody clicked anything in prod.
# MAGIC
# MAGIC | Gate | What it protects |
# MAGIC |---|---|
# MAGIC | **Automated checks** | The team's rules are enforced on every change, so nobody has to remember them |
# MAGIC | **Review** | A teammate reads the change. If it touches DevOps-owned files, like targets, DevOps approves too |
# MAGIC | **Cert run** | The orchestrator runs end to end on cert data before prod sees anything |
# MAGIC | **Prod approval** | A person signs off on the final step, and their name is recorded |
# MAGIC
# MAGIC Every production change leaves a record: the PR, the diff, the checks, the approver, and the deploy log. Run the
# MAGIC cell for links to browse them later.

# COMMAND ----------

REPO = "https://github.com/christinasong97/fresh-market-dabs-lab"
displayHTML(
    f'<a href="{REPO}/pulls?q=is%3Apr" target="_blank">Pull requests</a>'
    f' · <a href="{REPO}/actions" target="_blank">Actions (checks and deploys)</a>'
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.5 · Watch: production is locked (instructor's screen)
# MAGIC
# MAGIC It's 6am, a district manager wants the alert threshold changed, and someone with access is tempted to edit the
# MAGIC prod job in the UI.
# MAGIC 1. The instructor changes the prod orchestrator's schedule by hand. The UI warns that the job is managed by a
# MAGIC    bundle.
# MAGIC 2. The next deploy from `main` puts the schedule back. **Git is the record of what production should be.**
# MAGIC
# MAGIC **Why it matters:** a hand edit leaves no record and the next deploy erases it. The right way to change prod is
# MAGIC the path you just saw: change the files, open a pull request, pass the checks, get approval.
# MAGIC
# MAGIC The cell lists production jobs in this workspace and who can manage them. In your workspace there are none:
# MAGIC prod only exists where the CD pipeline deploys it.

# COMMAND ----------

prod_jobs = [j for j in w.jobs.list() if j.settings and j.settings.name.startswith(f"{BUNDLE}_prod_")]
if not prod_jobs:
    print("No production jobs in this workspace: prod only exists where the CD pipeline deploys it.")
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
# MAGIC **The guardrails you saw today, and where each one lives:**
# MAGIC
# MAGIC | Guardrail | Where it lives | Who owns it |
# MAGIC |---|---|---|
# MAGIC | Only the CI/CD pipeline deploys to shared targets | `databricks.yml`: `run_as`, `root_path`, `permissions` | DevOps |
# MAGIC | Team rules, checked on every change | `tests/bundle/` (run by `rule_checks()` and by CI) | DevOps |
# MAGIC | Genie Code follows the team's rules | `.assistant_workspace_instructions.md` | DevOps |
# MAGIC | Your own safe copy | The `dev` target (development mode) | DevOps sets it up; you use it |
# MAGIC | Review and approval before prod | Pull requests and the GitHub `prod` environment | The team |
# MAGIC | No hand edits in prod | Production mode, plus deploys from `main` | Everyone |
# MAGIC
# MAGIC | You did | Why it matters |
# MAGIC |---|---|
# MAGIC | Turned a hand-built job into bundle files | No more rebuilding by hand for each environment |
# MAGIC | Had Genie Code follow the DevOps team's rules | Standards set once, followed by everyone |
# MAGIC | Ran the same checks CI runs | You know a change passes before you open a pull request |
# MAGIC | Deployed your own `dev` copy | Test the real thing without touching shared environments |
# MAGIC | Saw a change go pull request → cert → approval → prod | Every production change is reviewed and recorded |
# MAGIC
# MAGIC **Take it home:** the repo's README explains how to set this up in your own workspace. In your team's bundle,
# MAGIC start with three things: a `dev` target, variables instead of hard-coded values, and `tests/bundle/test_rules.py`.
# MAGIC
# MAGIC **Clean up (optional):** Deployments panel → target `dev` → **Destroy** removes everything you deployed today.
