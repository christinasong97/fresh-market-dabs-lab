# Databricks notebook source
# MAGIC %md
# MAGIC # Module 5 · Pull request and checks (20 min)
# MAGIC
# MAGIC **Goal:** see how a change gets to production without anyone rebuilding it by hand.
# MAGIC
# MAGIC Your instructor shows the real pull request on screen. Then you catch the same mistake yourself, in your copy.
# MAGIC
# MAGIC **What's a pull request (PR)?** A request to merge your branch into the shared `main` branch. It shows exactly
# MAGIC what changed, runs automated checks, and needs a reviewer's approval. Merging is what triggers deployment.

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.1 · Watch: the promotion path (instructor)
# MAGIC
# MAGIC ```
# MAGIC  feature branch ──PR──►  checks: lint · unit tests · rule checks · validate int/cert/prod
# MAGIC                            │  (a failure blocks the merge)
# MAGIC                            ▼
# MAGIC                    merge to main ──► deploy to cert as the service principal
# MAGIC                                        └─► run the orchestrator as an integration test
# MAGIC                                              └─► wait for an approver ──► deploy to prod
# MAGIC ```
# MAGIC
# MAGIC 1. A teammate adds a weekly department report job, but sends failure emails to `jane.doe@...`.
# MAGIC 2. They open a pull request. The **rule checks fail**, so the merge button is blocked.
# MAGIC 3. They fix it and push. The checks go green. **CODEOWNERS** asks DevOps to review because a guarded path changed.
# MAGIC 4. Merge → deploy to **cert** as the service principal → the orchestrator runs as the integration test.
# MAGIC 5. **Prod** waits for an approver. The instructor approves; the same files deploy to prod.
# MAGIC
# MAGIC Every production change leaves a record: the PR, the diff, the checks, the approver, and the deploy log.
# MAGIC You can browse them in the repo's **Pull requests** and **Actions** tabs.

# COMMAND ----------

REPO = "https://github.com/christinasong97/fresh-market-dabs-lab"
displayHTML(
    f'<a href="{REPO}/pulls?q=is%3Apr" target="_blank">Pull requests</a>'
    f' · <a href="{REPO}/actions" target="_blank">Actions (checks and deploys)</a>'
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.2 · Try it: catch the teammate's mistake yourself
# MAGIC
# MAGIC This cell adds the teammate's new job to **your** Git folder, exactly as it was in their pull request.

# COMMAND ----------

add_teammates_change()

# COMMAND ----------

# MAGIC %md
# MAGIC Now deploy it (Deployments panel → `dev` → **Deploy**). It deploys fine. Then run the checks, the same ones the
# MAGIC pull request ran.
# MAGIC
# MAGIC ✅ You should see one failure: *Failure emails go to the team list, not a person*.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5.3 · Fix it
# MAGIC
# MAGIC Ask Genie Code: *"The rule checks say so_weekly_department_report sends failure emails to a person. Fix it."*
# MAGIC Or run the next cell. Then redeploy and rerun the checks.
# MAGIC
# MAGIC ✅ You should see every rule pass.

# COMMAND ----------

fix_teammates_change()

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 5
# MAGIC
# MAGIC The check that blocked the teammate's pull request is the same one you just ran. You'll know it passes before you
# MAGIC ever open a PR. **Next:** open **`06_Production_Is_Locked`**.
