# Instructor Talk Track: CI/CD with Declarative Automation Bundles

One story runs through the whole lab: **a developer gets their own change to production, and nobody rebuilds it by
hand.** Each module adds one piece of that story.

**How to read the cues**

| Cue | Meaning |
|---|---|
| **CLICK** | What to click on your screen (attendees follow along) |
| **SAY** | Suggested words. Paraphrase freely |
| **RUN** | A notebook cell to run, or code to paste |
| **ASK** | A question for the room |
| **CHECK** | What attendees should see before you move on |
| **WAIT** | Something takes a while. Use the filler ideas listed |
| **IF** | A likely problem and what to do |

## Before the session

**One day before**
- Your **demo workspace** (Free Edition, looks like an attendee's): Git folder created, `00_START_HERE` run, all ✅.
  Stop there. If you rehearsed in it, run `devops/instructor/reset_demo` first.
- Your **production demo workspace** (where GitHub Actions deploys int, cert, prod): prod deployed, the example pull
  request ready (the teammate's job with `jane.doe@example.com`), the cert integration test run once.
- Pre-work email sent (`devops/instructor/PRE_WORK_EMAIL.md`). Follow up with anyone who hasn't replied ✅.
- Backup: a screen recording of module 4's orchestrator run and dashboard, in case serverless is slow.

**Tabs to have open**
1. Demo workspace: the Git folder, with `00_START_HERE` open
2. GitHub: the repo's **Pull requests** and **Actions** tabs
3. Production demo workspace: the prod orchestrator job and the prod dashboard

**Timing (90 minutes)**

| Module | Minutes | Who drives |
|---|---|---|
| 0 · Welcome and the scenario | 10 | You |
| 1 · From handoff to bundle | 10 | Everyone |
| 2 · The guardrails DevOps owns | 10 | Everyone |
| 3 · Build the bundle with Genie Code | 20 | Everyone |
| 4 · Your own development target | 15 | Everyone |
| 5 · Pull request and checks | 20 | You, then everyone |
| 6 · Production is locked | 5 | You |

## Highlight features

| Feature | Where it shows up | One-line message |
|---|---|---|
| Bundles in the workspace (Git folders and the Deployments panel) | Every module | No IDE, no terminal. Developers stay in the workspace they already use |
| Add existing job to a bundle | Module 1 | The job you'd hand to DevOps becomes code you own, in a minute |
| Genie Code agent mode and workspace instructions | Modules 1 to 3 | DevOps writes the standard once; every developer's AI-written code follows it |
| Jobs, pipelines, dashboards, and Genie spaces as code | Modules 3 and 4 | The dashboard and agent ship with the tables they read, reviewed in the same PR |
| Rule checks as tests | Modules 1 to 5 | Team rules are enforced by code on every change, not by a reviewer's memory |
| Development mode | Module 4 | Every developer gets an isolated copy: prefixed names, paused schedules, own schema |
| Variables and targets | Module 4 | Same files everywhere; only the catalog, identity, and permissions change |
| `run_as` service principal and production mode | Modules 5 and 6 | No person deploys to a shared environment |
| GitHub environments and required reviewers | Module 5 | Every prod change carries a PR, a diff, an approver, and a deploy log |

## Module 0 · Welcome and the scenario (10 min)

**CLICK** `00_START_HERE`, top of the notebook.

**SAY** "In the next 90 minutes you'll take a job built by hand, turn it into code you own, test your own copy, and
watch it go to production through a pull request. Everything happens in the workspace. No terminal, no IDE."

**SAY** (name it up front) "Declarative Automation Bundles is the new name for Databricks Asset Bundles. Same
feature, same `databricks.yml`. If your wiki says Asset Bundles, it's the same thing."

**CLICK** scroll to **The scenario: Fresh Market**.

**SAY** "Fresh Market is a made-up grocery chain with 40 stores. Every morning, Store Ops needs to know which stores
are behind their sales target. Today a developer builds those jobs by hand in INT, and DevOps rebuilds them for CERT
and PROD. You're the developer today, and your job is to get it to production with no handoff."

**ASK** "How many of you have had a job behave differently in prod than it did in INT?" (Let two or three people
answer. Their stories are the reason for the rest of the lab.)

**CLICK** scroll to **What is a DAB?** Walk the folder diagram: `databricks.yml` (targets), `resources/` (what to
create), `src/` (the code).

**SAY** "The bundle is a folder. You don't click resources into existence; you deploy the folder, and Databricks
creates everything it describes. Same folder to dev, to cert, to prod."

**CLICK** the **click-ops vs. bundle** table. Pick one row that fits the room (usually "Moving to prod").

**RUN** Step 1 (setup) only if you skipped pre-work in this workspace. Otherwise **RUN** Step 2 (the checks).

**CHECK** Everyone has all ✅ in Step 2. **IF** someone doesn't: have them run Step 1 now; it runs while you go on.

## Module 1 · From handoff to bundle (10 min)

**CLICK** `lab/01_From_Handoff_to_Bundle`. **RUN** the helpers cell.

**SAY** "This is the job a developer built by hand. It's the daily store alert: it reads the last 15 days of sales,
compares each store with its target, and flags anyone under 85%."

**RUN** 1.1. **ASK** "What would break if we moved this to prod?" Then **CLICK** the **What's wrong with it?** list:
numbered names, Jane gets the failure emails, hard-coded INT catalog, reads raw files.

**CLICK** 1.2, Option A, on your screen, so attendees see the no-code path:
1. Workspace → your Git folder → **Open in editor**
2. **Deployments** (rocket) → **Bundle resources** → **Add** → **Add existing job**
3. Choose `Job_02_PL_Store_KPI_Alerts` → **(Advanced) Don't update** → **Add**

**SAY** "Pick **Don't update**. The bundle gets its own copy; the original job is untouched. The other two options
link the original to your bundle, so your deploys would overwrite it."

**SAY** "Option B does the same with one cell. Use whichever you like; the rest of the lab works with both."

**RUN** 1.3. **CLICK** the outline of the YAML. Point at the **resource key** and at `name`.

**SAY** "Every resource file has this shape: `resources`, the type, the key, then the settings you'd normally click
through. That's all a bundle is."

**RUN** 1.4: paste the Genie Code prompt. **SAY** "Genie Code knows our rules because DevOps published them as
workspace instructions. You'll see them in module 2."

**CLICK** 1.5: Deployments panel → `dev` → **Validate** → **Deploy**.

**RUN** 1.6 (`rule_checks()`). **CHECK** about five ❌.

**SAY** "It's valid YAML, it deploys, and it breaks five team rules. Validate checks the syntax; these checks enforce
the rules DevOps wrote. They're the same test files CI runs on every pull request, and they take a few seconds."

**IF** an attendee sees four failures instead of five: they used Option A, so the notebook isn't in `src/` yet. That's
fine.

## Module 2 · The guardrails DevOps owns (10 min)

**CLICK** `lab/02_Guardrails_with_Genie_Code`. **CLICK** the ownership table.

**SAY** "DevOps owns the targets, the rules, and the checks. You own your files and your dev copy."

**RUN** 2.1. **CLICK** the two-row table.

**SAY** "The team's rules are one Markdown file in the repo. DevOps changes it by pull request, and setup publishes
it to the workspace, where Genie Code reads it for everyone. Only workspace admins can edit the published copy."

**RUN** 2.2: paste the prompt into Genie Code (agent mode). **WAIT** about 5 minutes. While it works:
- **SAY** "Genie Code isn't guessing our conventions. It's reading them. Watch for the `so_` prefix, the naming
  pattern, `${var.notification_email}`, the tags."
- **CLICK** Genie Code's panel and narrate its plan as it goes.
- **SAY** (when someone sees "action denied" or an approval request) "That's a safety guardrail, not a bug. Genie
  Code can't run risky actions, like deleting files or touching anything outside your Git folder, without you.
  That's what you want from an agent with access to your workspace." The prompt tells it not to delete files, so
  these should be rare, but if they appear, it's a good moment to point at.

**RUN** 2.3: the first cell checks Genie Code's files, the second (`remove_imported_job()`) removes the old Job_02
files. **CHECK** three ✅, then "Old Job_02 files removed."

**SAY** "We remove the old files with a cell, not with Genie Code, so the agent never has to delete anything."

**CLICK** 2.4: Deploy, then **RUN** `rule_checks()`. **CHECK** all ✅.

**SAY** "Rules written once, followed by every developer and by the AI, and checked automatically."

**IF** Genie Code's version won't pass after one retry: uncomment and **RUN** the **Catch up** cell, redeploy.

## Module 3 · Build the bundle with Genie Code (20 min)

**CLICK** `lab/03_Build_the_Bundle`. **CLICK** the table of four pieces.

**SAY** "Your KPI job reads `gold_daily_store_sales`, and nothing creates it yet. In this module the whole data
product goes into one bundle: the pipeline that makes the data, the job that uses it, the run order, and the
dashboard. One pull request, one deploy, promoted together."

**CLICK** 3.1, the medallion table: bronze is raw, silver is clean, gold is business-ready.

**RUN** 3.1: paste the pipeline prompt into Genie Code. **WAIT** this is the longest wait in the lab, about 4 to 8
minutes. See **While Genie Code builds the pipeline** below.

**RUN** the 3.1 check cell. **CHECK** the pipeline YAML, `transformations/`, and `expectations/` all ✅.

**RUN** 3.2: paste the orchestrator prompt. **WAIT** about 1 minute.

**RUN** the 3.2 cell, then **CLICK** the annotated YAML below it.

**SAY** "Look at `${resources.pipelines.so_sales_medallion.id}`. The orchestrator points at the pipeline by its
resource key, not by an ID. Every environment has different IDs; this line works in all of them. And the run order
is in `depends_on`, not in job names."

**CLICK** 3.3, the dashboard sketch. **SAY** "This is what everything in this module feeds: the Store Performance
dashboard district managers open each morning. It's already in the bundle. The tables it reads don't exist yet; the
orchestrator builds them in module 4, and then you'll open it with your own data."

**CLICK** the table that maps each chart to its table and who builds it. **ASK** "Which of these breaks if the
pipeline doesn't run?" (All of them, which is why they deploy together.)

**RUN** the 3.3 cell. **SAY** "The dashboard has the same problem the job had: a hard-coded catalog would pin it to
INT. Its queries use bare table names, and two lines in the YAML fill in this target's catalog and schema. Same file,
dev data in dev, prod data in prod."

**CLICK** 3.4: Deploy, **RUN** `rule_checks()`. **CHECK** all ✅.

**IF** the pipeline won't validate: **RUN** the **Catch up** cell (both lines), then redeploy.

### While Genie Code builds the pipeline (3.1)

Pick two or three. Each takes 1 to 3 minutes. Stop as soon as most of the room has files.

**1. Narrate the agent (1 min).** **CLICK** your Genie Code panel. **SAY** "It's reading the workspace instructions,
then planning the files, then writing them. It's slower than autocomplete because it's doing several steps and
checking its own work." Point at each step as it appears.

**2. Draw the chain (2 min).** On a whiteboard or slide:
`register files → bronze → silver → gold → KPI job → dashboard / Genie space`.
**SAY** "Today, each arrow is a different job, and the order lives in the names `Job_00`, `Job_01`, `Job_02`. By the
end of this module, it's one bundle and one orchestrator."

**3. The data quality rules (2 to 3 min).** **SAY** "There are three kinds of expectation: `expect` records bad rows
and keeps them, `expect_or_drop` removes them, `expect_or_fail` stops the run. The team convention: record in bronze,
drop in silver, fail in gold. Nobody downstream ever sees bad data, and a broken gold table stops the run instead of
reaching a district manager."
**ASK** "Where do your data quality rules live today? Who finds out when a source file is bad?"
**SAY** "In module 4 you'll see exactly how many rows silver drops. About 1,400 bad rows are planted in the data."

**4. Show what good looks like (1 to 2 min).** **CLICK** `lab/solutions/module_03/src/store_ops/pipelines/
sales_medallion/expectations/silver_expectations.py`. **SAY** "This is the reference version. The rules are a plain
dictionary in a file, so changing what counts as a bad row is a one-line diff in a pull request."

**5. Why serverless and Auto Loader (1 min).** **SAY** "The pipeline uses Auto Loader, so it only reads new files each
day, and serverless, so nobody manages a cluster. In your real bundle you'd use job clusters with a policy, and the
rule checks already enforce that: `test_job_clusters_use_a_policy`."

**6. Questions from the room (any length).** Good prompts:
- **ASK** "What would you put in the workspace instructions for your team?"
- **ASK** "Which of your jobs would you move into a bundle first?"
- Likely questions are listed at the end of this doc.

**For attendees who finish early:**
- Ask Genie Code: *"Explain the pipeline you just wrote, layer by layer."*
- Read ahead to 3.2's prompt.
- Open `src/store_ops/pipelines/sales_medallion/expectations/` and compare with the reference version.

**IF** Genie Code is still running after about 8 minutes, or it errors: have that attendee **RUN** the Catch up cell
and keep going. They can look at Genie Code's version later.

## Module 4 · Your own development target (15 min)

**CLICK** `lab/04_Run_Your_Own_Copy`. **CLICK** the `dev` vs. `prod` table.

**SAY** "Many team templates deploy every target in production mode, so there's no safe place to test your own copy.
The `dev` target is that place: your name on everything, your own schema, schedules paused."

**CLICK** 4.1, Step 1: Deployments panel → `dev` → **Deploy**, and wait for it to finish. **SAY** "The cell runs your
deployed copy, so always deploy first."

**RUN** Step 2, `run_job("so_orchestrator")`. **WAIT** 3 to 5 minutes. While it runs:
- **CLICK** the run link. Show the two tasks: the pipeline first, then the KPI job.
- **SAY** "This is the same morning run prod does at 6am, in the right order, because the order is in the
  orchestrator."
- **CLICK** into the pipeline run and show the graph: bronze → silver → gold, with row counts and expectation
  results.

**CHECK** `so_orchestrator: SUCCESS`.

**RUN** 4.2. **CLICK** `bad_rows_dropped` (about 1,400) and the alert list.

**SAY** "Those are the silver rules at work: a register glitch never reaches a district manager's report. And this
is the list Store Ops follows up on."

**CLICK** 4.3. **SAY** "A Genie space can only be created once its tables exist, which is why it joins now."

**Two options, pick one to show on screen** (Option A is the better demo if you have 5 minutes):
- **Option A, the UI:** **CLICK** Genie → **New** → `fresh_market_lab_int` → your dev schema → the three gold tables →
  name it `My Store Ops Genie` → Serverless Starter Warehouse → save. Ask it one question. **RUN**
  `import_genie_space("My Store Ops Genie")`.
  **SAY** "There's no Add existing for Genie spaces in the Deployments panel yet, so a cell exports it. Notice it
  swaps my schema's name for the bundle's variables, so the same file works in prod."
- **Option B, the finished file:** **RUN** `add_genie_space()`. **SAY** "This one comes with instructions and example
  SQL, written once and reviewed like code."

**RUN** the YAML cell and **CLICK** the annotated parts: the title per target, the warehouse lookup, the table
identifiers using variables, the instructions.

**SAY** "Its instructions and example questions are code, reviewed in the same pull request as the tables."

**CLICK** Deploy again. **SAY** "The cell only adds the file. Deploying is what creates the Genie space."

**RUN** 4.4. **CLICK** the dashboard link. **SAY** "This is the dashboard from 3.3, now with our data." Then **CLICK**
the Genie space link and **RUN** `ask_genie(...)`.

**IF** there's no Genie space link: that attendee didn't deploy after 4.3. Deploy, then rerun the cell.

**CHECK** About six underperforming stores.

**SAY** "District managers don't write SQL. This is what Store Ops actually uses, and it all came from one deploy of
one bundle."

**RUN** 4.5 (`rule_checks()`). **CHECK** all ✅. **RUN** 4.6 and compare `dev` with `prod`.

**SAY** "Same resources. Different catalog, different identity, locked permissions. Nobody edits a file to promote."

**Optional, if there's time:** the dashboard change at the end of module 4. Ask Genie Code for a "net sales by store
format" chart, **CLICK** the branch name at the top of the Git folder to show the one-file diff, deploy, and refresh
the dashboard. **SAY** "Your dashboard change is a diff a reviewer can read, and the same file goes to prod."

**IF** the orchestrator is slow: play the backup recording and let attendees' runs finish in the background.

## Module 5 · Pull request and checks (20 min)

**CLICK** `lab/05_Pull_Request_and_Checks`, then **CLICK** the promotion diagram in 5.1.

**SAY** "Your alert works in dev. This is where the handoff to DevOps used to be. Now the files you tested go to
production through automatic gates."

**CLICK** GitHub → **Pull requests** → the teammate's PR (switch to your screen):
1. **CLICK** **Files changed**: the new job, with `jane.doe@example.com`.
2. **CLICK** **Checks**: `test_failure_notifications_go_to_a_group` failed, merge blocked.
3. Push the fix (`${var.notification_email}`). The checks go green.
4. Merge. **CLICK** **Actions**: deploy to cert as the service principal, then the orchestrator runs as the
   integration test.
5. **CLICK** the prod deploy waiting for review → **Approve**.

**SAY** "That's the change record: the PR, the diff, the checks, the approver, and the deploy log. Nobody rebuilt
anything."

**CLICK** the **Why each gate exists** table. One sentence per row.

**SAY** (on classic compute) "Your production jobs run on classic clusters with policies. A bundle handles that with
`job_clusters` and a policy, and the rule checks already enforce it. The lab uses serverless so it starts fast."

**Now attendees:** **RUN** 5.2 (`add_teammates_change()`), Deploy, **RUN** `rule_checks()`. **CHECK** one ❌.

**SAY** "The same check that blocked the PR, in your copy, in seconds."

**RUN** 5.3 (the fix, or ask Genie Code), redeploy, **RUN** `rule_checks()`. **CHECK** all ✅.

## Module 6 · Production is locked (5 min)

**CLICK** the production demo workspace → the prod orchestrator job.

**SAY** "It's 6am, a district manager wants the threshold changed, and someone is tempted to edit prod by hand."

**CLICK** edit the schedule in the UI. Point at the banner saying the job is managed by a bundle.

**RUN** the next deploy from `main` (re-run the deploy workflow). **CLICK** the job again: the schedule is back.

**SAY** "Git is the record of what production should be. A hand edit leaves no record, and the next deploy erases
it. The right way is the path you just saw: files, pull request, checks, approval."

**CLICK** the prod job's **Permissions**: the service principal has **Can Manage**, everyone else **Can View**.

**CLICK** the **Wrap-up** table in notebook 06 and close with the "take it home" line: start your team's bundle with a
`dev` target, variables instead of hard-coded values, and the rule checks.

## Likely questions

- **"Why GitHub? We use Azure DevOps."** The pattern is the same: Azure Pipelines environments with approvals replace
  GitHub environments, and Databricks supports workload identity federation from Azure DevOps.
- **"Why secrets instead of OIDC in this repo?"** Federation policies are set at the account level, and the lab
  workspace has no account admin. Production workspaces should use federation.
- **"Can Genie Code break the rules anyway?"** Yes, it can make mistakes. The instructions make the right answer
  likely; the rule checks make the wrong one visible.
- **"Can I edit a dashboard in the UI and keep it in the bundle?"** Yes. A dashboard in a bundle is a `.lvdash.json`
  file; edits show up as a diff in the Git folder and deploy like any other change.
- **"What about Agent Bricks?"** There's no bundle resource for Knowledge Assistants yet. Genie spaces, model serving
  endpoints, and apps are supported.
- **"What if two developers deploy dev at once?"** Each gets their own copy: names prefixed with their own name and
  their own schema. They never collide.

## If things go wrong

| Problem | What to do |
|---|---|
| Genie Code is slow or wrong | Uncomment and run the module's **Catch up** cell, then redeploy |
| Genie Code says "action denied" | A safety guardrail on risky actions. Approve what's expected; it carries on |
| `No dev copy of ... yet` | The attendee didn't deploy first. Deploy `dev`, then rerun the cell |
| Deploy fails on the Genie space | The tables don't exist yet. It only joins in module 4, after the orchestrator runs |
| `rule_checks()` says it couldn't run the checks | Rerun the cell once (the first run installs pytest) |
| Serverless is slow | Keep talking: each slow step above has filler ideas. Use the backup recording for module 4 |
| An attendee's workspace is broken | Pair them with a neighbor, or have them watch your screen |
| You need to rehearse again | Run `devops/instructor/reset_demo` in your demo workspace |
