"""
translations.py – All UI strings in Swedish (sv) and English (en).

Swedish is the default language. Language is stored in st.session_state["_lang"].
Use t("key") or t("key", var=value) everywhere in the app.
"""

from __future__ import annotations

TRANSLATIONS: dict[str, dict[str, str]] = {
    "sv": {
        # ── Language toggle ───────────────────────────────────────────────────────
        "lang_toggle":          "🇬🇧 EN",

        # ── Page / title ──────────────────────────────────────────────────────────
        "page_subtitle":        "Ladda upp ett policydokument och få en omedelbar AI-driven gapanalys mot GDPR, ISO 27001, NIST CSF 2.0 eller SOC 2.",

        # ── Public landing (unauthenticated) ──────────────────────────────────────
        "public_tagline":       "Automatiserad AI-driven compliance-gapanalys",
        "public_hero_text":     "Analysera policydokument mot GDPR, ISO 27001, NIST CSF 2.0 och SOC 2 på sekunder. Få strukturerade fynd, risknivåer, konfidanspoäng och en professionell PDF-rapport.",
        "public_features_label":"**Vad verktyget gör:**",
        "public_features":      "- Identifierar gap mot regulatoriska krav\n- Poängsätter efterlevnad 0–100\n- Visar risknivå och AI-konfidans per krav\n- Exporterar en professionell PDF-rapport\n- Stöder dokument upp till 10 MB (PDF, DOCX, TXT)",
        "public_built_heading": "#### Om projektet",
        "public_built_text":    "Byggt av **Mikael Sundberg** som ett portfolioprojekt inom GRC och AI-assisterad compliance-analys. Projektet demonstrerar praktisk förståelse för GDPR, ISO 27001, NIST CSF 2.0 och SOC 2, kombinerat med moderna AI-verktyg.\n\n🌐 [www.msun.se](https://www.msun.se)",
        "public_gate_heading":  "#### 🔐 Skyddad demo",
        "public_gate_text":     "Appen kräver en åtkomstkod. Kontakta Mikael Sundberg via [www.msun.se](https://www.msun.se) för att begära åtkomst.",

        # ── Demo output section (public landing) ──────────────────────────────────
        "demo_heading":         "#### 📊 Exempelutdata — GDPR-analys",
        "demo_subtext":         "Så här ser ett riktigt analysresultat ut (exempeldata, ingen AI-anropas).",
        "demo_score_label":     "Compliance-poäng",
        "demo_findings_label":  "Exempelfynd",
        "demo_badge_compliant": "✅ Uppfylld",
        "demo_badge_partial":   "⚠️ Delvis",
        "demo_badge_noncompliant": "❌ Ej uppfylld",
        "demo_risk_label":      "Risk",
        "demo_confidence_label":"Konfidans",
        "demo_finding_label":   "Fynd",
        "demo_rec_label":       "Rekommendation",
        # ── Radar chart ──────────────────────────────────────────────────────────
        "radar_title":              "Compliance-poäng per ramverk",
        # ── Donut chart ──────────────────────────────────────────────────────────
        "donut_title":              "Fördelning av krav",
        # ── Executive summary ─────────────────────────────────────────────────────
        "exec_summary_heading":     "Sammanfattning",
        "exec_summary_framework":   "Ramverk",
        "exec_summary_score":       "Poäng",
        "exec_summary_maturity":    "Mognadsnivå",
        "exec_summary_critical":    "Kritiska fynd",
        "exec_summary_top_action":  "Högsta prioritet",
        "exec_summary_findings_dist": "Fynd",
        # ── Remediation roadmap ───────────────────────────────────────────────────
        "roadmap_heading":          "Åtgärdsplan",
        "roadmap_phase1":           "0–30 dagar",
        "roadmap_phase2":           "30–90 dagar",
        "roadmap_phase3":           "90+ dagar",
        "roadmap_phase1_label":     "Snabbvinster",
        "roadmap_phase2_label":     "Medellång sikt",
        "roadmap_phase3_label":     "Strategiska åtgärder",
        # ── Risk matrix ──────────────────────────────────────────────────────────
        "risk_matrix_title":        "Riskmatris — Status × Risknivå",
        # ── Maturity level ───────────────────────────────────────────────────────
        "maturity_heading":         "Mognadsnivå",
        "maturity_1":               "Nivå 1 – Initial",
        "maturity_2":               "Nivå 2 – Utvecklande",
        "maturity_3":               "Nivå 3 – Definierad",
        "maturity_4":               "Nivå 4 – Hanterad",
        "maturity_5":               "Nivå 5 – Optimerad",
        "maturity_desc_1":          "Inga formella processer. Reaktiv hantering.",
        "maturity_desc_2":          "Vissa kontroller definierade, inkonsekvent tillämpade.",
        "maturity_desc_3":          "Processer dokumenterade och delvis implementerade.",
        "maturity_desc_4":          "Konsekvent implementation med mätning och uppföljning.",
        "maturity_desc_5":          "Kontinuerlig förbättring. Branschledande säkerhetsposition.",
        # ── Critical findings ────────────────────────────────────────────────────
        "critical_heading":         "🚨 Kritiska fynd — Hög risk · Ej uppfylld",
        "critical_empty":           "Inga kritiska fynd identifierade.",
        # ── CSV export ───────────────────────────────────────────────────────────
        "csv_btn":                  "Exportera CSV",
        "csv_download":             "Ladda ner rapport (.csv)",

        # ── GDPR data processing notice ───────────────────────────────────────────
        "data_notice_heading":  "ℹ️ Databehandling",
        "data_notice_text":     "Ditt dokument skickas till **Anthropic Claude API** för analys. Vi lagrar **inga** dokument. Anthropic kan använda API-anrop för att förbättra sina modeller enligt deras [användningsvillkor](https://www.anthropic.com/legal/aup). Ladda inte upp dokument med känsliga personuppgifter eller affärshemligheter.",
        "data_consent_label":   "Jag förstår och accepterar att mitt dokument behandlas av Anthropic Claude API",
        "data_consent_required":"Du måste godkänna databehandlingen för att köra analysen.",

        # ── Access gate (guard.py) ────────────────────────────────────────────────
        "gate_prompt":          "Ange åtkomstkod för att fortsätta.",
        "gate_input_label":     "Åtkomstkod",
        "gate_btn":             "Fortsätt",
        "gate_wrong_n":         "Felaktig åtkomstkod. {n} försök kvar.",
        "gate_locked":          "För många felaktiga försök — sessionen är låst. Öppna en ny flik eller kontakta [Mikael Sundberg](https://www.msun.se) för att begära åtkomst.",
        "gate_not_configured":  "Åtkomstkoden är inte konfigurerad på servern. Kontakta [Mikael Sundberg](https://www.msun.se).",

        # ── Sidebar ───────────────────────────────────────────────────────────────
        "sidebar_what":         "**Vad verktyget gör:**",
        "sidebar_bullets":      "- Analyserar policydokument mot compliance-ramverk\n- Poängsätter efterlevnad (0–100)\n- Visar risknivå och AI-konfidans per fynd\n- Exporterar en professionell PDF-rapport",
        "sidebar_fw_label":     "**Stödda ramverk:**",
        "sidebar_api_warning":  "ANTHROPIC_API_KEY ej inställd. Lägg till den innan du kör.",

        # ── Framework selector + uploader ─────────────────────────────────────────
        "all_frameworks":       "Alla ramverk",
        "fw_selector_label":    "① Compliance-ramverk",
        "fw_selector_help":     "Välj ett ramverk eller kör alla samtidigt.",
        "uploader_label":       "② Ladda upp dokument (PDF, DOCX eller TXT — max 10 MB)",

        # ── File errors ───────────────────────────────────────────────────────────
        "file_too_large":       "Filen är för stor ({size:.1f} MB). Maximal storlek är {max} MB.",
        "pdf_no_text":          "PDF:en verkar inte innehålla extraherbar text. Det beror troligen på att den är **skannad / bildbaserad**. Försök: öppna i Adobe Acrobat → Spara som → Word eller Text, ladda sedan upp igen.",
        "docx_error":           "Kunde inte läsa Word-filen. Se till att det är en vanlig .docx-fil (inte .doc eller lösenordsskyddad).",
        "file_empty":           "Filen verkar vara tom eller innehåller ingen läsbar text.",

        # ── Document loaded banner ────────────────────────────────────────────────
        "doc_loaded":           "Dokument laddat: **{name}** ({chars:,} tecken)",
        "doc_chunked":          "Dokument laddat: **{name}** ({chars:,} tecken)  \nDokumentet överstiger {max:,} tecken — det analyseras i delar och resultaten slås ihop automatiskt.",

        # ── Buttons / spinners ────────────────────────────────────────────────────
        "analyse_btn":          "Kör compliance-analys",
        "spinner_all":          "Analyserar mot alla ramverk… kan ta 60–90 sekunder.",
        "spinner_fw":           "Analyserar mot {fw}… ({n}/{total})",
        "spinner_single":       "Analyserar dokument mot {fw}… kan ta 30–60 sekunder.",

        # ── Analysis results messages ─────────────────────────────────────────────
        "analysis_complete_all":"Analys klar! ({done}/{total} ramverk)",
        "analysis_complete":    "Analys klar!",
        "analysis_failed":      "Analysen misslyckades. Se detaljer nedan.",
        "analysis_failed_fw":   "Analysen misslyckades för {fw}. Se detaljer nedan.",
        "api_key_missing":      "ANTHROPIC_API_KEY är inte inställd. Lägg till den under **Inställningar → Secrets** i Streamlit Cloud, eller ställ in den som en miljövariabel lokalt.",

        # ── Results UI ────────────────────────────────────────────────────────────
        "disclaimer":           "**AI-assisterad analys** — resultaten återspeglar enbart vad som uttryckligen framgår av det uppladdade dokumentet. Kontroller som implementeras via verbala processer, separata system eller stöddokumentation som inte inkluderats i uppladdningen kommer inte att identifieras. Validera alltid resultaten med en kvalificerad compliance-specialist.",
        "truncation_warning":   "Det här dokumentet översteg 14 000 tecken och analyserades i flera delar. Resultaten har slagits ihop automatiskt — överväg att dela upp dokumentet för högsta möjliga precision.",
        "score_good":           "Godkänd",
        "score_needs_improvement": "Behöver åtgärdas",
        "score_critical":       "Kritiska brister",
        "score_label":          "Efterlevnadspoäng",
        "metric_total":         "Antal krav",
        "metric_compliant":     "Uppfyllda",
        "metric_partial":       "Delvis uppfyllda",
        "metric_non_compliant": "Ej uppfyllda",
        "doc_summary":          "Dokumentsammanfattning",
        "key_gaps":             "Identifierade brister",
        "priority_actions":     "Rekommenderade åtgärder",
        "detailed_findings":    "Detaljerade fynd",
        "filter_label":         "Filtrera på status",
        "no_findings":          "Inga fynd matchar valt filter.",
        "finding_col":          "**Fynd**",
        "recommendation_col":   "**Rekommendation**",
        "confidence_label":     "konfidans",

        # Status labels (display only; AI always returns English values)
        "status_Compliant":     "Uppfyllt",
        "status_Partial":       "Delvis uppfyllt",
        "status_Non-compliant": "Ej uppfyllt",
        "status_Not Applicable":"Ej tillämpligt",

        # ── PDF export ────────────────────────────────────────────────────────────
        "export_heading":       "Exportera rapport",
        "pdf_btn":              "Generera PDF-rapport",
        "pdf_spinner":          "Genererar PDF…",
        "pdf_download":         "Ladda ned PDF",

        # ── Landing page ──────────────────────────────────────────────────────────
        "how_it_works":         "#### Hur fungerar det?",
        "step1_title":          "① Välj ramverk",
        "step1_text":           "Välj GDPR, ISO 27001, NIST CSF 2.0 eller SOC 2 — eller kör alla fyra parallellt med <strong>Alla ramverk</strong>.",
        "step2_title":          "② Ladda upp dokument",
        "step2_text":           "PDF, Word (.docx) eller vanlig text. Upp till 10 MB. Långa dokument delas upp och slås ihop automatiskt.",
        "step3_title":          "③ Få din gapanalys",
        "step3_text":           "Varje krav bedöms — Uppfyllt / Delvis uppfyllt / Ej uppfyllt — med risknivå, konfidanspoäng och en konkret rekommendation.",
        "step4_title":          "④ Ladda ned PDF-rapport",
        "step4_text":           "Exportera en professionell gapanalysrapport att dela med teamet eller bifoga i revisionsdokumentation.",
        "supported_fw":         "#### Stödda ramverk",
        "fw_gdpr_desc":         "Dataskydd och integritet<br>12 krav · EU-organisationer",
        "fw_iso_desc":          "Informationssäkerhetshantering<br>13 krav inkl. Annex A",
        "fw_nist_desc":         "Mognadsanalys av cybersäkerhetsprogram<br>6 funktioner · GV ID PR DE RS RC",
        "fw_soc2_desc":         "SaaS och molntjänstleverantörer<br>11 Trust Service Criteria",
        "limitations_title":    "ℹ️ Begränsningar",
        "limitations_text":     "Det här verktyget analyserar enbart vad som skrivits i det uppladdade dokumentet. Verbala policyer, odokumenterade kontroller och live-systemkonfigurationer bedöms inte. Resultaten är en strukturerad startpunkt, inte en formell revision.",
    },

    "en": {
        # ── Language toggle ───────────────────────────────────────────────────────
        "lang_toggle":          "🇸🇪 SV",

        # ── Page / title ──────────────────────────────────────────────────────────
        "page_subtitle":        "Upload a policy document and get an instant AI-powered gap analysis against GDPR, ISO 27001, NIST CSF 2.0, or SOC 2.",

        # ── Public landing (unauthenticated) ──────────────────────────────────────
        "public_tagline":       "Automated AI-powered compliance gap analysis",
        "public_hero_text":     "Analyse policy documents against GDPR, ISO 27001, NIST CSF 2.0, and SOC 2 in seconds. Get structured findings, risk ratings, confidence scores, and a professional PDF report.",
        "public_features_label":"**What this tool does:**",
        "public_features":      "- Identifies gaps against regulatory requirements\n- Scores compliance 0–100\n- Shows risk level and AI confidence per requirement\n- Exports a professional PDF report\n- Supports documents up to 10 MB (PDF, DOCX, TXT)",
        "public_built_heading": "#### About this project",
        "public_built_text":    "Built by **Mikael Sundberg** as a portfolio project in GRC and AI-assisted compliance analysis. Demonstrates practical understanding of GDPR, ISO 27001, NIST CSF 2.0, and SOC 2 combined with modern AI tooling.\n\n🌐 [www.msun.se](https://www.msun.se)",
        "public_gate_heading":  "#### 🔐 Access-protected demo",
        "public_gate_text":     "This app requires an access code. Contact Mikael Sundberg via [www.msun.se](https://www.msun.se) to request access.",

        # ── Demo output section (public landing) ──────────────────────────────────
        "demo_heading":         "#### 📊 Example Output — GDPR Analysis",
        "demo_subtext":         "This is what a real analysis result looks like (sample data, no AI called).",
        "demo_score_label":     "Compliance Score",
        "demo_findings_label":  "Sample Findings",
        "demo_badge_compliant": "✅ Compliant",
        "demo_badge_partial":   "⚠️ Partial",
        "demo_badge_noncompliant": "❌ Non-compliant",
        "demo_risk_label":      "Risk",
        "demo_confidence_label":"Confidence",
        "demo_finding_label":   "Finding",
        "demo_rec_label":       "Recommendation",
        # ── Radar chart ──────────────────────────────────────────────────────────
        "radar_title":              "Compliance Score per Framework",
        # ── Donut chart ──────────────────────────────────────────────────────────
        "donut_title":              "Requirements Distribution",
        # ── Executive summary ─────────────────────────────────────────────────────
        "exec_summary_heading":     "Executive Summary",
        "exec_summary_framework":   "Framework",
        "exec_summary_score":       "Score",
        "exec_summary_maturity":    "Maturity Level",
        "exec_summary_critical":    "Critical Findings",
        "exec_summary_top_action":  "Top Priority",
        "exec_summary_findings_dist": "Findings",
        # ── Remediation roadmap ───────────────────────────────────────────────────
        "roadmap_heading":          "Remediation Roadmap",
        "roadmap_phase1":           "0–30 Days",
        "roadmap_phase2":           "30–90 Days",
        "roadmap_phase3":           "90+ Days",
        "roadmap_phase1_label":     "Quick Wins",
        "roadmap_phase2_label":     "Medium-term",
        "roadmap_phase3_label":     "Strategic",
        # ── Risk matrix ──────────────────────────────────────────────────────────
        "risk_matrix_title":        "Risk Matrix — Status × Risk Level",
        # ── Maturity level ───────────────────────────────────────────────────────
        "maturity_heading":         "Maturity Level",
        "maturity_1":               "Level 1 – Initial",
        "maturity_2":               "Level 2 – Developing",
        "maturity_3":               "Level 3 – Defined",
        "maturity_4":               "Level 4 – Managed",
        "maturity_5":               "Level 5 – Optimized",
        "maturity_desc_1":          "No formal processes. Purely reactive.",
        "maturity_desc_2":          "Some controls defined, inconsistently applied.",
        "maturity_desc_3":          "Processes documented and partially implemented.",
        "maturity_desc_4":          "Consistent implementation, measured and monitored.",
        "maturity_desc_5":          "Continuous improvement. Industry-leading security posture.",
        # ── Critical findings ────────────────────────────────────────────────────
        "critical_heading":         "🚨 Critical Findings — High Risk · Non-compliant",
        "critical_empty":           "No critical findings identified.",
        # ── CSV export ───────────────────────────────────────────────────────────
        "csv_btn":                  "Export CSV",
        "csv_download":             "Download report (.csv)",

        # ── GDPR data processing notice ───────────────────────────────────────────
        "data_notice_heading":  "ℹ️ Data processing",
        "data_notice_text":     "Your document is sent to **Anthropic Claude API** for analysis. We store **no** documents. Anthropic may use API calls to improve their models per their [usage policy](https://www.anthropic.com/legal/aup). Do not upload documents containing sensitive personal data or trade secrets.",
        "data_consent_label":   "I understand and accept that my document will be processed by Anthropic Claude API",
        "data_consent_required":"You must accept the data processing terms before running the analysis.",

        # ── Access gate (guard.py) ────────────────────────────────────────────────
        "gate_prompt":          "Please enter the access code to continue.",
        "gate_input_label":     "Access code",
        "gate_btn":             "Continue",
        "gate_wrong_n":         "Incorrect access code. {n} attempt(s) remaining.",
        "gate_locked":          "Too many incorrect attempts — this session is locked. Open a new browser tab or contact [Mikael Sundberg](https://www.msun.se) to request access.",
        "gate_not_configured":  "Access code is not configured on this server. Contact [Mikael Sundberg](https://www.msun.se) to request access.",

        # ── Sidebar ───────────────────────────────────────────────────────────────
        "sidebar_what":         "**What this tool does:**",
        "sidebar_bullets":      "- Analyses policy documents against compliance frameworks\n- Scores compliance (0–100)\n- Shows risk level and AI confidence per finding\n- Exports a professional PDF report",
        "sidebar_fw_label":     "**Supported frameworks:**",
        "sidebar_api_warning":  "ANTHROPIC_API_KEY not set. Add it before running.",

        # ── Framework selector + uploader ─────────────────────────────────────────
        "all_frameworks":       "All Frameworks",
        "fw_selector_label":    "① Compliance framework",
        "fw_selector_help":     "Choose a framework or run all at once.",
        "uploader_label":       "② Upload document (PDF, DOCX or TXT — max 10 MB)",

        # ── File errors ───────────────────────────────────────────────────────────
        "file_too_large":       "File too large ({size:.1f} MB). Maximum size is {max} MB.",
        "pdf_no_text":          "The PDF appears to contain no extractable text. This usually means it is a **scanned / image-only PDF**. Try: open in Adobe Acrobat → Save As → Word or Text, then re-upload.",
        "docx_error":           "Could not read the Word file. Make sure it is a standard .docx file (not .doc or password-protected).",
        "file_empty":           "The file appears to be empty or contains no readable text.",

        # ── Document loaded banner ────────────────────────────────────────────────
        "doc_loaded":           "Document loaded: **{name}** ({chars:,} characters)",
        "doc_chunked":          "Document loaded: **{name}** ({chars:,} characters)  \nDocument exceeds {max:,} characters — it will be analysed in chunks and results merged automatically.",

        # ── Buttons / spinners ────────────────────────────────────────────────────
        "analyse_btn":          "Run Compliance Analysis",
        "spinner_all":          "Analysing against all frameworks… this may take 60–90 seconds.",
        "spinner_fw":           "Analysing against {fw}… ({n}/{total})",
        "spinner_single":       "Analysing document against {fw}… this may take 30–60 seconds.",

        # ── Analysis results messages ─────────────────────────────────────────────
        "analysis_complete_all":"Analysis complete! ({done}/{total} frameworks)",
        "analysis_complete":    "Analysis complete!",
        "analysis_failed":      "Analysis failed. See details below.",
        "analysis_failed_fw":   "Analysis failed for {fw}. See details below.",
        "api_key_missing":      "ANTHROPIC_API_KEY is not set. Add it under **Settings → Secrets** in Streamlit Cloud, or set it as an environment variable before running locally.",

        # ── Results UI ────────────────────────────────────────────────────────────
        "disclaimer":           "**AI-assisted analysis** — results reflect only what is explicitly stated in the uploaded document. Controls implemented through verbal processes, separate systems, or supporting documentation not included in this upload will not be detected. Always validate findings with a qualified compliance professional.",
        "truncation_warning":   "This document exceeded 14,000 characters and was analysed in multiple sections. Results have been merged automatically — consider splitting the document for highest accuracy.",
        "score_good":           "Good",
        "score_needs_improvement": "Needs Improvement",
        "score_critical":       "Critical Gaps",
        "score_label":          "Compliance Score",
        "metric_total":         "Total Requirements",
        "metric_compliant":     "Compliant",
        "metric_partial":       "Partial",
        "metric_non_compliant": "Non-compliant",
        "doc_summary":          "Document Summary",
        "key_gaps":             "Key Gaps",
        "priority_actions":     "Priority Actions",
        "detailed_findings":    "Detailed Findings",
        "filter_label":         "Filter by status",
        "no_findings":          "No findings match the selected filter.",
        "finding_col":          "**Finding**",
        "recommendation_col":   "**Recommendation**",
        "confidence_label":     "confidence",

        # Status labels (display only; AI always returns English values)
        "status_Compliant":     "Compliant",
        "status_Partial":       "Partial",
        "status_Non-compliant": "Non-compliant",
        "status_Not Applicable":"Not Applicable",

        # ── PDF export ────────────────────────────────────────────────────────────
        "export_heading":       "Export Report",
        "pdf_btn":              "Generate PDF Report",
        "pdf_spinner":          "Generating PDF…",
        "pdf_download":         "Download PDF",

        # ── Landing page ──────────────────────────────────────────────────────────
        "how_it_works":         "#### How it works",
        "step1_title":          "① Select a framework",
        "step1_text":           "Choose GDPR, ISO 27001, NIST CSF 2.0, or SOC 2 — or run all four in parallel with <strong>All Frameworks</strong>.",
        "step2_title":          "② Upload your document",
        "step2_text":           "PDF, Word (.docx), or plain text. Up to 10 MB. Long documents are split and merged automatically.",
        "step3_title":          "③ Get your gap analysis",
        "step3_text":           "Every requirement is assessed — Compliant / Partial / Non-compliant — with risk level, confidence score, and a concrete recommendation.",
        "step4_title":          "④ Download the PDF report",
        "step4_text":           "Export a professional gap analysis report to share with your team or include in audit documentation.",
        "supported_fw":         "#### Supported Frameworks",
        "fw_gdpr_desc":         "Data protection & privacy<br>12 requirements · EU organisations",
        "fw_iso_desc":          "Information security management<br>13 requirements incl. Annex A",
        "fw_nist_desc":         "Cybersecurity programme maturity<br>6 functions · GV ID PR DE RS RC",
        "fw_soc2_desc":         "SaaS & cloud service providers<br>11 Trust Service Criteria",
        "limitations_title":    "ℹ️ Limitations",
        "limitations_text":     "This tool analyses only what is written in the uploaded document. Verbal policies, undocumented controls, and live system configurations are not assessed. Results are a structured starting point, not a formal audit.",
    },
}


def t(key: str, **kwargs: object) -> str:
    """Return the translated string for key in the current language."""
    import streamlit as st  # imported here to keep module testable without Streamlit context
    lang = st.session_state.get("_lang", "sv")
    sv = TRANSLATIONS["sv"]
    en = TRANSLATIONS["en"]
    text = sv.get(key) if lang == "sv" else en.get(key)
    if text is None:
        text = en.get(key) if lang == "sv" else sv.get(key)
    if text is None:
        text = f"[{key}]"
    return text.format(**kwargs) if kwargs else text
