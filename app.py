"""
app.py – Streamlit frontend for the AI Compliance Checker.

Run with:
    streamlit run app.py

Requires ANTHROPIC_API_KEY environment variable (or Streamlit Cloud secret).
Swedish is the default UI language; switch via the flag button at the top.
"""

from __future__ import annotations

import os
import traceback

import plotly.graph_objects as go
import streamlit as st

from analyzer import FRAMEWORK_FILES, MAX_DOC_CHARS, ComplianceAnalysis, analyse_document
from config import MAX_FILE_SIZE_MB
from demo_data import DEMO_FINDINGS, DEMO_SCORE
from guard import check_request, record_run, require_access_code
from report_generator import generate_pdf
from translations import t

# ── Constants ────────────────────────────────────────────────────────────────────


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

    /* ── Language toggle button ──────────────────────────────────── */
    .lang-btn > button {
        background-color: transparent !important;
        border: 1px solid var(--border) !important;
        color: var(--tx2) !important;
        font-size: .8rem !important;
        min-height: 32px !important;
        padding: .2rem .75rem !important;
        border-radius: 20px !important;
    }
    .lang-btn > button:hover {
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

# ── Language initialisation (must happen before any t() call) ─────────────────────

if "_lang" not in st.session_state:
    st.session_state["_lang"] = "sv"   # Swedish default

# ── Language toggle (always visible – top-right corner) ───────────────────────────

_, _col_lang = st.columns([11, 1])
with _col_lang:
    st.markdown('<div class="lang-btn">', unsafe_allow_html=True)
    if st.button(t("lang_toggle"), key="_lang_btn", help="Switch language / Byt språk"):
        st.session_state["_lang"] = "en" if st.session_state["_lang"] == "sv" else "sv"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(t("api_key_missing"))
        st.stop()

    if framework == "All Frameworks":
        # Kick off the step-by-step state machine (one framework per rerun)
        frameworks = list(FRAMEWORK_FILES.keys())
        st.session_state["_fw_idx"]     = 0
        st.session_state["_fw_results"] = {}
        st.session_state["_fw_errors"]  = {}
        st.session_state["_fw_doc"]     = document_text
        st.session_state["_fw_running"] = True
        st.rerun()

    else:
        with st.spinner(t("spinner_single", fw=framework)):
            try:
                analysis: ComplianceAnalysis = analyse_document(document_text, framework)
                st.session_state["analysis"] = analysis
                st.session_state.pop("analyses", None)
            except Exception:
                st.error(t("analysis_failed"))
                st.code(traceback.format_exc())
                st.stop()

        record_run(document_text)
        st.success(t("analysis_complete"))
        render_results(analysis)


def step_fw_analysis() -> None:
    """Run one framework from the session-state queue, then rerun or finish."""
    frameworks = list(FRAMEWORK_FILES.keys())
    idx     = st.session_state["_fw_idx"]
    results = st.session_state["_fw_results"]
    errors  = st.session_state["_fw_errors"]
    doc     = st.session_state["_fw_doc"]
    total   = len(frameworks)

    if idx < total:
        fw = frameworks[idx]
        st.progress(idx / total)
        st.info(t("spinner_fw", fw=fw, n=idx + 1, total=total))
        token_counter = st.empty()
        token_counter.caption("⏳ Väntar på svar från Claude…")

        def _on_token(n: int) -> None:
            token_counter.caption(f"⚡ {n:,} tecken mottagna…")

        try:
            results[fw] = analyse_document(doc, fw, on_token=_on_token)
        except Exception:
            errors[fw] = traceback.format_exc()

        st.session_state["_fw_idx"]     = idx + 1
        st.session_state["_fw_results"] = results
        st.session_state["_fw_errors"]  = errors
        st.rerun()

    else:
        # All frameworks done
        st.session_state["_fw_running"] = False
        for fw, tb in errors.items():
            st.error(t("analysis_failed_fw", fw=fw))
            st.code(tb)
        if not results:
            st.stop()
        st.session_state["analyses"] = results
        st.session_state.pop("analysis", None)
        record_run(doc)
        st.success(t("analysis_complete_all", done=len(results), total=total))
        render_all_results(results)


def render_all_results(analyses: dict):
    """Render results for multiple frameworks in tabs, preceded by a radar chart."""
    # ── Radar chart ───────────────────────────────────────────────────────────────
    if len(analyses) > 1:
        labels = list(analyses.keys())
        scores = [a.overall_score for a in analyses.values()]
        # Close the polygon
        labels_closed = labels + [labels[0]]
        scores_closed = scores + [scores[0]]

        fig = go.Figure(go.Scatterpolar(
            r=scores_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(74,127,212,0.25)",
            line=dict(color="#4a7fd4", width=2),
            marker=dict(size=7, color="#79b8ff"),
            hovertemplate="%{theta}: %{r}/100<extra></extra>",
        ))
        fig.update_layout(
            polar=dict(
                bgcolor="#161b22",
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    tickfont=dict(color="#8b949e", size=10),
                    gridcolor="#30363d", linecolor="#30363d",
                ),
                angularaxis=dict(
                    tickfont=dict(color="#c9d1d9", size=12),
                    gridcolor="#30363d", linecolor="#30363d",
                ),
            ),
            paper_bgcolor="#0d1117",
            font=dict(color="#c9d1d9"),
            title=dict(text=t("radar_title"), font=dict(color="#79b8ff", size=14)),
            margin=dict(l=60, r=60, t=60, b=40),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Per-framework tabs ────────────────────────────────────────────────────────
    tabs = st.tabs(list(analyses.keys()))
    for tab, (fw_name, analysis) in zip(tabs, analyses.items()):
        with tab:
            render_results(analysis)


def render_results(analysis: ComplianceAnalysis):
    """Render the full analysis UI for a single framework."""

    # ── Disclaimer ────────────────────────────────────────────────────────────────
    st.info(t("disclaimer"))

    # ── Truncation / chunking notice ──────────────────────────────────────────────
    if getattr(analysis, "truncated", False):
        st.warning(t("truncation_warning"))

    # ── Score banner ──────────────────────────────────────────────────────────────
    score = analysis.overall_score
    if score >= 75:
        label, colour = t("score_good"), "#3fb950"
    elif score >= 50:
        label, colour = t("score_needs_improvement"), "#d29922"
    else:
        label, colour = t("score_critical"), "#f85149"

    st.markdown(f"""
    <div class="score-hero">
        <div class="score-num" style="color:{colour}">{score}<span style="font-size:.5em;color:#8b949e">/100</span></div>
        <div class="score-label">{t("score_label")} — <strong style="color:{colour}">{label}</strong></div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(score / 100)

    total         = len(analysis.findings)
    compliant     = sum(1 for f in analysis.findings if f.status == "Compliant")
    partial       = sum(1 for f in analysis.findings if f.status == "Partial")
    non_compliant = sum(1 for f in analysis.findings if f.status == "Non-compliant")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("metric_total"), total)
    c2.metric(t("metric_compliant"), compliant)
    c3.metric(t("metric_partial"), partial)
    c4.metric(t("metric_non_compliant"), non_compliant)

    # ── Document summary ──────────────────────────────────────────────────────────
    with st.expander(t("doc_summary"), expanded=True):
        st.write(analysis.document_summary)

    # ── Key gaps & priority actions ───────────────────────────────────────────────
    col_gaps, col_actions = st.columns(2)
    with col_gaps:
        st.subheader(t("key_gaps"))
        for gap in analysis.key_gaps:
            st.markdown(f"- {gap}")
    with col_actions:
        st.subheader(t("priority_actions"))
        for i, action in enumerate(analysis.priority_actions, 1):
            st.markdown(f"{i}. {action}")

    st.divider()

    # ── Detailed findings ─────────────────────────────────────────────────────────
    st.subheader(t("detailed_findings"))

    # Status values stay English (they come from AI); only display label is translated
    status_options = ["Compliant", "Partial", "Non-compliant", "Not Applicable"]
    status_labels  = {s: t(f"status_{s}") for s in status_options}

    status_filter = st.multiselect(
        t("filter_label"),
        status_options,
        default=["Partial", "Non-compliant"],
        format_func=lambda s: status_labels[s],
        key=f"filter_{analysis.framework_name}",
    )

    findings = [f for f in analysis.findings if not status_filter or f.status in status_filter]

    if not findings:
        st.info(t("no_findings"))
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
            confidence_str = f"  _({t('confidence_label')}: {confidence}%)_" if confidence is not None else ""

            with st.expander(
                f"{status_emoji} [{finding.requirement_id}] {finding.requirement_name} "
                f"— {t(f'status_{finding.status}')} {risk_emoji} {finding.risk_level}{confidence_str}",
                expanded=(finding.status == "Non-compliant"),
            ):
                col_f, col_r = st.columns(2)
                with col_f:
                    st.markdown(t("finding_col"))
                    st.write(finding.finding)
                with col_r:
                    st.markdown(t("recommendation_col"))
                    st.write(finding.recommendation)

    # ── PDF export ────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader(t("export_heading"))

    if st.button(t("pdf_btn"), type="secondary", key=f"pdf_{analysis.framework_name}"):
        with st.spinner(t("pdf_spinner")):
            pdf_bytes = generate_pdf(analysis)
        filename = f"compliance_report_{analysis.framework_name.replace(' ', '_').lower()}.pdf"
        st.download_button(
            label=t("pdf_download"),
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key=f"dl_{analysis.framework_name}",
        )


def render_public_landing():
    """Public showcase page — visible before authentication."""
    st.markdown(f"""
    <div style="padding:.5rem 0 1.5rem">
        <h1 style="margin:0 0 .4rem;background:linear-gradient(90deg,#79b8ff,#4a7fd4);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent">
            🛡️ AI Compliance Checker
        </h1>
        <p style="color:#79b8ff;font-size:1.05rem;margin:0 0 .5rem;font-weight:600">
            {t("public_tagline")}
        </p>
        <p style="color:#8b949e;font-size:.95rem;margin:0;max-width:680px">
            {t("public_hero_text")}
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_feat, col_fw = st.columns([1, 1])
    with col_feat:
        st.markdown(t("how_it_works"))
        st.markdown(f"""
        <div class="feature-card"><h4>{t("step1_title")}</h4><p>{t("step1_text")}</p></div>
        <div class="feature-card"><h4>{t("step2_title")}</h4><p>{t("step2_text")}</p></div>
        <div class="feature-card"><h4>{t("step3_title")}</h4><p>{t("step3_text")}</p></div>
        <div class="feature-card"><h4>{t("step4_title")}</h4><p>{t("step4_text")}</p></div>
        """, unsafe_allow_html=True)
    with col_fw:
        st.markdown(t("supported_fw"))
        st.markdown(f"""
        <div class="feature-card"><h4>🇪🇺 GDPR</h4><p>{t("fw_gdpr_desc")}</p></div>
        <div class="feature-card"><h4>🔒 ISO 27001:2022</h4><p>{t("fw_iso_desc")}</p></div>
        <div class="feature-card"><h4>🇺🇸 NIST CSF 2.0</h4><p>{t("fw_nist_desc")}</p></div>
        <div class="feature-card"><h4>🛡️ SOC 2 (TSC 2017)</h4><p>{t("fw_soc2_desc")}</p></div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Demo output section ───────────────────────────────────────────────────────
    st.markdown(t("demo_heading"))
    st.caption(t("demo_subtext"))

    status_colors = {
        "Compliant":     ("#1a7f37", "#dcffe4", t("demo_badge_compliant")),
        "Partial":       ("#9a6700", "#fff8c5", t("demo_badge_partial")),
        "Non-compliant": ("#cf222e", "#ffebe9", t("demo_badge_noncompliant")),
    }

    col_score, col_findings = st.columns([1, 2])
    with col_score:
        st.markdown(f"**{t('demo_score_label')}**")
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem;background:#1c2128;border:1px solid #30363d;
                    border-radius:12px;margin-bottom:.5rem">
            <div style="font-size:3rem;font-weight:700;
                        background:linear-gradient(90deg,#79b8ff,#4a7fd4);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent">
                {DEMO_SCORE}
            </div>
            <div style="color:#8b949e;font-size:.85rem">/ 100 — GDPR</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(DEMO_SCORE / 100)

    with col_findings:
        st.markdown(f"**{t('demo_findings_label')}**")
        for f in DEMO_FINDINGS:
            bg, fg, badge = status_colors.get(f["status"], ("#30363d", "#c9d1d9", f["status"]))
            risk_color = {"High": "#cf222e", "Medium": "#9a6700", "Low": "#1a7f37", "N/A": "#57606a"}.get(f["risk_level"], "#57606a")
            with st.expander(
                f"{badge}  [{f['id']}] {f['name']}",
                expanded=(f["status"] == "Non-compliant"),
            ):
                st.markdown(f"**{t('demo_finding_label')}:** {f['finding']}")
                st.markdown(f"**{t('demo_rec_label')}:** {f['recommendation']}")
                st.markdown(
                    f"<span style='color:{risk_color};font-size:.8rem'>"
                    f"⬤ {t('demo_risk_label')}: {f['risk_level']}</span>&nbsp;&nbsp;"
                    f"<span style='color:#57606a;font-size:.8rem'>"
                    f"{t('demo_confidence_label')}: {f['confidence']}%</span>",
                    unsafe_allow_html=True,
                )

    st.divider()

    col_about, col_gate = st.columns([1, 1])
    with col_about:
        st.markdown(t("public_built_heading"))
        st.markdown(t("public_built_text"))
    with col_gate:
        st.markdown(t("public_gate_heading"))
        st.markdown(t("public_gate_text"))
        st.markdown("")


def render_landing():
    """Show instructions before any file is uploaded (authenticated users)."""
    st.markdown(f"""
    <div style="margin-bottom:2rem">
        <p style="color:#8b949e;font-size:1rem;margin-top:-.5rem">{t("page_subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(t("how_it_works"))
    st.markdown(f"""
    <div class="feature-card">
        <h4>{t("step1_title")}</h4>
        <p>{t("step1_text")}</p>
    </div>
    <div class="feature-card">
        <h4>{t("step2_title")}</h4>
        <p>{t("step2_text")}</p>
    </div>
    <div class="feature-card">
        <h4>{t("step3_title")}</h4>
        <p>{t("step3_text")}</p>
    </div>
    <div class="feature-card">
        <h4>{t("step4_title")}</h4>
        <p>{t("step4_text")}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(t("supported_fw"))
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="feature-card">
            <h4>🇪🇺 GDPR</h4>
            <p>{t("fw_gdpr_desc")}</p>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="feature-card">
            <h4>🇺🇸 NIST CSF 2.0</h4>
            <p>{t("fw_nist_desc")}</p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="feature-card">
            <h4>🔒 ISO 27001:2022</h4>
            <p>{t("fw_iso_desc")}</p>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="feature-card">
            <h4>🛡️ SOC 2 (TSC 2017)</h4>
            <p>{t("fw_soc2_desc")}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:1.5rem;padding:1rem 1.25rem;background:#1c2128;border:1px solid #30363d;
                border-left:4px solid #388bfd;border-radius:8px;color:#8b949e;font-size:.88rem">
        <strong style="color:#79b8ff">{t("limitations_title")}</strong> — {t("limitations_text")}
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar (info only – no interactive controls) ─────────────────────────────────

with st.sidebar:
    st.title("AI Compliance Checker")
    st.caption("Mikael Sundberg · [www.msun.se](https://www.msun.se)")
    st.divider()
    st.markdown(t("sidebar_what"))
    st.markdown(t("sidebar_bullets"))
    st.markdown("")
    st.markdown(t("sidebar_fw_label"))
    st.markdown("GDPR · ISO 27001 · NIST CSF 2.0 · SOC 2")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning(t("sidebar_api_warning"))


# ── Main area ─────────────────────────────────────────────────────────────────────

# Show public landing (with access gate) to unauthenticated visitors
if not st.session_state.get("_g_authed", False):
    render_public_landing()
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

# ── Step 1 + 2: Framework selector and file uploader ──────────────────────────────

col_fw, col_up = st.columns([1, 2])
with col_fw:
    framework = st.selectbox(
        t("fw_selector_label"),
        options=["All Frameworks"] + list(FRAMEWORK_FILES.keys()),
        format_func=lambda x: t("all_frameworks") if x == "All Frameworks" else x,
        help=t("fw_selector_help"),
    )
with col_up:
    uploaded_file = st.file_uploader(
        t("uploader_label"),
        type=["pdf", "txt", "docx"],
        label_visibility="visible",
    )

st.divider()

if uploaded_file is None:
    render_landing()
else:
    # File size guard
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(t("file_too_large", size=uploaded_file.size / 1024 / 1024, max=MAX_FILE_SIZE_MB))
        st.stop()

    # Reset cached results when a different file is uploaded
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("_file_key") != file_key:
        st.session_state.pop("analysis", None)
        st.session_state.pop("analyses", None)
        st.session_state["_fw_running"] = False
        st.session_state["_file_key"] = file_key

    # Read file bytes once and pass to cached extractor
    file_bytes = uploaded_file.read()
    document_text = extract_text(file_bytes, uploaded_file.name)

    if not document_text.strip():
        name_lower = uploaded_file.name.lower()
        if name_lower.endswith(".pdf"):
            st.error(t("pdf_no_text"))
        elif name_lower.endswith(".docx"):
            st.error(t("docx_error"))
        else:
            st.error(t("file_empty"))
        st.stop()

    if len(document_text) > MAX_DOC_CHARS:
        st.warning(t("doc_chunked", name=uploaded_file.name,
                     chars=len(document_text), max=MAX_DOC_CHARS))
    else:
        st.success(t("doc_loaded", name=uploaded_file.name, chars=len(document_text)))

    # ── GDPR data processing notice ───────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin:.75rem 0 .5rem;padding:.75rem 1rem;background:#1c2128;border:1px solid #30363d;
                border-left:4px solid #388bfd;border-radius:8px;font-size:.85rem;color:#8b949e">
        <strong style="color:#79b8ff">{t("data_notice_heading")}</strong> — {t("data_notice_text")}
    </div>
    """, unsafe_allow_html=True)

    data_consent = st.checkbox(t("data_consent_label"), key="_data_consent")

    _, col_btn = st.columns([3, 1])
    with col_btn:
        analyse_btn = st.button(
            t("analyse_btn"), type="primary", use_container_width=True
        )

    if st.session_state.get("_fw_running"):
        step_fw_analysis()
    elif analyse_btn:
        if not data_consent:
            st.error(t("data_consent_required"))
        else:
            allowed, reason = check_request(document_text)
            if not allowed:
                st.error(reason)
            else:
                run_analysis(document_text, framework)
    elif "analyses" in st.session_state and framework == "All Frameworks":
        render_all_results(st.session_state["analyses"])
    elif "analysis" in st.session_state and framework != "All Frameworks":
        render_results(st.session_state["analysis"])
