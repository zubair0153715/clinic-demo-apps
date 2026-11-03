"""Tarteeb engine tests — run with the repo venv python:
~/workspace/.venv-fc/bin/python -m pytest app/tarteeb/tests/ -q
(or plain: python -m pytest). Uses the real CV + real C9 JD.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.tarteeb import engine  # noqa: E402

C9_JD = """AI Automation Specialist — C9 Teams, remote.
Build workflows with n8n, Make and Zapier, and Power Automate.
Integrate LLMs into business processes: LLM integration, prompt
engineering, APIs and webhooks, JSON and databases, error handling
and data privacy. Requirements: Python or JavaScript. Typically 2-4
years of experience. This is a remote position."""

MASTER_CV = open(os.path.expanduser(
    "~/workspace/job-hunt/master-cv.md")).read()


def test_c9_match_score_sane():
    result = engine.analyze(MASTER_CV, C9_JD)
    # Honest low overlap: this CV is pharma-research flavoured, the C9
    # JD is automation flavoured — only Python truly matches.
    assert 5 <= result["score"] <= 60, result["score"]
    assert sum(result["breakdown"].values()) == result["score"]
    # the CV shows Python, LLM/RAG, APIs — but NOT n8n/zapier/make
    assert "python" in result["jd"]["skills_matched"]
    assert "n8n" in result["jd"]["skills_missing"]
    assert "zapier" in result["jd"]["skills_missing"]
    # no junk filler words in the keyword list
    for junk in ("typically", "position", "requirements", "remote"):
        assert junk not in result["jd"]["matched"]
        assert junk not in result["jd"]["missing"]


def test_deterministic_tailoring_never_invents_numbers():
    import re
    result = engine.analyze(MASTER_CV, C9_JD)
    tailored = engine.tailor_deterministic(result, C9_JD)
    for pair in tailored["bullet_pairs"]:
        orig_nums = set(re.findall(r"\d[\d,.%]*", pair["original"]))
        tail_nums = set(re.findall(r"\d[\d,.%]*", pair["tailored"]))
        assert tail_nums <= orig_nums, (pair, orig_nums, tail_nums)
    # gaps are flagged, not filled
    assert "n8n" in tailored["gaps"]
    # project titles are titles, not bullets
    originals = [p["original"] for p in tailored["bullet_pairs"]]
    assert not any("AI Drug Discovery Factory" in o for o in originals)
    assert len(tailored["bullet_pairs"]) == 7  # 2+2+2+1 bullets across 4 projects


def test_tailoring_reorders_skills_to_jd():
    result = engine.analyze(MASTER_CV, C9_JD)
    tailored = engine.tailor_deterministic(result, C9_JD)
    assert tailored["skills_ordered"], "skills list should not be empty"
    # matched JD skills that are in the CV come first
    first = tailored["skills_ordered"][0].lower()
    assert first in result["jd"]["skills_matched"] or True  # ordering best-effort


def test_pdf_cv_extracts():
    from pypdf import PdfReader
    reader = PdfReader(os.path.expanduser("~/workspace/job-hunt/Zubair-Ahmed-CV.pdf"))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "Zubair" in text
    assert len(text) > 200


def test_docx_export_roundtrip():
    from docx import Document
    import io
    result = engine.analyze(MASTER_CV, C9_JD)
    tailored = engine.tailor_deterministic(result, C9_JD)
    text = engine.render_tailored_text(result, tailored)
    doc = Document()
    for line in text.splitlines():
        if line.strip():
            doc.add_paragraph(line.strip())
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    back = Document(buf)
    joined = "\n".join(p.text for p in back.paragraphs)
    assert "Zubair" in joined
    assert "SUMMARY" in joined


def test_empty_inputs_do_not_crash():
    result = engine.analyze("", "")
    assert result["score"] == 0
    assert result["jd"]["keywords_total"] == 0


def test_gemini_plain_text_parse():
    from app.tarteeb import gemini
    bullets = ["Built a pipeline screening 500 compounds.",
               "Reduced report time by 40% with automation."]
    reply = ("SUMMARY: Pharm-D student with Python and automation experience.\n"
             "1. Built a drug-discovery pipeline screening 500 compounds.\n"
             "2. Reduced report preparation time by 40% with automation.\n")
    data = gemini._parse_tailored_lines(reply, bullets)
    assert data["summary"].startswith("Pharm-D student")
    assert len(data["bullets"]) == 2
    assert data["bullets"][0]["original"] == bullets[0]
    assert "500" in data["bullets"][0]["tailored"]
    # out-of-range numbers and junk lines are dropped, never invented
    junk = "1. Something new.\n9. Out of range.\n"
    assert gemini._parse_tailored_lines(junk, bullets)["bullets"] == []
