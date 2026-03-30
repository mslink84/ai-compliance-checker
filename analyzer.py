"""
analyzer.py – Claude API integration for compliance gap analysis.
Uses claude-opus-4-6 with structured output (Pydantic).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel


# ── Pydantic models for structured output ──────────────────────────────────────

class GapFinding(BaseModel):
    requirement_id: str
    requirement_name: str
    status: Literal["Compliant", "Partial", "Non-compliant", "Not Applicable"]
    risk_level: Literal["High", "Medium", "Low", "N/A"]
    finding: str          # What was found (or not found) in the document
    recommendation: str   # Concrete next step


class ComplianceAnalysis(BaseModel):
    framework_name: str
    document_summary: str        # One-paragraph summary of the uploaded document
    overall_score: int           # 0–100 compliance score
    findings: list[GapFinding]
    key_gaps: list[str]          # Top 3–5 critical gaps as short bullet strings
    priority_actions: list[str]  # Top 3–5 recommended actions as short strings


# ── Framework loader ────────────────────────────────────────────────────────────

FRAMEWORKS_DIR = Path(__file__).parent / "frameworks"

FRAMEWORK_FILES = {
    "GDPR":          FRAMEWORKS_DIR / "gdpr.json",
    "ISO 27001":     FRAMEWORKS_DIR / "iso27001.json",
    "NIST CSF 2.0":  FRAMEWORKS_DIR / "nist_csf.json",
}


def load_framework(framework_name: str) -> dict:
    path = FRAMEWORK_FILES[framework_name]
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ── Core analysis function ──────────────────────────────────────────────────────

def analyse_document(
    document_text: str,
    framework_name: str,
) -> ComplianceAnalysis:
    """
    Send document_text to Claude and receive a structured ComplianceAnalysis.

    Args:
        document_text:  Extracted text from the uploaded policy/document.
        framework_name: One of "GDPR", "ISO 27001", "NIST CSF 2.0".

    Returns:
        ComplianceAnalysis Pydantic model.
    """
    framework = load_framework(framework_name)
    requirements_text = _format_requirements(framework)

    system_prompt = f"""You are a senior GRC (Governance, Risk, Compliance) consultant
specialising in {framework["full_name"]}.

Your task is to conduct a gap analysis of an organisation's policy or security document
against the {framework_name} framework requirements listed below.

For each requirement, assess whether the uploaded document:
- Explicitly addresses it (Compliant)
- Partially addresses it (Partial)
- Does not address it (Non-compliant)
- Is not applicable given the document's scope (Not Applicable)

Assign a risk level (High / Medium / Low) for Non-compliant and Partial items.
Use N/A for Compliant and Not Applicable items.

Be specific: reference actual content from the document when it exists.
Be practical: give concrete, actionable recommendations.
Overall score should reflect the percentage of requirements that are Compliant or Partial
(Compliant = full points, Partial = half points).

=== {framework_name} REQUIREMENTS ===
{requirements_text}
"""

    user_message = f"""Please analyse the following document against {framework_name}:

=== DOCUMENT ===
{document_text[:15000]}
{"[... document truncated for analysis – first 15,000 characters shown ...]" if len(document_text) > 15000 else ""}
=== END DOCUMENT ===

Provide a complete gap analysis with a finding for every single requirement listed above."""

    client = anthropic.Anthropic()

    response = client.messages.parse(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        output_format=ComplianceAnalysis,
    )

    return response.parsed_output


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _format_requirements(framework: dict) -> str:
    lines = []
    for req in framework["requirements"]:
        lines.append(f"[{req['id']}] {req['name']}")
        lines.append(f"  Description: {req['description']}")
        lines.append(f"  Keywords: {', '.join(req['keywords'])}")
        lines.append("")
    return "\n".join(lines)
