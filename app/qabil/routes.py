"""Qabil routes — free resume builder (Rezi/Kickresume gap build).

Original clean-room build. Not affiliated with Rezi, Kickresume or
Teal. Stateless: nothing is stored server-side; the resume exists
only in the request/response. No account, no card, no download cap,
no watermark, no trademark on the exported document.
"""

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from . import engine, gemini
from .pages import QABIL_HTML

router = APIRouter(prefix="/qabil")

FIELDS = ["name", "target_role", "email", "phone", "city", "company",
          "summary", "skills", "experience", "education", "job_description"]


@router.get("", response_class=HTMLResponse)
def index():
    return QABIL_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


def _collect(form):
    return {f: (form.get(f, "") or "") for f in FIELDS}


@router.post("/api/analyze")
async def analyze(
    name: str = Form(""), target_role: str = Form(""),
    email: str = Form(""), phone: str = Form(""),
    city: str = Form(""), company: str = Form(""),
    summary: str = Form(""), skills: str = Form(""),
    experience: str = Form(""), education: str = Form(""),
    job_description: str = Form(""),
):
    data = {"name": name, "target_role": target_role, "email": email,
            "phone": phone, "city": city, "company": company,
            "summary": summary, "skills": skills, "experience": experience,
            "education": education, "job_description": job_description}
    err = engine.check_caps(data)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    result = engine.analyze(data)
    result["ok"] = True
    result["resume_html"] = engine.render_resume_html(data)
    result["plain_text"] = engine.render_plain_text(data)
    result["cover_letter"] = engine.cover_letter(data)
    return result


@router.post("/api/ai-improve")
async def ai_improve(experience: str = Form("")):
    if not experience.strip():
        return JSONResponse({"ok": False, "error": "No bullets given."}, status_code=400)
    if len(experience) > engine.CAPS["experience"]:
        return JSONResponse({"ok": False, "error": "Experience text too long."},
                            status_code=400)
    text, err = gemini.ai_improve_bullets(experience)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "improved": text}
