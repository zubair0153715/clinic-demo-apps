"""Zubaan routes — free AI language tutor (Duolingo Max gap build).

Original clean-room build. Not affiliated with Duolingo. Stateless:
nothing is stored server-side; XP, streak and progress live in the
user's own browser (localStorage). No account, no card, no energy
meter, no subscription.

The server only serves the page, the content bank, and the optional
Gemini roleplay chat. Quiz answers ship with their rule on purpose:
this is a study app, and the explanation IS the feature.
"""

import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini, library
from .pages import ZUBAAN_HTML

router = APIRouter(prefix="/zubaan")


@router.get("", response_class=HTMLResponse)
def index():
    return ZUBAAN_HTML


@router.get("/api/bank")
def bank():
    errors = engine.validate_bank(library)
    data = library.bank()
    data["valid"] = not errors
    data["errors"] = errors
    return data


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/score-step")
async def score_step(payload: str = Form("{}")):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid JSON."},
                            status_code=400)
    matched, total, passed = engine.score_roleplay_step(
        data.get("keywords", []), data.get("text", ""))
    return {"ok": True, "matched": matched, "total": total,
            "passed": passed}


@router.post("/api/dictation")
async def dictation(payload: str = Form("{}")):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid JSON."},
                            status_code=400)
    frac, passed = engine.dictation_score(data.get("target", ""),
                                          data.get("typed", ""))
    return {"ok": True, "score": round(frac, 2), "passed": passed}


@router.post("/api/roleplay")
async def roleplay(scenario: str = Form(""), setting: str = Form(""),
                   history: str = Form("[]"), text: str = Form("")):
    if not text.strip():
        return JSONResponse({"ok": False, "error": "Apna jumla likhein."},
                            status_code=400)
    try:
        hist = json.loads(history)
    except json.JSONDecodeError:
        hist = []
    reply, err = gemini.roleplay_reply(scenario, setting, hist, text)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "reply": reply, "ai": True}
