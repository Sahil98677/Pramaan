"""Small deterministic Python and JSON security rules.

These are heuristic static checks, not proof that code is exploitable. The
analyzer parses source as data and never imports or executes it.
"""

import ast
import re
from collections.abc import Iterator
from typing import Any

from .models import Evidence, Finding, Severity

_PYTHON_SHELL_APIS = {"run", "Popen", "call", "check_call", "check_output"}
_SENSITIVE_NAME = re.compile(
    r"(?:password|passwd|secret|api[_-]?key|token|client[_-]?secret|private[_-]?key)",
    re.IGNORECASE,
)
_DEBUG_NAMES = {"debug", "debug_mode", "debugmode", "debug_enabled"}
_PLACEHOLDERS = {
    "", "example", "example-value", "dummy", "dummy-value", "changeme",
    "change_me", "change-me", "replace_me", "replace-me", "placeholder",
    "your-secret", "your_api_key", "your-api-key", "insert-secret-here",
    "not-a-secret", "redacted", "xxx", "none", "null", "test", "test-value",
}
_ENV_PLACEHOLDER = re.compile(r"^\$\{?[A-Z][A-Z0-9_]*\}?$")


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _PLACEHOLDERS:
        return True
    if normalized.startswith(("your_", "your-", "replace_me_", "replace-me-")):
        return True
    return bool(_ENV_PLACEHOLDER.fullmatch(value.strip()))


def _target_names(target: ast.expr) -> Iterator[str]:
    """Return names assigned by a Python assignment target."""
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, (ast.Tuple, ast.List)):
        for element in target.elts:
            yield from _target_names(element)


class _PythonRuleVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[Finding] = []

    def _finding(
        self,
        *,
        rule_id: str,
        title: str,
        description: str,
        severity: Severity,
        confidence: float,
        line: int,
        excerpt: str,
        remediation: str,
    ) -> None:
        self.findings.append(
            Finding(
                rule_id=rule_id,
                title=title,
                description=description,
                severity=severity,
                confidence=confidence,
                evidence=[
                    Evidence(
                        kind="static_pattern",
                        location=f"{self.filename}:{line}",
                        excerpt=excerpt,
                    )
                ],
                remediation=remediation,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
            name = node.func.id
            self._finding(
                rule_id="PRM-PY-DYN-001",
                title=f"Dynamic code execution via {name}()",
                description=(
                    f"A direct call to built-in {name}() evaluates dynamically supplied code. "
                    "Static analysis cannot establish whether its input is attacker-controlled."
                ),
                severity=Severity.HIGH,
                confidence=0.90,
                line=node.lineno,
                excerpt=(
                    f"Direct call to {name}() detected; arguments are not "
                    "included in evidence."
                ),
                remediation=(
                    "Avoid evaluating strings as code. Use a constrained parser or an explicit "
                    "mapping of permitted operations where possible."
                ),
            )

        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
            and node.func.attr in _PYTHON_SHELL_APIS
            and any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
        ):
            self._finding(
                rule_id="PRM-PY-SHELL-001",
                title="Subprocess call enables shell interpretation",
                description=(
                    "A recognized subprocess API is called with shell=True. If command content "
                    "includes untrusted data, shell metacharacters may change the command's "
                    "meaning. "
                    "This pattern alone does not prove attacker control or exploitability."
                ),
                severity=Severity.HIGH,
                confidence=0.82,
                line=node.lineno,
                excerpt=f"subprocess.{node.func.attr}(..., shell=True) detected.",
                remediation=(
                    "Prefer an argument list with shell=False. Validate arguments according to "
                    "their expected format and avoid building shell command strings."
                ),
            )

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._check_sensitive_assignment(node.targets, node.value, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._check_sensitive_assignment([node.target], node.value, node.lineno)
        self.generic_visit(node)

    def _check_sensitive_assignment(
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
                        rule_id="PRM-PY-SECRET-001",
                        title="Possible hard-coded credential",
                        description=(
                            f"Variable '{name}' contains a non-placeholder string literal and its "
                            "name suggests credential material. Confirm whether this is a real "
                            "secret."
                        ),
                        severity=Severity.HIGH,
                        confidence=0.78,
                        line=line,
                        excerpt=f"Credential-like assignment to '{name}'; literal value redacted.",
                        remediation=(
                            "Remove credentials from source control, rotate exposed values, and "
                            "load "
                            "secrets from an approved secret store or environment configuration."
                        ),
                    )


def analyze_python_source(source: str, filename: str = "<input>") -> list[Finding]:
    """Analyze Python syntax using AST only; the supplied source is never executed."""
    tree = ast.parse(source, filename=filename, mode="exec")
    visitor = _PythonRuleVisitor(filename)
    visitor.visit(tree)
    return visitor.findings


def analyze_json_value(value: Any, filename: str = "<input>") -> list[Finding]:
    """Analyze parsed JSON for credential-like literals and enabled debug flags."""
    findings: list[Finding] = []

    def walk(current: Any, pointer: str) -> None:
        if isinstance(current, dict):
            for key, child in current.items():
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                child_pointer = f"{pointer}/{escaped}"
                key_text = str(key)
                if (
                    _SENSITIVE_NAME.search(key_text)
                    and isinstance(child, str)
                    and not _is_placeholder(child)
                ):
                    findings.append(
                        Finding(
                            rule_id="PRM-JSON-SECRET-001",
                            title="Possible hard-coded credential in JSON",
                            description=(
                                f"JSON key '{key_text}' contains a non-placeholder string "
                                "literal and "
                                "its name suggests credential material. The value is "
                                "deliberately redacted."
                            ),
                            severity=Severity.HIGH,
                            confidence=0.78,
                            evidence=[
                                Evidence(
                                    kind="json_path",
                                    location=f"{filename}#{child_pointer}",
                                    excerpt=(
                                        f"Credential-like JSON key '{key_text}'; "
                                        "value redacted."
                                    ),
                                )
                            ],
                            remediation=(
                                "Remove credentials from JSON committed to source control, rotate "
                                "exposed "
                                "values, and inject secrets from an approved secret store."
                            ),
                        )
                    )
                if key_text.strip().lower() in _DEBUG_NAMES and child is True:
                    findings.append(
                        Finding(
                            rule_id="PRM-JSON-DEBUG-001",
                            title="Debug mode is enabled in JSON configuration",
                            description=(
                                "A debug-related JSON setting is true. Debug features can expose "
                                "verbose "
                                "errors or internal details; the correct setting depends on "
                                "deployment context."
                            ),
                            severity=Severity.MEDIUM,
                            confidence=0.80,
                            evidence=[
                                Evidence(
                                    kind="json_path",
                                    location=f"{filename}#{child_pointer}",
                                    excerpt=f"JSON setting '{key_text}' is true.",
                                )
                            ],
                            remediation=(
                                "Confirm the intended environment and disable debug mode in "
                                "production "
                                "configuration where it could expose internal details."
                            ),
                        )
                    )
                walk(child, child_pointer)
        elif isinstance(current, list):
            for index, child in enumerate(current):
                walk(child, f"{pointer}/{index}")

    walk(value, "")
    return findings
