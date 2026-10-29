"""Qabil engine — deterministic resume analysis, repair and rendering.

Original clean-room code. No external services, no storage: everything
is pure functions over the request's own text, so every number below
can be recomputed by hand. The score measures DOCUMENT quality only —
it is not a hiring prediction, and the page says so.
"""

import html
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "on", "of", "to",
    "we", "are", "is", "you", "your", "our", "us", "as", "at", "by", "from",
    "that", "this", "it", "be", "will", "can", "who", "what", "per", "via",
    "into", "over", "under", "about", "an", "if", "then", "than", "also",
    "experience", "years", "year", "role", "job", "work", "team",
}

ACTION_VERBS = {
    "built", "led", "managed", "improved", "increased", "reduced",
    "developed", "designed", "delivered", "launched", "created",
    "implemented", "automated", "optimized", "optimised", "analyzed",
    "analysed", "grew", "cut", "saved", "raised", "doubled", "tripled",
    "shipped", "wrote", "published", "presented", "trained", "mentored",
    "coordinated", "organized", "organised", "streamlined", "founded",
    "owned", "drove", "accelerated", "expanded", "secured", "negotiated",
    "tested", "validated", "audited", "deployed", "migrated", "integrated",
    "researched", "discovered", "identified", "solved", "fixed",
    "supported", "served", "advised", "taught", "tutored", "assisted",
    "prepared", "compiled", "reviewed", "monitored", "tracked",
    "achieved", "earned", "won", "completed", "established",
}

WEAK_OPENINGS = [
    (r"^responsible\s+for\s+", ""),
    (r"^was\s+responsible\s+for\s+", ""),
    (r"^worked\s+on\s+", ""),
    (r"^helped\s+with\s+", ""),
    (r"^i\s+", ""),
    (r"^my\s+role\s+was\s+to\s+", ""),
]

CAPS = {
    "name": 120, "target_role": 120, "email": 120, "phone": 60,
    "city": 120, "company": 120, "summary": 2000, "skills": 1000,
    "experience": 6000, "education": 2000, "job_description": 6000,
}


def check_caps(data):
    """Return an error string if any field exceeds its cap, else None."""
    for field, cap in CAPS.items():
        value = data.get(field, "")
        if len(value) > cap:
            return f"{field} exceeds {cap} characters ({len(value)} given)."
    return None


def tokenize(text):
    """Lowercase word tokens, stopwords removed, length >= 3 kept."""
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 3]


def split_bullets(experience):
    """One bullet per non-empty line, leading list markers stripped."""
    bullets = []
    for line in (experience or "").splitlines():
        line = line.strip()
        line = re.sub(r"^[-•*]\s+", "", line)
        if line:
            bullets.append(line)
    return bullets


def split_skills(skills):
    return [s.strip() for s in (skills or "").split(",") if s.strip()]


def _frac(numerator, denominator):
    return (numerator / denominator) if denominator else 0.0


def analyze(data):
    """Score a resume. Returns a dict with score, breakdown and lists.

    Weights (sum 100):
      contact 10 (email 5 + phone 5), summary 10, skills 15,
      bullets 20, quantified 15, action verbs 15, JD keywords 15.
    """
    bullets = split_bullets(data.get("experience", ""))
    skills = split_skills(data.get("skills", ""))
    summary_words = len((data.get("summary", "") or "").split())

    quantified = sum(1 for b in bullets if re.search(r"\d", b))
    action = sum(
        1 for b in bullets
        if b.split()[0].lower().strip(".,:;") in ACTION_VERBS
    ) if bullets else 0

    resume_text = " ".join([
        data.get("summary", ""), data.get("skills", ""),
        data.get("experience", ""), data.get("education", ""),
    ])
    resume_tokens = set(tokenize(resume_text))
    jd_keywords = sorted(set(tokenize(data.get("job_description", ""))))
    matched = [k for k in jd_keywords if k in resume_tokens]
    missing = [k for k in jd_keywords if k not in resume_tokens]
    coverage = _frac(len(matched), len(jd_keywords))

    summary_pts = 10 if summary_words >= 20 else (
        5 if summary_words >= 10 else (2 if summary_words >= 1 else 0))
    breakdown = {
        "contact": (5 if data.get("email", "").strip() else 0)
        + (5 if data.get("phone", "").strip() else 0),
        "summary": summary_pts,
        "skills": min(15, round(len(skills) * 15 / 8)) if skills else 0,
        "bullets": min(20, round(len(bullets) * 20 / 5)) if bullets else 0,
        "quantified": round(_frac(quantified, len(bullets)) * 15),
        "action_verbs": round(_frac(action, len(bullets)) * 15),
        "jd_keywords": round(coverage * 15),
    }
    score = min(100, sum(breakdown.values()))
    fixes = [fix_bullet(b) for b in bullets]
    return {
        "score": score,
        "breakdown": breakdown,
        "counts": {
            "bullets": len(bullets),
            "skills": len(skills),
            "summary_words": summary_words,
            "quantified_bullets": quantified,
            "action_bullets": action,
        },
        "jd": {
            "keywords_total": len(jd_keywords),
            "matched": matched,
            "missing": missing,
            "coverage": round(coverage, 4),
        },
        "bullet_fixes": fixes,
    }


