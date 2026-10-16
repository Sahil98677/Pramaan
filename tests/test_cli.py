"""Regression tests for the public command-line interface."""

import json
from pathlib import Path

from typer.testing import CliRunner

from pramaan.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "Pramaan 0.1.0"


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Usage:" in result.output
    assert "analyze" in result.output


def test_analyze_json_prints_versioned_report(tmp_path: Path) -> None:
    source = tmp_path / "safe.json"
    source.write_text('{"enabled": true}', encoding="utf-8")

    result = runner.invoke(app, ["analyze", str(source)])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["schema_version"] == "1.0"
    assert report["status"] == "completed"
    assert report["input_kind"] == "json"
    assert report["findings"] == []


def test_analyze_source_prints_report(tmp_path: Path) -> None:
    source = tmp_path / "safe.py"
    source.write_text("value = 42\n", encoding="utf-8")

    result = runner.invoke(app, ["analyze", str(source), "--kind", "source"])

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["status"] == "completed"
    assert report["input_kind"] == "source"


def test_invalid_json_returns_nonzero_and_failed_report(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text("{", encoding="utf-8")

    result = runner.invoke(app, ["analyze", str(source)])

    assert result.exit_code == 2
    report = json.loads(result.stdout)
    assert report["status"] == "failed"
    assert report["errors"]


def test_invalid_kind_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("data", encoding="utf-8")

    result = runner.invoke(app, ["analyze", str(source), "--kind", "unknown"])

    assert result.exit_code == 2
    assert "kind must be auto, json, or source" in result.output


def test_output_option_writes_parseable_report(tmp_path: Path) -> None:
    source = tmp_path / "safe.json"
    source.write_text('{"ok": true}', encoding="utf-8")
    destination = tmp_path / "reports" / "report.json"

    result = runner.invoke(
        app, ["analyze", str(source), "--output", str(destination)]
    )

    assert result.exit_code == 0
    assert destination.is_file()
    report = json.loads(destination.read_text(encoding="utf-8"))
    assert report["status"] == "completed"
    assert "Report written to" in result.stdout


def test_source_is_analyzed_without_executing_it(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-exist.txt"
    source = tmp_path / "input.py"
    source.write_text(
        "from pathlib import Path\n"
        + f"Path({str(marker)!r}).write_text('executed')\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["analyze", str(source), "--kind", "source"])

    assert result.exit_code == 0
    assert not marker.exists()
