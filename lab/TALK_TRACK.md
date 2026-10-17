# Instructor Talk Track

One story runs through the whole lab: **a developer gets their own change to production, and nobody rebuilds it
by hand.** Each module shows one or two platform features that make that possible.

## Highlight features

| Feature | Where it shows up | One-line message |
|---|---|---|
| Bundles in the workspace (Git folders + Deployments panel) | Every module | No IDE, no terminal. Developers stay in the workspace they already use |
| Import an existing job into a bundle | Module 1 | The job you'd hand to DevOps becomes code you own, in a minute |
| Genie Code agent mode + workspace instructions | Modules 1–3 | DevOps writes the standard once; every developer's AI-written code follows it |
| Jobs, pipelines, dashboards, and Genie spaces as code | Module 3 | The agent and the dashboard ship with the tables they read, reviewed in the same PR |
| Development mode | Module 4 | Every developer gets an isolated copy: prefixed names, paused schedules, own schema |
| Variables, lookups, targets | Module 4 | Same files everywhere; only the catalog, identity, and permissions change |
| `bundle validate --strict` | Modules 2–5 | It caught a real security issue while building this lab (see below) |
| Rule checks as tests | Modules 4–5 | Team rules are enforced by code on every change, not by a reviewer's memory |
| `run_as` service principal + production mode | Modules 5–6 | No person deploys to a shared environment; production can't be hand-edited for long |
| GitHub environments + required reviewers | Module 5 | Every prod change carries a PR, a diff, an approver, and a deploy log |
| Direct deployment engine | Background | No Terraform state to manage; required for Genie spaces |

## Module-by-module

### 0 · Today vs. target (10 min)
- "DevOps and the platform team already chose bundles. The open question is who does the work."
- Show today's handoff. Ask: *how many of you have had a job behave differently in prod than in INT?*
- Show the ownership split: DevOps owns `databricks.yml`, variables, CI, and the Genie Code instructions.
  Developers own `resources/` and `src/`.
- "Everything you'll see follows your DevOps team's bundle layout: `*.job.yml` and `*.vars.yml` siblings, domain prefixes,
  an orchestrator instead of `Job_00/01/02`, expectations next to the pipeline code."

### 1 · From handoff to bundle (10 min)
- Open `Job_02_PL_Store_KPI_Alerts`. Point out: numbered name, `Task_01_`, personal email, hard-coded catalog.
- Import it. "This YAML is exactly what you'd send DevOps today. It deploys. It just doesn't follow any of our rules."
- Genie Code prompt card 1. Let it list the problems; it usually finds the hard-coded catalog first.

### 2 · The guardrails DevOps owns (10 min)
- Open `.assistant_workspace_instructions.md`. "This is the wiki, written for Genie Code."
- Prompt card 2. While it works: "Genie Code isn't guessing our conventions. It's reading them."
- Validate. Key message: **rules written once, followed by every developer and by the AI**.

### 3 · Build the bundle with Genie Code (20 min)
- Prompt cards 3a and 3b. Point out `expect_all_or_drop` in silver vs `expect_all_or_fail` in gold, which is the
  wiki's severity convention.
- Open the dashboard and Genie space YAML. "The agent's tables, instructions, and example SQL are code. Change the
  gold table, and the Genie space change is in the same pull request."
- Show `${resources.schemas.so_store_ops.name}` in the Genie space: the agent automatically points at the right
  schema in every environment.

### 4 · Your own development target (15 min)
- "Today's template deploys every target in production mode, so there's no way to test your own copy. One target
  fixes that."
- After deploy: show `[dev <name>]` prefixes, paused schedules, and `dev_<name>_store_ops`.
- Run `admin_rule_checks`. "This is the exact test file CI runs. You'll know it passes before you open a PR."
- Compare `dev` and `prod` side by side.
- **Validate story:** while building this lab, `bundle validate --strict` flagged that putting shared targets
  under `/Workspace/Shared` makes them writable by every user. We moved them to the service principal's home
  folder. The tool caught a security problem before anyone noticed.

### 5 · Pull request and checks (20 min, instructor screen)
- Walk through the planted-violation PR: CI fails on `test_failure_notifications_go_to_a_group`, the merge is
  blocked, the fix goes green.
- Show CODEOWNERS requesting review because a guarded path changed.
- Merge → cert deploy as the service principal → orchestrator runs as the integration test → prod waits for approval.
- Approve live. "That's the change record: PR, diff, checks, approver, deploy log."
- On classic compute: "Your production jobs run on classic clusters with policies. The bundle handles that with
  `job_clusters` and a `policy_id` lookup, and `test_job_clusters_use_a_policy` already enforces it. The lab uses
  serverless only so it spins up fast."

### 6 · Production is locked (5 min)
- Edit the prod orchestrator schedule in the UI and redeploy. The change is gone.
- "If you need a change in prod, it goes through a PR. That's the point."

## Likely questions

- **"Why GitHub? We use Azure DevOps."** The pattern is the same: Azure Pipelines environments with approvals
  replace GitHub environments, and Databricks supports workload identity federation from Azure DevOps.
- **"Why secrets instead of OIDC in this repo?"** Federation policies are set at the account level. The lab
  workspace doesn't have account admin; your production workspaces should use federation.
- **"Can Genie Code break the rules anyway?"** Yes, it can make mistakes. That's why the rule checks exist: the
  instructions make the right answer likely, and the tests make the wrong one visible.
- **"What about Agent Bricks?"** There's no bundle resource for Knowledge Assistants yet. Genie spaces, model
  serving endpoints, and apps are supported.
