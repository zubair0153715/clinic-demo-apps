# -*- coding: utf-8 -*-
"""Poda routes — free AI plant identifier (PictureThis gap build).

Original clean-room build. Not affiliated with PictureThis or
Glority Global Group Ltd. Stateless: nothing is stored server-side;
photos are sent to Gemini for the one identification/diagnosis and
then discarded. My Plants lives in the user's own browser
(localStorage). No account, no card, no trial, no credits, no ads.
"""

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import PODA_HTML

router = APIRouter(prefix="/poda")


@router.get("", response_class=HTMLResponse)
def index():
    return PODA_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/common-plants")
def common_plants():
    return {"plants": engine.common_plants()}


def _bad(msg):
    return JSONResponse({"ok": False, "error": msg}, status_code=200)


@router.post("/api/water-schedule")
def water_schedule(plant_id: str = Form(""),
                   last_watered: str = Form(""),
                   month: int = Form(0)):
    plant = engine.find_common_plant(plant_id)
    if plant is None:
        return _bad("Poda nahi mila — list se chunein.")
    interval, err = engine.water_interval(plant_id, month)
    if err:
        return _bad(err)
    last, err = engine.parse_date(last_watered)
    if err:
        return _bad(err)
    status, err = engine.watering_status(last, interval)
    if err:
        return _bad(err)
    season, _ = engine.season_for_month(month)
    return {"ok": True, "plant": plant["name_en"],
            "name_ur": plant["name_ur"],
            "name_roman": plant["name_roman"],
            "season": season, "interval_days": interval, **status}


@router.post("/api/identify")
async def identify(photo: UploadFile = File(None),
                   language: str = Form("en")):
    if photo is None:
        return _bad("Pehle poday ki photo dein.")
    data = await photo.read()
    result, err = gemini.identify_from_file(
        data, photo.content_type or "", language)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/diagnose")
async def diagnose(photo: UploadFile = File(None),
                   language: str = Form("en")):
    if photo is None:
        return _bad("Pehle poday ki photo dein.")
    data = await photo.read()
    result, err = gemini.diagnose_from_file(
        data, photo.content_type or "", language)
    if err:
        return _bad(err)
    return {"ok": True, "result": result, "ai": True}
