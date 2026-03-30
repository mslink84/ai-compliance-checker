"""
app.py – Streamlit frontend for the AI Compliance Checker.

Run with:
    streamlit run app.py

Requires ANTHROPIC_API_KEY environment variable.
"""

from __future__ import annotations

import io
import os
import traceback

import streamlit as st

from analyzer import FRAMEWORK_FILES, ComplianceAnalysis, analyse_document
from report_generator import generate_pdf


# ── Page config ──────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Compliance Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helper functions (must be defined before they are called) ────────────────────

def extract_text(uploaded_file) -> str:
    """Extract plain text from PDF, DOCX or TXT file."""
    name = uploaded_file.name.lower()

    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            pdf_bytes = uploaded_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except Exception as e:
            st.error(f"PDF extraction error: {e}")
            return ""

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as e:
            st.error(f"DOCX extraction error: {e}")
            return ""

    return ""


def run_analysis(document_text: str, framework: str):
    """Call Claude, store result in session_state, then render."""
    with st.spinner(f"Analysing document against {framework}… this may take 30–60 seconds."):
        try:
            analysis: ComplianceAnalysis = analyse_document(document_text, framework)
            st.session_state["analysis"] = analysis
        except Exception:
            st.error("Analysis failed. See details below.")
            st.code(traceback.format_exc())
            st.stop()

    st.success("Analysis complete!")
    render_results(analysis)


def render_results(analysis: ComplianceAnalysis):
    """Render the full analysis UI."""
    # ── Score banner ──────────────────────────────────────────────────────────────
    score = analysis.overall_score
    if score >= 75:
        label = "Good"
    elif score >= 50:
        label = "Needs Improvement"
    else:
        label = "Critical Gaps"

    col_score, col_meta = st.columns([1, 3])
    with col_score:
        st.metric(
            label=f"Compliance Score ({label})",
            value=f"{score}/100",
        )
    with col_meta:
        total = len(analysis.findings)
        compliant = sum(1 for f in analysis.findings if f.status == "Compliant")
        partial = sum(1 for f in analysis.findings if f.status == "Partial")
        non_compliant = sum(1 for f in analysis.findings if f.status == "Non-compliant")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Requirements", total)
        c2.metric("Compliant", compliant)
        c3.metric("Partial", partial)
        c4.metric("Non-compliant", non_compliant)

    # ── Document summary ──────────────────────────────────────────────────────────
    with st.expander("Document Summary", expanded=True):
        st.write(analysis.document_summary)

    # ── Key gaps & actions (side by side) ─────────────────────────────────────────
    col_gaps, col_actions = st.columns(2)
    with col_gaps:
        st.subheader("Key Gaps")
        for gap in analysis.key_gaps:
            st.markdown(f"- {gap}")
    with col_actions:
        st.subheader("Priority Actions")
        for i, action in enumerate(analysis.priority_actions, 1):
            st.markdown(f"{i}. {action}")

    st.divider()

    # ── Detailed findings ─────────────────────────────────────────────────────────
    st.subheader("Detailed Findings")

    status_filter = st.multiselect(
        "Filter by status",
        ["Compliant", "Partial", "Non-compliant", "Not Applicable"],
        default=["Partial", "Non-compliant"],
    )

    findings = analysis.findings
    if status_filter:
        findings = [f for f in findings if f.status in status_filter]

    if not findings:
        st.info("No findings match the selected filter.")
    else:
        for finding in findings:
            status_emoji = {
                "Compliant": "✅",
                "Partial": "⚠️",
                "Non-compliant": "❌",
                "Not Applicable": "⬜",
            }.get(finding.status, "")
            risk_emoji = {
                "High": "🔴", "Medium": "🟠", "Low": "🟡", "N/A": "⚪",
            }.get(finding.risk_level, "")

            with st.expander(
                f"{status_emoji} [{finding.requirement_id}] {finding.requirement_name} "
                f"— {finding.status} {risk_emoji} {finding.risk_level}",
                expanded=(finding.status == "Non-compliant"),
            ):
                col_f, col_r = st.columns(2)
                with col_f:
                    st.markdown("**Finding**")
                    st.write(finding.finding)
                with col_r:
                    st.markdown("**Recommendation**")
                    st.write(finding.recommendation)

    # ── PDF export ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Export Report")

    if st.button("Generate PDF Report", type="secondary"):
        with st.spinner("Generating PDF…"):
            pdf_bytes = generate_pdf(analysis)
        filename = (
            f"compliance_report_{analysis.framework_name.replace(' ', '_').lower()}.pdf"
        )
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
        )


def render_landing():
    """Show instructions on the landing page before any file is uploaded."""
    st.markdown(
        """
        ### How it works

        1. **Upload** your security policy, data protection policy, or any relevant document
        2. **Select** a compliance framework (GDPR, ISO 27001, or NIST CSF 2.0)
        3. **Click** "Run Compliance Analysis"
        4. Review findings and download the PDF report

        ---

        ### Supported Frameworks

        | Framework | Best For |
        |---|---|
        | **GDPR** | Data protection & privacy policies, EU organisations |
        | **ISO 27001** | Information security management systems |
        | **NIST CSF 2.0** | Cybersecurity programmes, US organisations |

        ---

        ### Example output

        ```
        Compliance Score: 62/100 – Needs Improvement

        Compliant:      5 requirements
        Partial:        3 requirements
        Non-compliant:  4 requirements

        Key Gap: No documented breach notification procedure (GDPR Art.33)
        Priority: Implement a 72-hour breach notification process
        ```
        """
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("AI Compliance Checker")
    st.caption("Mikael Sundberg - www.msun.se")
    st.divider()

    st.subheader("1. Select Framework")
    framework = st.selectbox(
        "Compliance framework",
        options=list(FRAMEWORK_FILES.keys()),
        help="Choose the regulatory or security framework to analyse against.",
    )

    st.divider()
    st.subheader("2. Upload Document")
    uploaded_file = st.file_uploader(
        "Upload your policy or security document",
        type=["pdf", "txt", "docx"],
        help="Upload a PDF, Word document (.docx), or plain text file.",
    )

    st.divider()
    st.markdown(
        """
        **What this tool does:**
        - Extracts text from your document
        - Analyses each requirement
        - Scores compliance (0–100)
        - Identifies gaps and recommendations
        - Exports a professional PDF report
        """
    )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning(
            "ANTHROPIC_API_KEY not set. "
            "Add it to your environment before running."
        )


# ── Main area ─────────────────────────────────────────────────────────────────────

st.header("Gap Analysis Report")

if uploaded_file is None:
    render_landing()
else:
    document_text = extract_text(uploaded_file)

    if not document_text.strip():
        st.error(
            "Could not extract text from the uploaded file. "
            "Please try a different file or convert it to .txt."
        )
        st.stop()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.success(
            f"Document loaded: **{uploaded_file.name}**  "
            f"({len(document_text):,} characters)"
        )
    with col2:
        analyse_btn = st.button(
            "Run Compliance Analysis", type="primary", use_container_width=True
        )

    if analyse_btn:
        run_analysis(document_text, framework)
    elif "analysis" in st.session_state:
        render_results(st.session_state["analysis"])
