"""Review Booster: JSON API + dashboard + Meta webhook.

Reuses No-Show Guard clinic accounts (same login) via app.saas.auth.
"""
import logging
import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from app.saas import auth as nsg_auth
from app.saas import whatsapp

from . import db, engine
from pathlib import Path
from .dashboard import APP_HTML, LANDING_HTML

log = logging.getLogger("reviews.routes")
router = APIRouter(prefix="/reviews")

SESSION_COOKIE = "rb_session"
db.init()


def current_clinic(rb_session: str = Cookie(default="")) -> dict:
    c = nsg_auth.clinic_from_token(rb_session)
    if not c:
        raise HTTPException(status_code=401, detail="login_required")
    return c


# ---------- public pages ----------

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def landing():
    return HTMLResponse(LANDING_HTML)


@router.get("/app", response_class=HTMLResponse)
def app_page():
    return HTMLResponse(APP_HTML)


# ---------- PWA (installable) ----------
_PWA_DIR = Path(__file__).with_name("manifest.json").parent


@router.get("/manifest.json")
def pwa_manifest():
    return Response(content=(_PWA_DIR / "manifest.json").read_bytes(),
                    media_type="application/manifest+json")


@router.get("/sw.js")
def pwa_sw():
    return Response(content=(_PWA_DIR / "sw.js").read_bytes(),
                    media_type="application/javascript")


@router.get("/icon-192.png")
def pwa_icon192():
    return Response(content=(_PWA_DIR / "icon-192.png").read_bytes(),
                    media_type="image/png")


@router.get("/icon-512.png")
def pwa_icon512():
    return Response(content=(_PWA_DIR / "icon-512.png").read_bytes(),
                    media_type="image/png")


# ---------- auth (shared clinic accounts) ----------

class SignupIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def _safe_clinic(c: dict) -> dict:
    d = {k: c[k] for k in
         ("id", "name", "email", "whatsapp_number", "language", "is_active", "plan")
         if k in c}
    d["google_review_link"] = c.get("google_review_link") or ""
    return d


def _issue_session(c: dict) -> JSONResponse:
    token = nsg_auth.new_session(c["id"])
    resp = JSONResponse({"ok": True, "clinic": _safe_clinic(c)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=30 * 86400, httponly=True,
                    samesite="lax", path="/")
    return resp


@router.post("/api/signup")
def signup(inp: SignupIn):
    try:
        c = nsg_auth.create_clinic(inp.name, inp.email, inp.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _issue_session(c)


@router.post("/api/login")
def login(inp: LoginIn):
    c = nsg_auth.authenticate(inp.email, inp.password)
    if not c:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not c["is_active"]:
        raise HTTPException(status_code=403, detail="account_disabled")
    return _issue_session(c)


@router.post("/api/logout")
def logout(rb_session: str = Cookie(default="")):
    nsg_auth.destroy_session(rb_session)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/api/me")
def me(clinic: dict = Depends(current_clinic)):
    c = nsg_auth.get_clinic(clinic["id"])
    return {"clinic": _safe_clinic(c), "whatsapp": whatsapp.provider_status()}


# ---------- review requests ----------

@router.get("/api/requests")
def list_requests(clinic: dict = Depends(current_clinic)):
    rows = db.qall(
        "SELECT * FROM review_requests WHERE clinic_id=? ORDER BY id DESC LIMIT 100",
        (clinic["id"],))
    return {"requests": [dict(r) for r in rows]}


class SendNowIn(BaseModel):
    appointment_id: int


@router.post("/api/send-now")
def send_now(inp: SendNowIn, clinic: dict = Depends(current_clinic)):
    row = db.qone("SELECT * FROM appointments WHERE id=? AND clinic_id=?",
                  (inp.appointment_id, clinic["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    ok = engine.send_review_request(dict(clinic), dict(row))
    return {"ok": ok}


class SimulateIn(BaseModel):
    phone: str
    text: str


@router.post("/api/simulate-reply")
def simulate_reply(inp: SimulateIn, clinic: dict = Depends(current_clinic)):
    row = db.qone(
        "SELECT id FROM review_requests WHERE clinic_id=? AND patient_phone=? "
        "ORDER BY id DESC LIMIT 1",
        (clinic["id"], inp.phone.strip()))
    if not row:
        raise HTTPException(status_code=404, detail="no_pending_request")
    return engine.handle_incoming_by_phone(inp.phone.strip(), inp.text)


# ---------- feedback ----------

@router.get("/api/feedback")
def list_feedback(clinic: dict = Depends(current_clinic)):
    rows = db.qall(
        "SELECT * FROM feedback WHERE clinic_id=? ORDER BY id DESC LIMIT 100",
        (clinic["id"],))
    return {"feedback": [dict(r) for r in rows]}


# ---------- stats ----------

@router.get("/api/stats")
def stats(clinic: dict = Depends(current_clinic)):
    cid = clinic["id"]
    total = db.qone("SELECT COUNT(*) c FROM review_requests WHERE clinic_id=?", (cid,))["c"]
    responded = db.qone(
        "SELECT COUNT(*) c FROM review_requests WHERE clinic_id=? AND rating IS NOT NULL",
        (cid,))["c"]
    avg = db.qone(
        "SELECT AVG(rating) a FROM review_requests WHERE clinic_id=? AND rating IS NOT NULL",
        (cid,))["a"]
    low = db.qone(
        "SELECT COUNT(*) c FROM review_requests WHERE clinic_id=? AND rating IS NOT NULL"
        " AND rating <= 3", (cid,))["c"]
    dist = {r["rating"]: r["c"] for r in db.qall(
        "SELECT rating, COUNT(*) c FROM review_requests WHERE clinic_id=? "
        "AND rating IS NOT NULL GROUP BY rating", (cid,))}
    return {
        "total_requests": total,
        "responded": responded,
        "response_rate": round(100 * responded / total, 1) if total else 0,
        "avg_rating": round(avg, 2) if avg else None,
        "low_alerts": low,
        "distribution": dist,
        "whatsapp": whatsapp.provider_status(),
    }


# ---------- settings ----------

class SettingsIn(BaseModel):
    google_review_link: str = ""


@router.post("/api/settings")
def save_settings(inp: SettingsIn, clinic: dict = Depends(current_clinic)):
    db.q("UPDATE clinics SET google_review_link=? WHERE id=?",
         (inp.google_review_link.strip(), clinic["id"]))
    return {"ok": True, "clinic": _safe_clinic(nsg_auth.get_clinic(clinic["id"]))}


# ---------- eligible appointments (completed/past, no request yet) ----------

@router.get("/api/eligible")
def eligible(clinic: dict = Depends(current_clinic)):
    rows = db.qall(
        "SELECT a.* FROM appointments a LEFT JOIN review_requests r "
        "ON r.appointment_id=a.id WHERE a.clinic_id=? AND r.id IS NULL "
        "AND a.status IN ('completed','confirmed') ORDER BY a.appointment_at DESC LIMIT 50",
        (clinic["id"],))
    return {"appointments": [dict(r) for r in rows]}


# ---------- Meta webhook ----------

@router.get("/webhook/whatsapp")
def webhook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge", "")
    expected = os.environ.get("SAAS_WHATSAPP_VERIFY_TOKEN", "")
    if mode == "subscribe" and expected and token == expected:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification_failed")


@router.post("/webhook/whatsapp")
async def webhook_receive(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            for msg in val.get("messages", []):
                from_phone = msg.get("from", "")
                text = ((msg.get("text") or {}).get("body") or "").strip()
                if from_phone:
                    engine.handle_incoming_by_phone(from_phone, text)
    return {"ok": True}
