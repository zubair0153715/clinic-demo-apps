"""Saakht routes — free business-website builder (Durable gap build).

Original clean-room build. Not affiliated with Durable, Wix, Framer
or 10Web. Stateless: nothing is stored server-side; the site exists
only in the request/response. No account, no card, no subscription,
no lock-in — the owner downloads the .html file and keeps it.
"""

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import SAAKHT_HTML

router = APIRouter(prefix="/saakht")


@router.get("", response_class=HTMLResponse)
def index():
    return SAAKHT_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/build")
async def build(
    name: str = Form(""), btype: str = Form("other"),
    city: str = Form(""), phone: str = Form(""),
    tagline: str = Form(""), about: str = Form(""),
    services: str = Form(""), hours: str = Form(""),
    address: str = Form(""), theme: str = Form("teal"),
    language: str = Form("en"),
):
    data = {"name": name, "btype": btype, "city": city, "phone": phone,
            "tagline": tagline, "about": about, "services": services,
            "hours": hours, "address": address, "theme": theme,
            "language": language}
    err = engine.check_caps(data)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    result = engine.build_site(data)
    if not result.get("ok"):
        return JSONResponse(result, status_code=400)
    return result


@router.post("/api/ai-polish")
async def ai_polish(tagline: str = Form(""), about: str = Form("")):
    text, err = gemini.polish(tagline, about)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "polished": text}
