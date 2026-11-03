"""Tarteeb engine — deterministic resume-vs-JD analysis and tailoring.

Original clean-room code. Pure functions over the request's own text:
every number below can be recomputed by hand from the two pasted texts.

The match score is an ESTIMATE of keyword/skill overlap — it is NOT a
real ATS score and NOT a hiring prediction, and the page says so.

Tailoring NEVER invents experience, skills, degrees or achievements:
it rewords, reorders and emphasises only what the user supplied.
Anything the JD asks for that the resume does not show is FLAGGED as a
gap — never filled with fabricated content.
"""

import html
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "on", "of", "to",
    "we", "are", "is", "you", "your", "our", "us", "as", "at", "by", "from",
    "that", "this", "it", "be", "will", "can", "who", "what", "per", "via",
    "into", "over", "under", "about", "if", "then", "than", "also", "not",
    "have", "has", "had", "been", "being", "do", "does", "did", "but", "so",
    "such", "no", "nor", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "only", "own", "same", "too", "very", "just",
    "should", "now", "must", "may", "might", "shall", "could", "would",
    "experience", "years", "year", "role", "job", "work", "team", "candidate",
    "responsibilities", "requirements", "qualifications", "skills", "ability",
    "strong", "excellent", "good", "working", "knowledge", "understanding",
    "including", "etc", "eg", "ie", "using", "use", "used", "well", "able",
}

GENERIC_WORDS = {
    "experience", "years", "year", "role", "job", "work", "team",
    "candidate", "responsibilities", "requirements", "qualifications",
    "skills", "ability", "strong", "excellent", "good", "working",
    "knowledge", "understanding", "including", "etc", "using", "use",
    "used", "well", "able", "must", "will", "required", "preferred",
    "plus", "bonus", "etc", "etc.", "day", "days", "week", "month",
    "remote", "hybrid", "onsite", "on-site", "full-time", "fulltime",
    "part-time", "contract", "salary", "benefits", "location", "based",
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
    "engineered", "orchestrated", "documented", "screened", "curated",
}

WEAK_OPENINGS = [
    (r"^responsible\s+for\s+", ""),
    (r"^was\s+responsible\s+for\s+", ""),
    (r"^worked\s+on\s+", ""),
    (r"^helped\s+with\s+", ""),
    (r"^i\s+", ""),
    (r"^my\s+role\s+was\s+to\s+", ""),
]

# Curated skill phrases, matched case-insensitively with word boundaries.
SKILL_LEXICON = [
    # automation / no-code
    "n8n", "zapier", "power automate", "ifttt", "airtable",
    "notion", "integromat",
    # programming
    "python", "javascript", "typescript", "java", "c++", "c#", "go",
    "rust", "sql", "r", "html", "css", "react", "node.js", "nodejs",
    "fastapi", "django", "flask", "next.js", "vue", "angular",
    # AI / ML
    "llm", "large language model", "prompt engineering", "rag",
    "retrieval augmented generation", "langgraph", "langchain", "crewai",
    "openai", "anthropic", "claude", "gpt", "gemini", "hugging face",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "transformers", "fine-tuning", "fine tuning",
    "mcp", "model context protocol", "ai agents", "multi-agent",
    "autogen", "vector database", "embeddings", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy",
    # APIs / data / infra
    "rest api", "rest apis", "api", "apis", "webhooks", "webhook", "json",
    "graphql", "databases", "database", "postgresql", "mysql", "mongodb",
    "sqlite", "redis", "docker", "kubernetes", "aws", "azure", "gcp",
    "git", "github", "ci/cd", "linux", "bash", "excel", "power bi",
    "tableau", "data analysis", "data visualization", "etl",
    "error handling", "data privacy", "gdpr", "cybersecurity",
    # pharma / regulatory / science
    "gmp", "glp", "gdp", "ctd", "ectd", "drap", "fda", "ema", "who",
    "ich", "pharmacovigilance", "regulatory affairs", "clinical trials",
    "clinical research", "drug discovery", "cheminformatics", "bioinformatics",
    "rdkit", "molecular docking", "autodock vina", "alphafold",
    "admet", "pharmacology", "pharmaceutics", "hplc", "gcp",
    "quality assurance", "quality control", "audit", "auditing",
    "sop", "validation", "documentation",
    # work / soft skills
    "communication", "teamwork", "problem solving", "critical thinking",
    "project management", "time management", "leadership", "mentoring",
    "training", "presentation", "research", "writing", "teaching",
    "customer service", "sales", "marketing", "content writing",
    "video editing", "graphic design", "figma", "canva",
]

