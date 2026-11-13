# -*- coding: utf-8 -*-
"""Daftar routes — free AI study notebook (NotebookLM / Gemini Notebook
gap build).

Original clean-room build. Not affiliated with Google or NotebookLM.
Stateless: nothing is stored server-side; sources are sent to Gemini
for the one chat / audio script / study kit and then discarded.
Notebooks live in the user's own browser (localStorage). No account,
no card, no trial, no credits, no ads, no daily caps.
"""

import json

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from . import engine, gemini
from .pages import DAFTAR_HTML

router = APIRouter(prefix="/daftar")

MAX_KIT_CHUNKS = 12


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


def _sources_from_body(body):
    if not isinstance(body, dict):
        return None, "Request samajh nahi aaya."
    sources, err = engine.validate_sources(body.get("sources", []))
    if err:
        return None, err
    return sources, None


def _chunks_for(sources, limit=None):
    chunks, err = engine.chunk_sources(sources)
    if err:
        return None, err
    if limit and len(chunks) > limit:
        chunks = engine.sample_chunks(chunks, limit)
    return chunks, None


@router.get("", response_class=HTMLResponse)
def index():
    return DAFTAR_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/demo")
def demo():
    chunks = engine.demo_chunks()
    return {"ok": True, "source": engine.DEMO_SOURCE,
            "words": engine.word_count(engine.DEMO_SOURCE["text"]),
            "chunks": chunks}


@router.post("/api/extract-pdf")
async def extract_pdf(pdf: UploadFile = File(None)):
    if pdf is None:
        return _bad("Pehle PDF dein.")
    data = await pdf.read()
    text, pages, err = engine.extract_pdf_text(data)
    if err:
        return _bad(err)
    return {"ok": True, "text": text, "pages": pages,
            "words": engine.word_count(text)}


@router.post("/api/prepare")
async def prepare(body: dict):
    sources, err = _sources_from_body(body)
    if err:
        return _bad(err)
    chunks, err = engine.chunk_sources(sources)
    if err:
        return _bad(err)
    total_words = sum(s["words"] for s in sources)
    return {"ok": True,
            "sources": [{"id": s["id"], "title": s["title"],
                         "words": s["words"]} for s in sources],
            "chunks": chunks, "total_words": total_words,
            "reading_minutes": engine.reading_time_minutes(total_words)}


@router.post("/api/search")
async def search(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    sources, err = _sources_from_body(body)
    if err:
        return _bad(err)
    chunks, err = engine.chunk_sources(sources)
    if err:
        return _bad(err)
    ranked, err = engine.search_chunks(body.get("query", ""), chunks)
    if err:
        return _bad(err)
    return {"ok": True, "results": ranked}


@router.post("/api/chat")
async def chat(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    sources, err = _sources_from_body(body)
    if err:
        return _bad(err)
    chunks, err = engine.chunk_sources(sources)
    if err:
        return _bad(err)
    ranked, err = engine.retrieve(body.get("question", ""), chunks)
    if err:
        return _bad(err)
    if not ranked:
        return {"ok": True, "result": {
            "answer": "Ye jawab in sources mein nahi hai.",
            "not_found": True, "citations": [], "ai": False,
            "language": body.get("language", "en")}}
    language = body.get("language", "en")
    result, err = gemini.chat(body.get("question", ""), ranked, language)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "used_chunks": ranked}


@router.post("/api/audio")
async def audio(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    sources, err = _sources_from_body(body)
    if err:
        return _bad(err)
    chunks, err = _chunks_for(sources, limit=MAX_KIT_CHUNKS)
    if err:
        return _bad(err)
    result, err = gemini.audio_script(
        chunks, body.get("language", "en"), body.get("style", "deep"))
    if err:
        return _bad(err)
    return {"ok": True, "result": result,
            "chunks_used": len(chunks)}


@router.post("/api/study-kit")
async def study_kit(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    kind = body.get("kind", "")
    if kind not in ("flashcards", "quiz", "guide"):
        return _bad("Kind flashcards, quiz ya guide hona chahiye.")
    sources, err = _sources_from_body(body)
    if err:
        return _bad(err)
    chunks, err = _chunks_for(sources, limit=MAX_KIT_CHUNKS)
    if err:
        return _bad(err)
    language = body.get("language", "en")
    if kind == "flashcards":
        result, err = gemini.flashcards(chunks, language)
    elif kind == "quiz":
        result, err = gemini.quiz(chunks, language)
    else:
        result, err = gemini.study_guide(chunks, language)
    if err:
        return _bad(err)
    return {"ok": True, "result": result,
            "chunks_used": len(chunks)}


@router.post("/api/export-csv")
async def export_csv(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    text, err = engine.flashcards_to_csv(body.get("cards", []))
    if err:
        return _bad(err)
    return PlainTextResponse(text, media_type="text/csv",
                             headers={"Content-Disposition":
                                      'attachment; filename="daftar-flashcards.csv"'})


@router.post("/api/export-notebook")
async def export_notebook(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    text, err = engine.export_notebook(body)
    if err:
        return _bad(err)
    return PlainTextResponse(text, media_type="application/json",
                             headers={"Content-Disposition":
                                      'attachment; filename="daftar-notebook.json"'})


@router.post("/api/import-notebook")
async def import_notebook(body: dict):
    if not isinstance(body, dict):
        return _bad("Request samajh nahi aaya.")
    raw = body.get("json", "")
    notebook, err = engine.import_notebook(raw)
    if err:
        return _bad(err)
    return {"ok": True, "notebook": notebook}
