# -*- coding: utf-8 -*-
"""Kirdar routes — free AI character-chat platform (Character.AI
gap build).

Original clean-room build. Not affiliated with Character.AI.
Stateless: nothing is stored server-side; chats live in the user's
own browser (localStorage). No account, no card, no trial, no
credits, no ads, no daily caps, no time limits.
"""

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from . import engine, gemini
from .pages import KIRDAR_HTML

router = APIRouter(prefix="/kirdar")


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


def _character_from_body(body):
    data = body.get("character")
    if isinstance(data, dict) and data.get("id"):
        builtin = engine.builtin_by_id(data["id"])
        if builtin is not None:
            return builtin, None
    character, err = engine.validate_character(data or {})
    if err:
        return None, err
    return character, None


@router.get("", response_class=HTMLResponse)
def index():
    return KIRDAR_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/characters")
def characters():
    return {"ok": True, "characters": engine.BUILTIN_CHARACTERS}


@router.get("/api/demo")
def demo():
    chat = dict(engine.DEMO_CHAT)
    chat["character"] = engine.builtin_by_id(chat["character_id"])
    return {"ok": True, "chat": chat}


@router.post("/api/validate-character")
async def validate_character(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    character, err = engine.validate_character(body.get("character", {}))
    if err:
        return _bad(err)
    return {"ok": True, "character": character}


@router.post("/api/chat")
async def chat(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    character, err = _character_from_body(body)
    if err:
        return _bad(err)
    memory_card, err = engine.validate_memory_card(
        body.get("memory_card", []))
    if err:
        return _bad(err)
    summary = body.get("summary", "")
    if not isinstance(summary, str):
        return _bad("Summary ghalat hai.")
    summary = " ".join(summary.strip().split())
    if len(summary) > engine.MAX_SUMMARY:
        return _bad("Summary 1000 harf se chhoti honi chahiye.")
    history, err = engine.validate_history(body.get("history", []))
    if err:
        return _bad(err)
    language = body.get("language", character["language"])
    if language not in engine.LANGUAGES:
        return _bad("Language ghalat hai.")
    result, err = gemini.chat(character, memory_card, summary, history,
                              body.get("message", ""), language)
    if err:
        return _bad(err)
    return {"ok": True, "result": result}


@router.post("/api/summarize")
async def summarize(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    character, err = _character_from_body(body)
    if err:
        return _bad(err)
    history, err = engine.validate_history(body.get("turns", []))
    if err:
        return _bad(err)
    language = body.get("language", character["language"])
    if language not in engine.LANGUAGES:
        return _bad("Language ghalat hai.")
    summary, err = gemini.summarize(character, history, language)
    if err:
        return _bad(err)
    return {"ok": True, "summary": summary}


@router.post("/api/export-chat")
async def export_chat(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    text, err = engine.export_chat(body.get("chat", {}))
    if err:
        return _bad(err)
    return PlainTextResponse(text, media_type="application/json",
                             headers={"Content-Disposition":
                                      'attachment; filename="kirdar-chat.json"'})


@router.post("/api/import-chat")
async def import_chat(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    chat, err = engine.import_chat(body.get("json", ""))
    if err:
        return _bad(err)
    return {"ok": True, "chat": chat}
