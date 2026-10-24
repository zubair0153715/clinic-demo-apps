"""Dars routes — free AI study companion: text in, study pack out.

Original clean-room build. Not affiliated with Coconote, Quizlet, or any
other study-notes tool. Stateless: no server storage, nothing trains on
your content; SM-2 schedules live in the user's own browser.
"""
import csv
import io
import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from . import gemini
from . import notes as notesmod
from . import quiz as quizmod
from .pages import DARS_HTML

log = logging.getLogger("dars.routes")
router = APIRouter(prefix="/dars")

MAX_INPUT = 300_000


class BuildReq(BaseModel):
    text: str
    seed: int = 7


class AiPackReq(BaseModel):
    text: str
    lang: str = "en"


class AiChatReq(BaseModel):
    text: str
    question: str
    lang: str = "en"


def _pack(text: str, seed: int = 7) -> dict:
    notes = notesmod.build_notes(text)
    return {
        "notes": notes,
        "cards": quizmod.build_flashcards(notes),
        "quiz": quizmod.build_quiz(notes, seed=seed),
    }


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def page():
    return HTMLResponse(DARS_HTML)


@router.get("/api/ai-status")
def api_ai_status():
    return JSONResponse({"ai_available": gemini.key_available()})


@router.post("/api/build")
def api_build(req: BuildReq):
    text = req.text.strip()
    if len(text) < 50:
        return JSONResponse({"error": "Text bohat chhota hai (50+ chars chahiye)."},
                            status_code=400)
    return JSONResponse(_pack(text[:MAX_INPUT], seed=req.seed))


@router.post("/api/ai-pack")
def api_ai_pack(req: AiPackReq):
    text = req.text.strip()
    if len(text) < 50:
        return JSONResponse({"error": "Text bohat chhota hai."}, status_code=400)
    if req.lang not in ("en", "ur", "ru"):
        return JSONResponse({"error": "lang en/ur/ru me se ho."}, status_code=400)
    pack, err = gemini.ai_study_pack(text[:MAX_INPUT], lang=req.lang)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    return JSONResponse(pack)


@router.post("/api/ai-chat")
def api_ai_chat(req: AiChatReq):
    if not req.question.strip():
        return JSONResponse({"error": "Sawal likho."}, status_code=400)
    answer, err = gemini.ai_chat(req.text.strip()[:MAX_INPUT],
                                 req.question.strip(), lang=req.lang)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    return JSONResponse({"answer": answer})


@router.post("/api/download-md")
def api_download_md(req: BuildReq):
    notes = notesmod.build_notes(req.text.strip()[:MAX_INPUT])
    lines = ["# Dars — Study Notes", ""]
    if notes["headings"]:
        lines += ["## Sections", *[f"- {h}" for h in notes["headings"]], ""]
    lines += ["## Summary"]
    lines += [f"- {s}" for s in notes["summary"]] or ["- (koi summary nahi)"]
    lines += ["", "## Definitions"]
    lines += [f"- **{d['term']}** — {d['sentence']}" for d in notes["definitions"]] \
        or ["- (koi definition nahi mili)"]
    if notes["key_terms"]:
        lines += ["", "## Key Terms",
                  ", ".join(k["term"] for k in notes["key_terms"])]
    return Response("\n".join(lines).encode("utf-8"),
                    media_type="text/markdown",
                    headers={"Content-Disposition":
                             "attachment; filename=dars-notes.md"})


@router.post("/api/download-csv")
def api_download_csv(req: BuildReq):
    notes = notesmod.build_notes(req.text.strip()[:MAX_INPUT])
    cards = quizmod.build_flashcards(notes)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Front", "Back", "Kind"])
    for c in cards:
        w.writerow([c["front"], c["back"], c["kind"]])
    return Response(buf.getvalue().encode("utf-8"),
                    media_type="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=dars-flashcards.csv"})
