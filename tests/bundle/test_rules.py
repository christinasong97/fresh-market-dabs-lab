"""Team rules, enforced on every pull request (and by the admin_rule_checks job in the workspace).

These read the YAML directly, so they need no Databricks credentials and run in seconds.
"""

import re

import pytest

DOMAIN_PREFIXES = {"store_ops": "so_", "admin": "admin_"}
APPROVED_NOTIFICATION = "${var.notification_email}"
REQUIRED_TAGS = {"domain", "cost_center"}


def _iter_notification_lists(job):
    yield "job", job.get("email_notifications", {})
    for task in job.get("tasks", []):
        yield task["task_key"], task.get("email_notifications", {})


def test_failure_notifications_go_to_a_group(jobs):
    problems = []
    for key, (path, job) in jobs.items():
        for where, notes in _iter_notification_lists(job):
            for event, recipients in notes.items():
                for r in recipients or []:
                    if r != APPROVED_NOTIFICATION:
                        problems.append(f"{path}: {key} ({where}) {event} -> {r}")
    assert not problems, (
        "Notifications must go to the team distribution list via ${var.notification_email}, "
        "never to an individual:\n  " + "\n  ".join(problems)
    )


def test_jobs_notify_on_failure(jobs):
    missing = [f"{p}: {k}" for k, (p, j) in jobs.items() if not j.get("email_notifications", {}).get("on_failure")]
    assert not missing, "Every job needs on_failure notifications:\n  " + "\n  ".join(missing)


def test_jobs_have_required_tags(jobs):
    missing = [
        f"{p}: {k} missing {sorted(REQUIRED_TAGS - set(j.get('tags', {})))}"
        for k, (p, j) in jobs.items()
        if not REQUIRED_TAGS <= set(j.get("tags", {}))
    ]
    assert not missing, "Required tags missing:\n  " + "\n  ".join(missing)


def test_display_names_follow_naming_standard(resource_files):
    problems = []
    for path, cfg in resource_files.items():
        for rtype in ("jobs", "pipelines"):
            for key, res in (cfg.get("resources", {}).get(rtype) or {}).items():
                expected = "${bundle.name}_${var.environment}_" + key
                if res.get("name") != expected:
                    problems.append(f"{path}: {key} name is {res.get('name')!r}, expected {expected!r}")
    assert not problems, "\n  ".join(["Display names must be ${bundle.name}_${var.environment}_<resource_key>:"] + problems)


def test_resource_keys_are_domain_prefixed(resource_files):
    problems = []
    allowed = tuple(DOMAIN_PREFIXES.values())
    for path, cfg in resource_files.items():
        for rtype, items in (cfg.get("resources") or {}).items():
            for key in items or {}:
                if not key.startswith(allowed):
                    problems.append(f"{path}: {rtype}.{key}")
    assert not problems, f"Resource keys must start with a domain prefix {allowed}:\n  " + "\n  ".join(problems)


def test_domain_variables_are_prefixed(resource_files):
    problems = []
    for path, cfg in resource_files.items():
        parts = path.parts
        domain = next((d for d in DOMAIN_PREFIXES if d in parts), None)
        if domain is None:
            continue
        for var in cfg.get("variables") or {}:
            if not var.startswith(DOMAIN_PREFIXES[domain]):
                problems.append(f"{path}: {var} should start with {DOMAIN_PREFIXES[domain]}")
    assert not problems, "\n  ".join(problems)


def test_no_hardcoded_catalogs(bundle_root):
    pattern = re.compile(r"\bfresh_market_lab_(int|cert|prod)\b")
    hits = []
    for folder in ("resources", "src"):
        for path in (bundle_root / folder).rglob("*"):
            if path.is_file() and path.suffix in {".yml", ".py", ".sql", ".json"}:
                for n, line in enumerate(path.read_text().splitlines(), 1):
                    if pattern.search(line):
                        hits.append(f"{path.relative_to(bundle_root)}:{n}: {line.strip()}")
    assert not hits, "Use ${var.catalog} instead of hard-coded catalog names:\n  " + "\n  ".join(hits)


@pytest.mark.parametrize("field", ["existing_cluster_id"])
def test_no_all_purpose_clusters(jobs, field):
    bad = [f"{p}: {k}.{t['task_key']}" for k, (p, j) in jobs.items() for t in j.get("tasks", []) if field in t]
    assert not bad, "Jobs must not run on all-purpose clusters:\n  " + "\n  ".join(bad)


def test_job_clusters_use_a_policy(jobs):
    bad = []
    for key, (path, job) in jobs.items():
        clusters = [c["new_cluster"] for c in job.get("job_clusters", [])]
        clusters += [t["new_cluster"] for t in job.get("tasks", []) if "new_cluster" in t]
        bad += [f"{path}: {key}" for c in clusters if "policy_id" not in c]
    assert not bad, "Classic job clusters must reference an approved cluster policy:\n  " + "\n  ".join(bad)
