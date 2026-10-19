"""SehatPlate — honest AI calorie tracker with a South Asian food database.

Original clean-room build. Not affiliated with Cal AI / MyFitnessPal.
Diary + profile are stored on the user's device (localStorage); the server only
serves the food database, target math, and the Gemini AI estimate endpoint.
"""
import logging

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import engine, foods, gemini
from .pages import SEHAT_HTML

log = logging.getLogger("sehatplate.routes")
router = APIRouter(prefix="/sehatplate")


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def page():
    return HTMLResponse(SEHAT_HTML)


@router.get("/api/foods")
def api_foods(q: str = Query(default="", max_length=60)):
    return JSONResponse(foods.search(q))


@router.get("/api/targets")
def api_targets(weight_kg: float = 70, height_cm: float = 170, age: int = 22,
                sex: str = "male", activity: str = "moderate", goal: str = "maintain"):
    try:
        return JSONResponse(engine.targets(weight_kg, height_cm, age, sex, activity, goal))
    except Exception as e:
        return JSONResponse({"error": f"inputs check karo: {e}"}, status_code=400)


class EstimateIn(BaseModel):
    text: str = ""


@router.post("/api/estimate")
def api_estimate(body: EstimateIn):
    result, err = gemini.estimate_meal(body.text)
    if err:
        return JSONResponse({"error": err}, status_code=200)
    return JSONResponse(result)


@router.get("/api/ai-status")
def api_ai_status():
    return JSONResponse({"ai_available": gemini.key_available()})
