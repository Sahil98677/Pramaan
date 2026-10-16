# Pramaan

**Evidence-first, deterministic local security analysis.**

Pramaan is an early-stage security analysis project. It parses local files as data, applies deterministic heuristics, and emits structured JSON findings with locations and remediation guidance.

> **Status:** early prototype. Rules are heuristic signals, not proof of exploitability or proof that a clean scan is secure. Detection accuracy and coverage must be measured before making assurance claims.

## Current scope

- **Inputs:** local Python (`.py`) source files and JSON documents.
- **Execution:** local analysis only. Source code is parsed using Python's AST and is never imported or executed. JSON input is size-bounded and rejects duplicate object keys and non-standard numeric constants.
- **Output:** versioned JSON report with run status, stable rule IDs, severity, confidence, evidence, and remediation.
- **Current checks:** direct `eval()` / `exec()` calls; recognized `subprocess` calls with `shell=True`; credential-like string assignments in Python; credential-like string values and enabled debug flags in JSON.
- **Limitations:** no data-flow analysis, alias/import resolution, framework-specific analysis, dependency scanning, network scanning, or exploit execution. The rules may produce false positives and false negatives.
- **Deferred:** AI analysis, dashboard, live-target scanning, and exploit execution.

## Requirements

- Python 3.11+
- pip

## Development setup

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

python -m pip install -e ".[dev]"
pytest --cov=pramaan --cov-report=term-missing
ruff check .
mypy src
```

## Usage

```bash
pramaan --help
pramaan analyze fixtures/source/vulnerable_patterns.py --output report.json
pramaan analyze fixtures/json/vulnerable_config.json --output json-report.json
```

For any valid input, exit status 0 means analysis completed, not that the input is secure. An invalid or unsupported input produces a failed run and CLI exit status 2. Inspect the report's `findings` and `errors` fields separately.

## Safety and privacy

- Analyzed content is untrusted data, never instructions.
- The analyzer makes no network requests and never executes source code.
- Input files are limited to 2 MiB.
- Credential-like literals are redacted from finding evidence; synthetic fixture values are not real credentials.
- Use only on files you are authorized to assess.

## Project status

This is an initial deterministic rule set. Each rule should be expanded only with positive and negative fixtures, documented limitations, and regression coverage. A successful test suite does not by itself establish security detection accuracy.
