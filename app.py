"""
app.py – Streamlit frontend for the AI Compliance Checker.

Run with:
    streamlit run app.py

Requires ANTHROPIC_API_KEY environment variable (or Streamlit Cloud secret).
"""

from __future__ import annotations

import io
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from analyzer import FRAMEWORK_FILES, ComplianceAnalysis, analyse_document
from guard import check_request, record_run, require_access_code
from report_generator import generate_pdf

# ── Constants ────────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_MB = 10
CHUNK_THRESHOLD  = 14_000  # must match analyzer.MAX_DOC_CHARS

DISCLAIMER = (
    "**AI-assisted analysis** — results reflect only what is explicitly stated in the "
    "uploaded document. Controls implemented through verbal processes, separate systems, "
    "or supporting documentation not included in this upload will not be detected. "
    "Always validate findings with a qualified compliance professional."
)

# ── Page config ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Compliance Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Helper functions ──────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extract plain text from PDF, DOCX or TXT bytes. Cached by content + name."""
    name = file_name.lower()

    if name.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")

    if name.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except Exception as e:
            st.error(f"PDF extraction error: {e}")
            return ""

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as e:
            st.error(f"DOCX extraction error: {e}")
            return ""

    return ""


def run_analysis(document_text: str, framework: str):
    """Call Claude, store result in session_state, then render."""
    # Guard: API key must be set before any API call
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "ANTHROPIC_API_KEY is not set. "
            "Add it under **Settings → Secrets** in Streamlit Cloud, "
            "or set it as an environment variable before running locally."
        )
        st.stop()

    if framework == "All Frameworks":
        frameworks = list(FRAMEWORK_FILES.keys())
        analyses: dict[str, ComplianceAnalysis] = {}
        errors: dict[str, str] = {}

        with st.spinner("Analysing against all frameworks in parallel… this may take 60–90 seconds."):
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(analyse_document, document_text, fw): fw
                    for fw in frameworks
                }
                for future in as_completed(futures):
                    fw = futures[future]
                    try:
                        analyses[fw] = future.result()
                    except Exception:
                        errors[fw] = traceback.format_exc()

        for fw, tb in errors.items():
            st.error(f"Analysis failed for {fw}. See details below.")
            st.code(tb)

        if not analyses:
            st.stop()

        st.session_state["analyses"] = analyses
        st.session_state.pop("analysis", None)
        record_run(document_text)
        st.success(f"Analysis complete! ({len(analyses)}/{len(frameworks)} frameworks)")
        render_all_results(analyses)

    else:
        with st.spinner(f"Analysing document against {framework}… this may take 30–60 seconds."):
            try:
                analysis: ComplianceAnalysis = analyse_document(document_text, framework)
                st.session_state["analysis"] = analysis
                st.session_state.pop("analyses", None)
            except Exception:
                st.error("Analysis failed. See details below.")
                st.code(traceback.format_exc())
                st.stop()

        record_run(document_text)
        st.success("Analysis complete!")
        render_results(analysis)


def render_all_results(analyses: dict):
    """Render results for multiple frameworks in tabs."""
    tabs = st.tabs(list(analyses.keys()))
    for tab, (fw_name, analysis) in zip(tabs, analyses.items()):
        with tab:
            render_results(analysis)


