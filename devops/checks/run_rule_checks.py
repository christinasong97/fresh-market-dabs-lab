"""Run the same bundle rule checks CI runs on every pull request, from inside the workspace.

Usage (job task): run_rule_checks.py <bundle_root>
"""

import sys

# Workspace files do not allow __pycache__ folders, so never write bytecode.
sys.dont_write_bytecode = True

import pytest  # noqa: E402

bundle_root = sys.argv[1] if len(sys.argv) > 1 else "."
exit_code = pytest.main(
    [f"{bundle_root}/tests/bundle", "-v", "-o", "addopts=", "-p", "no:cacheprovider", f"--rootdir={bundle_root}"]
)
if exit_code != 0:
    raise SystemExit(f"Rule checks failed (pytest exit code {exit_code}). Fix the findings above before opening a pull request.")
