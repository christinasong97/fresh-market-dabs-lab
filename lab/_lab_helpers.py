# Databricks notebook source
# MAGIC %md
# MAGIC # Lab helpers
# MAGIC Shared code for the module notebooks (`%run ./_lab_helpers`). You don't need to open or change this.

# COMMAND ----------

import base64
import os
import re
import time

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
ME = w.current_user.me().user_name
HOST = w.config.host.rstrip("/")
BUNDLE = "fresh_market_dabs_lab"
CATALOG = "fresh_market_lab_int"
REPO_ROOT = os.path.abspath("..")  # module notebooks live in <git folder>/lab/

RULES = {
    "test_failure_notifications_go_to_a_group": "Failure emails go to the team list (${var.notification_email}), not a person",
    "test_jobs_notify_on_failure": "Every job notifies someone on failure",
    "test_jobs_have_required_tags": "Every job has domain and cost_center tags",
    "test_display_names_follow_naming_standard": "Names follow ${bundle.name}_${var.environment}_<resource_key>",
    "test_resource_keys_are_domain_prefixed": "Resource keys start with a domain prefix (so_, admin_)",
    "test_domain_variables_are_prefixed": "Domain variables start with the domain prefix",
    "test_no_hardcoded_catalogs": "No hard-coded catalog names in resources/ or src/",
    "test_no_all_purpose_clusters": "Jobs don't run on all-purpose clusters",
    "test_job_clusters_use_a_policy": "Classic job clusters use an approved policy",
    "test_dev_is_development_mode": "dev target is development mode",
    "test_shared_targets_are_production_mode": "int, cert, prod are production mode",
    "test_shared_targets_run_as_service_principal": "int, cert, prod run as the CI/CD service principal",
    "test_shared_targets_restrict_permissions": "Only the service principal can manage shared targets",
    "test_each_target_uses_its_own_catalog": "Each target uses its own catalog",
}


def link(path, text):
    displayHTML(f'<a href="{HOST}{path}" target="_blank" style="font-size:15px">{text}</a>')


def dev_job(key):
    """Your deployed dev copy of a bundle job, or None if you haven't deployed it yet."""
    suffix = f"{BUNDLE}_dev_{key}"
    for job in w.jobs.list():
        name = job.settings.name if job.settings else ""
        if name.startswith("[dev ") and name.endswith(suffix) and job.creator_user_name == ME:
            return job
    return None


def dev_prefix():
    """Development mode prefixes everything you deploy with '[dev <you>] '."""
    job = dev_job("admin_rule_checks")
    return job.settings.name.split("]")[0] + "]" if job else None


def dev_schema():
    prefix = dev_prefix()
    short = prefix[len("[dev ") : -1] if prefix else re.sub(r"[^a-z0-9]", "_", ME.split("@")[0].lower())
    return f"dev_{short}_store_ops"


def run_job(key, quiet=False):
    """Run one of your dev jobs and wait. Returns the finished run."""
    job = dev_job(key)
    if job is None:
        print(f"❌ No dev copy of '{key}' yet. Deploy the bundle (Deployments panel → target dev → Deploy) first.")
        return None
    run_id = w.jobs.run_now(job.job_id).run_id
    if not quiet:
        link(f"/jobs/{job.job_id}/runs/{run_id}", f"▶ {job.settings.name} (open the run)")
    while True:
        run = w.jobs.get_run(run_id)
        state = run.state.life_cycle_state.value
        if state in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
            break
        time.sleep(10)
    result = run.state.result_state.value if run.state.result_state else state
    if not quiet:
        print(f"{'✅' if result == 'SUCCESS' else '❌'} {key}: {result}")
        for task in run.tasks or []:
            ts = task.state.result_state.value if task.state and task.state.result_state else task.state.life_cycle_state.value
            print(f"   - {task.task_key}: {ts}")
    return run if quiet else None


def rule_checks():
    """Run the same checks CI runs on every pull request, and explain the results."""
    print("Running admin_rule_checks (about 1 minute)...")
    run = run_job("admin_rule_checks", quiet=True)
    if run is None:
        return
    logs = w.jobs.get_run_output(run.tasks[0].run_id).logs or ""
    logs = re.sub(r"\x1b\[[0-9;]*m", "", logs)
    results = {}
    for test, result in re.findall(r"::(test_\w+)(?:\[[^\]]*\])? (PASSED|FAILED|SKIPPED)", logs):
        # Parameterized tests appear once per target; any failure counts as a failure.
        if results.get(test) != "FAILED":
            results[test] = result
    if not results:
        print("Couldn't read the results. Open the job run to see the output.")
        return
    failed = [t for t, r in results.items() if r == "FAILED"]
    for test, result in results.items():
        icon = {"PASSED": "✅", "FAILED": "❌", "SKIPPED": "⏭"}[result]
        print(f"{icon} {RULES.get(test, test)}")
    print()
    if failed:
        print(f"{len(failed)} rule(s) failed. Details:")
        for line in logs.splitlines():
            text = line[1:].strip()
            if line.startswith("E ") and text and not text.startswith(("assert ", "+", "-", "where")):
                print("   " + text.replace("AssertionError: ", ""))
    else:
        print("All rules pass. This change would clear CI.")


def _exists(rel):
    # In a Git folder, a .py file with a notebook header shows up as a notebook without the extension.
    path = os.path.join(REPO_ROOT, rel)
    return os.path.exists(path) or (rel.endswith(".py") and os.path.exists(path[:-3]))


