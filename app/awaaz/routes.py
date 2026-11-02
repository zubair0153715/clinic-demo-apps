"""Awaaz routes — free read-aloud reader (Speechify gap build).

Original clean-room build. Not affiliated with Speechify. Stateless:
nothing is stored server-side; text exists only in the request/response
and in the user's own browser (localStorage library). No account, no
card, no subscription, no usage meter, no word limit.

The speaking itself runs in the browser (Web Speech API) — free,
unlimited, and impossible to quota-exhaust. The server only analyses
the text (sentences with offsets, language, reading stats) and offers
one optional Gemini summary.
"""
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import AWAAZ_HTML

router = APIRouter(prefix="/awaaz")


@router.get("", response_class=HTMLResponse)
def index():
    return AWAAZ_HTML


@router.post("/api/analyze")
async def analyze(text: str = Form("")):
    err = engine.check_caps(text)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    data = engine.analyze(text)
    data["ok"] = True
    return data


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/summarize")
async def summarize(text: str = Form(""), language: str = Form("en")):
    err = engine.check_caps(text)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    if not gemini.key_available():
        return JSONResponse(
            {"ok": False,
             "error": "AI summary ke liye GEMINI_API_KEY set nahi hai — "
                      "server par key set karein, phir dobara try karein."},
            status_code=400)
    summary, err = gemini.summarize_text(text, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "summary": summary}