def render_results(analysis: ComplianceAnalysis):
    """Render the full analysis UI for a single framework."""

    # ── Disclaimer ────────────────────────────────────────────────────────────────
    st.info(DISCLAIMER)

    # ── Truncation / chunking notice ──────────────────────────────────────────────
    if getattr(analysis, "truncated", False):
        st.warning(
            "This document exceeded 14,000 characters and was analysed in multiple sections. "
            "Results have been merged automatically — consider splitting the document for highest accuracy."
        )

    # ── Score banner ──────────────────────────────────────────────────────────────
    score = analysis.overall_score
    label = "Good" if score >= 75 else ("Needs Improvement" if score >= 50 else "Critical Gaps")

    col_score, col_meta = st.columns([1, 3])
    with col_score:
        st.metric(label=f"Compliance Score ({label})", value=f"{score}/100")
    with col_meta:
        total         = len(analysis.findings)
        compliant     = sum(1 for f in analysis.findings if f.status == "Compliant")
        partial       = sum(1 for f in analysis.findings if f.status == "Partial")
        non_compliant = sum(1 for f in analysis.findings if f.status == "Non-compliant")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Requirements", total)
        c2.metric("Compliant", compliant)
        c3.metric("Partial", partial)
        c4.metric("Non-compliant", non_compliant)

    # ── Document summary ──────────────────────────────────────────────────────────
    with st.expander("Document Summary", expanded=True):
        st.write(analysis.document_summary)

    # ── Key gaps & priority actions ───────────────────────────────────────────────
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
        key=f"filter_{analysis.framework_name}",
    )

    findings = [f for f in analysis.findings if not status_filter or f.status in status_filter]

    if not findings:
        st.info("No findings match the selected filter.")
    else:
        for finding in findings:
            status_emoji = {
                "Compliant": "✅", "Partial": "⚠️",
                "Non-compliant": "❌", "Not Applicable": "⬜",
            }.get(finding.status, "")
            risk_emoji = {
                "High": "🔴", "Medium": "🟠", "Low": "🟡", "N/A": "⚪",
            }.get(finding.risk_level, "")
            confidence = getattr(finding, "confidence", None)
            confidence_str = f"  _(confidence: {confidence}%)_" if confidence is not None else ""

            with st.expander(
                f"{status_emoji} [{finding.requirement_id}] {finding.requirement_name} "
                f"— {finding.status} {risk_emoji} {finding.risk_level}{confidence_str}",
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

    if st.button("Generate PDF Report", type="secondary", key=f"pdf_{analysis.framework_name}"):
        with st.spinner("Generating PDF…"):
            pdf_bytes = generate_pdf(analysis)
        filename = f"compliance_report_{analysis.framework_name.replace(' ', '_').lower()}.pdf"
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key=f"dl_{analysis.framework_name}",
        )


def render_landing():
    """Show instructions before any file is uploaded."""
    st.markdown(
        """
        ### How it works

        1. **Upload** your security policy, data protection policy, or any relevant document
        2. **Select** a compliance framework — or choose **All Frameworks** to run all three at once
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

        ### Limitations & Scope

        This tool performs **AI-assisted** document analysis — it reads what is written and
        compares it to framework requirements. It cannot:
        - Audit live systems, databases, or infrastructure
        - Detect verbal policies or undocumented controls
        - Replace a formal compliance audit or legal review

        Results should be treated as a **structured starting point**, not a definitive compliance verdict.
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
        options=["All Frameworks"] + list(FRAMEWORK_FILES.keys()),
        help="Choose a single framework or 'All Frameworks' to run all three in parallel.",
    )

    st.divider()
    st.subheader("2. Upload Document")
    uploaded_file = st.file_uploader(
        "Upload your policy or security document",
        type=["pdf", "txt", "docx"],
        help="PDF, Word (.docx), or plain text. Max 10 MB.",
    )

    st.divider()
    st.markdown(
        """
        **What this tool does:**
        - Extracts text from your document
        - Analyses each requirement
        - Scores compliance (0–100)
        - Shows AI confidence per finding
        - Exports a professional PDF report
        """
    )

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY not set. Add it before running.")


# ── Main area ─────────────────────────────────────────────────────────────────────

if not require_access_code():
    st.stop()

st.header("Gap Analysis Report")

if uploaded_file is None:
    render_landing()
else:
    # File size guard
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(
            f"File too large ({uploaded_file.size / 1024 / 1024:.1f} MB). "
            f"Maximum size is {MAX_FILE_SIZE_MB} MB."
        )
        st.stop()

    # Reset cached results when a different file is uploaded
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("_file_key") != file_key:
        st.session_state.pop("analysis", None)
        st.session_state.pop("analyses", None)
        st.session_state["_file_key"] = file_key

    # Read file bytes once and pass to cached extractor
    file_bytes = uploaded_file.read()
    document_text = extract_text(file_bytes, uploaded_file.name)

    if not document_text.strip():
        st.error(
            "Could not extract text from the uploaded file. "
            "Make sure the PDF is not scanned/image-only, or try converting to .txt."
        )
        st.stop()

    col1, col2 = st.columns([2, 1])
    with col1:
        base_msg = f"Document loaded: **{uploaded_file.name}** ({len(document_text):,} characters)"
        if len(document_text) > CHUNK_THRESHOLD:
            st.warning(
                f"{base_msg}  \nDocument exceeds {CHUNK_THRESHOLD:,} characters — "
                "it will be analysed in chunks and results merged automatically."
            )
        else:
            st.success(base_msg)
    with col2:
        analyse_btn = st.button(
            "Run Compliance Analysis", type="primary", use_container_width=True
        )

    if analyse_btn:
        allowed, reason = check_request(document_text)
        if not allowed:
            st.error(reason)
        else:
            run_analysis(document_text, framework)
    elif "analyses" in st.session_state and framework == "All Frameworks":
        render_all_results(st.session_state["analyses"])
    elif "analysis" in st.session_state and framework != "All Frameworks":
        render_results(st.session_state["analysis"])
