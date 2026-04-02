"""
regulatory_stakes.py – Real-world consequences for High-risk Non-compliant findings.

Keyed by (framework_name, requirement_id). Shown as amber badges in the
critical findings callout to demonstrate regulatory domain depth.
"""

from __future__ import annotations

STAKES: dict[tuple[str, str], str] = {
    # ── GDPR ─────────────────────────────────────────────────────────────────────
    ("GDPR", "GDPR-Art5"):     "Administrative fine up to €20M or 4% of annual turnover — GDPR Art. 83(5)(a)",
    ("GDPR", "GDPR-Art6"):     "Processing without lawful basis — fine up to €20M or 4% turnover — GDPR Art. 83(5)(a)",
    ("GDPR", "GDPR-Art7"):     "Invalid consent renders all consent-based processing unlawful — GDPR Art. 83(5)(a)",
    ("GDPR", "GDPR-Art12-14"): "Supervisory authority enforcement action; data subjects may claim compensation — GDPR Art. 82",
    ("GDPR", "GDPR-Art15-22"): "Failure to honour data subject rights — fine up to €20M or 4% turnover — GDPR Art. 83(5)(b)",
    ("GDPR", "GDPR-Art24-25"): "Absence of Data Protection by Design — fine up to €10M or 2% turnover — GDPR Art. 83(4)",
    ("GDPR", "GDPR-Art28"):    "Processing without a valid Data Processing Agreement — joint liability risk — GDPR Art. 82(2)",
    ("GDPR", "GDPR-Art30"):    "No Record of Processing Activities — fine up to €10M or 2% turnover — GDPR Art. 83(4)",
    ("GDPR", "GDPR-Art32"):    "Inadequate security of processing — fine up to €10M or 2% turnover — GDPR Art. 83(4)",
    ("GDPR", "GDPR-Art33-34"): "Failure to notify breach within 72 hours — fine up to €20M or 4% turnover — GDPR Art. 83(5)",
    ("GDPR", "GDPR-Art35"):    "Missing DPIA for high-risk processing — fine up to €10M or 2% turnover — GDPR Art. 83(4)",
    ("GDPR", "GDPR-Art37-39"): "No DPO where mandatory — fine up to €10M or 2% turnover — GDPR Art. 83(4)",

    # ── ISO 27001 ─────────────────────────────────────────────────────────────────
    ("ISO 27001", "ISO-4"):    "Non-conformity at Clause 4 — ISO 27001 certification cannot be issued or renewed",
    ("ISO 27001", "ISO-5"):    "Major non-conformity — ISO 27001 certificate suspension or withdrawal risk",
    ("ISO 27001", "ISO-6"):    "Missing risk assessment — major non-conformity, fails ISO 27001 Clause 6.1",
    ("ISO 27001", "ISO-7"):    "Inadequate support resources — non-conformity, fails ISO 27001 Clause 7",
    ("ISO 27001", "ISO-8"):    "Annex A controls not implemented — major non-conformity in certification audit",
    ("ISO 27001", "ISO-9"):    "No internal audit programme — major non-conformity, fails ISO 27001 Clause 9.2",
    ("ISO 27001", "ISO-10"):   "No continual improvement process — non-conformity, fails ISO 27001 Clause 10",

    # ── NIST CSF 2.0 ─────────────────────────────────────────────────────────────
    ("NIST CSF 2.0", "CSF-GV"): "Governance function gap — NIST CSF Tier below Tier 2 (Risk Informed); board-level accountability missing",
    ("NIST CSF 2.0", "CSF-ID"): "Identify function gap — asset inventory and risk assessment incomplete; NIST CSF Tier 1 (Partial)",
    ("NIST CSF 2.0", "CSF-PR"): "Protect function gap — access controls and awareness training deficient; NIST CSF Tier below Tier 2",
    ("NIST CSF 2.0", "CSF-DE"): "Detect function gap — no anomaly detection or continuous monitoring; NIST CSF Tier 1 (Partial)",
    ("NIST CSF 2.0", "CSF-RS"): "Respond function gap — no incident response plan; NIST CSF Tier 1; regulatory breach timelines at risk",
    ("NIST CSF 2.0", "CSF-RC"): "Recover function gap — no business continuity or disaster recovery plan; NIST CSF Tier 1",

    # ── SOC 2 ────────────────────────────────────────────────────────────────────
    ("SOC 2", "SOC2-CC1"):     "Control Environment failure — SOC 2 Type II qualified opinion; customer contracts at risk",
    ("SOC 2", "SOC2-CC2"):     "Communication and information gap — SOC 2 audit exception; enterprise customer procurement risk",
    ("SOC 2", "SOC2-CC3"):     "Risk assessment process missing — SOC 2 Type II adverse opinion likely on CC3",
    ("SOC 2", "SOC2-CC4"):     "Monitoring activities absent — SOC 2 Type II qualified opinion; audit exception",
    ("SOC 2", "SOC2-CC5"):     "Control activities gap — SOC 2 Type II adverse opinion; SaaS vendor agreements jeopardised",
    ("SOC 2", "SOC2-CC6"):     "Logical and physical access failure — SOC 2 Type II qualification; TSC CC6.1 exception",
    ("SOC 2", "SOC2-CC7"):     "System operations monitoring gap — SOC 2 Type II qualified opinion on CC7",
    ("SOC 2", "SOC2-CC8"):     "Change management deficiency — SOC 2 Type II exception; enterprise customer trust at risk",
    ("SOC 2", "SOC2-CC9"):     "Risk mitigation failure — SOC 2 Type II adverse finding on CC9",
}
