"""Sathi routes — free gentle self-care companion (Finch gap build).

Original clean-room build. Not affiliated with Finch / Finch Care.
Stateless: nothing is stored server-side; check-ins, habits,
gratitude and mood logs live in the user's own browser
(localStorage). No account, no card, no trial, no auto-renewal.
Sathi never diagnoses or treats anything — see Honest limits on
the page.
"""

import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import SATHI_HTML

router = APIRouter(prefix="/sathi")


@router.get("", response_class=HTMLResponse)
def index():
    return SATHI_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/journeys")
def journeys():
    return {"journeys": engine.journey_list()}


@router.get("/api/journey/{journey_id}")
def journey(journey_id: str):
    habits, err = engine.journey_habits(journey_id)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "journey": journey_id, "habits": habits}


@router.get("/api/pet")
def pet(points: int = 0):
    stage, err = engine.pet_stage(points)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **stage}


@router.post("/api/care")
def care(checkin: bool = Form(False), habits_done: int = Form(0),
          gratitude: bool = Form(False), breathing: bool = Form(False),
          lifetime_points: int = Form(0)):
    result, err = engine.care_points(checkin, habits_done, gratitude, breathing)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    total = lifetime_points + result["points"]
    if lifetime_points < 0:
        return JSONResponse({"ok": False,
                             "error": "Lifetime points 0 ya zyada hone chahiye."},
                            status_code=200)
    stage, err = engine.pet_stage(total)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **result, "lifetime_points": total, "pet": stage}


@router.post("/api/streak")
def streak(care_days: str = Form(""), rest_days: str = Form(""),
           today: str = Form("")):
    def _split(raw):
        return [x.strip() for x in raw.split(",") if x.strip()]
    result, err = engine.gentle_streak(_split(care_days), _split(rest_days), today)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **result}


@router.post("/api/mood")
def mood(entries: str = Form("[]")):
    try:
        data = json.loads(entries)
    except (ValueError, TypeError):
        return JSONResponse({"ok": False, "error": "Entries JSON nahi hain."},
                            status_code=200)
    result, err = engine.mood_average(data)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **result}


@router.post("/api/gratitude")
def gratitude(items: str = Form("[]")):
    try:
        data = json.loads(items)
    except (ValueError, TypeError):
        return JSONResponse({"ok": False, "error": "Items JSON nahi hain."},
                            status_code=200)
    clean, err = engine.validate_gratitude(data)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "items": clean, "count": len(clean)}


@router.get("/api/breathing")
def breathing(cycles: int = 4):
    schedule, err = engine.breathing_schedule(cycles)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **schedule}


@router.post("/api/prompt-ai")
async def prompt_ai(language: str = Form("en"), mood: int = Form(0)):
    result, err = gemini.daily_prompt(language, mood if mood else None)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/reflection-ai")
async def reflection_ai(language: str = Form("en"),
                        mood_summary: str = Form("")):
    result, err = gemini.weekly_reflection(language, mood_summary)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}
