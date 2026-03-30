# AI Compliance Checker

An AI-powered document analysis tool that performs compliance gap analysis against GDPR, ISO 27001:2022, and NIST CSF 2.0. Upload a policy or security document and receive a structured gap analysis report with findings, risk ratings, confidence scores, and a downloadable PDF.

**Live demo:** [Streamlit Cloud deployment](https://ai-compliance-checker.streamlit.app)
**Built by:** Mikael Sundberg · [www.msun.se](https://www.msun.se)

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
| **ISO 27001:2022** | Information security management — 13 requirements |
| **NIST CSF 2.0** | Cybersecurity programme maturity — 6 functions |

Select "All Frameworks" to run all three analyses in parallel.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI Analysis | Claude Sonnet 4.6 via Anthropic Python SDK |
| Structured output | Pydantic v2 models + JSON schema prompting |
| PDF generation | ReportLab |
| Text extraction | PyMuPDF (PDF), python-docx (DOCX) |
| Deployment | Streamlit Cloud (auto-deploy on git push) |

---

## Running Locally

```bash
git clone https://github.com/mslink84/ai-compliance-checker.git
cd ai-compliance-checker

pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key-here"
streamlit run app.py
```

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: framework JSON loading, Pydantic model validation, text extraction (TXT/DOCX/PDF), and PDF generation.

---

## Project Structure

```
├── app.py                  # Streamlit frontend
├── analyzer.py             # Claude API integration, chunking, result merging
├── report_generator.py     # ReportLab PDF generation
├── requirements.txt
├── frameworks/
│   ├── gdpr.json
│   ├── iso27001.json
│   └── nist_csf.json
└── tests/
    ├── test_framework_loading.py
    ├── test_result_validation.py
    ├── test_text_extraction.py
    └── test_pdf_generation.py
```

---

## Limitations & Prototype Scope

This tool is a **portfolio prototype**, not a production compliance platform. Key limitations:

- **Text-only analysis** — only what is written in the uploaded document is assessed. Verbal policies, undocumented controls, live system configurations, and supplementary documents are invisible to the tool.
- **AI interpretation** — Claude may misinterpret ambiguous language, policy shorthand, or non-standard document structures. Confidence scores indicate signal strength, not absolute accuracy.
- **Simplified requirements** — the framework requirement descriptions in the JSON files are informative summaries. Authoritative definitions require the original ISO, NIST, and GDPR source documents.
- **No audit trail** — this tool produces no legally defensible evidence of compliance. It is a structured starting point for internal review.
- **Chunking trade-offs** — for very long documents, cross-section context (e.g., a control mentioned early that qualifies a statement made late) may be partially lost during chunk merging.

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
- Python, Streamlit, and API integration skills
