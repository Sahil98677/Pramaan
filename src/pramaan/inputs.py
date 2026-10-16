"""Bounded local input loading. No code execution and no network access."""

import json
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 2 * 1024 * 1024


class InputError(ValueError):
    """Raised when local input cannot be safely loaded."""


class _DuplicateJSONKeyError(ValueError):
    """Raised when a JSON object contains an ambiguous duplicate key."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            # Do not echo the key: it may itself contain sensitive data.
            raise _DuplicateJSONKeyError
        result[key] = value
    return result


def _reject_nonstandard_constant(value: str) -> None:
    # Python's JSON parser otherwise accepts NaN and Infinity extensions.
    raise ValueError(f"Non-standard JSON constant {value} is not allowed.")


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
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonstandard_constant,
        )
    except _DuplicateJSONKeyError as exc:
        raise InputError(
            "JSON contains duplicate object keys, which are ambiguous and unsafe to analyze."
        ) from exc
    except json.JSONDecodeError as exc:
        raise InputError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except RecursionError as exc:
        raise InputError("JSON nesting is too deep to parse safely.") from exc
    except ValueError as exc:
        raise InputError("JSON contains a non-standard numeric constant.") from exc
