"""Target guardrails: shared environments are production mode and run as the CI/CD service principal."""

import pytest

SHARED_TARGETS = ["int", "cert", "prod"]


def test_dev_is_development_mode(root_config):
    if "dev" not in root_config["targets"]:
        pytest.skip("No dev target yet (added in module 4)")
    assert root_config["targets"]["dev"]["mode"] == "development"


@pytest.mark.parametrize("target", SHARED_TARGETS)
def test_shared_targets_are_production_mode(root_config, target):
    assert root_config["targets"][target]["mode"] == "production"


@pytest.mark.parametrize("target", SHARED_TARGETS)
def test_shared_targets_run_as_service_principal(root_config, target):
    run_as = root_config["targets"][target].get("run_as", {})
    assert run_as.get("service_principal_name") == "${var.cicd_service_principal}"


@pytest.mark.parametrize("target", SHARED_TARGETS)
def test_shared_targets_restrict_permissions(root_config, target):
    levels = {
        (p["level"], p.get("group_name") or p.get("service_principal_name"))
        for p in root_config["targets"][target].get("permissions", [])
    }
    assert ("CAN_MANAGE", "${var.cicd_service_principal}") in levels
    assert all(level != "CAN_MANAGE" for level, who in levels if who == "users")


@pytest.mark.parametrize(
    "target,catalog", [("int", "fresh_market_lab_int"), ("cert", "fresh_market_lab_cert"), ("prod", "fresh_market_lab_prod")]
)
def test_each_target_uses_its_own_catalog(root_config, target, catalog):
    assert root_config["targets"][target]["variables"]["catalog"] == catalog
