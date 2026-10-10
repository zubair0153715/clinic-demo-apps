"""The 10 DRAP audit-readiness questions + scoring logic."""
import json

# (key, area, question, fix-if-no)
QUESTIONS = [
    ("sop", "Documentation",
     "Are all manufacturing SOPs documented, version-controlled, and current?",
     "Implement a document control SOP with version numbers, review dates, and approval signatures."),
    ("qc", "Quality Control",
     "Do you have a dedicated QC lab with calibrated instruments and trained analysts?",
     "Set up QC with calibrated equipment (calibration stickers + records) before the audit."),
    ("validation", "Validation",
     "Are equipment qualification records (IQ/OQ/PQ) complete for critical equipment?",
     "Run IQ/OQ/PQ protocols for autoclaves, HVAC, water systems — auditors always ask."),
    ("change", "Change Control",
     "Is there a formal change-control procedure for processes, equipment, and suppliers?",
     "Create a change-control log: every change needs risk assessment + QA approval."),
    ("capa", "Deviation / CAPA",
     "Are deviations investigated with documented CAPA (corrective & preventive actions)?",
     "Start a deviation register today — undocumented deviations are critical observations."),
    ("training", "Training",
     "Are training records maintained for all production and QC staff?",
     "Keep individual training files with SOP read-and-understood signatures."),
    ("data", "Data Integrity",
     "Is there a data-integrity policy (ALCOA+) for electronic and paper records?",
     "Restrict shared logins, enable audit trails — data integrity is DRAP's top focus area."),
    ("stability", "Stability Studies",
     "Are stability studies conducted per ICH guidelines for your products?",
     "Place at least one batch per product on long-term + accelerated stability."),
    ("bmr", "Batch Release",
     "Is every Batch Manufacturing Record reviewed by QA before product release?",
     "No BMR review = no release. Make QA sign-off mandatory in your SOP."),
    ("audit", "Audit Readiness",
     "Was your last internal/DRAP audit within 12 months with no critical observations?",
     "Run a mock audit now — a full PharmaReg AI audit finds gaps before DRAP does."),
]


def score_answers(answers) -> dict:
    """answers: list of 10 bools (True=yes). Returns score, band, gaps."""
    yes = sum(1 for a in answers[:10] if a)
    score = yes * 10
    gaps = [{"area": area, "question": q, "fix": fix}
            for (_, area, q, fix), a in zip(QUESTIONS, answers[:10]) if not a]
    if score >= 80:
        band = "ready"
        band_label = "✅ Audit-ready"
        band_text = ("Strong position. A professional mock audit will confirm you're "
                     "DRAP-ready and catch the last few gaps.")
    elif score >= 50:
        band = "gaps"
        band_label = "⚠️ Gaps to fix"
        band_text = ("You have real gaps DRAP auditors will flag. Fix the red areas below — "
                     "most are documentation fixes, not expensive ones.")
    else:
        band = "risk"
        band_label = "🔴 High risk"
        band_text = ("A DRAP inspection right now would likely produce critical observations. "
                     "Don't wait — get a professional gap assessment first.")
    return {"score": score, "band": band, "band_label": band_label,
            "band_text": band_text, "gaps": gaps}


def questions_payload():
    return [{"key": k, "area": area, "question": q}
            for (k, area, q, _) in QUESTIONS]


def dump(o) -> str:
    return json.dumps(o)
