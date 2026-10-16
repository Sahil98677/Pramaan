# Initial quality gates

Before a milestone is accepted:

1. Unit tests cover normal, malformed, boundary, and negative cases.
2. Findings have stable rule IDs, bounded confidence, and evidence.
3. Invalid input produces explicit errors rather than a clean scan result.
4. Report output is valid JSON and written atomically.
5. Source input is never executed.
6. `pytest`, `ruff check .`, and `mypy src` pass.
7. Documentation accurately states current coverage and limitations.

Coverage percentages alone are not sufficient evidence of detection accuracy. Future rules require positive and negative fixtures and regression tests.
