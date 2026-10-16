# Architecture (initial scaffold)

```text
CLI
 ├── bounded local input loader
 ├── deterministic analysis entry points
 ├── shared Pydantic run/finding models
 └── versioned JSON report serializer
```

## Trust boundaries

- All analyzed files are untrusted data.
- Source is never imported, evaluated, or executed.
- No network access is performed by the analyzer.
- Inputs are limited to 2 MiB in the initial scaffold.
- Findings must include evidence; malformed input becomes an explicit failed run.
- The current JSON/source handlers are scaffolding and do not imply meaningful security detection coverage.
