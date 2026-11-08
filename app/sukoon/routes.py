"""Sukoon routes — free sleep & calm studio (Calm gap build).

Original clean-room build. Not affiliated with Calm / Headspace.
Stateless: nothing is stored server-side; dhikr totals, diary and
wind-down settings live in the user's own browser (localStorage).
No account, no card, no trial, no auto-renewal. Sukoon never
diagnoses or treats anything — see Honest limits on the page.
"""

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini, stories
from .pages import SUKOON_HTML

router = APIRouter(prefix="/sukoon")


@router.get("", response_class=HTMLResponse)
def index():
    return SUKOON_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/stories")
def list_stories():
    errors = stories.validate_stories()
    return {"stories": stories.story_meta(),
            "valid": not errors, "errors": errors}


@router.get("/api/story/{story_id}")
def get_story(story_id: str, lang: str = "en"):
    for s in stories.STORIES:
        if s["id"] == story_id:
            if lang not in engine.LANGUAGES:
                return JSONResponse({"ok": False,
                                     "error": "Language ghalat hai."},
                                    status_code=200)
            text = s[lang]
            return {"ok": True, "id": s["id"],
                    "title": s[f"title_{lang}"],
                    "text": text, "words": engine.word_count(text),
                    "minutes": engine.reading_minutes(text),
                    "language": lang, "ai": False}
    return JSONResponse({"ok": False, "error": "Kahani nahi mili."},
                        status_code=200)


@router.get("/api/breathing")
def breathing(pattern: str = "478", cycles: int = 4):
    schedule, err = engine.breathing_schedule(pattern, cycles)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **schedule}


@router.get("/api/sounds")
def sounds():
    return {"sounds": engine.SOUND_RECIPES,
            "timers": engine.SLEEP_TIMERS}


@router.post("/api/dhikr")
def dhikr(key: str = Form(""), count: int = Form(0)):
    result, err = engine.dhikr_progress(key, count)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **result}


@router.post("/api/wind-down")
def wind_down(isha: str = Form(""), bedtime: str = Form("")):
    plan, err = engine.build_wind_down(isha, bedtime)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **plan}


@router.post("/api/sleep")
def sleep(bed: str = Form(""), wake: str = Form("")):
    result, err = engine.sleep_duration(bed, wake)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, **result}


@router.post("/api/sleep-average")
def sleep_average(minutes: str = Form("")):
    try:
        vals = [int(x) for x in minutes.split(",") if x.strip()]
    except ValueError:
        return JSONResponse({"ok": False,
                             "error": "Minutes numbers me likhein."},
                            status_code=200)
    avg = engine.sleep_average(vals)
    if avg is None:
        return JSONResponse({"ok": False,
                             "error": "Koi valid neend record nahi mila."},
                            status_code=200)
    return {"ok": True, **avg}


@router.post("/api/story-ai")
async def story_ai(theme: str = Form("river"),
                   language: str = Form("en")):
    result, err = gemini.story_ai(theme, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/wind-down-ai")
async def wind_down_ai(bedtime: str = Form(""),
                       wake: str = Form(""),
                       stress: int = Form(3),
                       worry: str = Form(""),
                       language: str = Form("en")):
    result, err = gemini.wind_down_ai(bedtime, wake, stress, worry, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}
