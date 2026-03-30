"""
report_generator.py – PDF report generation using ReportLab.
Takes a ComplianceAnalysis object and returns PDF bytes.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from analyzer import ComplianceAnalysis

# ── Colour palette ────────────────────────────────────────────────────────────────

DARK_BLUE   = colors.HexColor("#1a2744")
MID_BLUE    = colors.HexColor("#2c4a8c")
LIGHT_BLUE  = colors.HexColor("#dce8f5")
RED         = colors.HexColor("#c0392b")
AMBER       = colors.HexColor("#e67e22")
GREEN       = colors.HexColor("#27ae60")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MID_GREY    = colors.HexColor("#888888")

STATUS_COLOURS = {
    "Compliant":      GREEN,
    "Partial":        AMBER,
    "Non-compliant":  RED,
    "Not Applicable": MID_GREY,
}

RISK_COLOURS = {
    "High":   RED,
    "Medium": AMBER,
    "Low":    GREEN,
    "N/A":    MID_GREY,
}

PAGE_WIDTH, PAGE_HEIGHT = A4


# ── Page-number callback ──────────────────────────────────────────────────────────

def _draw_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GREY)
    canvas.drawRightString(
        PAGE_WIDTH - 2 * cm,
        1.2 * cm,
        f"Page {canvas.getPageNumber()}",
    )
    canvas.restoreState()


# ── Main entry point ──────────────────────────────────────────────────────────────

def generate_pdf(analysis: ComplianceAnalysis) -> bytes:
    """
    Generate a professional PDF compliance gap analysis report.

    Returns:
        PDF content as bytes – ready for st.download_button().
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.5 * cm,   # extra space for page numbers
        title=f"Compliance Report – {analysis.framework_name}",
        author="AI Compliance Checker",
    )

    styles = _build_styles()
    story = []

    _add_header(story, styles, analysis)
    _add_summary_section(story, styles, analysis)
    _add_score_section(story, styles, analysis)
    _add_key_gaps_section(story, styles, analysis)
    _add_priority_actions_section(story, styles, analysis)
    _add_findings_table(story, styles, analysis)
    _add_limitations_section(story, styles)
    _add_footer_note(story, styles)

    doc.build(
        story,
        onFirstPage=_draw_page_number,
        onLaterPages=_draw_page_number,
    )
    return buffer.getvalue()


# ── Section builders ──────────────────────────────────────────────────────────────

