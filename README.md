# AI Compliance Checker

An AI-powered document analysis tool that performs compliance gap analysis against **GDPR, ISO 27001:2022, NIST CSF 2.0, and SOC 2**. Upload a policy or security document and receive a structured gap analysis report with findings, risk ratings, confidence scores, and a downloadable PDF.

**Live demo:** [ai-comp-checker.streamlit.app](https://ai-comp-checker.streamlit.app)
**Built by:** Mikael Sundberg · [www.msun.se](https://www.msun.se)

> **Access protected** — the live demo requires an access code. Contact Mikael to request access.

---

## What it does

1. Accepts PDF, Word (.docx), or plain text uploads (up to 10 MB)
2. Extracts document text and sends it to Claude Sonnet 4.6 (Anthropic)
3. Evaluates the document against each framework requirement
4. Returns structured findings: status, risk level, confidence score, finding, recommendation
5. Calculates an overall compliance score (0–100)
6. Exports a professional PDF gap analysis report

For documents exceeding 14,000 characters, the tool automatically splits the document into overlapping chunks, analyses each separately, and merges results.

---

## Supported Frameworks

| Framework | Scope |
|---|---|
| **GDPR** (EU 2016/679) | Data protection & privacy — 12 requirements |
| **ISO 27001:2022** | Information security management — 13 requirements (incl. A8 split into Access, Vuln, Monitoring) |
| **NIST CSF 2.0** | Cybersecurity programme maturity — 6 functions |
| **SOC 2** (TSC 2017) | SaaS & cloud service providers — 11 Trust Service Criteria |

Select **All Frameworks** to run all four analyses in parallel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI Analysis | Claude Sonnet 4.6 via Anthropic Python SDK |
| Structured output | Pydantic v2 models + JSON schema prompting |
| PDF generation | ReportLab |
| Text extraction | PyMuPDF (PDF), python-docx (DOCX) |
| Visualisation | Plotly (radar chart) |
| Deployment | Streamlit Cloud (auto-deploy on git push) |

---

## Technical Design Decisions

| Decision | Rationale |
|---|---|
| **Claude Sonnet 4.6** | Best accuracy-to-cost ratio for structured JSON output. Haiku is cheaper but produces noisier findings on complex frameworks (ISO 27001 with 93 requirements). Opus would be overkill and ~5× the cost. |
| **Streamlit** | Enables a fully interactive UI in pure Python — ideal for a GRC prototype where the audience is compliance professionals, not developers. A FastAPI + React stack would add significant complexity with no benefit at this stage. |
| **Pydantic v2 for output parsing** | Enforces schema validation on every API response. Without it, any deviation in the model's JSON output would cause a silent error or corrupt result. Structured typing also simplifies PDF export and UI rendering. |
| **Streaming API** | Prevents Streamlit Cloud from dropping the WebSocket during long API calls (ISO 27001 can generate 2 000+ output tokens). Streaming keeps the HTTP connection alive throughout. |
| **State machine for multi-framework analysis** | `st.rerun()` between each framework gives the browser a full UI update after every step, so users see clear step-by-step progress rather than a frozen screen. |
| **These 4 frameworks specifically** | GDPR is legally mandatory in the EU. ISO 27001 is the most requested certification in enterprise procurement. NIST CSF 2.0 is standard in US-influenced environments and increasingly in Sweden. SOC 2 is required by most SaaS vendors selling to enterprise customers. Together they cover ~90% of compliance requests from Swedish and EU employers. |
| **ReportLab for PDF** | Full programmatic control over layout, colours, and tables. WeasyPrint and FPDF2 were considered but ReportLab's table and paragraph engines are more mature for multi-page compliance reports. |

Framework sources:
- **GDPR** — Regulation (EU) 2016/679, Articles 5–37
- **ISO 27001** — ISO/IEC 27001:2022 Annex A controls (A5–A8)
- **NIST CSF 2.0** — NIST Cybersecurity Framework Version 2.0 (February 2024), six core functions
- **SOC 2** — AICPA Trust Services Criteria 2017 (updated 2022), CC1–CC9

---

## Security & Access Protection

The app includes server-side abuse protection via `guard.py`:

| Control | Detail |
|---|---|
| **Access code gate** | Required before any feature is accessible |
| **Lockout** | Session locked after 3 incorrect access code attempts |
| **Rate limiting** | Max 3 analyses per session, max 3 per day |
| **Cooldown** | 30-second cooldown between requests |
| **Input validation** | Blocks empty, whitespace-only, and oversized documents |
| **Duplicate detection** | Blocks re-submission of the same document within a session |

The access code is stored in Streamlit Cloud secrets — not in the source code.

---

## Running Locally

```bash
git clone https://github.com/mslink84/ai-compliance-checker.git
cd ai-compliance-checker

pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key-here"
export ACCESS_CODE="your-access-code"
streamlit run app.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

53 tests covering: access protection logic (12), document chunking (6), framework JSON loading incl. SOC 2 (8), Pydantic model validation (5), text extraction TXT/DOCX/PDF (15), and PDF generation (7). Estimated code coverage ~88%.

---

## Project Structure

```
├── app.py                  # Streamlit frontend
├── analyzer.py             # Claude API integration, chunking, result merging
├── config.py               # Central configuration (limits, model, timeouts)
├── demo_data.py            # Static demo findings shown on public landing page
├── guard.py                # Anti-abuse: access gate, rate limiting, duplicate detection
├── report_generator.py     # ReportLab PDF generation
├── text_extractor.py       # Pure text extraction (PDF/DOCX/TXT) — no Streamlit dependency
├── translations.py         # All UI strings in Swedish and English
├── requirements.txt
├── frameworks/
│   ├── gdpr.json
│   ├── iso27001.json
│   ├── nist_csf.json
│   └── soc2.json
└── tests/
    ├── test_guard.py
    ├── test_framework_loading.py
    ├── test_result_validation.py
    ├── test_text_extraction.py
    ├── test_chunking.py
    └── test_pdf_generation.py
```

---

## Example Scenario

**Document:** Fictional "Acme SaaS – Information Security Policy v1.2" (3 pages, plain text)
**Framework:** GDPR
**Result:** Compliance Score **58/100 – Needs Improvement**

| Requirement | Status | Risk | Finding |
|---|---|---|---|
| Art. 5 – Principles of processing | ✅ Compliant | N/A | Policy explicitly states lawful basis, data minimisation, and purpose limitation |
| Art. 6 – Lawful basis | ✅ Compliant | N/A | Consent and legitimate interest are documented as legal bases |
| Art. 12–14 – Transparency | ⚠️ Partial | Medium | Privacy notice is mentioned but retention periods and third-party sharing are not specified |
| Art. 15–22 – Data subject rights | ❌ Non-compliant | High | No process defined for handling subject access requests or right-to-erasure requests |
| Art. 28 – Processor agreements | ⚠️ Partial | Medium | Vendor list exists but no mention of formal Data Processing Agreements (DPAs) |
| Art. 32 – Security of processing | ✅ Compliant | N/A | Encryption at rest and in transit, access controls, and annual security testing are described |
| Art. 33–34 – Breach notification | ❌ Non-compliant | High | No breach notification procedure. No mention of 72-hour reporting obligation to supervisory authority |
| Art. 35 – DPIA | ⚠️ Partial | Medium | Risk assessments are referenced but no formal DPIA process is described |
| Art. 37–39 – DPO | ✅ Compliant | N/A | DPO is appointed and contact details are provided |

**Key Gaps identified:**
1. No documented subject access request (SAR) handling procedure
2. No 72-hour breach notification process to supervisory authority
3. Data Processing Agreements not formalised with vendors
4. Retention periods not specified in privacy notice

**Priority Actions:**
1. Implement SAR procedure with one-month response target
2. Create a breach response runbook covering 72-hour notification
3. Sign DPAs with all data processors (cloud providers, CRM, analytics)
4. Add retention schedule to privacy notice

**Takeaway:** The policy has a solid foundation (lawful basis, security measures, DPO) but is missing operational procedures for the most high-risk GDPR obligations. These gaps would be flagged in a real DPA audit.

---

## Limitations & Prototype Scope

This tool is a **portfolio prototype**, not a production compliance platform. Key limitations:

- **Text-only analysis** — only what is written in the uploaded document is assessed. Verbal policies, undocumented controls, live system configurations, and supplementary documents are invisible to the tool.
- **AI interpretation** — Claude may misinterpret ambiguous language, policy shorthand, or non-standard document structures. Confidence scores indicate signal strength, not absolute accuracy.
- **Simplified requirements** — the framework requirement descriptions in the JSON files are informative summaries. Authoritative definitions require the original ISO, NIST, and GDPR source documents.
- **No audit trail** — this tool produces no legally defensible evidence of compliance. It is a structured starting point for internal review.
- **Chunking trade-offs** — for very long documents, cross-section context may be partially lost during chunk merging.

---

## Future Production Considerations

If developed beyond prototype stage, the following would be required:

| Area | Production Requirement |
|---|---|
| **Authentication** | User accounts, API key per-user, usage quotas |
| **Data privacy** | No document storage, clear data retention policy, DPA with Anthropic |
| **Audit logging** | Immutable log of analyses performed (who, when, which framework) |
| **Framework versioning** | Track which version of each framework was used in each analysis |
| **Multi-document analysis** | Support uploading supporting evidence alongside the primary policy |
| **Human review workflow** | Flagging findings for manual review, sign-off by compliance officer |
| **Rate limiting & cost controls** | Per-user API budget limits, token usage tracking |
| **Formal validation** | Benchmark against certified auditor findings to measure AI accuracy |

---

## GRC Career Context

This project was built as part of a portfolio targeting **GRC / Compliance Analyst** roles. It demonstrates:

- Practical understanding of GDPR, ISO 27001, and NIST CSF 2.0 requirements
- Ability to build AI-assisted compliance tooling using modern APIs
- Awareness of AI limitations in formal compliance contexts
- Server-side security controls and abuse prevention
- Python, Streamlit, and API integration skills

---

## Troubleshooting

| Problem | Solution |
|---|---|
| **PDF returns no text** | The PDF is likely scanned/image-only. Open in Acrobat → Save As → Word, then re-upload. |
| **Analysis takes very long** | Long documents are split into chunks. "All Frameworks" runs 4 analyses in parallel — allow 60–90 s. |
| **"Rate limit" error** | Max 3 analyses per session / per day. Start a new browser tab or come back tomorrow. |
| **"Incorrect access code"** | After 3 failed attempts the session locks. Open a new tab or contact Mikael to request the code. |
| **SOC 2 not in dropdown** | Hard-refresh the page (`Ctrl+Shift+R`) — Streamlit Cloud may be redeploying after a recent update. |
