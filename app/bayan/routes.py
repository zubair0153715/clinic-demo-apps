"""Bayan — free AI slide-deck builder.

Original clean-room build. Not affiliated with Gamma or any other
presentation tool. Drafts live in the user's browser (localStorage);
the server stores nothing and trains on nothing.
"""
import logging
import re

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from . import deck as deckmod
from . import gemini, pptxgen
from .pages import BAYAN_HTML

log = logging.getLogger("bayan.routes")
router = APIRouter(prefix="/bayan")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def page():
    return HTMLResponse(BAYAN_HTML)


@router.get("/api/themes")
def api_themes():
    return JSONResponse({k: {"label": v["label"]} for k, v in deckmod.THEMES.items()})


@router.get("/api/ai-status")
def api_ai_status():
    return JSONResponse({"ai_available": gemini.key_available()})


class OutlineIn(BaseModel):
    topic: str = ""
    notes: str = ""
    slide_count: int = 8
    tone: str = "punchy"
    use_ai: bool = True


@router.post("/api/outline")
def api_outline(body: OutlineIn):
    topic = (body.topic or "").strip()[:200]
    if not topic:
        return JSONResponse({"error": "Topic likho to outline banaun."}, status_code=400)
    if body.use_ai and gemini.key_available():
        d, warnings, err = gemini.generate_outline(
            topic, body.notes, body.slide_count, body.tone)
        if err:
            # Honest fallback: still give the user their structured notes.
            d2, w2 = deckmod.rule_based_outline(topic, body.notes, body.slide_count)
            w2.append(f"AI unavailable ({err})")
            return JSONResponse({"deck": d2, "warnings": w2, "ai": False})
        return JSONResponse({"deck": d, "warnings": warnings, "ai": True})
    d, warnings = deckmod.rule_based_outline(topic, body.notes, body.slide_count)
    return JSONResponse({"deck": d, "warnings": warnings, "ai": False})


class RegenIn(BaseModel):
    deck_title: str = ""
    slide: dict = {}
    instruction: str = ""
    tone: str = "punchy"


@router.post("/api/regenerate-slide")
def api_regenerate_slide(body: RegenIn):
    slide, err = gemini.regenerate_slide(
        body.deck_title, body.slide, body.instruction, body.tone)
    if err:
        return JSONResponse({"error": err}, status_code=200)
    return JSONResponse({"slide": slide})


class PptxIn(BaseModel):
    deck: dict = {}
    theme: str = "midnight"


@router.post("/api/download-pptx")
def api_download_pptx(body: PptxIn):
    d, _warnings = deckmod.normalize_deck(body.deck)
    try:
        data = pptxgen.build_pptx(d, body.theme)
    except Exception as e:
        log.exception("pptx build failed")
        return JSONResponse({"error": f"PPTX banane mein masla: {type(e).__name__}"},
                            status_code=500)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", d["title"]).strip("-")[:60] or "bayan-deck"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument"
                   ".presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{safe}.pptx"'},
    )
