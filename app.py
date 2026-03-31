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

# ── CSS injection ─────────────────────────────────────────────────────────────────

def _inject_css():
    st.markdown("""
    <style>

    /* ── Hide Streamlit chrome ───────────────────────────────────── */
    #MainMenu          {visibility: hidden;}
    footer             {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}

    /* ── CSS variables ───────────────────────────────────────────── */
    :root {
        --bg:       #0d1117;
        --bg2:      #161b22;
        --card:     #1c2128;
        --border:   #30363d;
        --accent:   #4a7fd4;
        --accent2:  #79b8ff;
        --tx:       #e6edf3;
        --tx2:      #8b949e;
        --green:    #3fb950;
        --amber:    #d29922;
        --red:      #f85149;
        --blue:     #388bfd;
        --r:        8px;
    }

    /* ── App background ──────────────────────────────────────────── */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main {
        background-color: var(--bg) !important;
    }

    .main .block-container {
        padding: 1.5rem 2rem 3rem !important;
        max-width: 1100px !important;
    }

    /* ── Sidebar ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--bg2) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebarContent"] {
        padding: 1.5rem 1.25rem !important;
    }

    /* ── Top header bar ──────────────────────────────────────────── */
    [data-testid="stHeader"] {
        background-color: var(--bg) !important;
        border-bottom: 1px solid var(--border) !important;
    }

    /* ── Headings ────────────────────────────────────────────────── */
    h1 { font-size: clamp(1.4rem, 4vw, 2rem)   !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    h2 { font-size: clamp(1.1rem, 3vw, 1.5rem) !important; font-weight: 600 !important; }
    h3 { font-size: clamp(1rem,  2.5vw, 1.2rem)!important; font-weight: 600 !important; }

    /* ── Metric cards ────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
        padding: 1rem 1.25rem !important;
        transition: border-color .2s;
    }
    [data-testid="metric-container"]:hover {
        border-color: var(--accent) !important;
    }
    [data-testid="stMetricLabel"] {
        color: var(--tx2) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: .06em;
    }
    [data-testid="stMetricValue"] {
        color: var(--tx) !important;
        font-size: clamp(1.3rem, 4vw, 1.9rem) !important;
        font-weight: 700 !important;
    }

    /* ── Progress bar (score) ────────────────────────────────────── */
    [data-testid="stProgress"] > div > div > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
        border-radius: 4px !important;
    }
    [data-testid="stProgress"] > div > div > div {
        background-color: var(--border) !important;
        border-radius: 4px !important;
    }

    /* ── Buttons ─────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: var(--r) !important;
        font-weight: 600 !important;
        min-height: 44px !important;
        transition: all .2s ease !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1a3a7a 0%, var(--accent) 100%) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 2px 10px rgba(74,127,212,.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 18px rgba(74,127,212,.55) !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        color: var(--tx) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: var(--accent) !important;
        color: var(--accent2) !important;
    }

    /* ── Download button ─────────────────────────────────────────── */
    [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #1a6b3a, var(--green)) !important;
        border: none !important;
        color: #fff !important;
        border-radius: var(--r) !important;
        font-weight: 600 !important;
        min-height: 44px !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        box-shadow: 0 4px 14px rgba(63,185,80,.4) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Expanders (findings) ────────────────────────────────────── */
    [data-testid="stExpander"] {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
        margin-bottom: .5rem !important;
    }
    [data-testid="stExpander"]:hover {
        border-color: var(--accent) !important;
    }
    .streamlit-expanderHeader {
        background-color: var(--card) !important;
        color: var(--tx) !important;
        font-size: .88rem !important;
        padding: .75rem 1rem !important;
        font-weight: 500 !important;
    }
    .streamlit-expanderContent {
        background-color: var(--bg2) !important;
        border-top: 1px solid var(--border) !important;
        padding: 1rem !important;
    }

    /* ── Alerts ──────────────────────────────────────────────────── */
    [data-testid="stAlert"] {
        border-radius: var(--r) !important;
        border-left-width: 4px !important;
    }

    /* ── File uploader ───────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background-color: var(--card) !important;
        border: 2px dashed var(--border) !important;
        border-radius: var(--r) !important;
        transition: border-color .2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent) !important;
    }

    /* ── Selectbox ───────────────────────────────────────────────── */
    [data-testid="stSelectbox"] > div > div {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
    }

    /* ── Multiselect ─────────────────────────────────────────────── */
    [data-testid="stMultiSelect"] > div > div {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
    }

    /* ── Text input (access gate) ────────────────────────────────── */
    [data-testid="stTextInput"] > div > div > input {
        background-color: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
        color: var(--tx) !important;
        padding: .75rem 1rem !important;
        font-size: 1rem !important;
    }
    [data-testid="stTextInput"] > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(74,127,212,.2) !important;
    }

    /* ── Tabs ────────────────────────────────────────────────────── */
    [data-testid="stTabs"] [role="tablist"] {
        background-color: var(--bg2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--r) !important;
        padding: .25rem !important;
        gap: .25rem;
    }
    [data-testid="stTabs"] [role="tab"] {
        border-radius: 6px !important;
        color: var(--tx2) !important;
        font-weight: 500 !important;
        padding: .4rem 1rem !important;
        transition: all .2s !important;
        min-height: 44px !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background-color: var(--accent) !important;
        color: #fff !important;
    }

    /* ── Divider ─────────────────────────────────────────────────── */
    hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

    /* ── Caption ─────────────────────────────────────────────────── */
    [data-testid="stCaptionContainer"] { color: var(--tx2) !important; }

    /* ── Landing page feature cards ──────────────────────────────── */
    .feature-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--r);
        padding: 1.25rem 1.5rem;
        margin-bottom: .75rem;
        transition: border-color .2s;
    }
    .feature-card:hover { border-color: var(--accent); }
    .feature-card h4 {
        color: var(--accent2) !important;
        margin: 0 0 .4rem 0;
        font-size: 1rem;
        font-weight: 600;
    }
    .feature-card p {
        color: var(--tx2);
        margin: 0;
        font-size: .9rem;
        line-height: 1.5;
    }

    /* ── Score hero ──────────────────────────────────────────────── */
    .score-hero {
        background: linear-gradient(135deg, #1a2744 0%, var(--card) 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    .score-hero .score-num {
        font-size: clamp(2.5rem, 8vw, 4rem);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.03em;
    }
    .score-hero .score-label {
        font-size: .9rem;
        color: var(--tx2);
        margin-top: .25rem;
    }

    /* ── Mobile ──────────────────────────────────────────────────── */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem .75rem 2rem !important;
        }
        .stButton > button {
            width: 100% !important;
            font-size: 1rem !important;
        }
        /* Wrap 4-column metric rows into 2×2 grid */
        [data-testid="column"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }
        .streamlit-expanderHeader {
            font-size: .8rem !important;
        }
        [data-testid="stTabs"] [role="tab"] {
            padding: .4rem .6rem !important;
            font-size: .85rem !important;
        }
    }

    @media (max-width: 480px) {
        .main .block-container {
            padding: .75rem .5rem 2rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
        }
    }

    </style>
    """, unsafe_allow_html=True)

