"""Quwwat routes — free AI strength-training planner.

Original clean-room build. Not affiliated with Fitbod or any other
fitness app. Stateless: no server storage, no account, no card, no
trial clock; plans save to the user's own browser.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import engine
from . import gemini
from .pages import QUWWAT_HTML

router = APIRouter(prefix="/quwwat")


class OneRepMaxReq(BaseModel):
    weight: float = 0
    reps: int = 1


class LiftInput(BaseModel):
    weight: float = 0
    reps: int = 1


class PlanReq(BaseModel):
    goal: str = "general"
    level: str = "intermediate"
    days: int = 3
    equipment: str = "full_gym"
    injuries: list = []
    lifts: dict = {}


class ExplainReq(BaseModel):
    summary: str = ""
    lang: str = "en"


@router.get("", response_class=HTMLResponse)
def index():
    return QUWWAT_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/exercises")
def exercises():
    return {"count": len(engine.EXERCISES),
            "muscles": engine.MUSCLES,
            "blocks": {g: [{"sets": s, "reps": r, "intensity": p}
                            for s, r, p in weeks]
                       for g, weeks in engine.BLOCKS.items()}}


@router.post("/api/one-rep-max")
def one_rep_max(req: OneRepMaxReq):
    try:
        val = engine.epley_1rm(req.weight, req.reps)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return {"one_rep_max_kg": round(val, 2),
            "formula": f"Epley: {req.weight:g} x (1 + {req.reps}/30) = {val:.2f} kg"}


@router.post("/api/plan")
def plan(req: PlanReq):
    lifts = {}
    for name, val in (req.lifts or {}).items():
        if isinstance(val, dict):
            lifts[name] = val
    return engine.build_plan(
        goal=req.goal, level=req.level, days=req.days,
        equipment=req.equipment, injuries=req.injuries, lifts=lifts)


@router.post("/api/ai-explain")
def ai_explain(req: ExplainReq):
    if not req.summary.strip():
        return JSONResponse({"error": "summary empty"}, status_code=400)
    text, err = gemini.ai_explain(req.summary, req.lang)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    return {"notes": text}
