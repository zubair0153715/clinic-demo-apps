"""Tarteeb routes — free AI resume tailorer (Koncept "AI Resume Tailorer"
idea, original clean-room build).

Not affiliated with any existing resume-tailoring product. Stateless:
nothing is stored server-side; the resume exists only in the
request/response. No account, no card, no download cap, no watermark.
Tailoring never invents facts — gaps are flagged, never filled.
"""

import io

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from . import engine, gemini
from .pages import TARTEEB_HTML

router = APIRouter(prefix="/tarteeb")


@router.get("", response_class=HTMLResponse)
def index():
    return TARTEEB_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


def _extract_file_text(upload):
    """Extract pasted-resume text from an uploaded PDF or DOCX file."""
    if upload is None or not upload.filename:
        return "", None
    data = upload.file.read()
    if len(data) > engine.MAX_FILE_BYTES:
        return "", "File too large (max 5 MB)."
    name = upload.filename.lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            parts = [(p.extract_text() or "") for p in reader.pages]
            return "\n".join(parts), None
        if name.endswith(".docx"):
            from docx import Document
            doc = Document(io.BytesIO(data))
            parts = [p.text for p in doc.paragraphs]
            for table in doc.tables:
                for row in table.rows:
                    parts.extend(c.text for c in row.cells)
            return "\n".join(parts), None
    except Exception as e:
        return "", f"Could not read that file ({type(e).__name__}). Try pasting the text instead."
    return "", "Only .pdf and .docx files are supported (or paste the text)."


def _analyze_payload(resume_text, jd_text):
    err = engine.check_caps(resume_text, jd_text)
    if err:
        return None, err
    result = engine.analyze(resume_text, jd_text)
    tailored = engine.tailor_deterministic(result, jd_text)
    result["tailored"] = tailored
    result["tailored_html"] = engine.render_tailored_html(result, tailored)
    result["tailored_text"] = engine.render_tailored_text(result, tailored)
    # parsed is internal (tuples); strip before JSON
    result.pop("parsed", None)
    result["ok"] = True
    return result, None


@router.post("/api/analyze")
async def analyze(
    resume_text: str = Form(""),
    job_description: str = Form(""),
    resume_file: UploadFile = File(None),
):
    if resume_file is not None and resume_file.filename:
        resume_text, err = _extract_file_text(resume_file)
        if err:
            return JSONResponse({"ok": False, "error": err}, status_code=400)
    if not resume_text.strip():
        return JSONResponse(
            {"ok": False, "error": "Resume text dein — paste karein ya PDF/DOCX upload karein."},
            status_code=400)
    if not job_description.strip():
        return JSONResponse(
            {"ok": False, "error": "Job description paste karein — uske baghair match nahi banta."},
            status_code=400)
    result, err = _analyze_payload(resume_text, job_description)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return result


@router.post("/api/ai-tailor")
async def ai_tailor_endpoint(
    resume_text: str = Form(""),
    job_description: str = Form(""),
):
    err = engine.check_caps(resume_text, job_description)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    if not resume_text.strip() or not job_description.strip():
        return JSONResponse(
            {"ok": False, "error": "Resume aur job description dono chahiye."},
            status_code=400)
    parsed = engine.parse_resume(resume_text)
    bullets = engine.split_bullets(engine._section_lines(parsed, "experience"))
    if not bullets:
        return JSONResponse(
            {"ok": False, "error": "Resume mein koi experience bullets nahi mile."},
            status_code=400)
    data, err = gemini.ai_tailor(resume_text, job_description, bullets)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    # safety: drop any tailored bullet whose numbers are not in the original
    import re as _re
    clean = []
    for item in data["bullets"]:
        orig_nums = set(_re.findall(r"\d[\d,.%]*", item["original"]))
        tail_nums = set(_re.findall(r"\d[\d,.%]*", item["tailored"]))
        if tail_nums <= orig_nums:
            clean.append(item)
    data["bullets"] = clean
    return {"ok": True, "ai_summary": data["summary"], "ai_bullets": clean}


@router.post("/api/download")
async def download(
    tailored_text: str = Form(""),
    name: str = Form("resume"),
    fmt: str = Form("txt"),
):
    if not tailored_text.strip():
        return JSONResponse({"ok": False, "error": "Nothing to download."},
                            status_code=400)
    safe = "".join(c for c in name.strip() if c.isalnum() or c in ("-", "_", " ")) or "resume"
    safe = safe.replace(" ", "-")[:60]
    if fmt == "docx":
        from docx import Document
        from docx.shared import Pt
        doc = Document()
        first = True
        for line in tailored_text.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.isupper() and len(s) <= 40:
                doc.add_heading(s.title(), level=2)
            elif s.startswith("- "):
                doc.add_paragraph(s[2:], style="List Bullet")
            else:
                p = doc.add_paragraph(s)
                if first:
                    for run in p.runs:
                        run.bold = True
                        run.font.size = Pt(16)
                first = False
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe}-tailored.docx"'},
        )
    buf = io.BytesIO(tailored_text.encode("utf-8"))
    return StreamingResponse(
        buf, media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{safe}-tailored.txt"'},
    )
