"""Khulasa routes — free AI book-summary studio (Headway gap build).

Original clean-room build. Not affiliated with Headway. Stateless:
nothing is stored server-side; XP, streak, checklist and flashcard
progress live in the user's own browser (localStorage). No account,
no card, no trial, no auto-renewal.

The server serves the page, the starter library of original
summaries of public-domain classics, and the optional Gemini
summariser for text the user pastes. Quiz answers ship with their
explanation on purpose: this is a study app, and the explanation
IS the feature.
"""

import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini, library
from .pages import KHULASA_HTML

router = APIRouter(prefix="/khulasa")


@router.get("", response_class=HTMLResponse)
def index():
    return KHULASA_HTML


@router.get("/api/library")
def get_library():
    errors = engine.validate_library(library)
    books = []
    for book in library.BOOKS:
        entry = dict(book)
        entry["depths"] = {
            depth: {
                "words": engine.word_count(text),
                "minutes": engine.reading_minutes(engine.word_count(text)),
                "label": engine.DEPTHS[depth]["label"],
            }
            for depth, text in book["summaries"].items()
        }
        books.append(entry)
    return {"books": books, "depths": engine.DEPTHS,
            "valid": not errors, "errors": errors}


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/summarize")
async def summarize(text: str = Form(""), depth: str = Form("standard"),
                    language: str = Form("en")):
    result, err = gemini.summarize_text(text, depth, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/quiz-score")
async def quiz_score(payload: str = Form("{}")):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid JSON."},
                            status_code=400)
    quiz = data.get("quiz", [])
    answers = data.get("answers", [])
    if not isinstance(quiz, list) or not isinstance(answers, list):
        return JSONResponse({"ok": False, "error": "Quiz ya answers ghalat hain."},
                            status_code=400)
    correct, total = engine.quiz_score(answers, quiz)
    return {"ok": True, "correct": correct, "total": total}
