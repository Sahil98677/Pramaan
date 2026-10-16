# Pramaan

**Evidence-first, deterministic local security analysis.**

Pramaan is an early-stage security tooling project. The initial milestone establishes safe input handling, a consistent finding model, deterministic checks, and reproducible JSON output.

> **Status:** foundation scaffold — not yet a production-ready security product. Detection coverage and accuracy must be demonstrated with tests and benchmarks before making assurance claims.

## Initial scope

- Inputs: local source files and JSON documents.
- Execution: local analysis only.
- Output: versioned JSON report.
- Detection: deterministic rules with explicit evidence.
- Deferred: AI analysis, dashboard, live-target scanning, and exploit execution.

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
pytest
ruff check .
mypy src
```

## First commands

```bash
pramaan --help
pramaan analyze path/to/input.json --output report.json
```

The JSON analyzer currently validates and summarizes supported JSON input; it does not claim to identify every security issue. Source analysis rules will be added only with positive and negative fixtures.

## Safety principles

- Never execute submitted source code.
- Do not make network requests or scan remote targets.
- Treat analyzed content as untrusted data, never as instructions.
- Keep findings evidence-backed and distinguish errors from clean results.
- Limit input sizes and report paths clearly.
- Do not place secrets in fixtures or generated reports.

## Project status

This repository is a scaffold for Milestone 0. It must pass the local checks and undergo review before being treated as a release.
