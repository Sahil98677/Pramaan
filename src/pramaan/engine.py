"""Deterministic analysis entry points."""

from pathlib import Path
from uuid import uuid4

from .inputs import InputError, load_json, read_bounded_text
from .models import RunReport, RunStatus
from .rules import analyze_json_value, analyze_python_source


def analyze_json(path: Path) -> RunReport:
    """Validate JSON and apply deterministic configuration heuristics."""
    try:
        value = load_json(path)
    except InputError as exc:
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="json",
            input_label=path.name,
            errors=[str(exc)],
        )

    if isinstance(value, dict):
        shape = f"object with {len(value)} top-level keys"
    elif isinstance(value, list):
        shape = f"array with {len(value)} items"
    else:
        shape = f"JSON scalar of type {type(value).__name__}"

    try:
        findings = analyze_json_value(value, filename=path.name)
    except RecursionError:
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="json",
            input_label=path.name,
            errors=["JSON nesting is too deep to analyze safely."],
        )
    return RunReport(
        run_id=str(uuid4()),
        status=RunStatus.COMPLETED,
        input_kind="json",
        input_label=path.name,
        findings=findings,
        metadata={
            "json_shape": shape,
            "rules_applied": ["PRM-JSON-SECRET-001", "PRM-JSON-DEBUG-001"],
        },
    )


def analyze_source(path: Path) -> RunReport:
    """Analyze a Python file without importing or executing it."""
    if path.suffix.lower() != ".py":
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="source",
            input_label=path.name,
            errors=["Source analysis currently supports Python (.py) files only."],
        )

    try:
        source = read_bounded_text(path)
        findings = analyze_python_source(source, filename=path.name)
    except InputError as exc:
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="source",
            input_label=path.name,
            errors=[str(exc)],
        )
    except SyntaxError as exc:
        location = f"line {exc.lineno}, column {exc.offset}" if exc.lineno else "unknown location"
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="source",
            input_label=path.name,
            errors=[f"Invalid Python syntax at {location}: {exc.msg}"],
        )
    except (ValueError, RecursionError) as exc:
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="source",
            input_label=path.name,
            errors=[f"Python source could not be analyzed safely: {type(exc).__name__}"],
        )

    return RunReport(
        run_id=str(uuid4()),
        status=RunStatus.COMPLETED,
        input_kind="source",
        input_label=path.name,
        findings=findings,
        metadata={
            "line_count": len(source.splitlines()),
            "bytes_read": len(source.encode("utf-8")),
            "analysis_note": "Parsed with Python AST; source was never executed.",
            "rules_applied": [
                "PRM-PY-DYN-001",
                "PRM-PY-SHELL-001",
                "PRM-PY-SECRET-001",
            ],
        },
    )
