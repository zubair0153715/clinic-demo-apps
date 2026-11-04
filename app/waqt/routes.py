"""Waqt routes — free AI day planner (Motion gap build).

Original clean-room build. Not affiliated with Motion. Stateless:
nothing is stored server-side; tasks and plans live in the user's
own browser (localStorage). No account, no card, no subscription,
no usage meter.

The server only runs the deterministic scheduler, parses quick-add
text, and offers optional Gemini breakdown/estimate. The plan is
drawn in the browser from the returned blocks.
"""
import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import WAQT_HTML

router = APIRouter(prefix="/waqt")


@router.get("", response_class=HTMLResponse)
def index():
    return WAQT_HTML


@router.post("/api/schedule")
async def schedule(payload: str = Form("{}")):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid JSON."},
                            status_code=400)
    result, err = engine.schedule(
        data.get("tasks", []), events=data.get("events", []),
        settings=data.get("settings", {}),
        start_date=data.get("start_date"))
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    result["ok"] = True
    return result


@router.post("/api/parse")
async def parse(text: str = Form("")):
    tasks, errors = engine.parse_quick(text)
    return {"ok": True, "tasks": tasks, "errors": errors}


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/breakdown")
async def breakdown(title: str = Form(""), minutes: str = Form("60"),
                    language: str = Form("en")):
    if not title.strip():
        return JSONResponse({"ok": False, "error": "Task title missing."},
                            status_code=400)
    try:
        mins = int(minutes)
    except ValueError:
        mins = 60
    mins = min(8 * 60, max(10, mins))
    subtasks, err = gemini.breakdown_task(title.strip(), mins, language)
    if err:
        # Deterministic fallback: equal chunks, always available.
        n = 3 if mins >= 90 else 2
        chunk = (mins // n // 5) * 5
        fallback = [{"title": f"{title.strip()} — hissa {i + 1}",
                     "minutes": chunk} for i in range(n)]
        fallback[-1]["minutes"] += mins - chunk * n
        return {"ok": True, "subtasks": fallback, "ai": False,
                "note": err}
    return {"ok": True, "subtasks": subtasks, "ai": True}


@router.post("/api/estimate")
async def estimate(title: str = Form(""), language: str = Form("en")):
    if not title.strip():
        return JSONResponse({"ok": False, "error": "Task title missing."},
                            status_code=400)
    minutes, note, err = gemini.estimate_duration(title.strip(), language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "minutes": minutes, "note": note}
