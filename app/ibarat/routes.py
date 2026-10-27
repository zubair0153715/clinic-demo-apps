"""Ibarat routes — free writing studio (QuillBot gap build).

Original clean-room build. Not affiliated with QuillBot or any other
writing tool. Stateless: no server storage, no account, no card, no
word cap; results save to the user's own browser if they want them.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import engine
from . import gemini
from .pages import IBARAT_HTML

router = APIRouter(prefix="/ibarat")


class ParaphraseReq(BaseModel):
    text: str = ""
    mode: str = "standard"
    protected: list = []


class SummarizeReq(BaseModel):
    text: str = ""
    sentences: int = 3


class AnalyzeReq(BaseModel):
    text: str = ""


class CiteReq(BaseModel):
    style: str = "apa"
    surname: str = ""
    initials: str = ""
    year: str = ""
    title: str = ""
    container: str = ""
    url: str = ""
    doi: str = ""


class AIRewriteReq(BaseModel):
    text: str = ""
    mode: str = "standard"


@router.get("", response_class=HTMLResponse)
def index():
    return IBARAT_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/modes")
def modes():
    return {"modes": engine.MODES,
            "engine": "rule-based (curated synonym/phrase tables)"}


@router.post("/api/paraphrase")
def paraphrase(req: ParaphraseReq):
    if not req.text.strip():
        return JSONResponse({"error": "text empty"}, status_code=400)
    return engine.paraphrase(req.text, req.mode, req.protected)


@router.post("/api/summarize")
def summarize(req: SummarizeReq):
    if not req.text.strip():
        return JSONResponse({"error": "text empty"}, status_code=400)
    return engine.summarize(req.text, max(1, req.sentences))


@router.post("/api/analyze")
def analyze(req: AnalyzeReq):
    if not req.text.strip():
        return JSONResponse({"error": "text empty"}, status_code=400)
    return engine.analyze(req.text)


@router.post("/api/cite")
def cite(req: CiteReq):
    if not req.title.strip() and not req.surname.strip():
        return JSONResponse({"error": "title or author required"},
                            status_code=400)
    return engine.build_citation(req.style, req.surname, req.initials,
                                 req.year, req.title, req.container,
                                 req.url, req.doi)


@router.post("/api/ai-rewrite")
def ai_rewrite(req: AIRewriteReq):
    if not req.text.strip():
        return JSONResponse({"error": "text empty"}, status_code=400)
    text, err = gemini.ai_rewrite(req.text, req.mode)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    return {"rewritten": text, "engine": "Gemini (neural rewrite)",
            "mode": req.mode}
