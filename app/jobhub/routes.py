"""Auto-Apply Hub routes — dashboard + profile vault + worker API.

Unlisted route (/jobhub): no link from the landing page, noindex.
Worker API is key-gated (X-Worker-Key == JOBHUB_WORKER_KEY env var).
"""

import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import db
from . import pages

router = APIRouter(prefix="/jobhub")


def _worker_ok(request: Request) -> bool:
    key = os.environ.get("JOBHUB_WORKER_KEY", "")
    if not key:
        return False
    return request.headers.get("X-Worker-Key") == key


@router.get("", response_class=HTMLResponse)
def index():
    counts = db.counts()
    matches = db.get_matches()
    queue = db.get_queue()
    applied = db.get_applications()
    profile = db.get_profile()
    return pages.render_dashboard(counts, matches, queue, applied, profile)


@router.get("/profile", response_class=HTMLResponse)
def profile_form():
    return pages.render_profile_form(db.get_profile())


@router.post("/profile")
async def profile_save(
    name: str = Form(""), cv_name: str = Form(""), email: str = Form(""),
    phone: str = Form(""), city: str = Form(""), country: str = Form(""),
    dob: str = Form(""), degree: str = Form(""), institution: str = Form(""),
    session: str = Form(""), start_year: str = Form(""),
    education_status: str = Form(""), skills: str = Form(""),
    github: str = Form(""), linkedin: str = Form(""),
    pharmareg: str = Form(""), leadforge: str = Form(""),
    relocation: str = Form(""), daily_cap: str = Form("4"),
):
    try:
        start_year_i = int(start_year)
    except Exception:
        start_year_i = 2024
    try:
        cap_i = int(daily_cap)
    except Exception:
        cap_i = 4
    cap_i = max(1, min(10, cap_i))
    data = {
        "name": name, "cv_name": cv_name, "email": email, "phone": phone,
        "city": city, "country": country, "dob": dob, "degree": degree,
        "institution": institution, "session": session,
        "start_year": start_year_i, "education_status": education_status,
        "skills": skills, "github": github, "linkedin": linkedin,
        "pharmareg": pharmareg, "leadforge": leadforge,
        "relocation": relocation, "daily_cap": cap_i,
    }
    db.save_profile(data)
    return RedirectResponse("/jobhub", status_code=303)


@router.get("/api/status")
def api_status():
    return {"ok": True, **db.counts()}


@router.get("/api/worker/profile")
def worker_profile(request: Request):
    if not _worker_ok(request):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    return {"ok": True, "profile": db.get_profile()}


@router.post("/api/worker/upsert")
async def worker_upsert(request: Request):
    if not _worker_ok(request):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    body = await request.json()
    saved_profile = None
    if isinstance(body.get("profile"), dict):
        saved_profile = db.save_profile(body["profile"])
    n_matches = 0
    for m in body.get("matches", []) or []:
        if isinstance(m, dict) and db.upsert_match(m):
            n_matches += 1
    n_queue = 0
    for q in body.get("queue", []) or []:
        if isinstance(q, dict) and db.upsert_queue(q):
            n_queue += 1
    return {"ok": True, "matches_upserted": n_matches,
            "queue_upserted": n_queue,
            "profile_saved": saved_profile is not None}


@router.post("/api/worker/mark")
async def worker_mark(request: Request):
    if not _worker_ok(request):
        return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    body = await request.json()
    mid = body.get("id", "")
    status = body.get("status", "")
    if not mid or status not in ("new", "queued", "applied", "held", "expired"):
        return JSONResponse({"ok": False, "error": "bad id/status"}, status_code=400)
    ok = db.set_match_status(mid, status, body.get("confirmation", ""),
                             body.get("applied_at", ""))
    return {"ok": ok}
