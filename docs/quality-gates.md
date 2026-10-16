# Quality gates

Before a milestone is accepted:

1. Unit tests cover positive detections, negative fixtures, malformed input, and boundaries.
2. Findings have stable rule IDs, bounded confidence, evidence locations, and remediation.
3. Credential-like values are redacted from report evidence.
4. Invalid input produces an explicit failed run rather than a clean scan result.
5. Source is parsed as data and never executed.
6. `pytest`, `ruff check .`, and `mypy src` pass.
7. Documentation accurately states supported inputs and rule limitations.
8. Rules are not described as proof of exploitability or complete coverage.

Coverage percentages alone do not establish detection precision or recall. Future rules require version-controlled positive and negative fixtures and regression tests.