def _add_header(story, styles, analysis: ComplianceAnalysis):
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("AI COMPLIANCE CHECKER", styles["report_label"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Gap Analysis Report", styles["title"]))
    story.append(Paragraph(analysis.framework_name, styles["subtitle_framework"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}",
        styles["subtitle"],
    ))
    if getattr(analysis, "truncated", False):
        story.append(Paragraph(
            "Note: document exceeded analysis limit and was processed in multiple sections.",
            styles["warning_note"],
        ))
    story.append(HRFlowable(width="100%", thickness=2, color=MID_BLUE, spaceAfter=12))


def _add_summary_section(story, styles, analysis: ComplianceAnalysis):
    story.append(Paragraph("Document Summary", styles["section_heading"]))
    story.append(Paragraph(analysis.document_summary, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))


def _add_score_section(story, styles, analysis: ComplianceAnalysis):
    score = analysis.overall_score
    if score >= 75:
        score_colour, score_label = GREEN, "Good"
    elif score >= 50:
        score_colour, score_label = AMBER, "Needs Improvement"
    else:
        score_colour, score_label = RED, "Critical Gaps"

    total         = len(analysis.findings)
    compliant     = sum(1 for f in analysis.findings if f.status == "Compliant")
    partial       = sum(1 for f in analysis.findings if f.status == "Partial")
    non_compliant = sum(1 for f in analysis.findings if f.status == "Non-compliant")
    not_applicable = sum(1 for f in analysis.findings if f.status == "Not Applicable")

    story.append(Paragraph("Compliance Score", styles["section_heading"]))

    score_data = [
        ["Overall Score", f"{score}/100", score_label],
        ["Requirements reviewed", str(total), ""],
        ["Compliant",     str(compliant),     ""],
        ["Partial",       str(partial),       ""],
        ["Non-compliant", str(non_compliant), ""],
        ["Not Applicable", str(not_applicable), ""],
    ]

    table = Table(score_data, colWidths=[7 * cm, 3 * cm, 5 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 12),
        ("BACKGROUND",  (1, 0), (1,  0), score_colour),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("FONTNAME",    (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 1), (-1, -1), 10),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("ALIGN",       (1, 0), (1, -1), "CENTER"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))


def _add_key_gaps_section(story, styles, analysis: ComplianceAnalysis):
    if not analysis.key_gaps:
        return
    story.append(Paragraph("Key Gaps Identified", styles["section_heading"]))
    for gap in analysis.key_gaps:
        story.append(Paragraph(f"• {gap}", styles["bullet"]))
    story.append(Spacer(1, 0.4 * cm))


def _add_priority_actions_section(story, styles, analysis: ComplianceAnalysis):
    if not analysis.priority_actions:
        return
    story.append(Paragraph("Priority Actions", styles["section_heading"]))
    for i, action in enumerate(analysis.priority_actions, 1):
        story.append(Paragraph(f"{i}. {action}", styles["bullet"]))
    story.append(Spacer(1, 0.5 * cm))


def _add_findings_table(story, styles, analysis: ComplianceAnalysis):
    story.append(Paragraph("Detailed Findings", styles["section_heading"]))
    story.append(Spacer(1, 0.2 * cm))

    headers = ["Requirement", "Status", "Risk", "Conf.", "Finding", "Recommendation"]
    col_widths = [3.2 * cm, 2.1 * cm, 1.4 * cm, 1.2 * cm, 5.0 * cm, 4.3 * cm]

    rows = [headers]
    for finding in analysis.findings:
        confidence = getattr(finding, "confidence", None)
        conf_str = f"{confidence}%" if confidence is not None else "–"
        rows.append([
            Paragraph(
                f"<b>{finding.requirement_id}</b><br/>{finding.requirement_name}",
                styles["table_cell"],
            ),
            Paragraph(finding.status,      styles["table_cell"]),
            Paragraph(finding.risk_level,  styles["table_cell"]),
            Paragraph(conf_str,            styles["table_cell"]),
            Paragraph(finding.finding,     styles["table_cell"]),
            Paragraph(finding.recommendation, styles["table_cell"]),
        ])

    table = Table(rows, colWidths=col_widths, repeatRows=1, splitByRow=1)

    table_style = [
        ("BACKGROUND",  (0, 0), (-1, 0), DARK_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("ALIGN",       (0, 0), (-1, 0), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
        ("SPLITLONGROWS", (0, 0), (-1, -1), 1),
    ]

    for row_idx, finding in enumerate(analysis.findings, start=1):
        table_style.append(("BACKGROUND", (1, row_idx), (1, row_idx), _lighten(STATUS_COLOURS.get(finding.status, MID_GREY))))
        table_style.append(("BACKGROUND", (2, row_idx), (2, row_idx), _lighten(RISK_COLOURS.get(finding.risk_level, MID_GREY))))

    table.setStyle(TableStyle(table_style))
    story.append(table)


def _add_limitations_section(story, styles):
    story.append(Paragraph("Methodology & Limitations", styles["section_heading"]))
    story.append(Paragraph(
        "This report was produced by AI Compliance Checker using Claude Sonnet 4.6 (Anthropic). "
        "The analysis compares extracted document text against a curated set of framework "
        "requirements. Confidence scores (0–100) indicate how clearly the document addresses "
        "or fails to address each requirement — not absolute compliance certainty.",
        styles["body"],
    ))
    story.append(Spacer(1, 0.2 * cm))
    limitations = [
        "Only text extracted from the uploaded file is analysed — verbal policies, separate systems, or supplementary documents are not assessed.",
        "AI may misinterpret ambiguous language or complex document structures.",
        "Framework requirements used here are informative summaries; refer to the original standards for authoritative definitions.",
        "This report is a starting point only and must be reviewed by a qualified compliance professional before use in formal assessments.",
        "If the document was chunked (truncated flag), results are merged automatically and some cross-section context may be reduced.",
    ]
    for lim in limitations:
        story.append(Paragraph(f"• {lim}", styles["bullet"]))
    story.append(Spacer(1, 0.4 * cm))


def _add_footer_note(story, styles):
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GREY))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "AI Compliance Checker — prototype tool for portfolio demonstration. "
        "Not a substitute for professional compliance advice.",
        styles["footer"],
    ))


# ── Style definitions ─────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    getSampleStyleSheet()   # initialise ReportLab defaults
    return {
        "report_label": ParagraphStyle(
            "report_label", fontSize=9, textColor=MID_GREY, spaceAfter=2,
        ),
        "title": ParagraphStyle(
            "title", fontSize=22, fontName="Helvetica-Bold",
            textColor=DARK_BLUE, spaceAfter=4,
        ),
        "subtitle_framework": ParagraphStyle(
            "subtitle_framework", fontSize=13, fontName="Helvetica-Bold",
            textColor=MID_BLUE, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontSize=10, textColor=MID_GREY, spaceAfter=8,
        ),
        "warning_note": ParagraphStyle(
            "warning_note", fontSize=9, textColor=AMBER, spaceAfter=6,
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontSize=13, fontName="Helvetica-Bold",
            textColor=MID_BLUE, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", fontSize=10, leading=14, textColor=colors.black,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontSize=10, leading=14, leftIndent=14, spaceAfter=3,
        ),
        "table_cell": ParagraphStyle(
            "table_cell", fontSize=8, leading=11,
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=8, textColor=MID_GREY, alignment=TA_CENTER,
        ),
    }


def _lighten(colour: colors.Color, factor: float = 0.25) -> colors.Color:
    """Return a lighter version of a colour by blending with white."""
    r = colour.red   + (1 - colour.red)   * (1 - factor)
    g = colour.green + (1 - colour.green) * (1 - factor)
    b = colour.blue  + (1 - colour.blue)  * (1 - factor)
    return colors.Color(r, g, b)
