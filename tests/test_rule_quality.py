"""Rule-quality regression tests: expected positives and deliberate negatives."""

import pytest

from pramaan.models import Severity
from pramaan.rules import analyze_json_value, analyze_python_source


@pytest.mark.parametrize(
    ("source", "expected_rule"),
    [
        ("value = eval(user_input)\n", "PRM-PY-DYN-001"),
        ("exec(untrusted_text)\n", "PRM-PY-DYN-001"),
        (
            "import subprocess\nsubprocess.run(command, shell=True)\n",
            "PRM-PY-SHELL-001",
        ),
        (
            "import subprocess\nsubprocess.Popen(command, shell=True)\n",
            "PRM-PY-SHELL-001",
        ),
        ('API_KEY = "synthetic_non_placeholder_key_12345"\n', "PRM-PY-SECRET-001"),
        ('client_secret = "synthetic_client_secret_12345"\n', "PRM-PY-SECRET-001"),
    ],
)
def test_rule_quality_expected_python_positives(source: str, expected_rule: str) -> None:
    findings = analyze_python_source(source, filename="quality_case.py")
    assert expected_rule in {finding.rule_id for finding in findings}


@pytest.mark.parametrize(
    "source",
    [
        "# eval(user_input) in a comment\n",
        'message = "exec(user_input)"\n',
        "import subprocess\nsubprocess.run(command, shell=False)\n",
        "import subprocess\nsubprocess.run(command, check=True)\n",
        'API_KEY = "${SERVICE_API_KEY}"\n',
        'PASSWORD = "replace_me"\n',
        'password = "your_password"\n',
    ],
)
def test_rule_quality_expected_python_negatives(source: str) -> None:
    assert analyze_python_source(source, filename="negative_case.py") == []


@pytest.mark.parametrize(
    ("value", "expected_rule"),
    [
        ({"auth": {"api_key": "synthetic_key_material_12345"}}, "PRM-JSON-SECRET-001"),
        ({"debug": True}, "PRM-JSON-DEBUG-001"),
        (
            [{"credentials": {"client_secret": "synthetic_secret_material_12345"}}],
            "PRM-JSON-SECRET-001",
        ),
    ],
)
def test_rule_quality_expected_json_positives(value: object, expected_rule: str) -> None:
    findings = analyze_json_value(value, filename="quality_case.json")
    assert expected_rule in {finding.rule_id for finding in findings}


@pytest.mark.parametrize(
    "value",
    [
        {"debug": False},
        {"api_key": "${SERVICE_API_KEY}"},
        {"nested": [{"password": "replace_me"}]},
        {"message": "debug=true is only documentation"},
        {"debug": "true"},
    ],
)
def test_rule_quality_expected_json_negatives(value: object) -> None:
    assert analyze_json_value(value, filename="negative_case.json") == []


def test_findings_have_evidence_and_bounded_confidence() -> None:
    findings = analyze_python_source('API_KEY = "synthetic_key_material_12345"\n', filename="x.py")
    assert findings
    for finding in findings:
        assert finding.evidence
        assert 0.0 <= finding.confidence <= 1.0
        assert finding.rule_id
        assert finding.severity in {
            Severity.INFO,
            Severity.LOW,
            Severity.MEDIUM,
            Severity.HIGH,
            Severity.CRITICAL,
        }