def expect_files(paths):
    """Check that files exist in your Git folder."""
    ok = True
    for p in paths:
        exists = _exists(p)
        ok &= exists
        print(f"{'✅' if exists else '❌'} {p}")
    print("\nAll there." if ok else "\nSomething is missing. Check the step above, or use the Catch up cell at the end.")


def show_file(rel):
    """Print a file from your Git folder, or say it isn't there yet."""
    if not _exists(rel):
        print(f"❌ {rel} doesn't exist yet.")
        return
    print(f"--- {rel} ---")
    print(read_repo_file(rel))


def read_repo_file(rel):
    """Read a file from your Git folder, whether it's stored as a file or as a notebook."""
    path = os.path.join(REPO_ROOT, rel)
    if os.path.isfile(path):
        return open(path).read()
    return base64.b64decode(w.workspace.export(path[:-3] if path.endswith(".py") else path).content).decode()


def write_repo_file(rel, content):
    path = os.path.join(REPO_ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def remove_repo_file(rel):
    path = os.path.join(REPO_ROOT, rel)
    for p in (path, path[:-3] if path.endswith(".py") else None):
        if p and os.path.exists(p):
            os.remove(p) if os.path.isfile(p) else w.workspace.delete(p)


IMPORTED_FILES = ["resources/job_02_pl_store_kpi_alerts.job.yml", "src/Job_02_Store_KPI_Alerts.py"]


def catch_up(module):
    """Copy the finished files for a module into your Git folder, then redeploy to keep going."""
    root = os.path.join(REPO_ROOT, "lab", "solutions", f"module_{module:02d}").removeprefix("/Workspace")
    copied = []
    for entry in w.workspace.list(root, recursive=True):
        if entry.object_type.value == "DIRECTORY":
            continue
        rel = os.path.relpath(entry.path.removeprefix("/Workspace"), root)
        rel = rel + ".py" if entry.object_type.value == "NOTEBOOK" else rel
        content = base64.b64decode(w.workspace.export(entry.path).content).decode()
        write_repo_file(rel, content)
        copied.append(rel)
    if module >= 2:
        for rel in IMPORTED_FILES:
            remove_repo_file(rel)
    for rel in sorted(copied):
        print(f"✅ {rel}")
    print("\nCaught up. Now redeploy: Deployments panel → target dev → Deploy.")


VIOLATION_FILE = "resources/jobs/store_ops/so_weekly_department_report.job.yml"
VIOLATION_YAML = """# A teammate's new job: weekly department sales for merchandising.
resources:
  jobs:
    so_weekly_department_report:
      name: ${bundle.name}_${var.environment}_so_weekly_department_report
      description: Week-over-week net sales by department.
      tags:
        domain: store_ops
        cost_center: ${var.cost_center}
      email_notifications:
        on_failure:
          - jane.doe@example.com
      tasks:
        - task_key: publish_department_report
          notebook_task:
            notebook_path: ../../../src/store_ops/notebooks/store_kpis/notify_store_ops.py
            base_parameters:
              catalog: ${var.catalog}
              schema: ${resources.schemas.so_store_ops.name}
"""


def add_teammates_change():
    write_repo_file(VIOLATION_FILE, VIOLATION_YAML)
    print(f"✅ Added {VIOLATION_FILE}\n")
    print(VIOLATION_YAML)


def fix_teammates_change():
    content = read_repo_file(VIOLATION_FILE).replace("- jane.doe@example.com", "- ${var.notification_email}")
    write_repo_file(VIOLATION_FILE, content)
    print("✅ Failure emails now go to ${var.notification_email}")


def _list_all(path, key):
    # Plain REST calls, so this works whatever SDK version the notebook has.
    items, token = [], None
    while True:
        query = {"page_size": 100, **({"page_token": token} if token else {})}
        page = w.api_client.do("GET", path, query=query)
        items += page.get(key, [])
        token = page.get("next_page_token")
        if not token:
            return items


def find_dev_dashboard():
    """Your deployed dev dashboard as {"id", "name"}, or None."""
    prefix = dev_prefix() or "[dev"
    for d in _list_all("/api/2.0/lakeview/dashboards", "dashboards"):
        name = d.get("display_name", "")
        if name.startswith(prefix) and "Store Performance" in name:
            return {"id": d["dashboard_id"], "name": name}
    return None


def find_dev_genie_space():
    """Your deployed dev Genie space as {"id", "name"}, or None."""
    prefix = dev_prefix() or "[dev"
    for s in _list_all("/api/2.0/genie/spaces", "spaces"):
        title = s.get("title", "")
        if title.startswith(prefix) and "Store Ops Genie" in title:
            return {"id": s["space_id"], "name": title}
    return None


def ask_genie(question):
    """Ask your dev Genie space a question and print the SQL it wrote and its answer."""
    space = find_dev_genie_space()
    if space is None:
        print("❌ No dev Genie space yet. Run the cell in 4.3, then deploy again.")
        return
    base = f"/api/2.0/genie/spaces/{space['id']}"
    started = w.api_client.do("POST", f"{base}/start-conversation", body={"content": question})
    path = f"{base}/conversations/{started['conversation_id']}/messages/{started['message_id']}"
    for _ in range(60):
        msg = w.api_client.do("GET", path)
        if msg.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(3)
    if msg.get("status") != "COMPLETED":
        print(f"❌ Genie didn't finish ({msg.get('status')}). Try asking in the Genie space itself.")
        return
    for att in msg.get("attachments") or []:
        if att.get("query"):
            print("SQL Genie wrote:\n  " + att["query"]["query"].replace("\n", "\n  "))
        if att.get("text"):
            print("\n" + att["text"]["content"])


print(f"Helpers loaded for {ME}")
