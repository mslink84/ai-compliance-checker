"""
analyzer.py – Claude API integration for compliance gap analysis.
Uses client.messages.create() with structured JSON output parsed via Pydantic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from collections.abc import Callable
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────────

MAX_DOC_CHARS = 14_000   # ~3 500 tokens – leaves room for prompts and full output
OVERLAP_CHARS = 400      # overlap between chunks to avoid cutting mid-sentence


# ── Pydantic models ───────────────────────────────────────────────────────────────

class GapFinding(BaseModel):
    requirement_id: str
    requirement_name: str
    status: Literal["Compliant", "Partial", "Non-compliant", "Not Applicable"]
    risk_level: Literal["High", "Medium", "Low", "N/A"]
    confidence: int = Field(
        default=50, ge=0, le=100,
        description="AI confidence in this finding (0–100). "
                    "High when requirement is clearly addressed or clearly absent; "
                    "low when the document is ambiguous.",
    )
    finding: str          # What was found (or not found) in the document
    recommendation: str   # Concrete next step


class ComplianceAnalysis(BaseModel):
    framework_name: str
    document_summary: str
    overall_score: int = Field(ge=0, le=100)
    findings: list[GapFinding]
    key_gaps: list[str]
    priority_actions: list[str]
    truncated: bool = Field(
        default=False,
        description="True when the document was too long and was analysed in chunks.",
    )


# ── Framework loader ─────────────────────────────────────────────────────────────

FRAMEWORKS_DIR = Path(__file__).parent / "frameworks"

FRAMEWORK_FILES = {
    "GDPR":          FRAMEWORKS_DIR / "gdpr.json",
    "ISO 27001":     FRAMEWORKS_DIR / "iso27001.json",
    "NIST CSF 2.0":  FRAMEWORKS_DIR / "nist_csf.json",
    "SOC 2":         FRAMEWORKS_DIR / "soc2.json",
}


def load_framework(framework_name: str) -> dict:
    path = FRAMEWORK_FILES[framework_name]
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# ── Public API ───────────────────────────────────────────────────────────────────

def analyse_document(
    document_text: str,
    framework_name: str,
    on_token: Callable[[int], None] | None = None,
) -> ComplianceAnalysis:
    """
    Analyse document_text against framework_name using Claude.

    Automatically chunks documents longer than MAX_DOC_CHARS and merges results.

    Args:
        document_text:  Extracted plain text from the uploaded policy/document.
        framework_name: One of "GDPR", "ISO 27001", "NIST CSF 2.0", "SOC 2".

    Returns:
        ComplianceAnalysis Pydantic model.

    Raises:
        RuntimeError: On API errors or unparseable responses.
    """
    framework = load_framework(framework_name)
    requirements_text = _format_requirements(framework)
    truncated = len(document_text) > MAX_DOC_CHARS

    if truncated:
        logger.info(
            "Document length %d chars exceeds limit %d – using chunked analysis.",
            len(document_text), MAX_DOC_CHARS,
        )
        analysis = _analyse_chunked(document_text, framework, framework_name, requirements_text, on_token)
    else:
        analysis = _call_claude(document_text, framework, framework_name, requirements_text, on_token)

    analysis.truncated = truncated
    return analysis


# ── Internal: single-call analysis ───────────────────────────────────────────────

def _call_claude(
    document_text: str,
    framework: dict,
    framework_name: str,
    requirements_text: str,
    on_token: Callable[[int], None] | None = None,
) -> ComplianceAnalysis:
    system_prompt = _build_system_prompt(framework, framework_name, requirements_text)
    user_message = (
        f"Please analyse the following document against {framework_name}:\n\n"
        f"=== DOCUMENT ===\n{document_text}\n=== END DOCUMENT ===\n\n"
        "Provide a finding for every single requirement listed in the system prompt. "
        "Respond with ONLY valid JSON – no markdown fences, no explanation."
    )

    # timeout=60 s applies to connection + first byte; streaming keeps the link
    # alive for the full response so large frameworks (ISO 27001, NIST) don't drop.
    client = anthropic.Anthropic(timeout=60.0)

    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            parts: list[str] = []
            char_count = 0
            for chunk in stream.text_stream:
                parts.append(chunk)
                char_count += len(chunk)
                if on_token and char_count % 200 == 0:
                    on_token(char_count)
            if on_token:
                on_token(char_count)
            raw = "".join(parts)
    except anthropic.AuthenticationError as exc:
        raise RuntimeError(
            "Invalid API key. Check your ANTHROPIC_API_KEY environment variable."
        ) from exc
    except anthropic.RateLimitError as exc:
        raise RuntimeError(
            "Claude API rate limit reached. Please wait a moment and try again."
        ) from exc
    except anthropic.APITimeoutError as exc:
        raise RuntimeError(
            "The Claude API did not respond in time. "
            "Try again — Anthropic may be experiencing high load."
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(
            f"Could not connect to the Claude API. Check your internet connection.\n{exc}"
        ) from exc
    except anthropic.APIError as exc:
        raise RuntimeError(f"Claude API error: {exc}") from exc

    if not raw:
        raise RuntimeError(
            "Claude returned an empty response. This is unexpected — please try again."
        )

    # Strip markdown code fences if the model added them despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()

    try:
        return ComplianceAnalysis.model_validate_json(raw)
    except Exception as exc:
        raise RuntimeError(
            f"Claude returned a response that could not be parsed as valid JSON.\n"
            f"Parse error: {exc}\n"
            f"Raw response (first 500 chars):\n{raw[:500]}"
        ) from exc


# ── Internal: chunked analysis ────────────────────────────────────────────────────

def _analyse_chunked(
    document_text: str,
    framework: dict,
    framework_name: str,
    requirements_text: str,
    on_token: Callable[[int], None] | None = None,
) -> ComplianceAnalysis:
    chunks = _split_into_chunks(document_text)
    logger.info("Analysing %d chunks for %s.", len(chunks), framework_name)

    results: list[ComplianceAnalysis] = []
    for i, chunk in enumerate(chunks, 1):
        labelled = f"[Document section {i}/{len(chunks)}]\n\n{chunk}"
        result = _call_claude(labelled, framework, framework_name, requirements_text, on_token)
        results.append(result)

    return _merge_analyses(results, framework_name)


def _split_into_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_DOC_CHARS, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - OVERLAP_CHARS
    return chunks


# Status/risk priorities for merging (higher = more evidence of compliance)
_STATUS_PRIORITY = {"Compliant": 3, "Partial": 2, "Not Applicable": 1, "Non-compliant": 0}
_RISK_PRIORITY   = {"High": 3, "Medium": 2, "Low": 1, "N/A": 0}


def _merge_analyses(
    analyses: list[ComplianceAnalysis],
    framework_name: str,
) -> ComplianceAnalysis:
    """Merge chunk results: best (most compliant) status wins per requirement."""
    if len(analyses) == 1:
        return analyses[0]

    by_req: dict[str, list[GapFinding]] = {}
    for analysis in analyses:
        for finding in analysis.findings:
            by_req.setdefault(finding.requirement_id, []).append(finding)

    merged_findings: list[GapFinding] = []
    for findings in by_req.values():
        best   = max(findings, key=lambda f: _STATUS_PRIORITY.get(f.status, 0))
        worst  = max(findings, key=lambda f: _RISK_PRIORITY.get(f.risk_level, 0))
        avg_confidence = int(sum(f.confidence for f in findings) / len(findings))

        # Combine unique finding texts (capped)
        seen_texts: set[str] = set()
        combined_parts: list[str] = []
        for f in findings:
            snippet = f.finding[:200]
            if snippet not in seen_texts:
                combined_parts.append(f.finding)
                seen_texts.add(snippet)
        combined_finding = " | ".join(combined_parts)[:600]

        merged_findings.append(GapFinding(
            requirement_id=best.requirement_id,
            requirement_name=best.requirement_name,
            status=best.status,
            risk_level=worst.risk_level,
            confidence=avg_confidence,
            finding=combined_finding,
            recommendation=best.recommendation,
        ))

    # Recalculate overall score
    total = len(merged_findings)
    if total > 0:
        points = sum(
            1.0 if f.status == "Compliant" else 0.5 if f.status == "Partial" else 0.0
            for f in merged_findings
        )
        overall_score = int(round(points / total * 100))
    else:
        overall_score = 0

    # Deduplicate key_gaps and priority_actions
    def _dedupe(items: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            if item not in seen:
                result.append(item)
                seen.add(item)
        return result

    key_gaps = _dedupe([g for a in analyses for g in a.key_gaps])[:5]
    priority_actions = _dedupe([act for a in analyses for act in a.priority_actions])[:5]

    return ComplianceAnalysis(
        framework_name=framework_name,
        document_summary=analyses[0].document_summary,
        overall_score=overall_score,
        findings=merged_findings,
        key_gaps=key_gaps,
        priority_actions=priority_actions,
        truncated=True,
    )


# ── Prompt builders ───────────────────────────────────────────────────────────────

def _build_system_prompt(
    framework: dict,
    framework_name: str,
    requirements_text: str,
) -> str:
    # Include JSON schema so the model knows exactly what to produce
    schema_str = json.dumps(ComplianceAnalysis.model_json_schema(), indent=2)

    return f"""You are a senior GRC (Governance, Risk, Compliance) consultant specialising in {framework["full_name"]}.

