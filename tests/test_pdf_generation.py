"""Tests for PDF report generation."""

import pytest

from analyzer import ComplianceAnalysis, GapFinding
from report_generator import generate_pdf


def _sample_analysis(truncated: bool = False) -> ComplianceAnalysis:
    findings = [
        GapFinding(
            requirement_id="GDPR-Art5",
            requirement_name="Principles of data processing",
            status="Compliant",
            risk_level="N/A",
            confidence=88,
            finding="The document explicitly states lawful basis and data minimisation.",
            recommendation="No action required.",
        ),
        GapFinding(
            requirement_id="GDPR-Art33-34",
            requirement_name="Breach notification",
            status="Non-compliant",
            risk_level="High",
            confidence=95,
            finding="No breach notification procedure is mentioned.",
            recommendation="Implement a 72-hour breach notification process.",
        ),
        GapFinding(
            requirement_id="GDPR-Art28",
            requirement_name="Data processor agreements",
            status="Partial",
            risk_level="Medium",
            confidence=60,
            finding="Processor relationships are mentioned but DPA requirements are vague.",
            recommendation="Formalise Data Processing Agreements with all processors.",
        ),
    ]
    return ComplianceAnalysis(
        framework_name="GDPR",
        document_summary="A sample data protection policy covering core GDPR obligations.",
        overall_score=50,
        findings=findings,
        key_gaps=["No breach notification procedure"],
        priority_actions=["Implement 72-hour breach notification"],
        truncated=truncated,
    )


def test_generate_pdf_returns_bytes():
    pdf = generate_pdf(_sample_analysis())
    assert isinstance(pdf, bytes)
    assert len(pdf) > 0


def test_pdf_starts_with_pdf_header():
    pdf = generate_pdf(_sample_analysis())
    assert pdf[:4] == b"%PDF", "Output does not start with PDF magic bytes"


def test_pdf_non_empty_for_truncated_analysis():
    pdf = generate_pdf(_sample_analysis(truncated=True))
    assert len(pdf) > 1000  # should produce a real document


def test_pdf_with_empty_gaps_and_actions():
    analysis = _sample_analysis()
    analysis.key_gaps = []
    analysis.priority_actions = []
    pdf = generate_pdf(analysis)
    assert pdf[:4] == b"%PDF"


def test_pdf_finding_without_confidence():
    """Findings without confidence field should not crash PDF generation."""
    analysis = _sample_analysis()
    # Simulate old-style finding by removing confidence
    for f in analysis.findings:
        object.__setattr__(f, "confidence", None)
    # generate_pdf should handle None confidence gracefully
    pdf = generate_pdf(analysis)
    assert pdf[:4] == b"%PDF"