def fix_bullet(bullet):
    """Rule-based repair. Never invents numbers, employers or results.

    Strips responsibility-language openings, capitalises, ends with a
    full stop. Missing numbers are FLAGGED, never fabricated.
    """
    original = bullet.strip()
    text = original
    for pattern, repl in WEAK_OPENINGS:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    text = text.strip()
    if text:
        text = text[0].upper() + text[1:]
    text = text.rstrip(".")
    if text:
        text += "."
    notes = []
    if not re.search(r"\d", original):
        notes.append("No number — add a real result (%, count, time or money saved).")
    first = original.split()[0].lower().strip(".,:;") if original.split() else ""
    if first not in ACTION_VERBS:
        notes.append("Weak opening — start with a strong action verb (Built, Led, Improved…).")
    return {"original": original, "fixed": text, "notes": notes}


def _esc(text):
    return html.escape(text or "")


def render_resume_html(data):
    """Single-column, plain selectable text, conventional headings.

    No graphics, no sidebars, no watermark, no branding line — this is
    the document the user sends to employers.
    """
    bullets = split_bullets(data.get("experience", ""))
    skills = split_skills(data.get("skills", ""))
    edu = [l.strip() for l in (data.get("education", "") or "").splitlines() if l.strip()]
    contact = " | ".join(
        p for p in [data.get("email", "").strip(), data.get("phone", "").strip(),
                    data.get("city", "").strip()] if p)
    parts = [f"<h1>{_esc(data.get('name', ''))}</h1>"]
    if data.get("target_role", "").strip():
        parts.append(f"<p class='role'>{_esc(data['target_role'])}</p>")
    if contact:
        parts.append(f"<p class='contact'>{_esc(contact)}</p>")
    if data.get("summary", "").strip():
        parts.append(f"<h2>Summary</h2><p>{_esc(data['summary'])}</p>")
    if skills:
        parts.append("<h2>Skills</h2><p>" + ", ".join(_esc(s) for s in skills) + "</p>")
    if bullets:
        parts.append("<h2>Experience</h2><ul>" + "".join(
            f"<li>{_esc(b)}</li>" for b in bullets) + "</ul>")
    if edu:
        parts.append("<h2>Education</h2><ul>" + "".join(
            f"<li>{_esc(e)}</li>" for e in edu) + "</ul>")
    return "\n".join(parts)


def render_plain_text(data):
    """Plain-text version for the ATS paste test / .txt download."""
    bullets = split_bullets(data.get("experience", ""))
    skills = split_skills(data.get("skills", ""))
    edu = [l.strip() for l in (data.get("education", "") or "").splitlines() if l.strip()]
    lines = [data.get("name", "").strip()]
    if data.get("target_role", "").strip():
        lines.append(data["target_role"].strip())
    contact = " | ".join(
        p for p in [data.get("email", "").strip(), data.get("phone", "").strip(),
                    data.get("city", "").strip()] if p)
    if contact:
        lines.append(contact)
    if data.get("summary", "").strip():
        lines += ["", "SUMMARY", data["summary"].strip()]
    if skills:
        lines += ["", "SKILLS", ", ".join(skills)]
    if bullets:
        lines += ["", "EXPERIENCE"] + [f"- {b}" for b in bullets]
    if edu:
        lines += ["", "EDUCATION"] + [f"- {e}" for e in edu]
    return "\n".join(lines)


def cover_letter(data):
    """Cover letter from SUPPLIED facts only — nothing invented."""
    name = data.get("name", "").strip()
    role = data.get("target_role", "").strip() or "this role"
    company = data.get("company", "").strip() or "your team"
    skills = split_skills(data.get("skills", ""))[:3]
    skill_part = (", ".join(skills) if skills else "my background")
    summary = data.get("summary", "").strip()
    lines = [
        f"Dear {company} hiring team,",
        "",
        f"I am writing to apply for {role}.",
        "",
    ]
    if summary:
        lines.append(summary)
        lines.append("")
    lines += [
        f"My strengths most relevant to this role are {skill_part}.",
        "",
        "I would welcome the opportunity to discuss how I can contribute "
        "to your team. Thank you for your consideration.",
        "",
        name,
    ]
    return "\n".join(lines)
