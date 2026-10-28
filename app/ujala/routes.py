"""Ujala routes — free photo enhancer (Evoto gap build).

Original clean-room build. Not affiliated with Evoto or any other
retoucher. Stateless: photos are processed in memory and never stored,
never used for training, never sent to a third party. No account, no
card, no credits, no watermark.
"""

import base64

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import UJALA_HTML

router = APIRouter(prefix="/ujala")


@router.get("", response_class=HTMLResponse)
def index():
    return UJALA_HTML


@router.get("/api/presets")
def presets():
    return {k: v["label"] for k, v in engine.PRESETS.items()}


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/enhance")
async def enhance(
    file: UploadFile = File(...),
    preset: str = Form("auto"),
    brightness: float = Form(None),
    contrast: float = Form(None),
    color: float = Form(None),
    sharpness: float = Form(None),
    warmth: float = Form(None),
    smooth: float = Form(None),
):
    try:
        data = await file.read()
        overrides = {k: v for k, v in {
            "brightness": brightness, "contrast": contrast, "color": color,
            "sharpness": sharpness, "warmth": warmth, "smooth": smooth,
        }.items() if v is not None}
        result = engine.enhance(data, preset=preset, overrides=overrides)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return {
        "ok": True,
        "image_b64": base64.b64encode(result["jpeg"]).decode(),
        "before": result["before"],
        "after": result["after"],
        "preset": result["preset"],
        "params": result["params"],
    }


@router.post("/api/advise")
async def advise(payload: dict):
    goal = (payload or {}).get("goal", "")
    if not goal.strip():
        return JSONResponse({"ok": False, "error": "Goal likhein."}, status_code=400)
    data, err = gemini.advise(goal)
    if err:
        return {"ok": False, "error": err}
    return {"ok": True, **data}
