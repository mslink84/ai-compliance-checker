"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from analyzer import ComplianceAnalysis, GapFinding


def _make_finding(**overrides) -> dict:
    base = {
        "requirement_id": "TEST-1",
        "requirement_name": "Test Requirement",
        "status": "Compliant",
        "risk_level": "N/A",
        "confidence": 90,
        "finding": "The document explicitly addresses this requirement.",
        "recommendation": "No action required.",
    }
    return {**base, **overrides}


def _make_analysis(**overrides) -> dict:
    base = {
        "framework_name": "GDPR",
        "document_summary": "A sample data protection policy.",
        "overall_score": 75,
        "findings": [_make_finding()],
        "key_gaps": ["Missing breach notification procedure"],
        "priority_actions": ["Implement 72-hour breach notification"],
        "truncated": False,
    }
    return {**base, **overrides}


def test_valid_finding():
    f = GapFinding(**_make_finding())
    assert f.status == "Compliant"
    assert f.confidence == 90


def test_finding_confidence_defaults_to_50():
    data = _make_finding()
    del data["confidence"]
    f = GapFinding(**data)
    assert f.confidence == 50


def test_finding_invalid_status():
    with pytest.raises(ValidationError):
        GapFinding(**_make_finding(status="Unknown"))


def test_finding_invalid_risk_level():
    with pytest.raises(ValidationError):
        GapFinding(**_make_finding(risk_level="Critical"))


def test_finding_confidence_out_of_range():
    with pytest.raises(ValidationError):
        GapFinding(**_make_finding(confidence=101))
    with pytest.raises(ValidationError):
        GapFinding(**_make_finding(confidence=-1))


def test_valid_analysis():
    a = ComplianceAnalysis(**_make_analysis())
    assert a.overall_score == 75
    assert len(a.findings) == 1
    assert a.truncated is False


def test_analysis_score_out_of_range():
    with pytest.raises(ValidationError):
        ComplianceAnalysis(**_make_analysis(overall_score=101))


def test_analysis_truncated_defaults_false():
    data = _make_analysis()
    del data["truncated"]
    a = ComplianceAnalysis(**data)
    assert a.truncated is False


def test_analysis_model_validate_json():
    import json
    data = _make_analysis()
    raw = json.dumps(data)
    a = ComplianceAnalysis.model_validate_json(raw)
    assert a.framework_name == "GDPR"
