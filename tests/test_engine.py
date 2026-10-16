from pathlib import Path

from pramaan.engine import analyze_json, analyze_source
from pramaan.models import RunStatus
from pramaan.reporting import report_json, write_report


def test_json_analysis_completes_for_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "valid.json"
    path.write_text('{"enabled": false, "api_key": "your_api_key"}', encoding="utf-8")
    report = analyze_json(path)
    assert report.status is RunStatus.COMPLETED
    assert report.input_kind == "json"
    assert report.findings == []


def test_json_analysis_fails_for_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    report = analyze_json(path)
    assert report.status is RunStatus.FAILED
    assert report.errors


def test_source_is_not_executed_and_is_analyzed(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text('print("data only")\n', encoding="utf-8")
    report = analyze_source(path)
    assert report.status is RunStatus.COMPLETED
    assert "never executed" in report.metadata["analysis_note"]
    assert report.findings == []


def test_invalid_python_syntax_is_a_failed_run(tmp_path: Path) -> None:
    path = tmp_path / "invalid.py"
    path.write_text("def missing_colon()\n    pass\n", encoding="utf-8")
    report = analyze_source(path)
    assert report.status is RunStatus.FAILED
    assert "Invalid Python syntax" in report.errors[0]


def test_unsupported_source_extension_is_a_failed_run(tmp_path: Path) -> None:
    path = tmp_path / "sample.js"
    path.write_text("const safe = true;", encoding="utf-8")
    report = analyze_source(path)
    assert report.status is RunStatus.FAILED
    assert "Python (.py)" in report.errors[0]


def test_report_serializes_and_writes_atomically(tmp_path: Path) -> None:
    source = tmp_path / "data.json"
    source.write_text("[]", encoding="utf-8")
    report = analyze_json(source)
    serialized = report_json(report)
    assert '"schema_version": "1.0"' in serialized
    output = tmp_path / "reports" / "report.json"
    write_report(report, output)
    assert output.exists()
    assert '"status": "completed"' in output.read_text(encoding="utf-8")


def test_excessively_nested_json_returns_failed_run(tmp_path: Path) -> None:
    path = tmp_path / "deep.json"
    path.write_text("[" * 1500 + "0" + "]" * 1500, encoding="utf-8")
    report = analyze_json(path)
    assert report.status is RunStatus.FAILED
    assert report.errors
