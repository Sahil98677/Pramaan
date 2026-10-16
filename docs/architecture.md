# Architecture

```text
CLI
 ├── bounded local input loader (2 MiB maximum)
 ├── JSON parser or Python AST parser (no source execution)
 ├── deterministic rule functions
 ├── shared Pydantic run/finding/evidence models
 └── versioned JSON report serializer with atomic output writes
```

## Initial rule inventory

| Rule ID | Input | Signal | Severity |
|---|---|---|---|
| `PRM-PY-DYN-001` | Python | Direct built-in `eval()` / `exec()` call | High |
| `PRM-PY-SHELL-001` | Python | Recognized `subprocess` API with `shell=True` | High |
| `PRM-PY-SECRET-001` | Python | Credential-like variable assigned a non-placeholder string literal | High |
| `PRM-JSON-SECRET-001` | JSON | Credential-like key holding a non-placeholder string literal | High |
| `PRM-JSON-DEBUG-001` | JSON | Debug-related key is boolean `true` | Medium |

These rules are heuristic. The Python rules do not resolve aliases or track user-controlled data flow. A matching pattern is not proof of exploitability, and no finding is not proof of safety.

## Trust boundaries

- All analyzed files are untrusted data.
- Python AST parsing does not import or execute the analyzed source.
- JSON is parsed without evaluating embedded strings.
- Inputs are limited to 2 MiB in the initial implementation.
- Evidence intentionally omits credential literal values.
- Invalid syntax, malformed JSON, and unsupported source types produce explicit failed runs rather than a clean result.
