"""Deterministic analysis entry points."""

from pathlib import Path
from typing import Any
from uuid import uuid4

from .inputs import InputError, load_json, read_bounded_text
from .models import RunReport, RunStatus


def analyze_json(path: Path) -> RunReport:
    """Validate JSON and return a report. No security coverage is implied yet."""
    try:
        value: Any = load_json(path)
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

    return RunReport(
        run_id=str(uuid4()),
        status=RunStatus.COMPLETED,
        input_kind="json",
        input_label=path.name,
        metadata={"json_shape": shape},
    )


def analyze_source(path: Path) -> RunReport:
    """Read source as data only; actual source rules will arrive with fixtures."""
    try:
        text = read_bounded_text(path)
    except InputError as exc:
        return RunReport(
            run_id=str(uuid4()),
            status=RunStatus.FAILED,
            input_kind="source",
            input_label=path.name,
            errors=[str(exc)],
        )

    return RunReport(
        run_id=str(uuid4()),
        status=RunStatus.COMPLETED,
        input_kind="source",
        input_label=path.name,
        metadata={
            "line_count": len(text.splitlines()),
            "bytes_read": len(text.encode("utf-8")),
            "analysis_note": "Source was read as data; no code was executed.",
        },
    )
