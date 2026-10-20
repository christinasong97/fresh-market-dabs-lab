# Databricks notebook source
# MAGIC %md
# MAGIC # Reset the demo (instructor)
# MAGIC
# MAGIC Puts **your** workspace back to where an attendee starts: just after `00_START_HERE`. Use it between rehearsals
# MAGIC so you never need a new workspace.
# MAGIC
# MAGIC **Removes:**
# MAGIC - Everything you deployed to `dev`: jobs, pipeline, dashboard, Genie space (and `My Store Ops Genie` from the UI),
# MAGIC   your `dev_<you>_store_ops` schema,
# MAGIC   and the `dev` deployment state
# MAGIC - Files the modules added to this Git folder: module 1's imports, Genie Code's files, catch-up files, and the
# MAGIC   teammate's job from module 5
# MAGIC
# MAGIC **Keeps:** catalogs, landing data, the warehouse, the legacy job, Genie Code instructions, and the starting files.
# MAGIC
# MAGIC Only touches things you created. Run it from the Git folder you'll demo from, then click **Run all**.
# MAGIC
# MAGIC **One manual step after:** if you edited any *starting* file (for example the dashboard in the UI), open the Git
# MAGIC dialog (the branch name button at the top of the Git folder) and discard those changes.

# COMMAND ----------

import os
import re

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ME = w.current_user.me().user_name
BUNDLE = "fresh_market_dabs_lab"
CATALOG = "fresh_market_lab_int"
REPO_ROOT = os.path.abspath("../..")  # this notebook lives in <git folder>/devops/instructor/

# Files in the Git folder at the start of the lab. Anything else under these folders was added by the modules.
STARTING_FILES = {
    "resources/dashboards/store_ops/so_store_performance.dashboard.yml",
    "resources/jobs/admin/admin_rule_checks.job.yml",
    "resources/schemas/store_ops.schema.yml",
    "resources/variables/common.vars.yml",
    "src/store_ops/dashboards/store_performance.lvdash.json",
    "tests/bundle/test_rules.py",
    "tests/bundle/test_targets.py",
    "tests/conftest.py",
}
CHECKED_FOLDERS = ("resources", "src", "tests")

# Development mode names everything "[dev <short name>] ...".
short = re.sub(r"[^a-z0-9]", "_", ME.split("@")[0].lower())
mine = [j for j in w.jobs.list() if j.creator_user_name == ME and j.settings and j.settings.name.startswith("[dev ")]
mine = [j for j in mine if f"{BUNDLE}_dev_" in j.settings.name]
prefix = mine[0].settings.name.split("]")[0] + "]" if mine else f"[dev {short}]"
schema = f"dev_{prefix[len('[dev ') : -1]}_store_ops"
print(f"Resetting the demo for {ME} (deployed as {prefix})")

# COMMAND ----------

# MAGIC %md ## 1. Remove your dev deployment

# COMMAND ----------


def list_all(path, key):
    items, token = [], None
    while True:
        page = w.api_client.do("GET", path, query={"page_size": 100, **({"page_token": token} if token else {})})
        items += page.get(key, [])
        token = page.get("next_page_token")
        if not token:
            return items


for job in mine:
    w.jobs.delete(job.job_id)
    print(f"deleted job: {job.settings.name}")

for p in w.pipelines.list_pipelines():
    if p.name and p.name.startswith(prefix) and p.creator_user_name == ME:
        w.pipelines.delete(p.pipeline_id)
        print(f"deleted pipeline: {p.name}")

for s in list_all("/api/2.0/genie/spaces", "spaces"):
    # The dev copy, plus the one built in the UI for module 4's Option A.
    if s.get("title", "").startswith(prefix) or s.get("title", "") == "My Store Ops Genie":
        w.api_client.do("DELETE", f"/api/2.0/genie/spaces/{s['space_id']}")
        print(f"deleted Genie space: {s['title']}")

for d in list_all("/api/2.0/lakeview/dashboards", "dashboards"):
    if d.get("display_name", "").startswith(prefix):
        w.api_client.do("DELETE", f"/api/2.0/lakeview/dashboards/{d['dashboard_id']}")
        print(f"deleted dashboard: {d['display_name']}")

try:
    spark.sql(f"DROP SCHEMA IF EXISTS `{CATALOG}`.`{schema}` CASCADE")
    print(f"dropped schema: {CATALOG}.{schema}")
except Exception as e:  # noqa: BLE001 - catalog not set up in this workspace
    print(f"skipped schema: {str(e).splitlines()[0][:120]}")

state = f"/Workspace/Users/{ME}/.bundle/{BUNDLE}/dev"
try:
    w.workspace.delete(state, recursive=True)
    print(f"deleted deployment state: {state}")
except Exception:  # noqa: BLE001 - nothing deployed yet
    print("no deployment state to delete")

# COMMAND ----------

# MAGIC %md ## 2. Remove the files the modules added

# COMMAND ----------

removed = []
for folder in CHECKED_FOLDERS:
    for entry in w.workspace.list(f"{REPO_ROOT}/{folder}", recursive=True):
        if entry.object_type.value == "DIRECTORY":
            continue
        rel = os.path.relpath(entry.path.removeprefix("/Workspace"), REPO_ROOT.removeprefix("/Workspace"))
        # In a Git folder, a .py file with a notebook header shows up as a notebook without the extension.
        if rel not in STARTING_FILES and f"{rel}.py" not in STARTING_FILES:
            w.workspace.delete(entry.path)
            removed.append(rel)

# Remove the folders the modules added: any folder that holds no starting file.
starting_dirs = set()
for f in STARTING_FILES:
    parts = f.split("/")[:-1]
    starting_dirs.update("/".join(parts[:n]) for n in range(1, len(parts) + 1))


def remove_added_folders(path):
    for entry in w.workspace.list(path):
        if entry.object_type.value != "DIRECTORY":
            continue
        rel = os.path.relpath(entry.path.removeprefix("/Workspace"), REPO_ROOT.removeprefix("/Workspace"))
        if rel in starting_dirs:
            remove_added_folders(entry.path)
        else:
            w.workspace.delete(entry.path, recursive=True)


for folder in CHECKED_FOLDERS:
    remove_added_folders(f"{REPO_ROOT}/{folder}")

for rel in sorted(removed):
    print(f"removed: {rel}")
print(f"\n{len(removed)} file(s) removed. The demo is back to the start of module 1.")
