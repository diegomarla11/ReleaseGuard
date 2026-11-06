import pytest
from scripts.policy import REQUIRED, assert_scenario, decide, evaluate_scan


def checks(**overrides):
    return {key: {"status": overrides.get(key, "pass")} for key in REQUIRED}


@pytest.mark.parametrize("status", ["not_run", "error", "unknown"])
def test_unavailable_scanner_never_approves(status):
    assert decide(checks(scan=status)) == "incomplete"


def test_missing_control_never_approves():
    assert decide({}) == "incomplete"


def test_exact_expected_failure_is_successful_lab_but_blocked_app():
    observed = checks(health="fail")
    assert decide(observed) == "blocked"
    assert assert_scenario(observed, "health")["status"] == "pass"


@pytest.mark.parametrize("observed", [checks(), checks(health="fail", nonroot="fail"), checks(health="fail", scan="error")])
def test_expected_failure_does_not_hide_other_errors(observed):
    assert assert_scenario(observed, "health")["status"] == "fail"


def scan(vulns):
    return {"SchemaVersion": 2, "ArtifactType": "container_image", "Results": [{"Class": "os-pkgs", "Vulnerabilities": vulns}]}


@pytest.mark.parametrize("severity", ["HIGH", "CRITICAL"])
def test_unfixed_severe_findings_block(severity):
    # Synthetic unit fixture, never exported as a scan or a CVE.
    result = evaluate_scan(scan([{"Severity": severity, "FixedVersion": ""}]))
    assert result["status"] == "fail"
    assert result["counts"][severity] == 1


def test_lower_severities_are_visible_without_blocking():
    result = evaluate_scan(scan([{"Severity": "MEDIUM"}, {"Severity": "UNKNOWN"}]))
    assert result["status"] == "pass"
    assert result["counts"]["UNKNOWN"] == 1


@pytest.mark.parametrize("document", [{}, {"SchemaVersion": 2, "ArtifactType": "container_image", "Results": []},
                                          {"SchemaVersion": 2, "ArtifactType": "filesystem", "Results": [{"Class": "os-pkgs"}]}])
def test_invalid_scan_is_never_clean(document):
    with pytest.raises(ValueError):
        evaluate_scan(document)


def test_all_controls_pass():
    assert decide(checks()) == "approved"