Your task: conduct a gap analysis of an organisation's policy/security document against the {framework_name} requirements below.

For each requirement assess whether the document:
- Explicitly addresses it → "Compliant"
- Partially addresses it → "Partial"
- Does not address it    → "Non-compliant"
- Is out of scope        → "Not Applicable"

risk_level: High/Medium/Low for Non-compliant and Partial items; "N/A" for others.
confidence: 0–100. High (80–100) when the document clearly addresses or clearly misses the requirement. Low (0–40) when language is ambiguous.

Be specific: quote or reference actual document content when it exists.
Be practical: give concrete, actionable recommendations.
overall_score = round((compliant_count + 0.5 × partial_count) / total_requirements × 100).

=== {framework_name} REQUIREMENTS ===
{requirements_text}

=== OUTPUT FORMAT ===
Respond with ONLY a single valid JSON object. No markdown, no prose, no code fences.
All text fields (finding, recommendation, document_summary, key_gaps, priority_actions) must be written in English regardless of the language of the uploaded document.
The JSON must match this schema exactly:
{schema_str}"""


# ── Helpers ───────────────────────────────────────────────────────────────────────

def _format_requirements(framework: dict) -> str:
    lines: list[str] = []
    for req in framework["requirements"]:
        lines.append(f"[{req['id']}] {req['name']}")
        lines.append(f"  Description: {req['description']}")
        lines.append(f"  Keywords: {', '.join(req['keywords'])}")
        lines.append("")
    return "\n".join(lines)
