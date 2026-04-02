"""
demo_data.py – Static sample analysis result shown on the public landing page.

No AI call is made; this is hard-coded data that gives recruiters a realistic
preview of what a real compliance analysis looks like.
"""

from __future__ import annotations

DEMO_SCORE = 58

DEMO_FINDINGS = [
    {
        "status":       "Compliant",
        "risk_level":   "N/A",
        "id":           "GDPR-Art5",
        "name":         "Principles of Processing (Art. 5)",
        "finding":      "The policy explicitly states that personal data is processed "
                        "lawfully, fairly and transparently. Data minimisation and "
                        "purpose limitation are referenced in Section 3.",
        "recommendation": "No immediate action required. Schedule annual review to "
                          "verify principles remain embedded as the data landscape evolves.",
        "confidence":   88,
    },
    {
        "status":       "Partial",
        "risk_level":   "Medium",
        "id":           "GDPR-Art32",
        "name":         "Security of Processing (Art. 32)",
        "finding":      "Encryption in transit (TLS 1.2+) and at rest (AES-256) are "
                        "mentioned. However, the policy lacks a defined key management "
                        "procedure and does not address pseudonymisation or regular "
                        "security testing requirements.",
        "recommendation": "Extend the policy with a Key Management Procedure covering "
                          "key generation, rotation (annual), storage (HSM or KMS), and "
                          "destruction. Add a requirement for annual penetration testing.",
        "confidence":   82,
    },
    {
        "status":       "Non-compliant",
        "risk_level":   "High",
        "id":           "GDPR-Art33",
        "name":         "Breach Notification to Supervisory Authority (Art. 33)",
        "finding":      "The incident response section states a 24-hour internal "
                        "reporting obligation, but makes no mention of the mandatory "
                        "72-hour notification to the supervisory authority (IMY) "
                        "required by GDPR Art. 33 in the event of a personal data breach.",
        "recommendation": "Add an explicit clause: 'In the event of a personal data "
                          "breach, the DPO must assess reportability within 24 hours and "
                          "notify IMY within 72 hours of becoming aware of the breach "
                          "(GDPR Art. 33). Maintain a breach register for all incidents "
                          "regardless of reportability.'",
        "confidence":   95,
    },
]
