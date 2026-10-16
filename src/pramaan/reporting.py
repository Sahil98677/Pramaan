"""Report serialization and safe output writes."""

import json
import os
import tempfile
from pathlib import Path

from .models import RunReport


def report_json(report: RunReport) -> str:
    return json.dumps(
        report.model_dump(mode="json"),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def write_report(report: RunReport, output: Path) -> None:
    """Write via a temporary file and atomic replace in the destination directory."""
    destination = output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(report_json(report))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    finally:
        if temp_name is not None:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
