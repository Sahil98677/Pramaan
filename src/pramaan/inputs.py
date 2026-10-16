"""Bounded local input loading. No code execution and no network access."""

import json
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 2 * 1024 * 1024


class InputError(ValueError):
    """Raised when local input cannot be safely loaded."""


def read_bounded_text(path: Path) -> str:
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_file():
            raise InputError("Input path must refer to a regular file.")
        size = resolved.stat().st_size
        if size > MAX_INPUT_BYTES:
            raise InputError(f"Input exceeds the {MAX_INPUT_BYTES}-byte limit.")
        return resolved.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Input must be valid UTF-8 text.") from exc
    except OSError as exc:
        raise InputError(f"Unable to read input: {exc}") from exc


def load_json(path: Path) -> Any:
    text = read_bounded_text(path)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
