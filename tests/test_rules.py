import json

from pramaan.models import Severity
from pramaan.rules import analyze_json_value, analyze_python_source


def test_python_detects_eval_and_exec_without_executing_source() -> None:
    source = "result = eval(expression)\nexec(statement)\n"
    findings = analyze_python_source(source, filename="demo.py")
    assert [finding.rule_id for finding in findings] == [
        "PRM-PY-DYN-001",
        "PRM-PY-DYN-001",
    ]
    assert all(finding.severity is Severity.HIGH for finding in findings)
    assert findings[0].evidence[0].location == "demo.py:1"


def test_python_detects_shell_true_but_not_shell_false() -> None:
    findings = analyze_python_source(
        "import subprocess\n"
        "subprocess.run(command, shell=True)\n"
        "subprocess.run([program, argument], shell=False)\n",
        filename="commands.py",
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "PRM-PY-SHELL-001"
    assert findings[0].evidence[0].location == "commands.py:2"


def test_python_detects_credential_like_assignment_and_redacts_value() -> None:
    synthetic_secret = "NOT_A_REAL_SECRET_demo_1287"
    findings = analyze_python_source(
        f'API_KEY = "{synthetic_secret}"\nPASSWORD = "replace_me"\n',
        filename="config.py",
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "PRM-PY-SECRET-001"
    assert findings[0].evidence[0].location == "config.py:1"
    assert synthetic_secret not in json.dumps(findings[0].model_dump(mode="json"))
    assert "redacted" in findings[0].evidence[0].excerpt.lower()


def test_python_ignores_comments_and_string_contents() -> None:
    findings = analyze_python_source(
        '# eval(user_input)\n'
        'message = "exec(untrusted_code)"\n'
        'PASSWORD = "your_password"\n',
        filename="safe.py",
    )
    assert findings == []


def test_json_detects_nested_credential_and_debug_flag_without_secret_value() -> None:
    synthetic_secret = "NOT_A_REAL_SECRET_demo_56321"
    findings = analyze_json_value(
        {
            "auth": {"api_key": synthetic_secret},
            "debug": True,
        },
        filename="settings.json",
    )
    assert {finding.rule_id for finding in findings} == {
        "PRM-JSON-SECRET-001",
        "PRM-JSON-DEBUG-001",
    }
    serialized = json.dumps([finding.model_dump(mode="json") for finding in findings])
    assert synthetic_secret not in serialized
    assert "/auth/api_key" in serialized


def test_json_ignores_placeholder_credentials_and_disabled_debug() -> None:
    findings = analyze_json_value(
        {"api_key": "${API_KEY}", "debug": False, "nested": [{"password": "replace_me"}]},
        filename="safe.json",
    )
    assert findings == []


def test_json_escapes_json_pointer_segments() -> None:
    findings = analyze_json_value({"auth/token": "fake-token-value-long"}, filename="x.json")
    assert len(findings) == 1
    assert "/auth~1token" in findings[0].evidence[0].location
