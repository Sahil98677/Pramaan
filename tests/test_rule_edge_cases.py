"""Additional edge-case regressions for Pramaan's deterministic rules."""

import pytest

from pramaan.rules import analyze_json_value, analyze_python_source


@pytest.mark.parametrize(
    ("source", "expected_rule"),
    [
        (
            "import subprocess\nsubprocess.call(command, shell=True)\n",
            "PRM-PY-SHELL-001",
        ),
        (
            "import subprocess\nsubprocess.check_output(command, shell=True)\n",
            "PRM-PY-SHELL-001",
        ),
        (
            'api_key: str = "synthetic_key_material_12345"\n',
            "PRM-PY-SECRET-001",
        ),
    ],
)
def test_python_edge_cases_detect_expected_patterns(
    source: str, expected_rule: str
) -> None:
    findings = analyze_python_source(source, filename="edge_case.py")
    assert expected_rule in {finding.rule_id for finding in findings}


@pytest.mark.parametrize(
    "source",
    [
        "obj.eval(user_input)\n",
        "obj.exec(user_input)\n",
        "import subprocess\nsubprocess.run(command, shell=bool_value)\n",
        "import subprocess\nsubprocess.run(command, shell=False)\n",
        'API_KEY = "${SERVICE_API_KEY}"\n',
        'client_secret = "replace-me"\n',
    ],
)
def test_python_edge_cases_do_not_flag_nonmatching_patterns(source: str) -> None:
    assert analyze_python_source(source, filename="negative_edge.py") == []


def test_json_finds_multiple_nested_credentials_and_debug_flags() -> None:
    value = {
        "services": [
            {"api_key": "synthetic_key_one_12345"},
            {"client_secret": "synthetic_secret_two_12345"},
        ],
        "debug_mode": True,
    }

    findings = analyze_json_value(value, filename="settings.json")
    rule_ids = [finding.rule_id for finding in findings]

    assert rule_ids.count("PRM-JSON-SECRET-001") == 2
    assert rule_ids.count("PRM-JSON-DEBUG-001") == 1
    assert all(finding.evidence for finding in findings)


def test_json_pointer_escapes_slashes_and_tildes() -> None:
    findings = analyze_json_value(
        {"auth/config~old": {"api_key": "synthetic_key_material_12345"}},
        filename="config.json",
    )

    assert len(findings) == 1
    assert "/auth~1config~0old/api_key" in (findings[0].evidence[0].location or "")


@pytest.mark.parametrize(
    "value",
    [
        {"debug_mode": 1},
        {"debug_enabled": "true"},
        {"service": {"api_key": None}},
        {"service": {"api_key": "${SERVICE_API_KEY}"}},
        {"message": "api_key=example is documentation"},
    ],
)
def test_json_edge_cases_do_not_flag_nonmatching_values(value: object) -> None:
    assert analyze_json_value(value, filename="negative_edge.json") == []


def test_credential_values_never_appear_in_json_finding_evidence() -> None:
    sentinel = "SYNTHETIC_SECRET_SENTINEL_7f41"
    findings = analyze_json_value({"api_key": sentinel}, filename="secret.json")

    assert len(findings) == 1
    finding = findings[0]
    rendered = " ".join(
        [
            finding.description,
            finding.evidence[0].excerpt or "",
            finding.evidence[0].location or "",
        ]
    )
    assert sentinel not in rendered
    assert "redacted" in rendered.lower()
