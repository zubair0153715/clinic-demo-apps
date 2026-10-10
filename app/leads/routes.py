"""Lead Qualifier: JSON API + dashboard + Meta webhook (agency tenants)."""
import logging
import os

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel

from app.saas import whatsapp

from . import auth, db, qualify
from pathlib import Path
from .dashboard import APP_HTML, LANDING_HTML

log = logging.getLogger("leads.routes")
router = APIRouter(prefix="/leads")

SESSION_COOKIE = "lq_session"


def current_agency(lq_session: str = Cookie(default="")) -> dict:
    a = auth.agency_from_token(lq_session)
    if not a:
        raise HTTPException(status_code=401, detail="login_required")
    return a


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


# ---------- auth ----------

class SignupIn(BaseModel):
    name: str
    email: str
    password: str
    agency_name: str = ""
    city: str = "Dubai"


class LoginIn(BaseModel):
    email: str
    password: str


def _safe_agency(a: dict) -> dict:
    return {k: a[k] for k in
            ("id", "name", "agency_name", "email", "phone", "city",
             "whatsapp_number", "language", "is_active", "plan") if k in a}


def _issue_session(a: dict) -> JSONResponse:
    token = auth.new_session(a["id"])
    resp = JSONResponse({"ok": True, "agency": _safe_agency(a)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=30 * 86400, httponly=True,
                    samesite="lax", path="/")
    return resp


@router.post("/api/signup")
def signup(inp: SignupIn):
    if inp.city not in ("Dubai", "Riyadh", "Jeddah", "Abu Dhabi", "Sharjah", "Doha", "Other"):
        raise HTTPException(status_code=400, detail="bad_city")
    try:
        a = auth.create_agency(inp.name, inp.agency_name, inp.email, inp.password, inp.city)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _issue_session(a)


@router.post("/api/login")
def login(inp: LoginIn):
    a = auth.authenticate(inp.email, inp.password)
    if not a:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not a["is_active"]:
        raise HTTPException(status_code=403, detail="account_disabled")
    return _issue_session(a)


@router.post("/api/logout")
def logout(lq_session: str = Cookie(default="")):
    auth.destroy_session(lq_session)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/api/me")
def me(agency: dict = Depends(current_agency)):
    a = auth.get_agency(agency["id"])
    return {"agency": _safe_agency(a), "whatsapp": whatsapp.provider_status()}


# ---------- leads ----------

@router.get("/api/leads")
def list_leads(agency: dict = Depends(current_agency)):
    rows = db.qall(
        "SELECT * FROM leads WHERE agency_id=? ORDER BY updated_at DESC LIMIT 200",
        (agency["id"],))
    counts = {r["score"]: r["c"] for r in db.qall(
        "SELECT score, COUNT(*) c FROM leads WHERE agency_id=? GROUP BY score",
        (agency["id"],))}
    return {"leads": [dict(r) for r in rows], "counts": counts}


@router.get("/api/leads/{lead_id}")
def lead_detail(lead_id: int, agency: dict = Depends(current_agency)):
    row = db.qone("SELECT * FROM leads WHERE id=? AND agency_id=?",
                  (lead_id, agency["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    msgs = db.qall("SELECT * FROM lead_messages WHERE lead_id=? ORDER BY id",
                   (lead_id,))
    return {"lead": dict(row), "messages": [dict(m) for m in msgs]}


class SimulateIn(BaseModel):
    phone: str
    text: str


@router.post("/api/simulate")
def simulate(inp: SimulateIn, agency: dict = Depends(current_agency)):
    """Demo: pretend a lead messaged on WhatsApp."""
    if not inp.phone.strip() or not inp.text.strip():
        raise HTTPException(status_code=400, detail="phone_and_text_required")
    return qualify.handle_incoming(agency["id"], inp.phone.strip(), inp.text.strip(),
                                   agency=auth.get_agency(agency["id"]))


class SendIn(BaseModel):
    lead_id: int
    text: str


@router.post("/api/send")
def agency_send(inp: SendIn, agency: dict = Depends(current_agency)):
    """Agency manually messages a lead."""
    row = db.qone("SELECT * FROM leads WHERE id=? AND agency_id=?",
                  (inp.lead_id, agency["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    res = whatsapp.send_text(row["phone"], inp.text.strip())
    qualify.log_msg(row["id"], "out", inp.text.strip())
    return {"ok": res["ok"], "simulated": res.get("simulated", False)}


# ---------- settings ----------

class SettingsIn(BaseModel):
    name: str = ""
    agency_name: str = ""
    phone: str = ""
    city: str = ""
    whatsapp_number: str = ""
    language: str = ""


@router.post("/api/settings")
def save_settings(inp: SettingsIn, agency: dict = Depends(current_agency)):
    fields = {}
    if inp.name.strip():
        fields["name"] = inp.name.strip()
    if inp.agency_name.strip():
        fields["agency_name"] = inp.agency_name.strip()
    if inp.phone is not None:
        fields["phone"] = inp.phone.strip()
    if inp.city in ("Dubai", "Riyadh", "Jeddah", "Abu Dhabi", "Sharjah", "Doha", "Other"):
        fields["city"] = inp.city
    if inp.whatsapp_number is not None:
        fields["whatsapp_number"] = inp.whatsapp_number.strip()
    if inp.language in ("en", "ar"):
        fields["language"] = inp.language
    auth.update_settings(agency["id"], fields)
    return {"ok": True, "agency": _safe_agency(auth.get_agency(agency["id"]))}


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
    """Route incoming messages to the agency.

    Multi-tenant routing: match the sender phone to an existing lead;
    otherwise attach to the most recently active agency (demo-friendly).
    In production each agency connects its own WhatsApp number; the
    receiving number (change.value.metadata.phone_number) selects the agency.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            recv_number = ((val.get("metadata") or {}).get("phone_number") or "").strip()
            for msg in val.get("messages", []):
                from_phone = msg.get("from", "")
                text = ((msg.get("text") or {}).get("body") or "").strip()
                if not from_phone:
                    continue
                agency = None
                if recv_number:
                    row = db.qone(
                        "SELECT * FROM agencies WHERE whatsapp_number=? AND is_active=1",
                        (recv_number,))
                    if row:
                        agency = dict(row)
                if not agency:
                    hit = db.qone(
                        "SELECT agency_id FROM leads WHERE phone=? ORDER BY updated_at DESC LIMIT 1",
                        (from_phone,))
                    if hit:
                        agency = auth.get_agency(hit["agency_id"])
                if not agency:
                    row = db.qone("SELECT * FROM agencies WHERE is_active=1 ORDER BY id DESC LIMIT 1")
                    agency = dict(row) if row else None
                if agency:
                    try:
                        qualify.handle_incoming(agency["id"], from_phone, text, agency=agency)
                    except Exception:
                        log.exception("lead qualify failed")
    return {"ok": True}
