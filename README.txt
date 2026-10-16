Pramaan tuple-assignment secret detection patch

From the Pramaan repository root, extract this ZIP, then run:
    python apply_patch.py

The script checks expected source blocks before changing either file. If the repository differs from the expected baseline, it stops without writing changes.

Then run:
    pytest
    ruff check .
    mypy src

Review the diff before committing. This is a targeted heuristic, not complete secret detection.