# ── Page config ───────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Compliance Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

_inject_css()


# ── Helper functions ──────────────────────────────────────────────────────────────

from text_extractor import extract_text as _extract_text_raw

@st.cache_data(show_spinner=False)
def extract_text(file_bytes: bytes, file_name: str) -> str:
    """Extract plain text from PDF, DOCX or TXT bytes. Cached by content + name."""
    result = _extract_text_raw(file_bytes, file_name)
    if result.startswith("[") and "error" in result:
        st.error(result)
        return ""
    return result


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
    if score >= 75:
        label, colour = "Good", "#3fb950"
    elif score >= 50:
        label, colour = "Needs Improvement", "#d29922"
    else:
        label, colour = "Critical Gaps", "#f85149"

    st.markdown(f"""
    <div class="score-hero">
        <div class="score-num" style="color:{colour}">{score}<span style="font-size:.5em;color:#8b949e">/100</span></div>
        <div class="score-label">Compliance Score — <strong style="color:{colour}">{label}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(score / 100)

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
    st.markdown("""
    <div style="margin-bottom:2rem">
        <p style="color:#8b949e;font-size:1rem;margin-top:-.5rem">
            Upload a policy document and get an instant AI-powered gap analysis against
            GDPR, ISO 27001, or NIST CSF 2.0.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### How it works")
    st.markdown("""
    <div class="feature-card">
        <h4>① Select a framework</h4>
        <p>Choose GDPR, ISO 27001, NIST CSF 2.0 — or run all three in parallel with <strong>All Frameworks</strong>.</p>
    </div>
    <div class="feature-card">
        <h4>② Upload your document</h4>
        <p>PDF, Word (.docx), or plain text. Up to 10 MB. Long documents are split and merged automatically.</p>
    </div>
    <div class="feature-card">
        <h4>③ Get your gap analysis</h4>
        <p>Every requirement is assessed — Compliant / Partial / Non-compliant — with risk level, confidence score, and a concrete recommendation.</p>
    </div>
    <div class="feature-card">
        <h4>④ Download the PDF report</h4>
        <p>Export a professional gap analysis report to share with your team or include in audit documentation.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Supported Frameworks")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🇪🇺 GDPR</h4>
            <p>Data protection & privacy<br>12 requirements · EU organisations</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🔒 ISO 27001:2022</h4>
            <p>Information security management<br>13 requirements incl. Annex A</p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🇺🇸 NIST CSF 2.0</h4>
            <p>Cybersecurity programme maturity<br>6 functions · GV ID PR DE RS RC</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1.5rem;padding:1rem 1.25rem;background:#1c2128;border:1px solid #30363d;
                border-left:4px solid #388bfd;border-radius:8px;color:#8b949e;font-size:.88rem">
        <strong style="color:#79b8ff">ℹ️ Limitations</strong> — This tool analyses only what is written in the
        uploaded document. Verbal policies, undocumented controls, and live system configurations are not assessed.
        Results are a structured starting point, not a formal audit.
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar (info only – no interactive controls) ─────────────────────────────────

with st.sidebar:
    st.title("AI Compliance Checker")
    st.caption("Mikael Sundberg - www.msun.se")
    st.divider()
    st.markdown(
        """
        **What this tool does:**
        - Analyses policy documents against compliance frameworks
        - Scores compliance (0–100)
        - Shows risk level and AI confidence per finding
        - Exports a professional PDF report

        **Supported frameworks:**
        GDPR · ISO 27001 · NIST CSF 2.0 · SOC 2
        """
    )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY not set. Add it before running.")


# ── Main area ─────────────────────────────────────────────────────────────────────

if not require_access_code():
    st.stop()

st.markdown("""
<div style="padding:.5rem 0 1rem">
    <h1 style="margin:0;background:linear-gradient(90deg,#79b8ff,#4a7fd4);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent">
        🛡️ AI Compliance Checker
    </h1>
</div>
""", unsafe_allow_html=True)

# ── Step 1 + 2: Framework selector and file uploader always in main area ──────────

col_fw, col_up = st.columns([1, 2])
with col_fw:
    framework = st.selectbox(
        "① Compliance framework",
        options=["All Frameworks"] + list(FRAMEWORK_FILES.keys()),
        help="Choose a framework or run all at once.",
    )
with col_up:
    uploaded_file = st.file_uploader(
        "② Upload document (PDF, DOCX or TXT — max 10 MB)",
        type=["pdf", "txt", "docx"],
        label_visibility="visible",
    )

st.divider()

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
