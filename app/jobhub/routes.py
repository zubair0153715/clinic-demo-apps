"""Auto-Apply Hub routes — dashboard + profile vault + worker API.

Unlisted route (/jobhub): no link from the landing page, noindex.
Dashboard is owner-only: sign in at /jobhub/login with the JOBHUB_PASSWORD
secret (set in the FastAPI Cloud dashboard). Worker API is key-gated
(X-Worker-Key == JOBHUB_WORKER_KEY env var) and is not affected by login.
"""

import os

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import auth
from . import db
from . import pages

router = APIRouter(prefix="/jobhub")


def _worker_ok(request: Request) -> bool:
    key = os.environ.get("JOBHUB_WORKER_KEY", "")
    if not key:
        return False
    return request.headers.get("X-Worker-Key") == key


def _authed(request: Request) -> bool:
    return auth.valid_session(request.cookies.get(auth.COOKIE, ""))


def _need_login():
    return RedirectResponse("/jobhub/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if _authed(request):
        return RedirectResponse("/jobhub", status_code=303)
    return pages.render_login_page(setup_needed=not auth.password_set())


@router.post("/login")
async def login_submit(request: Request, password: str = Form("")):
    if not auth.password_set():
        return pages.render_login_page(
            error="Password not set yet.",
            setup_needed=True)
    if not auth.check_password(password):
        return pages.render_login_page(error="Wrong password — try again.")
    resp = RedirectResponse("/jobhub", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.new_session(),
                    max_age=auth.SESSION_DAYS * 86400, httponly=True)
    return resp


@router.get("/logout")
def logout(request: Request):
    auth.destroy_session(request.cookies.get(auth.COOKIE, ""))
    resp = RedirectResponse("/jobhub/login", status_code=303)
    resp.delete_cookie(auth.COOKIE)
    return resp


@router.get("", response_class=HTMLResponse)
def index(request: Request):
    if not _authed(request):
        return _need_login()
    counts = db.counts()
    matches = db.get_matches()
    queue = db.get_queue()
    applied = db.get_applications()
    profile = db.get_profile()
    return pages.render_dashboard(counts, matches, queue, applied, profile,
                                  config=db.get_config(),
                                  checklist=db.get_login_checklist(),
                                  team=db.get_team())


@router.get("/profile", response_class=HTMLResponse)
def profile_form(request: Request):
    if not _authed(request):
        return _need_login()
    return pages.render_profile_form(db.get_profile())


@router.post("/profile")
async def profile_save(
    request: Request,
    name: str = Form(""), cv_name: str = Form(""), email: str = Form(""),
    phone: str = Form(""), city: str = Form(""), country: str = Form(""),
    dob: str = Form(""), degree: str = Form(""), institution: str = Form(""),
    session: str = Form(""), start_year: str = Form(""),
    education_status: str = Form(""), skills: str = Form(""),
    github: str = Form(""), linkedin: str = Form(""),
    pharmareg: str = Form(""), leadforge: str = Form(""),
    relocation: str = Form(""), daily_cap: str = Form("4"),
):
    if not _authed(request):
        return _need_login()
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
def api_status(request: Request):
    if not _authed(request):
        return JSONResponse({"ok": False, "error": "unauthorized"},
                            status_code=401)
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
    if isinstance(body.get("config"), dict):
        db.set_meta("config", body["config"])
    if isinstance(body.get("team"), dict):
        db.set_meta("team", body["team"])
    if isinstance(body.get("login_checklist"), str):
        db.set_meta("login_checklist", body["login_checklist"])
    if body.get("replace"):
        db.clear_matches_and_queue()
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
