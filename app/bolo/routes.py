"""Bolo routes — free AI dictation studio (Voicy / Otter.ai gap build).

Original clean-room build. Not affiliated with Voicy or Otter.ai.
Stateless: nothing is stored server-side; sessions live in the
user's own browser (localStorage). No account, no card, no trial,
no minute cap. Recognition runs in the user's browser via the Web
Speech API — Bolo's server never hears any audio.
"""

import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import BOLO_HTML

router = APIRouter(prefix="/bolo")


@router.get("", response_class=HTMLResponse)
def index():
    return BOLO_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/languages")
def languages():
    return {"languages": engine.languages()}


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


@router.post("/api/commands")
def commands(text: str = Form(""), language: str = Form("en")):
    result, err = engine.apply_voice_commands(text, language)
    if err:
        return _bad(err)
    return {"ok": True, "text": result, "words": engine.word_count(result)}


@router.post("/api/stats")
def stats(text: str = Form(""), seconds: float = Form(0)):
    result, err = engine.session_stats(text, seconds)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/export")
def export(text: str = Form(""), title: str = Form(""),
            fmt: str = Form("txt")):
    result, err = engine.format_export(text, title, fmt)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/polish-ai")
async def polish_ai(language: str = Form("en"),
                    text: str = Form(""),
                    style: str = Form("saaf")):
    result, err = gemini.polish(language, text, style)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/roman-ai")
async def roman_ai(text: str = Form("")):
    result, err = gemini.romanize(text)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/translate-ai")
async def translate_ai(text: str = Form("")):
    result, err = gemini.translate_to_urdu(text)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}
