# Rule-quality evaluation

Pramaan's current rules are deterministic heuristics. This curated smoke corpus checks whether representative examples continue to match their expected outcomes; it is not evidence of production detection rates.

## Run

```bash
python -m pip install -e ".[dev]"
pytest -q
python scripts/evaluate_rules.py
```

## Current curated corpus

The script includes six Python cases and four JSON cases covering direct `eval`/`exec`, recognized `subprocess` calls with `shell=True`, credential-like literals, comments/string literals, `shell=False`, placeholders, and debug flags.

The script reports TP, FP, FN, TN, precision, recall, and accuracy. These numbers describe only this small hand-authored corpus. Do not present them as real-world accuracy or generalize them to arbitrary repositories.

## Known limitations to address next

- `eval`/`exec` may be legitimate when input is trusted; current rule reports the pattern without proving taint or attacker control.
- `shell=True` is a risk indicator, not proof that the command is injectable.
- Credential-name heuristics can miss secrets under unfamiliar names and can flag non-secret values.
- Debug configuration varies by framework and deployment environment.
- The benchmark is intentionally small and synthetic; future evaluation needs a larger, reviewed corpus with documented labels and regression review.
