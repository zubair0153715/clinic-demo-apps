"""No-Show Guard SaaS: JSON API + dashboard + Meta webhook + admin."""
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from . import auth, db, reminders, whatsapp
from pathlib import Path
from .dashboard import DASHBOARD_HTML, LANDING_HTML

# Review Booster shares this webhook entry: try rating replies first.
try:
    from app.reviews import engine as reviews_engine
except Exception:  # pragma: no cover
    reviews_engine = None

log = logging.getLogger("nsg.routes")
router = APIRouter(prefix="/saas")

SESSION_COOKIE = "nsg_session"


def current_clinic(nsg_session: str = Cookie(default="")) -> dict:
    c = auth.clinic_from_token(nsg_session)
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
    return HTMLResponse(DASHBOARD_HTML)


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


class LoginIn(BaseModel):
    email: str
    password: str


def _safe_clinic(c: dict) -> dict:
    return {k: c[k] for k in
            ("id", "name", "email", "whatsapp_number", "language", "timezone",
             "reminder_hours", "template_24h", "template_2h", "is_active", "plan")
            if k in c}


@router.post("/api/signup")
def signup(inp: SignupIn):
    try:
        c = auth.create_clinic(inp.name, inp.email, inp.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    token = auth.new_session(c["id"])
    resp = JSONResponse({"ok": True, "clinic": _safe_clinic(c)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=30 * 86400, httponly=True,
                    samesite="lax", path="/")
    return resp


@router.post("/api/login")
def login(inp: LoginIn):
    c = auth.authenticate(inp.email, inp.password)
    if not c:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not c["is_active"]:
        raise HTTPException(status_code=403, detail="account_disabled")
    token = auth.new_session(c["id"])
    resp = JSONResponse({"ok": True, "clinic": _safe_clinic(c)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=30 * 86400, httponly=True,
                    samesite="lax", path="/")
    return resp


@router.post("/api/logout")
def logout(nsg_session: str = Cookie(default="")):
    auth.destroy_session(nsg_session)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/api/me")
def me(clinic: dict = Depends(current_clinic)):
    c = auth.get_clinic(clinic["id"])
    return {"clinic": _safe_clinic(c), "whatsapp": whatsapp.provider_status()}


# ---------- appointments ----------

class ApptIn(BaseModel):
    patient_name: str
    patient_phone: str
    appointment_at: str  # ISO datetime with offset
    treatment: str = ""
    language: str = "en"


def _appt_row(r) -> dict:
    d = dict(r)
    return d


@router.get("/api/appointments")
def list_appointments(clinic: dict = Depends(current_clinic)):
    rows = db.qall(
        "SELECT * FROM appointments WHERE clinic_id=? ORDER BY appointment_at",
        (clinic["id"],))
    return {"appointments": [_appt_row(r) for r in rows]}


@router.post("/api/appointments")
def create_appointment(inp: ApptIn, clinic: dict = Depends(current_clinic)):
    try:
        dt = datetime.fromisoformat(inp.appointment_at)
    except Exception:
        raise HTTPException(status_code=400, detail="bad_datetime")
    if not inp.patient_name.strip() or not inp.patient_phone.strip():
        raise HTTPException(status_code=400, detail="name_and_phone_required")
    cur = db.q(
        "INSERT INTO appointments (clinic_id, patient_name, patient_phone, appointment_at,"
        " treatment, language, created_at) VALUES (?,?,?,?,?,?,?)",
        (clinic["id"], inp.patient_name.strip(), inp.patient_phone.strip(),
         dt.isoformat(), inp.treatment.strip(), inp.language or "en", db.now()))
    row = db.qone("SELECT * FROM appointments WHERE id=?", (cur.lastrowid,))
    return {"ok": True, "appointment": _appt_row(row)}


class ApptPatch(BaseModel):
    status: str = ""
    patient_name: str = ""
    patient_phone: str = ""
    appointment_at: str = ""
    treatment: str = ""
    language: str = ""


@router.patch("/api/appointments/{appt_id}")
def patch_appointment(appt_id: int, inp: ApptPatch, clinic: dict = Depends(current_clinic)):
    row = db.qone("SELECT * FROM appointments WHERE id=? AND clinic_id=?",
                  (appt_id, clinic["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    sets, args = [], []
    if inp.status in ("scheduled", "reminder_sent", "confirmed", "cancelled",
                      "completed", "no_show"):
        sets.append("status=?")
        args.append(inp.status)
    for field in ("patient_name", "patient_phone", "treatment", "language"):
        v = getattr(inp, field)
        if v:
            sets.append(f"{field}=?")
            args.append(v.strip())
    if inp.appointment_at:
        try:
            datetime.fromisoformat(inp.appointment_at)
        except Exception:
            raise HTTPException(status_code=400, detail="bad_datetime")
        sets.append("appointment_at=?")
        args.append(inp.appointment_at)
    if sets:
        args.append(appt_id)
        db.q(f"UPDATE appointments SET {', '.join(sets)} WHERE id=?", tuple(args))
    row = db.qone("SELECT * FROM appointments WHERE id=?", (appt_id,))
    return {"ok": True, "appointment": _appt_row(row)}


@router.delete("/api/appointments/{appt_id}")
def delete_appointment(appt_id: int, clinic: dict = Depends(current_clinic)):
    db.q("DELETE FROM appointments WHERE id=? AND clinic_id=?", (appt_id, clinic["id"]))
    return {"ok": True}


# ---------- settings ----------

class SettingsIn(BaseModel):
    name: str = ""
    whatsapp_number: str = ""
    language: str = ""
    timezone: str = ""
    reminder_hours: str = ""
    template_24h: str = ""
    template_2h: str = ""


@router.post("/api/settings")
def save_settings(inp: SettingsIn, clinic: dict = Depends(current_clinic)):
    fields = {}
    if inp.name.strip():
        fields["name"] = inp.name.strip()
    if inp.whatsapp_number is not None:
        fields["whatsapp_number"] = inp.whatsapp_number.strip()
    if inp.language in ("en", "ar"):
        fields["language"] = inp.language
    if inp.timezone.strip():
        fields["timezone"] = inp.timezone.strip()
    if inp.reminder_hours.strip():
        try:
            hours = json.loads(inp.reminder_hours)
            assert isinstance(hours, list) and all(float(h) > 0 for h in hours)
            fields["reminder_hours"] = json.dumps(sorted([float(h) for h in hours], reverse=True))
        except Exception:
            raise HTTPException(status_code=400, detail="bad_reminder_hours")
    # templates: empty string = reset to default
    fields["template_24h"] = inp.template_24h or ""
    fields["template_2h"] = inp.template_2h or ""
    auth.update_settings(clinic["id"], fields)
    return {"ok": True, "clinic": _safe_clinic(auth.get_clinic(clinic["id"]))}


# ---------- stats ----------

@router.get("/api/stats")
def stats(clinic: dict = Depends(current_clinic)):
    cid = clinic["id"]
    upcoming = db.qone(
        "SELECT COUNT(*) c FROM appointments WHERE clinic_id=? AND status IN "
        "('scheduled','reminder_sent') AND appointment_at > ?",
        (cid, datetime.now(timezone.utc).isoformat()))["c"]
    by_status = {r["status"]: r["c"] for r in db.qall(
        "SELECT status, COUNT(*) c FROM appointments WHERE clinic_id=? GROUP BY status",
        (cid,))}
    sent = db.qone(
        "SELECT COUNT(*) c FROM messages WHERE clinic_id=? AND direction='out'",
        (cid,))["c"]
    simulated = db.qone(
        "SELECT COUNT(*) c FROM messages WHERE clinic_id=? AND direction='out'"
        " AND status='simulated'", (cid,))["c"]
    recent = db.qall(
        "SELECT m.*, a.patient_name FROM messages m LEFT JOIN appointments a "
        "ON a.id=m.appointment_id WHERE m.clinic_id=? ORDER BY m.id DESC LIMIT 20",
        (cid,))
    return {
        "upcoming": upcoming,
        "by_status": by_status,
        "reminders_sent": sent,
        "simulated": simulated,
        "whatsapp": whatsapp.provider_status(),
        "recent_messages": [dict(r) for r in recent],
    }


# ---------- patient reply handling (shared) ----------

def handle_incoming(clinic_id: int, from_phone: str, text: str) -> dict:
    """Match a patient reply to their latest upcoming appointment and update it."""
    intent = whatsapp.parse_reply(text)
    db.q(
        "INSERT INTO messages (clinic_id, appointment_id, direction, body, created_at)"
        " VALUES (?,?,?,?,?)",
        (clinic_id, None, "in", text or "", db.now()))
    if intent == "unknown":
        return {"ok": True, "intent": "unknown"}
    row = db.qone(
        "SELECT * FROM appointments WHERE clinic_id=? AND patient_phone=? "
        "AND status IN ('scheduled','reminder_sent') ORDER BY appointment_at LIMIT 1",
        (clinic_id, from_phone))
    if not row:
        return {"ok": True, "intent": intent, "matched": False}
    new_status = "confirmed" if intent == "confirmed" else "cancelled"
    db.q("UPDATE appointments SET status=? WHERE id=?", (new_status, row["id"]))
    return {"ok": True, "intent": intent, "matched": True,
            "appointment_id": row["id"], "status": new_status}


class SimulateIn(BaseModel):
    appointment_id: int
    text: str


@router.post("/api/simulate-reply")
def simulate_reply(inp: SimulateIn, clinic: dict = Depends(current_clinic)):
    """Demo mode: pretend the patient replied on WhatsApp."""
    row = db.qone("SELECT * FROM appointments WHERE id=? AND clinic_id=?",
                  (inp.appointment_id, clinic["id"]))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    return handle_incoming(clinic["id"], row["patient_phone"], inp.text)


# ---------- Meta webhook ----------

@router.get("/webhook/whatsapp")
def webhook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge", "")
    expected = __import__("os").environ.get("SAAS_WHATSAPP_VERIFY_TOKEN", "")
    if mode == "subscribe" and expected and token == expected:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="verification_failed")


@router.post("/webhook/whatsapp")
async def webhook_receive(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}
    # Route incoming messages to the clinic owning the receiving number is
    # ambiguous in multi-tenant mode; match sender phone across active clinics.
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            val = change.get("value", {})
            for msg in val.get("messages", []):
                from_phone = msg.get("from", "")
                text = ((msg.get("text") or {}).get("body") or "").strip()
                if not from_phone:
                    continue
                # 1) Review Booster: pending rating requests get first pick
                if reviews_engine:
                    try:
                        if reviews_engine.handle_incoming_by_phone(from_phone, text).get("handled"):
                            continue
                    except Exception:
                        log.exception("review reply handling failed")
                # 2) No-Show Guard: match sender phone across active clinics
                hit = db.qone(
                    "SELECT clinic_id FROM appointments WHERE patient_phone=? "
                    "AND status IN ('scheduled','reminder_sent') LIMIT 1",
                    (from_phone,))
                if hit:
                    handle_incoming(hit["clinic_id"], from_phone, text)
    return {"ok": True}


# ---------- admin (Zubair: manual billing control) ----------

def _require_admin(x_admin_key: str = Header(default="")):
    if not auth.admin_key_ok(x_admin_key):
        raise HTTPException(status_code=403, detail="forbidden")


@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(
        "<!doctype html><html><head><meta charset=utf-8><meta name=viewport "
        "content='width=device-width,initial-scale=1'><title>No-Show Guard Admin</title>"
        "<style>body{font-family:system-ui;max-width:900px;margin:0 auto;padding:20px}"
        "table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:8px}"
        "input,button{padding:8px;margin:4px}</style></head><body>"
        "<h2>No-Show Guard — Admin</h2>"
        "<p>Enter your admin key (saved as a secret env var on the server), then manage clinics.</p>"
        "<input id=k type=password placeholder='Admin key' style='width:300px'>"
        "<button onclick='load()'>Load clinics</button><div id=out></div>"
        "<script>async function api(p,m,b){const r=await fetch(p,{method:m||'GET',"
        "headers:{'X-Admin-Key':document.getElementById('k').value,'Content-Type':'application/json'},"
        "body:b?JSON.stringify(b):undefined});return r.json()}"
        "async function load(){const d=await api('/saas/api/admin/clinics');"
        "if(d.detail){out.innerHTML='<b style=color:red>'+d.detail+'</b>';return}"
        "let h='<table><tr><th>ID</th><th>Clinic</th><th>Email</th><th>Appts</th>"
        "<th>Reminders</th><th>Active</th><th></th></tr>';"
        "for(const c of d.clinics){h+='<tr><td>'+c.id+'</td><td>'+c.name+'</td><td>'+c.email+'</td>"
        "<td>'+c.appointments+'</td><td>'+c.reminders+'</td><td>'+(c.is_active?'✅':'⛔')+'</td>"
        "<td><button onclick=\"toggle('+c.id+','+(c.is_active?0:1)+')\">'+(c.is_active?'Deactivate':'Activate')+'</button></td></tr>'}"
        "out.innerHTML=h+'</table>'}"
        "async function toggle(id,a){await api('/saas/api/admin/clinics/'+id,{active:!!a},'POST');load()}"
        "</script></body></html>")


@router.get("/api/admin/clinics")
def admin_list(_: None = Depends(_require_admin)):
    return {"clinics": auth.list_clinics()}


class ActiveIn(BaseModel):
    active: bool


@router.post("/api/admin/clinics/{clinic_id}")
def admin_toggle(clinic_id: int, inp: ActiveIn, _: None = Depends(_require_admin)):
    auth.set_active(clinic_id, inp.active)
    return {"ok": True}
