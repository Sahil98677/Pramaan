import pytest
from pydantic import ValidationError

from pramaan.models import Evidence, Finding, Severity


def test_finding_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Finding(
            rule_id="TEST-1",
            title="Example",
            description="Example finding",
            severity=Severity.LOW,
            confidence=0.5,
            evidence=[],
        )


def test_finding_rejects_confidence_out_of_range() -> None:
    with pytest.raises(ValidationError):
        Finding(
            rule_id="TEST-1",
            title="Example",
            description="Example finding",
            severity=Severity.LOW,
            confidence=1.5,
            evidence=[Evidence(kind="fixture", note="test")],
        )


def test_finding_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Finding(
            rule_id="TEST-1",
            title="Example",
            description="Example finding",
            severity=Severity.LOW,
            confidence=0.5,
            evidence=[Evidence(kind="fixture", note="test")],
            surprise="not allowed",
        )