SECTION_HEADINGS = {
    "summary": ["summary", "profile", "objective", "about", "professional summary"],
    "skills": ["skills", "technical skills", "core skills", "competencies"],
    "experience": ["experience", "work experience", "employment", "work history",
                   "projects", "research projects", "research", "key projects"],
    "education": ["education", "academic", "qualifications"],
}

CAPS = {"resume": 12000, "jd": 8000}
MAX_FILE_BYTES = 5 * 1024 * 1024


def check_caps(resume, jd):
    if len(resume or "") > CAPS["resume"]:
        return f"Resume exceeds {CAPS['resume']} characters ({len(resume)} given)."
    if len(jd or "") > CAPS["jd"]:
        return f"Job description exceeds {CAPS['jd']} characters ({len(jd)} given)."
    return None


def _norm(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def tokenize(text):
    tokens = re.findall(r"[a-z0-9][a-z0-9+\-#]*", (text or "").lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 3]


def _phrase_in(phrase, norm_text):
    pattern = r"\b" + re.escape(phrase) + r"s?\b"
    return re.search(pattern, norm_text) is not None


def extract_jd_keywords(jd):
    """JD keywords = lexicon skill phrases found in the JD (singular/plural
    duplicates merged) + signature terms: non-generic JD tokens that
    repeat (>= 2 times). Generic filler words (typically, position,
    requirements…) are never keywords — a missing-keywords list full of
    filler would be bad advice. Sorted: skills first (JD order), then
    signature terms by frequency."""
    norm = _norm(jd)
    raw_skills = [s for s in SKILL_LEXICON if _phrase_in(s, norm)]
    skills = []
    for s in raw_skills:
        # merge singular/plural variants: keep the shorter form
        if any(other != s and (other == s + "s" or s == other + "s")
               for other in raw_skills):
            if s.endswith("s") and s[:-1] in raw_skills:
                continue
        skills.append(s)
    tokens = tokenize(jd)
    counts = {}
    for t in tokens:
        if t in GENERIC_WORDS or t in skills:
            continue
        counts[t] = counts.get(t, 0) + 1
    signature = sorted(
        (t for t, c in counts.items() if c >= 2 and len(t) >= 4),
        key=lambda t: (-counts[t], t),
    )[:10]
    seen = set()
    keywords = []
    for k in skills + signature:
        if k not in seen:
            seen.add(k)
            keywords.append(k)
    return keywords, skills


def parse_resume(resume):
    """Split a pasted resume into header lines + sections.

    Returns {"header": [lines], "sections": [(kind, heading, [lines])]}.
    A section starts at a line that looks like a heading (short, known
    heading words, or ALL-CAPS). Everything before the first heading is
    the header (name/contact)."""
    lines = [l.rstrip() for l in (resume or "").splitlines()]
    header, sections = [], []
    current = None
    for raw_line in lines:
        # clean markdown: strip heading #'s and bold markers so pasted
        # markdown CVs (## Skills, **Pharm-D**) parse like plain text
        line = re.sub(r"^#{1,6}\s*", "", raw_line)
        line = line.replace("**", "")
        stripped = line.strip()
        low = stripped.lower().strip(":")
        kind = None
        for k, names in SECTION_HEADINGS.items():
            if low in names:
                kind = k
                break
        if kind is None and re.match(r"^[A-Z][A-Z\s&/]{3,40}$", stripped):
            for k, names in SECTION_HEADINGS.items():
                if stripped.lower() in names:
                    kind = k
                    break
        if kind is not None:
            current = (kind, stripped, [])
            sections.append(current)
            continue
        if current is None:
            if stripped:
                header.append(stripped)
        else:
            current[2].append(line)
    return {"header": header, "sections": sections}


def _section_lines(parsed, kind):
    out = []
    for k, _h, lines in parsed["sections"]:
        if k == kind:
            out.extend(lines)
    return out


def split_bullets(lines):
    """Flat bullet list. If the section uses list markers, ONLY marker
    lines are bullets — plain lines are project titles, not bullets.
    Otherwise (no markers at all) every non-empty line is a bullet."""
    marker = [l for l in lines if re.match(r"^\s*[-•*]\s+", l)]
    source = marker if marker else lines
    bullets = []
    for line in source:
        s = line.strip()
        s = re.sub(r"^[-•*]\s+", "", s)
        if s:
            bullets.append(s)
    return bullets


def split_bullets_grouped(lines):
    """Experience section as groups: {"title": str|None, "bullets": [...]}.
    A plain line starts a new group (project/job title); marker lines
    belong to the current group. Falls back to one bullet per line when
    no markers exist."""
    marker = [l for l in lines if re.match(r"^\s*[-•*]\s+", l)]
    if not marker:
        return [{"title": None, "bullets": split_bullets(lines)}]
    groups = []
    current = {"title": None, "bullets": []}
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if re.match(r"^[-•*]\s+", s):
            current["bullets"].append(re.sub(r"^[-•*]\s+", "", s))
        else:
            if current["bullets"] or current["title"]:
                groups.append(current)
            current = {"title": s, "bullets": []}
    if current["bullets"] or current["title"]:
        groups.append(current)
    return groups


def split_skills(lines):
    skills = []
    for line in lines:
        for part in re.split(r"[,;|]", line):
            p = part.strip().strip("•-")
            # "Category: Skill" lines — keep the skill, not the label
            if ":" in p:
                p = p.rsplit(":", 1)[-1].strip()
            # trailing "(descriptor)" notes are not the skill itself
            p = re.sub(r"\s*\([^)]*\)\s*$", "", p).strip()
            if p and len(p) <= 60:
                skills.append(p)
    return skills


def fix_bullet(bullet):
    """Rule-based repair. Never invents numbers, employers or results."""
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


def analyze(resume, jd):
    """Score resume vs JD. Weights (sum 100):
      JD keyword coverage 40, required-skill coverage 30,
      bullet quality 15, tailored summary 15."""
    parsed = parse_resume(resume)
    resume_norm = _norm(resume)
    resume_tokens = set(tokenize(resume))

    jd_keywords, jd_skills = extract_jd_keywords(jd)
    matched_kw = [k for k in jd_keywords
                  if k in resume_tokens or _phrase_in(k, resume_norm)]
    missing_kw = [k for k in jd_keywords if k not in matched_kw]
    matched_skills = [s for s in jd_skills if _phrase_in(s, resume_norm)]
    missing_skills = [s for s in jd_skills if s not in matched_skills]

    exp_lines = _section_lines(parsed, "experience")
    groups = split_bullets_grouped(exp_lines)
    bullets = [b for g in groups for b in g["bullets"]]
    title_of = {}
    for g in groups:
        for b in g["bullets"]:
            title_of[b] = g["title"]
    skills_lines = _section_lines(parsed, "skills")
    skills = split_skills(skills_lines)
    summary_lines = [l.strip() for l in _section_lines(parsed, "summary") if l.strip()]
    summary_text = " ".join(summary_lines)

    quantified = sum(1 for b in bullets if re.search(r"\d", b))
    action = sum(1 for b in bullets
                 if b.split() and b.split()[0].lower().strip(".,:;") in ACTION_VERBS)

    kw_cov = (len(matched_kw) / len(jd_keywords)) if jd_keywords else 0.0
    sk_cov = (len(matched_skills) / len(jd_skills)) if jd_skills else 0.0
    summary_kw = sum(1 for k in jd_keywords
                     if k in tokenize(summary_text) or _phrase_in(k, _norm(summary_text)))

    breakdown = {
        "jd_keywords": round(kw_cov * 40),
        "required_skills": round(sk_cov * 30),
        "bullet_quality": round(
            ((action / len(bullets)) * 7.5 + (quantified / len(bullets)) * 7.5)
            if bullets else 0),
        "tailored_summary": (5 if summary_text else 0) + (10 if summary_kw >= 3 else
                             (5 if summary_kw >= 1 else 0)),
    }
    score = min(100, sum(breakdown.values()))

    explanation = _explain(score, breakdown, len(matched_kw), len(jd_keywords),
                           len(matched_skills), len(jd_skills), len(bullets))
    return {
        "score": score,
        "breakdown": breakdown,
        "explanation": explanation,
        "counts": {
            "bullets": len(bullets),
            "skills": len(skills),
            "summary_words": len(summary_text.split()),
            "quantified_bullets": quantified,
            "action_bullets": action,
        },
        "jd": {
            "keywords_total": len(jd_keywords),
            "matched": matched_kw,
            "missing": missing_kw,
            "coverage": round(kw_cov, 4),
            "required_skills_total": len(jd_skills),
            "skills_matched": matched_skills,
            "skills_missing": missing_skills,
            "skills_coverage": round(sk_cov, 4),
        },
        "bullets": bullets,
        "bullet_groups": groups,
        "title_of": title_of,
        "skills_list": skills,
        "summary": summary_text,
        "header": parsed["header"],
        "parsed": parsed,
    }


def _explain(score, breakdown, m_kw, t_kw, m_sk, t_sk, n_bullets):
    if score >= 75:
        verdict = "Strong overlap — this resume already speaks the JD's language."
    elif score >= 50:
        verdict = "Decent overlap — a few targeted edits will lift it a lot."
    elif score >= 30:
        verdict = "Weak overlap — the JD asks for several things this resume does not show."
    else:
        verdict = "Very low overlap — either the resume is for a different field, or the key skills are missing from it."
    parts = [
        verdict,
        f"JD keywords: {m_kw}/{t_kw} present ({breakdown['jd_keywords']}/40).",
        f"Required skills: {m_sk}/{t_sk} present ({breakdown['required_skills']}/30).",
        f"Bullet quality: {breakdown['bullet_quality']}/15 across {n_bullets} bullets.",
        f"Summary fit: {breakdown['tailored_summary']}/15.",
        "This is an estimate of keyword/skill overlap, not a real ATS score "
        "and not a hiring prediction — real hiring also weighs experience, "
        "portfolio and interviews.",
    ]
    return " ".join(parts)


def tailor_deterministic(result, jd):
    """Deterministic tailoring from the analysis only — no AI, no invention.

    - Skills reordered: JD-matched first (JD order), then the rest.
    - Bullets reordered by JD-keyword density, openings repaired.
    - Summary: the user's own summary + one factual sentence listing the
      JD-matched skills already present in the resume.
    - Gaps stay gaps: listed, never filled."""
    parsed = result["parsed"]
    jd_keywords = result["jd"]["matched"] + result["jd"]["missing"]
    norm_jd = _norm(jd)

    def bullet_density(b):
        nb = _norm(b)
        return sum(1 for k in jd_keywords if _phrase_in(k, nb) or k in tokenize(b))

    bullets = result["bullets"]
    title_of = result.get("title_of", {})
    ordered = sorted(bullets, key=lambda b: -bullet_density(b))
    pairs = []
    for b in ordered:
        fixed = fix_bullet(b)
        pairs.append({"original": b, "tailored": fixed["fixed"],
                      "notes": fixed["notes"],
                      "jd_hits": bullet_density(b),
                      "title": title_of.get(b)})

    skills = result["skills_list"]
    matched_set = set(result["jd"]["skills_matched"])
    ordered_skills = [s for s in skills if _norm(s) in
                      {_norm(m) for m in matched_set}]
    ordered_skills += [s for s in skills if s not in ordered_skills]
    # also surface matched JD skills that appear in the resume text but
    # were not listed in a skills section
    resume_norm = _norm(" ".join(result["header"]) + " " +
                        result["summary"] + " " +
                        " ".join(result["skills_list"]) + " " +
                        " ".join(result["bullets"]))
    for s in result["jd"]["skills_matched"]:
        if s not in [x.lower() for x in ordered_skills] and _phrase_in(s, resume_norm):
            ordered_skills.append(s)

    summary = result["summary"]
    matched = result["jd"]["skills_matched"]
    if summary and matched:
        summary = (summary.rstrip(".") + ". Relevant strengths for this role: " +
                   ", ".join(matched[:8]) + ".")
    elif matched:
        summary = "Relevant strengths for this role: " + ", ".join(matched[:8]) + "."

    return {
        "summary": summary,
        "skills_ordered": ordered_skills,
        "bullet_pairs": pairs,
        "gaps": result["jd"]["skills_missing"],
    }


def _esc(text):
    return html.escape(text or "")


def render_tailored_html(result, tailored):
    """Tailored resume as clean single-column HTML for on-page view/print."""
    parsed = result["parsed"]
    parts = []
    header = result["header"]
    if header:
        parts.append(f"<h1>{_esc(header[0])}</h1>")
        for line in header[1:]:
            parts.append(f"<p class='contact'>{_esc(line)}</p>")
    if tailored["summary"]:
        parts.append(f"<h2>Summary</h2><p>{_esc(tailored['summary'])}</p>")
    if tailored["skills_ordered"]:
        parts.append("<h2>Skills</h2><p>" +
                     ", ".join(_esc(s) for s in tailored["skills_ordered"]) + "</p>")
    if tailored["bullet_pairs"]:
        parts.append("<h2>Experience</h2>")
        last_title = object()
        open_ul = False
        for p in tailored["bullet_pairs"]:
            if p.get("title") != last_title:
                if open_ul:
                    parts.append("</ul>")
                    open_ul = False
                if p.get("title"):
                    parts.append(f"<p><b>{_esc(p['title'])}</b></p>")
                last_title = p.get("title")
            if not open_ul:
                parts.append("<ul>")
                open_ul = True
            parts.append(f"<li>{_esc(p['tailored'])}</li>")
        if open_ul:
            parts.append("</ul>")
    edu_lines = [l.strip() for l in _section_lines(parsed, "education") if l.strip()]
    if edu_lines:
        parts.append("<h2>Education</h2><ul>" + "".join(
            f"<li>{_esc(e)}</li>" for e in edu_lines) + "</ul>")
    return "\n".join(parts)


def render_tailored_text(result, tailored):
    """Plain-text tailored resume for .txt download."""
    lines = []
    header = result["header"]
    if header:
        lines.extend(header)
    if tailored["summary"]:
        lines += ["", "SUMMARY", tailored["summary"]]
    if tailored["skills_ordered"]:
        lines += ["", "SKILLS", ", ".join(tailored["skills_ordered"])]
    if tailored["bullet_pairs"]:
        lines += ["", "EXPERIENCE"]
        last_title = object()
        for p in tailored["bullet_pairs"]:
            if p.get("title") != last_title:
                lines.append(p["title"])
                last_title = p.get("title")
            lines.append(f"- {p['tailored']}")
    parsed = result["parsed"]
    edu_lines = [l.strip() for l in _section_lines(parsed, "education") if l.strip()]
    if edu_lines:
        lines += ["", "EDUCATION"] + [f"- {e}" for e in edu_lines]
    return "\n".join(lines)
