"""Zehn routes — free brain-training studio (Lumosity gap build).

Original clean-room build. Not affiliated with Lumos Labs /
Lumosity. Stateless: nothing is stored server-side; scores and
levels live in the user's own browser (localStorage). No account,
no card, no trial, no auto-renewal. Zehn makes no claim to raise
IQ, prevent dementia or treat any condition — see Honest limits
on the page.
"""

import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import ZEHN_HTML

router = APIRouter(prefix="/zehn")


@router.get("", response_class=HTMLResponse)
def index():
    return ZEHN_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/games")
def games():
    return {"games": engine.game_list()}


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


@router.get("/api/memory")
def memory(level: int = 1, seed: int = None):
    result, err = engine.memory_round(level, seed)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/memory/score")
def memory_score(digits: str = Form("[]"), answer: str = Form("")):
    try:
        data = json.loads(digits)
    except (ValueError, TypeError):
        return _bad("Digits JSON nahi hain.")
    result, err = engine.score_memory(data, answer)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.get("/api/stroop")
def stroop(level: int = 1, seed: int = None):
    result, err = engine.stroop_round(level, seed)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/stroop/score")
def stroop_score(trials: str = Form("[]"), answers: str = Form("[]")):
    try:
        tdata, adata = json.loads(trials), json.loads(answers)
    except (ValueError, TypeError):
        return _bad("Trials ya jawab JSON nahi hain.")
    result, err = engine.score_stroop(tdata, adata)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.get("/api/math")
def math_q(level: int = 1, seed: int = None):
    result, err = engine.math_question(level, seed)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/math/check")
def math_check(answer: int = Form(...), given: int = Form(...)):
    result, err = engine.check_math({"answer": answer}, given)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.get("/api/nback")
def nback(level: int = 1, seed: int = None):
    result, err = engine.nback_sequence(level, seed)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/nback/score")
def nback_score(targets: str = Form("[]"), answers: str = Form("[]")):
    try:
        tdata, adata = json.loads(targets), json.loads(answers)
    except (ValueError, TypeError):
        return _bad("Targets ya jawab JSON nahi hain.")
    result, err = engine.score_nback(tdata, adata)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.get("/api/grid")
def grid(level: int = 1, seed: int = None):
    result, err = engine.grid_round(level, seed)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/grid/score")
def grid_score(lit: str = Form("[]"), picked: str = Form("[]"),
               size: int = Form(3)):
    try:
        ldata, pdata = json.loads(lit), json.loads(picked)
    except (ValueError, TypeError):
        return _bad("Cells JSON nahi hain.")
    result, err = engine.score_grid(ldata, pdata, size)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/score")
def score(accuracy: float = Form(...), avg_seconds: float = Form(...),
          game: str = Form("")):
    target = engine.TARGET_SECONDS.get(game)
    if target is None:
        return _bad("Game ghalat hai — list me se chunein.")
    result, err = engine.zehn_score(accuracy, avg_seconds, target)
    if err:
        return _bad(err)
    return {"ok": True, "game": game, **result}


@router.post("/api/adapt")
def adapt(level: int = Form(...), accuracy: float = Form(...),
          avg_seconds: float = Form(None),
          target_seconds: float = Form(None)):
    result, err = engine.adaptive_level(level, accuracy, avg_seconds,
                                        target_seconds)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.get("/api/workout")
def workout(day: int = 1, weakest: str = None):
    result, err = engine.workout_plan(day, weakest)
    if err:
        return _bad(err)
    return {"ok": True, **result}


@router.post("/api/tip-ai")
async def tip_ai(language: str = Form("en"),
                 score_summary: str = Form("")):
    result, err = gemini.daily_tip(language, score_summary)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/summary-ai")
async def summary_ai(language: str = Form("en"),
                     week_summary: str = Form("")):
    result, err = gemini.weekly_summary(language, week_summary)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}
