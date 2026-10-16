"""Run a small deterministic precision/recall smoke benchmark for Pramaan rules.

This is a curated regression corpus, not a representative security benchmark.
Run from the repository root after installing the dev extras:
    python scripts/evaluate_rules.py
"""

from __future__ import annotations

from dataclasses import dataclass

from pramaan.rules import analyze_json_value, analyze_python_source


@dataclass(frozen=True)
class Case:
    name: str
    expected: bool
    detected: bool


def main() -> int:
    cases: list[Case] = []

    python_cases = [
        ("python_eval", "result = eval(user_input)\n", "PRM-PY-DYN-001", True),
        ("python_shell_true", "import subprocess\nsubprocess.run(cmd, shell=True)\n", "PRM-PY-SHELL-001", True),
        ("python_secret", 'API_KEY = "synthetic_key_material_12345"\n', "PRM-PY-SECRET-001", True),
        ("python_comment_only", "# eval(user_input)\n", "PRM-PY-DYN-001", False),
        ("python_shell_false", "import subprocess\nsubprocess.run(cmd, shell=False)\n", "PRM-PY-SHELL-001", False),
        ("python_placeholder", 'API_KEY = "${SERVICE_API_KEY}"\n', "PRM-PY-SECRET-001", False),
    ]
    for name, source, rule_id, expected in python_cases:
        detected = any(
            finding.rule_id == rule_id
            for finding in analyze_python_source(source, filename=f"{name}.py")
        )
        cases.append(Case(name, expected, detected))

    json_cases = [
        ("json_secret", {"api_key": "synthetic_key_material_12345"}, "PRM-JSON-SECRET-001", True),
        ("json_debug_true", {"debug": True}, "PRM-JSON-DEBUG-001", True),
        ("json_placeholder", {"api_key": "${SERVICE_API_KEY}"}, "PRM-JSON-SECRET-001", False),
        ("json_debug_false", {"debug": False}, "PRM-JSON-DEBUG-001", False),
    ]
    for name, value, rule_id, expected in json_cases:
        detected = any(
            finding.rule_id == rule_id
            for finding in analyze_json_value(value, filename=f"{name}.json")
        )
        cases.append(Case(name, expected, detected))

    true_positive = sum(c.expected and c.detected for c in cases)
    false_negative = sum(c.expected and not c.detected for c in cases)
    false_positive = sum(not c.expected and c.detected for c in cases)
    true_negative = sum(not c.expected and not c.detected for c in cases)
    total = len(cases)
    accuracy = (true_positive + true_negative) / total if total else 0.0
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 0.0
    recall = true_positive / recall_denominator if recall_denominator else 0.0

    print(f"Cases: {total}")
    print(f"TP={true_positive} FP={false_positive} FN={false_negative} TN={true_negative}")
    print(f"Precision={precision:.3f} Recall={recall:.3f} Accuracy={accuracy:.3f}")
    failed = [c for c in cases if c.expected != c.detected]
    if failed:
        print("Mismatches:")
        for case in failed:
            print(f"  {case.name}: expected_detected={case.expected}, detected={case.detected}")
        return 1
    print("All curated smoke cases matched their expected outcomes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
