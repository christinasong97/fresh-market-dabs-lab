# Databricks notebook source
# MAGIC %md
# MAGIC # Module 5 · Pull request and checks (20 min)
# MAGIC
# MAGIC **Goal:** see how a change gets to production without anyone rebuilding it by hand.
# MAGIC
# MAGIC Your alert works in dev. Now it has to reach production, where Store Ops depends on it every morning. This is
# MAGIC where the handoff to DevOps used to be: send the definition, wait, and hope it gets rebuilt the same way. With a
# MAGIC bundle, the same files you tested go to production, and a few automatic gates make sure they're safe.
# MAGIC
# MAGIC This module has two parts:
# MAGIC
# MAGIC | Part | What happens | You |
# MAGIC |---|---|---|
# MAGIC | **Part 1 · Watch** (10 min) | A real pull request goes to production on GitHub | Watch the instructor's screen |
# MAGIC | **Part 2 · Your turn** (10 min) | You find and fix the same mistake in your own copy | Run the cells |

# COMMAND ----------

# MAGIC %run ./_lab_helpers

# COMMAND ----------

# MAGIC %md
# MAGIC ## Part 1 · Watch: the path to production (instructor's screen)
# MAGIC
# MAGIC **You don't need to do anything in Part 1.** Follow along on the instructor's screen. Four words you'll hear:
# MAGIC
# MAGIC | Word | What it means |
# MAGIC |---|---|
# MAGIC | **Branch** | Your own copy of the code in Git, where you make changes without affecting anyone else |
# MAGIC | **Pull request (PR)** | A request to merge your branch into `main`. It shows the change and needs approval |
# MAGIC | **Checks** | Automated tests that run on every pull request. If one fails, the merge is blocked |
# MAGIC | **Deploy pipeline** | After the merge, GitHub deploys the bundle as the service principal: first to cert, then to prod |
# MAGIC
# MAGIC **The path a change takes:**
# MAGIC
# MAGIC ```
# MAGIC  teammate's branch ──PR──►  checks: lint · unit tests · rule checks · validate int/cert/prod
# MAGIC                               │  (a failure blocks the merge)
# MAGIC                               ▼
# MAGIC                       merge to main ──► deploy to cert as the service principal
# MAGIC                                           └─► run the orchestrator as an integration test
# MAGIC                                                 └─► wait for an approver ──► deploy to prod
# MAGIC ```
# MAGIC
# MAGIC **What you'll see:**
# MAGIC 1. A teammate adds a weekly department report job, but sends failure emails to `jane.doe@example.com`.
# MAGIC 2. They open a pull request. The **rule checks fail**, so the merge button is blocked.
# MAGIC 3. They fix it and push. The checks go green, and a reviewer approves the pull request.
# MAGIC 4. They merge. GitHub deploys to **cert** as the service principal, and the orchestrator runs as a test.
# MAGIC 5. **Prod** waits for an approver. The instructor approves, and the same files deploy to prod.
# MAGIC
# MAGIC **Why each gate exists:**
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
# MAGIC ## Part 2 · Your turn: catch the mistake yourself
# MAGIC
# MAGIC You can't open a pull request on the shared repo, so you'll reproduce the most important moment from Part 1 in
# MAGIC your own copy: the check that blocked the teammate's pull request.
# MAGIC
# MAGIC ### Step 1 · Add the teammate's change
# MAGIC
# MAGIC Run the cell. It adds the teammate's new job to **your** Git folder, exactly as it was in their pull request.
# MAGIC
# MAGIC **Why it matters:** the mistake is easy to make and hard to spot in review. The job works fine, but when it
# MAGIC fails, only Jane hears about it, and Jane might be on vacation. A rule catches it every time.

# COMMAND ----------

add_teammates_change()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 · Deploy it, then run the checks
# MAGIC
# MAGIC 1. **Deploy:** in your Git folder in Databricks, open `databricks.yml` → **Deployments** panel → target **`dev`** →
# MAGIC    **Deploy**. It deploys fine: the YAML is valid.
# MAGIC 2. **Run the cell.** These are the same checks the pull request ran.
# MAGIC
# MAGIC ✅ You should see one failure: *Failure emails go to the team list, not a person*. In Part 1, this is what blocked
# MAGIC the merge.

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 · Fix it
# MAGIC
# MAGIC 1. **Fix the email.** Either **ask Genie Code:** *"The rule checks say so_weekly_department_report sends failure
# MAGIC    emails to a person. Fix it."* Or run the first cell below.
# MAGIC 2. **Redeploy:** Deployments panel → target **`dev`** → **Deploy**.
# MAGIC 3. **Rerun the checks** with the second cell.
# MAGIC
# MAGIC ✅ You should see every rule pass.
# MAGIC
# MAGIC **Why it matters:** it's a one-line fix, made by the person who made the change, before it ever reaches
# MAGIC production. Nobody in DevOps had to find it or fix it for them.

# COMMAND ----------

fix_teammates_change()

# COMMAND ----------

rule_checks()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done with module 5
# MAGIC
# MAGIC The check that blocked the teammate's pull request is the same one you just ran. You'll know a change passes
# MAGIC before you ever open a pull request. **Next:** open **`06_Production_Is_Locked`**.
