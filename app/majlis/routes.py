"""Majlis routes — free AI meeting-notes studio (Granola gap build).

Original clean-room build. Not affiliated with Granola, Otter,
Fireflies, Fathom or tl;dv. Stateless: nothing is stored
server-side; minutes exist only in the request/response and in the
user's own browser (localStorage history). No account, no card, no
subscription, no 30-day lock. v1 does NOT record audio and does
NOT transcribe speech — paste a transcript or type notes live.
"""

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import MAJLIS_HTML

router = APIRouter(prefix="/majlis")


@router.get("", response_class=HTMLResponse)
def index():
    return MAJLIS_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/structure")
async def structure(
    title: str = Form(""), date: str = Form(""),
    mtype: str = Form("other"), language: str = Form("en"),
    transcript: str = Form(""),
):
    data = {"title": title, "date": date, "mtype": mtype,
            "language": language, "transcript": transcript}
    err = engine.check_caps(data)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    if not transcript.strip():
        return JSONResponse(
            {"ok": False, "error": "Transcript khaali hai — paste a "
             "transcript or type your meeting notes first."},
            status_code=400)
    return engine.structure_meeting(data)


@router.post("/api/ai-polish")
async def ai_polish(summary: str = Form(""), language: str = Form("en")):
    text, err = gemini.polish_summary(summary, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "polished": text}
