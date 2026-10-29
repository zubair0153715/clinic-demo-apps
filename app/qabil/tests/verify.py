"""Qabil verification — every number hand-computed, no invented stats.

Fixture (hand count):
  summary: 20 words -> summary pts 10
  contact: email + phone -> 10
  skills: 4 -> round(4*15/8) = round(7.5) = 8
  bullets: 5 -> 20 ; quantified 3/5 -> round(9.0) = 9
  action verbs: 4/5 (Built, Reduced, Managed, Presented; NOT
    "Responsible") -> round(12.0) = 12
  JD keywords: python, docking, hplc, bioinformatics, research = 5,
    all present -> coverage 1.0 -> 15
  TOTAL = 10+10+8+20+9+12+15 = 84
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.qabil import engine  # noqa: E402

FIXTURE = {
    "name": "Test User",
    "target_role": "Bioinformatics Research Assistant",
    "email": "test@example.com",
    "phone": "+92 300 1234567",
    "city": "Larkana",
    "company": "Test University",
    "summary": ("Pharm-D student with research experience in drug discovery "
                "molecular docking and data analysis seeking a bioinformatics "
                "role in Pakistan today"),
    "skills": "Python, RDKit, docking, HPLC",
    "experience": (
        "Built a pipeline screening 500 compounds\n"
        "Reduced report time by 40 percent\n"
        "Responsible for lab documentation\n"
        "Managed a team of 6 students\n"
        "Presented findings at a conference"
    ),
    "education": "Pharm-D, SMBBMU Larkana (ongoing)",
    "job_description": "python docking hplc bioinformatics research",
}

failures = []


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + (f" [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(label)


def main():
    assert engine.check_caps(FIXTURE) is None
    long_name = dict(FIXTURE, name="x" * 121)
    check("cap rejects 121-char name", engine.check_caps(long_name) is not None)

    r = engine.analyze(FIXTURE)
    check("summary word count 20", r["counts"]["summary_words"] == 20,
          str(r["counts"]))
    check("breakdown exact", r["breakdown"] == {
        "contact": 10, "summary": 10, "skills": 8, "bullets": 20,
        "quantified": 9, "action_verbs": 12, "jd_keywords": 15},
        str(r["breakdown"]))
    check("score 84", r["score"] == 84, str(r["score"]))
    check("jd matched 5/5", r["jd"]["matched"] == [
        "bioinformatics", "docking", "hplc", "python", "research"],
        str(r["jd"]["matched"]))
    check("jd missing empty", r["jd"]["missing"] == [])

    # Partial keyword coverage: 2 of 3 present -> 0.6667, 10 pts.
    partial = dict(FIXTURE, job_description="python sql docking")
    rp = engine.analyze(partial)
    check("partial coverage 2/3", rp["jd"]["coverage"] == round(2 / 3, 4)
          and rp["jd"]["matched"] == ["docking", "python"]
          and rp["jd"]["missing"] == ["sql"], str(rp["jd"]))
    check("partial jd pts 10", rp["breakdown"]["jd_keywords"] == 10)

    # Bullet repair: strips responsibility language, never invents.
    f = engine.fix_bullet("Responsible for lab documentation")
    check("fix strips weak opening", f["fixed"] == "Lab documentation.",
          f["fixed"])
    check("fix flags missing number", any("No number" in n for n in f["notes"]))
    check("fix flags weak opening", any("Weak opening" in n for n in f["notes"]))
    f2 = engine.fix_bullet("Built a pipeline screening 500 compounds")
    check("good bullet unchanged + no notes",
          f2["fixed"] == "Built a pipeline screening 500 compounds." and f2["notes"] == [],
          str(f2))
    f3 = engine.fix_bullet("worked on data entry")
    check("fix 'worked on' + flags", f3["fixed"] == "Data entry."
          and len(f3["notes"]) == 2, str(f3))

    # Rendering: clean, no watermark/trademark, all sections present.
    html_out = engine.render_resume_html(FIXTURE)
    txt = engine.render_plain_text(FIXTURE)
    check("html has name", "Test User" in html_out)
    check("html has no watermark", "watermark" not in html_out.lower())
    check("html has no trademark", "qabil" not in html_out.lower())
    check("txt sections", all(s in txt for s in
          ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION"]))
    check("txt has bullets", "- Built a pipeline" in txt)

    # Cover letter uses supplied facts only: 500 lives in experience,
    # which the letter never touches, so it must NOT appear.
    letter = engine.cover_letter(FIXTURE)
    check("letter has role + skills",
          "Bioinformatics Research Assistant" in letter and "Python" in letter)
    check("letter invents nothing (no 500)", "500" not in letter)

    # Empty resume scores 0, does not crash.
    empty = {k: "" for k in FIXTURE}
    re_ = engine.analyze(empty)
    check("empty scores 0", re_["score"] == 0, str(re_["score"]))

    # Route smoke via TestClient.
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    check("GET /qabil 200", c.get("/qabil").status_code == 200)
    resp = c.post("/qabil/api/analyze", data=FIXTURE)
    check("POST analyze 200 + score 84",
          resp.status_code == 200 and resp.json().get("score") == 84,
          str(resp.status_code))
    check("analyze returns resume_html + plain_text",
          "Test User" in resp.json().get("resume_html", "")
          and "SUMMARY" in resp.json().get("plain_text", ""))
    check("GET ai-status 200", c.get("/qabil/api/ai-status").status_code == 200)
    check("oversize field -> 400",
          c.post("/qabil/api/analyze",
                 data=dict(FIXTURE, summary="x" * 2001)).status_code == 400)
    for route in ["/ujala", "/ibarat", "/quwwat", "/ishtehar", "/dars", "/bayan"]:
        check(f"no regression {route}",
              c.get(route).status_code == 200)

    print(f"\n{len(failures)} failures" if failures else "\nALL CHECKS PASSED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
