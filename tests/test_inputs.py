import json
from pathlib import Path

import pytest

from pramaan.inputs import InputError, load_json, read_bounded_text


def test_load_json_object(tmp_path: Path) -> None:
    path = tmp_path / "sample.json"
    path.write_text('{"ok": true}', encoding="utf-8")
    assert load_json(path) == {"ok": True}


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"broken": ', encoding="utf-8")
    with pytest.raises(InputError, match="Invalid JSON"):
        load_json(path)


def test_directory_is_not_accepted(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="regular file"):
        read_bounded_text(tmp_path)


def test_json_fixture_round_trip(tmp_path: Path) -> None:
    data = {"items": [1, 2, 3], "safe": True}
    path = tmp_path / "data.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_json(path) == data


def test_excessively_nested_json_is_rejected_safely(tmp_path: Path) -> None:
    path = tmp_path / "deep.json"
    path.write_text("[" * 10000 + "0" + "]" * 10000, encoding="utf-8")
    with pytest.raises(InputError, match="nesting is too deep"):
        load_json(path)
