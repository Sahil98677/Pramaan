from pathlib import Path

rules_path = Path("src/pramaan/rules.py")
tests_path = Path("tests/test_rule_edge_cases.py")

rules = rules_path.read_text(encoding="utf-8")
old_helper = '''def _target_names(target: ast.expr) -> Iterator[str]:
    """Return names assigned by a Python assignment target."""
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _target_names(element)
'''

new_helper = '''def _target_names(target: ast.expr) -> Iterator[str]:
    """Return names assigned by a Python assignment target."""
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _target_names(element)


def _assigned_name_values(
    target: ast.expr, value: ast.expr
) -> Iterator[tuple[str, ast.expr]]:
    """Pair assigned names with values, including tuple/list destructuring."""
    if isinstance(target, ast.Name):
        yield target.id, value
    elif (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
    ):
        for target_item, value_item in zip(target.elts, value.elts):
            yield from _assigned_name_values(target_item, value_item)
'''

old_check = '''    def _check_sensitive_assignment(
        self, targets: list[ast.expr], value: ast.expr | None, line: int
    ) -> None:
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            return
        literal = value.value
        if _is_placeholder(literal):
            return
        for target in targets:
            for name in _target_names(target):
                if _SENSITIVE_NAME.search(name):
                    self._finding(
'''

new_check = '''    def _check_sensitive_assignment(
        self, targets: list[ast.expr], value: ast.expr | None, line: int
    ) -> None:
        if value is None:
            return
        for target in targets:
            for name, assigned_value in _assigned_name_values(target, value):
                if (
                    isinstance(assigned_value, ast.Constant)
                    and isinstance(assigned_value.value, str)
                    and not _is_placeholder(assigned_value.value)
                    and _SENSITIVE_NAME.search(name)
                ):
                    self._finding(
'''

if old_helper not in rules:
    raise SystemExit("Could not find expected _target_names block; no files changed.")
if old_check not in rules:
    raise SystemExit("Could not find expected assignment-check block; no files changed.")
if "_assigned_name_values(" in rules:
    raise SystemExit("Tuple/list assignment support may already be present; no files changed.")

rules = rules.replace(old_helper, new_helper, 1)
rules = rules.replace(old_check, new_check, 1)

tests = tests_path.read_text(encoding="utf-8")
anchor = '''def test_json_finds_multiple_nested_credentials_and_debug_flags() -> None:
'''
addition = '''def test_python_detects_secret_in_tuple_assignment() -> None:
    source = (
        'api_key, display_name = ("synthetic_key_material_12345", "service")\n'
    )

    findings = analyze_python_source(source, filename="tuple_assignment.py")

    assert [finding.rule_id for finding in findings] == ["PRM-PY-SECRET-001"]
    assert "synthetic_key_material_12345" not in findings[0].evidence[0].excerpt


def test_python_does_not_pair_tuple_assignment_with_mismatched_lengths() -> None:
    source = 'api_key, display_name = ("synthetic_key_material_12345",)\n'

    assert analyze_python_source(source, filename="mismatched_tuple.py") == []


'''

if "def test_python_detects_secret_in_tuple_assignment" in tests:
    raise SystemExit("Tuple-assignment regression tests already exist; no files changed.")
if anchor not in tests:
    raise SystemExit("Could not find expected test insertion point; no files changed.")

tests = tests.replace(anchor, addition + anchor, 1)

rules_path.write_text(rules, encoding="utf-8")
tests_path.write_text(tests, encoding="utf-8")
print("Patch applied. Run pytest, ruff check ., and mypy src.")
