"""Hotel PMS v1 — single-hotel property management system. Route: /hotelpms

Modules: rooms/rack, reservations, front desk, housekeeping, restaurant POS-lite,
FBR-core billing (SRB 8% card / 15% cash + FBR invoice JSON + QR, TEST MODE default),
guest CRM, reports, marriage-hall events, owner + staff-PIN auth.

Demo seed: owner@demo.pk / demo1234 (owner), PIN 1234 (receptionist Ahmed).
"""
import html
import io
import json
import time
from datetime import date, timedelta

from fastapi import APIRouter, Request, Form
from fastapi.responses import (HTMLResponse, RedirectResponse, FileResponse,
                               StreamingResponse)

from app.hotelpms import db, auth, fbr, i18n

router = APIRouter()


# ------------------------------------------------------------------ helpers
def _lang(request: Request) -> str:
    """Effective UI language: cookie override, else hotel setting."""
    c = (request.cookies.get("hp_lang", "") or "").strip()
    if c in ("en", "ur"):
        return c
    return (db.get_settings().get("lang") or "en")


def _tr(request: Request):
    lang = _lang(request)
    return lambda s: i18n.T(s, lang)
def money(x) -> str:
    try:
        return f"Rs {float(x):,.0f}"
    except Exception:
        return "Rs 0"


def today_str() -> str:
    return date.today().isoformat()


def current_user(request: Request):
    return auth.user_from_token(request.cookies.get(auth.COOKIE, ""))


def need_login(request: Request):
    u = current_user(request)
    if not u:
        return None
    return u


def need_owner(request: Request):
    u = current_user(request)
    if not u or not auth.is_owner(u):
        return None
    return u


def login_redirect():
    return RedirectResponse("/hotelpms/login", status_code=303)


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;
background:#f1f5f9;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px}
.nav{background:#0f172a;color:#fff;padding:10px 0;position:sticky;top:0;z-index:5}
.nav a{color:#e2e8f0;text-decoration:none;margin-right:16px;font-size:.9rem;font-weight:600}
.nav a.brand{color:#fff;font-size:1.05rem;font-weight:800;margin-right:24px}
.nav .who{float:right;color:#94a3b8;font-size:.85rem}
h1{font-size:1.5rem;margin:18px 0 6px}h2{font-size:1.15rem;margin:20px 0 8px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:14px 0}
.card{background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card .big{font-size:1.7rem;font-weight:800}.card .lbl{color:#64748b;font-size:.85rem}
.panel{background:#fff;border-radius:12px;padding:18px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.08)}
table{border-collapse:collapse;width:100%;background:#fff;font-size:.92rem}
td,th{border:1px solid #e2e8f0;padding:8px 10px;text-align:left}th{background:#f8fafc}
.btn{display:inline-block;background:#2563eb;color:#fff;font-weight:700;padding:9px 18px;border-radius:9px;
text-decoration:none;margin:4px 6px 4px 0;border:0;cursor:pointer;font-size:.95rem}
.btn.green{background:#16a34a}.btn.red{background:#dc2626}.btn.gray{background:#64748b}
.btn.amber{background:#d97706}.btn.small{padding:6px 12px;font-size:.85rem}
input,select,textarea{padding:9px 11px;border:1px solid #cbd5e1;border-radius:8px;font-size:1rem;
margin:4px 0;width:100%;box-sizing:border-box}
label{font-weight:600;font-size:.9rem;display:block;margin-top:10px}
.formrow{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.rack{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px;margin:12px 0}
.room{border-radius:10px;padding:12px;text-align:center;color:#fff;font-weight:700;cursor:pointer}
.room .n{font-size:1.3rem}.room .t{font-size:.75rem;font-weight:400;opacity:.9}
.st-ready{background:#16a34a}.st-occupied{background:#dc2626}.st-dirty{background:#d97706}
.st-cleaning{background:#2563eb}.st-maintenance{background:#475569}
.alert{background:#fef3c7;border:1px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:12px 0}
.ok{background:#dcfce7;border:1px solid #16a34a;border-radius:10px;padding:12px 16px;margin:12px 0}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.78rem;font-weight:700;color:#fff}
.b-confirmed{background:#2563eb}.b-checked_in{background:#16a34a}.b-checked_out{background:#64748b}
.b-cancelled{background:#dc2626}.b-booked{background:#7c3aed}.b-completed{background:#16a34a}
.task{border-left:4px solid #d97706;background:#fff;padding:10px 14px;border-radius:8px;margin:8px 0;
box-shadow:0 1px 2px rgba(0,0,0,.06)}
.task.done{border-color:#16a34a;opacity:.7}
.inv{max-width:700px;margin:0 auto;background:#fff;padding:28px;border-radius:8px}
.inv h2{margin:0}.inv .qr{float:right;text-align:center}
table.inv-tbl td,table.inv-tbl th{border:0;border-bottom:1px solid #e2e8f0}
@media print{.nav,.noprint{display:none}body{background:#fff}.inv{box-shadow:none}}
footer{padding:24px 0;color:#94a3b8;font-size:.85rem;text-align:center}
"""


def _page(title, body, user=None, lang="en"):
    s = db.get_settings()
    who = ""
    if user:
        who = (f"<span class='who'>{html.escape(user['name'] or user.get('email',''))} "
               f"({html.escape(user['role'])}) · <a href='/hotelpms/logout' "
               f"style='color:#fbbf24'>logout</a></span>")
    other = "en" if lang == "ur" else "ur"
    other_lbl = "EN" if lang == "ur" else "اردو"
    T = lambda x: i18n.T(x, lang)
    nav = f"""
<div class="nav"><div class="wrap">{who}
<a class="brand" href="/hotelpms">🏨 {html.escape(s['hotel_name'] or 'Hotel PMS')}</a>
<a href="/hotelpms/rooms">{T('Rooms')}</a><a href="/hotelpms/bookings">{T('Bookings')}</a>
<a href="/hotelpms/frontdesk">{T('Front Desk')}</a><a href="/hotelpms/housekeeping">{T('Housekeeping')}</a>
<a href="/hotelpms/restaurant">{T('Restaurant')}</a><a href="/hotelpms/inventory">{T('Inventory')}</a>
<a href="/hotelpms/payroll">{T('Payroll')}</a><a href="/hotelpms/guests">{T('Guests')}</a>
<a href="/hotelpms/events">{T('Events')}</a><a href="/hotelpms/reports">{T('Reports')}</a>
<a href="/hotelpms/settings">⚙️</a>
<a href="/hotelpms/lang/{other}" style="float:right;color:#fbbf24;font-weight:800">{other_lbl}</a></div></div>"""
    rtl = ' lang="ur" dir="rtl"' if lang == "ur" else ' lang="en"'
    return f"""<!doctype html><html{rtl}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Hotel PMS</title><style>{CSS}</style></head><body>
{nav}<div class="wrap">{body}</div>
<footer>Hotel PMS v2 · FBR mode: {html.escape(s['fbr_mode']).upper()} (test = not submitted)</footer>
</body></html>"""


def page(title, body, request):
    u = current_user(request)
    if not u:
        return login_redirect()
    return HTMLResponse(_page(title, body, u, _lang(request)))


@router.get("/hotelpms/lang/{lang}")
def lang_switch(lang: str, request: Request):
    """UI language toggle — cookie + hotel default."""
    resp = RedirectResponse(request.headers.get("referer", "/hotelpms"), status_code=303)
    if lang in ("en", "ur"):
        resp.set_cookie("hp_lang", lang, max_age=365 * 86400)
        u = current_user(request)
        if u and auth.is_owner(u):
            db.q("UPDATE settings SET lang=?, updated_at=? WHERE id=1",
                 (lang, db.now()))
    return resp


# -------------------------------------------------------------------- auth
@router.get("/hotelpms/login", response_class=HTMLResponse)
def login_form(request: Request):
    T = _tr(request)
    return HTMLResponse(_page(T("Login"), f"""
<h1>🏨 Hotel PMS — {T('Login')}</h1>
<div class="panel" style="max-width:420px">
<form method="post" action="/hotelpms/login/owner">
<h2>{T('Owner login')}</h2>
<label>{T('Email')}</label><input type="email" name="email" required>
<label>{T('Password')}</label><input type="password" name="password" required>
<button class="btn" type="submit">{T('Login as Owner')}</button>
</form></div>
<div class="panel" style="max-width:420px">
<form method="post" action="/hotelpms/login/pin">
<h2>{T('Staff login (PIN)')}</h2>
<label>{T('4-digit PIN')}</label><input type="password" name="pin" maxlength="8" required>
<button class="btn green" type="submit">{T('Login as Staff')}</button>
</form></div>
<p style="color:#64748b;font-size:.9rem">Demo: owner@demo.pk / demo1234 · staff PIN 1234</p>
""", None, _lang(request)))


@router.post("/hotelpms/login/owner")
def login_owner(email: str = Form(""), password: str = Form("")):
    u = auth.authenticate_owner(email, password)
    if not u:
        return HTMLResponse(_page("Login failed",
            '<div class="alert">❌ Wrong email or password. <a href="/hotelpms/login">Try again</a></div>',
            None, "en"),
            status_code=401)
    resp = RedirectResponse("/hotelpms", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.new_session(u["id"]), max_age=30 * 86400, httponly=True)
    return resp


@router.post("/hotelpms/login/pin")
def login_pin(pin: str = Form("")):
    u = auth.authenticate_pin(pin)
    if not u:
        return HTMLResponse(_page("Login failed",
            '<div class="alert">❌ Wrong PIN. <a href="/hotelpms/login">Try again</a></div>',
            None, "en"),
            status_code=401)
    resp = RedirectResponse("/hotelpms", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.new_session(u["id"]), max_age=30 * 86400, httponly=True)
    return resp


@router.get("/hotelpms/logout")
def logout(request: Request):
    auth.destroy_session(request.cookies.get(auth.COOKIE, ""))
    resp = RedirectResponse("/hotelpms/login", status_code=303)
    resp.delete_cookie(auth.COOKIE)
    return resp


# --------------------------------------------------------------- dashboard
@router.get("/hotelpms", response_class=HTMLResponse)
@router.get("/hotelpms/", response_class=HTMLResponse)
def dashboard(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    T = _tr(request)
    total_rooms = db.qone("SELECT COUNT(*) c FROM rooms")["c"]
    occupied = db.qone("SELECT COUNT(*) c FROM rooms WHERE status='occupied'")["c"]
    occ_pct = round(occupied / total_rooms * 100) if total_rooms else 0
    today0 = int(time.mktime(date.today().timetuple()))
    rev = db.qone("SELECT COALESCE(SUM(total),0) t FROM invoices WHERE created_at>=?",
                  (today0,))["t"]
    arrivals = db.qall(
        "SELECT b.*, g.name gname FROM bookings b JOIN guests g ON g.id=b.guest_id "
        "WHERE b.status='confirmed' AND b.check_in_date=?", (today_str(),))
    inhouse = db.qall(
        "SELECT s.*, g.name gname, r.number rno FROM stays s "
        "JOIN guests g ON g.id=s.guest_id JOIN rooms r ON r.id=s.room_id "
        "WHERE s.status='active'")
    open_tasks = db.qone(
        "SELECT COUNT(*) c FROM housekeeping_tasks WHERE status!='done'")["c"]
    arr_html = "".join(
        f"<tr><td>{html.escape(a['gname'])}</td><td>{a['check_in_date']} → {a['check_out_date']}</td>"
        f"<td>{a['nights']}n</td><td>{money(a['rate'])}</td>"
        f"<td><a class='btn small' href='/hotelpms/frontdesk/checkin?booking_id={a['id']}'>{T('Check-in')}</a></td></tr>"
        for a in arrivals) or f"<tr><td colspan=5>{T('No arrivals today.')}</td></tr>"
    inh_html = "".join(
        f"<tr><td>{T('Room')} {html.escape(s['rno'])}</td><td>{html.escape(s['gname'])}</td>"
        f"<td><a class='btn small amber' href='/hotelpms/billing/{s['id']}'>{T('Bill / Check-out')}</a></td></tr>"
        for s in inhouse) or f"<tr><td colspan=3>{T('No in-house guests.')}</td></tr>"
    body = f"""
<h1>📊 {T('Dashboard')}</h1>
<div class="cards">
<div class="card"><div class="big">{occ_pct}%</div><div class="lbl">{T('Occupancy')} ({occupied}/{total_rooms} {T('rooms')})</div></div>
<div class="card"><div class="big">{money(rev)}</div><div class="lbl">{T('Revenue today')}</div></div>
<div class="card"><div class="big">{len(arrivals)}</div><div class="lbl">{T('Arrivals today')}</div></div>
<div class="card"><div class="big">{len(inhouse)}</div><div class="lbl">{T('In-house guests')}</div></div>
<div class="card"><div class="big">{open_tasks}</div><div class="lbl">{T('Open housekeeping tasks')}</div></div>
</div>
<div class="panel"><h2>🛎️ {T("Today's arrivals")}</h2>
<table><tr><th>{T('Guest')}</th><th>{T('Dates')}</th><th>{T('Nights')}</th><th>{T('Rate')}</th><th></th></tr>{arr_html}</table></div>
<div class="panel"><h2>🛏️ {T('In-house guests')}</h2>
<table><tr><th>{T('Room')}</th><th>{T('Guest')}</th><th></th></tr>{inh_html}</table></div>
<p><a class="btn" href="/hotelpms/bookings/new">{T('+ New Booking')}</a>
<a class="btn green" href="/hotelpms/rooms">{T('Room Rack')}</a>
<a class="btn amber" href="/hotelpms/restaurant">{T('Restaurant POS')}</a></p>
"""
    return HTMLResponse(_page(T("Dashboard"), body, u, _lang(request)))

# ------------------------------------------------------------------- rooms
@router.get("/hotelpms/rooms", response_class=HTMLResponse)
def rooms(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    rows = db.qall(
        "SELECT r.*, t.name tname, t.rate FROM rooms r JOIN room_types t ON t.id=r.room_type_id "
        "ORDER BY r.number")
    rack = "".join(
        f"<div class='room st-{r['status']}' title='{html.escape(r['tname'])} — {money(r['rate'])}'>"
        f"<div class='n'>{html.escape(r['number'])}</div><div class='t'>{r['status'].title()}</div></div>"
        for r in rows)
    tbl = "".join(
        f"<tr><td><b>{html.escape(r['number'])}</b></td><td>{html.escape(r['tname'])}</td>"
        f"<td>{money(r['rate'])}</td><td>{r['status'].title()}</td>"
        f"<td><form method='post' action='/hotelpms/rooms/{r['id']}/status' style='display:inline'>"
        f"<select name='status' onchange='this.form.submit()'>"
        + "".join(f"<option value='{s}' {'selected' if r['status']==s else ''}>{s.title()}</option>"
                  for s in ("ready", "occupied", "dirty", "cleaning", "maintenance"))
        + "</select></form></td></tr>"
        for r in rows)
    types = db.qall("SELECT * FROM room_types")
    type_opts = "".join(f"<option value='{t['id']}'>{html.escape(t['name'])} — {money(t['rate'])}</option>"
                        for t in types)
    body = f"""
<h1>🛏️ {T('Room Rack')}</h1>
<div class="rack">{rack}</div>
<div class="panel"><h2>{T('Manage rooms')}</h2>
<table><tr><th>{T('Room')}</th><th>{T('Type')}</th><th>{T('Rate')}</th><th>{T('Status')}</th><th>{T('Change')}</th></tr>{tbl}</table></div>
<div class="panel"><h2>{T('+ Add room')}</h2>
<form method="post" action="/hotelpms/rooms/add"><div class="formrow">
<div><label>{T('Room number')}</label><input name="number" required></div>
<div><label>{T('Type')}</label><select name="room_type_id">{type_opts}</select></div>
</div><button class="btn" type="submit">{T('Add room')}</button></form></div>
<div class="panel"><h2>{T('Room types')}</h2>
<table><tr><th>{T('Type')}</th><th>{T('Rate/night')}</th><th>{T('Description')}</th></tr>
{"".join(f"<tr><td>{html.escape(t['name'])}</td><td>{money(t['rate'])}</td><td>{html.escape(t['description'])}</td></tr>" for t in types)}
</table>
<form method="post" action="/hotelpms/roomtypes/add" style="margin-top:10px"><div class="formrow">
<div><label>{T('Name')}</label><input name="name" required></div>
<div><label>{T('Rate/night')}</label><input name="rate" type="number" min="0" required></div>
</div><button class="btn small" type="submit">{T('Add type')}</button></form></div>
"""
    return HTMLResponse(_page(T("Rooms"), body, u, _lang(request)))


@router.post("/hotelpms/rooms/add")
def room_add(request: Request, number: str = Form(""), room_type_id: int = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    try:
        db.q("INSERT INTO rooms (number, room_type_id, status) VALUES (?,?, 'ready')",
             (number.strip(), room_type_id))
    except Exception:
        pass
    return RedirectResponse("/hotelpms/rooms", status_code=303)


@router.post("/hotelpms/rooms/{rid}/status")
def room_status(request: Request, rid: int, status: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    if status in ("ready", "occupied", "dirty", "cleaning", "maintenance"):
        db.q("UPDATE rooms SET status=? WHERE id=?", (status, rid))
    return RedirectResponse("/hotelpms/rooms", status_code=303)


@router.post("/hotelpms/roomtypes/add")
def roomtype_add(request: Request, name: str = Form(""), rate: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("INSERT INTO room_types (name, rate) VALUES (?,?)", (name.strip(), rate))
    return RedirectResponse("/hotelpms/rooms", status_code=303)


# --------------------------------------------------------------- bookings
@router.get("/hotelpms/bookings", response_class=HTMLResponse)
def bookings(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    rows = db.qall(
        "SELECT b.*, g.name gname, g.phone, t.name tname FROM bookings b "
        "JOIN guests g ON g.id=b.guest_id JOIN room_types t ON t.id=b.room_type_id "
        "ORDER BY b.check_in_date DESC LIMIT 100")
    tbl = "".join(
        f"<tr><td>#{b['id']}</td><td>{html.escape(b['gname'])}</td><td>{html.escape(b['tname'])}</td>"
        f"<td>{b['check_in_date']} → {b['check_out_date']}</td><td>{b['nights']}n</td>"
        f"<td>{money(b['advance'])}</td><td><span class='badge b-{b['status']}'>{b['status'].replace('_',' ').title()}</span></td>"
        f"<td>" + (
            f"<a class='btn small' href='/hotelpms/frontdesk/checkin?booking_id={b['id']}'>{T('Check-in')}</a> "
            f"<form method='post' action='/hotelpms/bookings/{b['id']}/cancel' style='display:inline'>"
            f"<button class='btn small red' type='submit'>{T('Cancel')}</button></form>"
            if b['status'] == 'confirmed' else "") + "</td></tr>"
        for b in rows) or f"<tr><td colspan=8>{T('No bookings.')}</td></tr>"
    body = f"""
<h1>📅 {T('Reservations')}</h1>
<p><a class="btn" href="/hotelpms/bookings/new">{T('+ New Booking')}</a></p>
<div class="panel"><table>
<tr><th>{T('ID')}</th><th>{T('Guest')}</th><th>{T('Type')}</th><th>{T('Dates')}</th><th>{T('Nights')}</th><th>{T('Advance')}</th><th>{T('Status')}</th><th></th></tr>
{tbl}</table></div>
"""
    return HTMLResponse(_page(T("Bookings"), body, u, _lang(request)))


@router.get("/hotelpms/bookings/new", response_class=HTMLResponse)
def booking_new(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    types = db.qall("SELECT * FROM room_types")
    type_opts = "".join(f"<option value='{t['id']}'>{html.escape(t['name'])} — {money(t['rate'])}</option>"
                        for t in types)
    d0, d1 = today_str(), (date.today() + timedelta(days=1)).isoformat()
    body = f"""
<h1>📅 {T('New Booking')}</h1>
<div class="panel"><form method="post" action="/hotelpms/bookings/create">
<div class="formrow">
<div><label>{T('Guest name')}</label><input name="guest_name" required></div>
<div><label>{T('Phone')}</label><input name="phone"></div></div>
<div class="formrow">
<div><label>{T('CNIC / Passport')}</label><input name="cnic"></div>
<div><label>{T('Source')}</label><select name="source">
<option>walk-in</option><option>phone</option><option>online</option></select></div></div>
<div class="formrow">
<div><label>{T('Room type')}</label><select name="room_type_id">{type_opts}</select></div>
<div><label>{T('Check-in / Check-out')}</label>
<div style="display:flex;gap:8px"><input type="date" name="check_in" value="{d0}" required>
<input type="date" name="check_out" value="{d1}" required></div></div></div>
<div class="formrow">
<div><label>{T('Advance (Rs)')}</label><input type="number" name="advance" min="0" value="0"></div>
<div><label>{T('Notes')}</label><input name="notes"></div></div>
<button class="btn" type="submit">{T('Create booking')}</button></form></div>
"""
    return HTMLResponse(_page(T("New Booking"), body, u, _lang(request)))


@router.post("/hotelpms/bookings/create")
def booking_create(request: Request, guest_name: str = Form(""), phone: str = Form(""),
                   cnic: str = Form(""), source: str = Form("walk-in"),
                   room_type_id: int = Form(0), check_in: str = Form(""),
                   check_out: str = Form(""), advance: float = Form(0), notes: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    rt = db.qone("SELECT * FROM room_types WHERE id=?", (room_type_id,))
    if not rt:
        return RedirectResponse("/hotelpms/bookings/new", status_code=303)
    nights = max(1, (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days)
    g = db.qone("SELECT * FROM guests WHERE phone=? AND phone!=''", (phone.strip(),)) if phone.strip() else None
    if g:
        gid = g["id"]
        db.q("UPDATE guests SET repeat_count=repeat_count+1 WHERE id=?", (gid,))
    else:
        cur = db.q("INSERT INTO guests (name, cnic, phone, repeat_count, created_at) VALUES (?,?,?,?,?)",
                   (guest_name.strip(), cnic.strip(), phone.strip(), 1, db.now()))
        gid = cur.lastrowid
    db.q("""INSERT INTO bookings (guest_id, room_type_id, check_in_date, check_out_date, nights,
           rate, advance, status, source, created_at, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
         (gid, room_type_id, check_in, check_out, nights, rt["rate"], advance,
          "confirmed", source, db.now(), u["name"] or u["role"]))
    return RedirectResponse("/hotelpms/bookings", status_code=303)


@router.post("/hotelpms/bookings/{bid}/cancel")
def booking_cancel(request: Request, bid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE bookings SET status='cancelled' WHERE id=? AND status='confirmed'", (bid,))
    return RedirectResponse("/hotelpms/bookings", status_code=303)


# -------------------------------------------------------------- front desk
@router.get("/hotelpms/frontdesk", response_class=HTMLResponse)
def frontdesk(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    arrivals = db.qall(
        "SELECT b.*, g.name gname FROM bookings b JOIN guests g ON g.id=b.guest_id "
        "WHERE b.status='confirmed' ORDER BY b.check_in_date LIMIT 20")
    inhouse = db.qall(
        "SELECT s.*, g.name gname, r.number rno FROM stays s "
        "JOIN guests g ON g.id=s.guest_id JOIN rooms r ON r.id=s.room_id "
        "WHERE s.status='active'")
    arr = "".join(
        f"<tr><td>{html.escape(a['gname'])}</td><td>{a['check_in_date']} → {a['check_out_date']}</td>"
        f"<td><a class='btn small' href='/hotelpms/frontdesk/checkin?booking_id={a['id']}'>{T('Check-in →')}</a></td></tr>"
        for a in arrivals) or f"<tr><td colspan=3>{T('No pending arrivals.')}</td></tr>"
    inh = "".join(
        f"<tr><td>{T('Room')} {html.escape(s['rno'])}</td><td>{html.escape(s['gname'])}</td>"
        f"<td><a class='btn small amber' href='/hotelpms/billing/{s['id']}'>{T('Bill / Check-out')}</a></td></tr>"
        for s in inhouse) or f"<tr><td colspan=3>{T('No in-house guests.')}</td></tr>"
    body = f"""
<h1>🛎️ {T('Front Desk')}</h1>
<div class="panel"><h2>{T('Arrivals (check-in)')}</h2>
<table><tr><th>{T('Guest')}</th><th>{T('Booking')}</th><th></th></tr>{arr}</table></div>
<div class="panel"><h2>{T('In-house (check-out)')}</h2>
<table><tr><th>{T('Room')}</th><th>{T('Guest')}</th><th></th></tr>{inh}</table></div>
"""
    return HTMLResponse(_page(T("Front Desk"), body, u, _lang(request)))


@router.get("/hotelpms/frontdesk/checkin", response_class=HTMLResponse)
def checkin_form(request: Request, booking_id: int = 0):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    b = db.qone(
        "SELECT b.*, g.name gname, g.cnic, g.phone FROM bookings b JOIN guests g ON g.id=b.guest_id "
        "WHERE b.id=?", (booking_id,))
    if not b or b["status"] != "confirmed":
        return RedirectResponse("/hotelpms/frontdesk", status_code=303)
    free = db.qall(
        "SELECT r.* FROM rooms r WHERE r.room_type_id=? AND r.status='ready' ORDER BY r.number",
        (b["room_type_id"],))
    opts = "".join(f"<option value='{r['id']}'>{T('Room')} {html.escape(r['number'])}</option>" for r in free)
    if not opts:
        opts = f"<option value=''>— {T('no ready rooms of this type')} —</option>"
    body = f"""
<h1>🛎️ {T('Check-in')} — {html.escape(b['gname'])}</h1>
<div class="panel"><form method="post" action="/hotelpms/frontdesk/checkin">
<input type="hidden" name="booking_id" value="{b['id']}">
<div class="formrow">
<div><label>{T('Guest name')}</label><input value="{html.escape(b['gname'])}" disabled></div>
<div><label>{T('CNIC / Passport')}</label><input name="cnic" value="{html.escape(b['cnic'] or '')}" required></div></div>
<div class="formrow">
<div><label>{T('Assign room')}</label><select name="room_id" required>{opts}</select></div>
<div><label>{T('Rate/night')}</label><input value="{money(b['rate'])}" disabled></div></div>
<p>{T('Booking')}: {b['check_in_date']} → {b['check_out_date']} ({b['nights']} {T('Nights')}) ·
{T('Advance paid')}: {money(b['advance'])}</p>
<button class="btn green" type="submit">✅ {T('Check-in')} (2-minute flow)</button></form></div>
"""
    return HTMLResponse(_page(T("Check-in"), body, u, _lang(request)))


@router.post("/hotelpms/frontdesk/checkin")
def checkin_do(request: Request, booking_id: int = Form(0), room_id: int = Form(0),
               cnic: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    b = db.qone("SELECT * FROM bookings WHERE id=? AND status='confirmed'", (booking_id,))
    r = db.qone("SELECT * FROM rooms WHERE id=? AND status='ready'", (room_id,))
    if not b or not r:
        return RedirectResponse("/hotelpms/frontdesk", status_code=303)
    if cnic.strip():
        db.q("UPDATE guests SET cnic=? WHERE id=?", (cnic.strip(), b["guest_id"]))
    folio_no = f"F-{1000 + db.qone('SELECT COUNT(*) c FROM stays')['c'] + 1}"
    cur = db.q(
        "INSERT INTO stays (booking_id, guest_id, room_id, check_in_at, status, folio_no) "
        "VALUES (?,?,?,?,?,?)",
        (booking_id, b["guest_id"], room_id, db.now(), "active", folio_no))
    sid = cur.lastrowid
    db.q("""INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at, created_by)
            VALUES (?,?,?,?,?,?,?,?)""",
         (sid, "room", f"Room {r['number']} — {b['nights']} night(s)", b["nights"],
          b["rate"], b["nights"] * b["rate"], db.now(), u["name"] or u["role"]))
    if b["advance"] > 0:
        db.q("""INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at)
                VALUES (?,?,?,?,?,?,?)""",
             (sid, "discount", f"Advance paid (booking #{booking_id})", 1, -b["advance"],
              -b["advance"], db.now()))
    db.q("UPDATE rooms SET status='occupied' WHERE id=?", (room_id,))
    db.q("UPDATE bookings SET status='checked_in', room_id=? WHERE id=?", (room_id, booking_id))
    return RedirectResponse(f"/hotelpms/billing/{sid}", status_code=303)

# ------------------------------------------------------------ housekeeping
@router.get("/hotelpms/housekeeping", response_class=HTMLResponse)
def housekeeping(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    tasks = db.qall(
        "SELECT t.*, r.number rno FROM housekeeping_tasks t JOIN rooms r ON r.id=t.room_id "
        "ORDER BY CASE t.status WHEN 'open' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END, t.created_at DESC")
    def tcard(t):
        cls = "done" if t["status"] == "done" else ""
        acts = ""
        if t["status"] == "open":
            acts = (f"<form method='post' action='/hotelpms/housekeeping/{t['id']}/start' style='display:inline'>"
                    f"<button class='btn small' type='submit'>▶ {T('Start')}</button></form>")
        elif t["status"] == "in_progress":
            acts = (f"<form method='post' action='/hotelpms/housekeeping/{t['id']}/done' style='display:inline'>"
                    f"<button class='btn small green' type='submit'>✅ {T('Done')}</button></form>")
        assigned = f" <span style='color:#64748b'>({html.escape(t['assigned_to'])})</span>" if t["assigned_to"] else ""
        return (f"<div class='task {cls}'><b>{T('Room')} {html.escape(t['rno'])}</b> · "
                f"{html.escape(t['task_type'].title())} · {t['status'].replace('_',' ').title()}<br>"
                f"{html.escape(t['description'])}{assigned}<br>{acts}</div>")
    open_h = "".join(tcard(t) for t in tasks if t["status"] != "done") or f"<p>{T('No open tasks.')}</p>"
    done_h = "".join(tcard(t) for t in tasks if t["status"] == "done") or f"<p>{T('None yet.')}</p>"
    dirty_rooms = db.qall("SELECT * FROM rooms WHERE status IN ('dirty','cleaning') ORDER BY number")
    dopts = "".join(f"<option value='{r['id']}'>{T('Room')} {html.escape(r['number'])} ({r['status']})</option>"
                    for r in dirty_rooms)
    body = f"""
<h1>🧹 {T('Housekeeping')}</h1>
<div class="panel"><h2>{T('Open tasks')}</h2>{open_h}</div>
<div class="panel"><h2>{T('+ New task / complaint')}</h2>
<form method="post" action="/hotelpms/housekeeping/add"><div class="formrow">
<div><label>{T('Room')}</label><select name="room_id">
{"".join(f"<option value='{r['id']}'>{T('Room')} {html.escape(r['number'])}</option>" for r in db.qall('SELECT * FROM rooms ORDER BY number'))}
</select></div>
<div><label>{T('Type')}</label><select name="task_type"><option>cleaning</option><option>maintenance</option></select></div>
</div><label>{T('Description')}</label><input name="description" placeholder="e.g. AC not cooling" required>
<label>{T('Assigned to')}</label><input name="assigned_to" placeholder="e.g. Cleaner team">
<button class="btn" type="submit">{T('Add task')}</button></form></div>
<div class="panel"><h2>{T('Quick: mark room dirty → auto task')}</h2>
<form method="post" action="/hotelpms/housekeeping/markdirty" style="display:flex;gap:8px">
<select name="room_id">{dopts or f"<option value=''>{T('all clean')}</option>"}</select>
<button class="btn amber" type="submit">{T('Mark dirty + task')}</button></form></div>
<div class="panel"><h2>{T('Completed')}</h2>{done_h}</div>
"""
    return HTMLResponse(_page(T("Housekeeping"), body, u, _lang(request)))


@router.post("/hotelpms/housekeeping/add")
def hk_add(request: Request, room_id: int = Form(0), task_type: str = Form("cleaning"),
           description: str = Form(""), assigned_to: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("""INSERT INTO housekeeping_tasks (room_id, task_type, description, status, assigned_to, created_at)
            VALUES (?,?,?,?,?,?)""",
         (room_id, task_type, description.strip(), "open", assigned_to.strip(), db.now()))
    if task_type == "cleaning":
        db.q("UPDATE rooms SET status='dirty' WHERE id=? AND status='ready'", (room_id,))
    return RedirectResponse("/hotelpms/housekeeping", status_code=303)


@router.post("/hotelpms/housekeeping/markdirty")
def hk_markdirty(request: Request, room_id: int = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE rooms SET status='dirty' WHERE id=?", (room_id,))
    db.q("""INSERT INTO housekeeping_tasks (room_id, task_type, description, status, created_at)
            VALUES (?,?,?, 'open', ?)""",
         (room_id, "cleaning", "Checkout cleaning — full service", db.now()))
    return RedirectResponse("/hotelpms/housekeeping", status_code=303)


@router.post("/hotelpms/housekeeping/{tid}/start")
def hk_start(request: Request, tid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE housekeeping_tasks SET status='in_progress' WHERE id=?", (tid,))
    r = db.qone("SELECT room_id FROM housekeeping_tasks WHERE id=?", (tid,))
    if r:
        db.q("UPDATE rooms SET status='cleaning' WHERE id=?", (r["room_id"],))
    return RedirectResponse("/hotelpms/housekeeping", status_code=303)


@router.post("/hotelpms/housekeeping/{tid}/done")
def hk_done(request: Request, tid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE housekeeping_tasks SET status='done', done_at=? WHERE id=?", (db.now(), tid))
    r = db.qone("SELECT room_id FROM housekeeping_tasks WHERE id=?", (tid,))
    if r:
        db.q("UPDATE rooms SET status='ready' WHERE id=? AND status IN ('dirty','cleaning')",
             (r["room_id"],))
    return RedirectResponse("/hotelpms/housekeeping", status_code=303)


# ------------------------------------------------------------- restaurant
@router.get("/hotelpms/restaurant", response_class=HTMLResponse)
def restaurant(request: Request, stock_warn: str = ""):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    warn_html = (f"<div class='alert'>⚠️ <b>{T('Low stock!')}</b> {html.escape(stock_warn)} — "
                 f"<a href='/hotelpms/inventory'>{T('Inventory / Store')}</a></div>"
                 if stock_warn else "")
    menu = db.qall("SELECT * FROM restaurant_items WHERE active=1 ORDER BY category, name")
    cats = {}
    for m in menu:
        cats.setdefault(m["category"], []).append(m)
    menu_html = ""
    for cat, items in cats.items():
        rows = "".join(
            f"<tr><td>{html.escape(i['name'])} <a href='/hotelpms/inventory/recipe/{i['id']}' title='Recipe' style='font-size:.8rem'>🧪</a></td><td>{money(i['price'])}</td>"
            f"<td><input type='number' name='qty_{i['id']}' min='0' value='0' style='width:70px'></td></tr>"
            for i in items)
        menu_html += f"<h3>{html.escape(cat)}</h3><table><tr><th>{T('Item')}</th><th>{T('Price')}</th><th>{T('Qty')}</th></tr>{rows}</table>"
    inhouse = db.qall(
        "SELECT s.id, r.number rno, g.name gname FROM stays s "
        "JOIN rooms r ON r.id=s.room_id JOIN guests g ON g.id=s.guest_id WHERE s.status='active'")
    stay_opts = "".join(
        f"<option value='{s['id']}'>Room {html.escape(s['rno'])} — {html.escape(s['gname'])}</option>"
        for s in inhouse)
    open_orders = db.qall(
        "SELECT o.*, s.id sid FROM restaurant_orders o LEFT JOIN stays s ON s.id=o.stay_id "
        "WHERE o.status='open' ORDER BY o.created_at DESC")
    oh = ""
    for o in open_orders:
        lines = db.qall(
            "SELECT l.*, i.name FROM order_lines l JOIN restaurant_items i ON i.id=l.item_id "
            "WHERE l.order_id=?", (o["id"],))
        lhtml = ", ".join(f"{l['qty']}× {html.escape(l['name'])}" for l in lines)
        total = sum(l["amount"] for l in lines)
        dest = f"{T('Room order')}" if o["stay_id"] else f"{T('Counter (cash)')}"
        oh += (f"<div class='task'><b>{T('Order')} #{o['id']}</b> · {dest} · {lhtml} · <b>{money(total)}</b><br>"
               f"<form method='post' action='/hotelpms/restaurant/order/{o['id']}/bill' style='display:inline'>"
               f"<button class='btn small green' type='submit'>{T('Post / Bill')}</button></form> "
               f"<form method='post' action='/hotelpms/restaurant/order/{o['id']}/cancel' style='display:inline'>"
               f"<button class='btn small red' type='submit'>{T('Cancel')}</button></form></div>")
    body = f"""
<h1>🍽️ {T('Restaurant POS')}</h1>
{warn_html}
<div class="panel"><h2>{T('Open orders')}</h2>{oh or f"<p>{T('No open orders.')}</p>"}</div>
<div class="panel"><h2>{T('+ New order')}</h2>
<form method="post" action="/hotelpms/restaurant/order">
<label>{T('Send to')}</label><select name="stay_id">
<option value="">{T('Counter — direct cash bill')}</option>{stay_opts}</select>
<label>{T('Table no.')}</label><input name="table_no" placeholder="e.g. T-5" style="max-width:200px">
{menu_html}
<button class="btn green" type="submit">{T('Create order')}</button></form></div>
<div class="panel"><h2>{T('Menu management')}</h2>
<form method="post" action="/hotelpms/restaurant/menu/add" style="display:flex;gap:8px;flex-wrap:wrap">
<input name="name" placeholder="{T('Item name')}" required style="flex:2;min-width:160px">
<input name="category" placeholder="{T('Category')}" style="flex:1;min-width:110px">
<input name="price" type="number" min="0" placeholder="{T('Price')}" required style="flex:1;min-width:100px">
<button class="btn small" type="submit">{T('+ Add')}</button></form>
<p><a class="btn small gray" href="/hotelpms/inventory">📦 {T('Inventory / Store')}</a></p></div>
"""
    return HTMLResponse(_page(T("Restaurant POS"), body, u, _lang(request)))


@router.post("/hotelpms/restaurant/order")
async def order_create(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    form = await request.form()
    stay_id = form.get("stay_id") or None
    table_no = (form.get("table_no") or "").strip()
    items = []
    for key, val in form.items():
        if key.startswith("qty_") and val:
            try:
                qty = float(val)
            except Exception:
                continue
            if qty > 0:
                iid = int(key[4:])
                it = db.qone("SELECT * FROM restaurant_items WHERE id=?", (iid,))
                if it:
                    items.append((it, qty))
    if not items:
        return RedirectResponse("/hotelpms/restaurant", status_code=303)
    cur = db.q("INSERT INTO restaurant_orders (stay_id, table_no, status, created_at, created_by) "
               "VALUES (?,?,?,?,?)",
               (int(stay_id) if stay_id else None, table_no, "open", db.now(), u["name"] or u["role"]))
    oid = cur.lastrowid
    for it, qty in items:
        db.q("INSERT INTO order_lines (order_id, item_id, qty, price, amount) VALUES (?,?,?,?,?)",
             (oid, it["id"], qty, it["price"], qty * it["price"]))
    return RedirectResponse("/hotelpms/restaurant", status_code=303)


@router.post("/hotelpms/restaurant/order/{oid}/bill")
def order_bill(request: Request, oid: int):
    """Post room orders to folio; counter orders → instant cash invoice."""
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    o = db.qone("SELECT * FROM restaurant_orders WHERE id=? AND status='open'", (oid,))
    if not o:
        return RedirectResponse("/hotelpms/restaurant", status_code=303)
    lines = db.qall(
        "SELECT l.*, i.name FROM order_lines l JOIN restaurant_items i ON i.id=l.item_id "
        "WHERE l.order_id=?", (oid,))
    total = sum(l["amount"] for l in lines)
    desc = "Restaurant — " + ", ".join(f"{l['qty']}× {l['name']}" for l in lines)
    # v2: auto-deduct recipe stock (billing proceeds even if short — warning shown)
    shorts = _deduct_stock_for_order(oid, u["name"] or u["role"])
    warn = ""
    if shorts:
        warn = "?stock_warn=" + ",".join(
            f"{n.replace(',', ' ')}({need}/{have}{unit})" for n, need, have, unit in shorts)
    if o["stay_id"]:
        db.q("""INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at, created_by)
                VALUES (?,?,?,?,?,?,?,?)""",
             (o["stay_id"], "restaurant", desc, 1, total, total, db.now(), u["name"] or u["role"]))
        db.q("UPDATE restaurant_orders SET status='billed' WHERE id=?", (oid,))
    else:
        # Direct cash bill → instant invoice
        inv_id = create_invoice(guest_id=None, stay_id=None, event_id=None,
                                lines=[{"description": desc, "qty": 1,
                                        "unit_price": total, "amount": total}],
                                payment_method="cash", created_by=u["name"] or u["role"])
        db.q("UPDATE restaurant_orders SET status='billed' WHERE id=?", (oid,))
        return RedirectResponse(f"/hotelpms/invoice/{inv_id}" + warn, status_code=303)
    return RedirectResponse("/hotelpms/restaurant" + warn, status_code=303)


@router.post("/hotelpms/restaurant/order/{oid}/cancel")
def order_cancel(request: Request, oid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE restaurant_orders SET status='cancelled' WHERE id=?", (oid,))
    return RedirectResponse("/hotelpms/restaurant", status_code=303)


@router.post("/hotelpms/restaurant/menu/add")
def menu_add(request: Request, name: str = Form(""), category: str = Form("Food"),
             price: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("INSERT INTO restaurant_items (name, category, price) VALUES (?,?,?)",
         (name.strip(), (category or "Food").strip(), price))
    return RedirectResponse("/hotelpms/restaurant", status_code=303)

# ------------------------------------------------------------------ billing
def create_invoice(guest_id, stay_id, event_id, lines, payment_method, created_by) -> int:
    """Core billing: folio lines → invoice with SRB tax + FBR QR (TEST mode default)."""
    s = db.get_settings()
    subtotal = sum(l["amount"] for l in lines)
    rate = db.tax_rate_for(payment_method)
    tax = round(subtotal * rate / 100, 2)
    total = round(subtotal + tax, 2)
    seq = s["invoice_seq"]
    inv_no = f"{s['invoice_prefix']}-{seq}"
    db.q("UPDATE settings SET invoice_seq=? WHERE id=1", (seq + 1,))
    cur = db.q(
        """INSERT INTO invoices (invoice_no, stay_id, event_id, guest_id, lines_json, subtotal,
           tax_rate, tax_amount, total, payment_method, fbr_status, created_at, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (inv_no, stay_id, event_id, guest_id, json.dumps(lines), round(subtotal, 2),
         rate, tax, total, payment_method, "test", db.now(), created_by))
    inv_id = cur.lastrowid
    # FBR QR payload (TEST — not submitted)
    inv = dict(db.qone("SELECT * FROM invoices WHERE id=?", (inv_id,)))
    g = db.qone("SELECT * FROM guests WHERE id=?", (guest_id,)) if guest_id else None
    inv["guest_name"] = g["name"] if g else "Walk-in Guest"
    inv["guest_cnic"] = g["cnic"] if g else ""
    qr_text = fbr.qr_payload_text(inv, s)
    db.q("UPDATE invoices SET fbr_qr_payload=? WHERE id=?", (qr_text, inv_id))
    db.q("INSERT INTO payments (invoice_id, amount, method, created_at) VALUES (?,?,?,?)",
         (inv_id, total, payment_method, db.now()))
    return inv_id


@router.get("/hotelpms/billing/{sid}", response_class=HTMLResponse)
def billing(request: Request, sid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    st = db.qone(
        "SELECT s.*, g.name gname, g.cnic, g.phone, r.number rno, t.name tname FROM stays s "
        "JOIN guests g ON g.id=s.guest_id JOIN rooms r ON r.id=s.room_id "
        "JOIN room_types t ON t.id=r.room_type_id WHERE s.id=?", (sid,))
    if not st:
        return RedirectResponse("/hotelpms/frontdesk", status_code=303)
    items = db.qall("SELECT * FROM folio_items WHERE stay_id=? ORDER BY created_at", (sid,))
    subtotal = sum(i["amount"] for i in items)
    s = db.get_settings()
    rows = "".join(
        f"<tr><td>{html.escape(i['description'])}</td><td>{i['qty']}</td>"
        f"<td>{money(i['unit_price'])}</td><td>{money(i['amount'])}</td></tr>"
        for i in items)
    body = f"""
<h1>🧾 {T('Folio')} — {T('Room')} {html.escape(st['rno'])} · {html.escape(st['gname'])}</h1>
<div class="panel"><table>
<tr><th>{T('Description')}</th><th>{T('Qty')}</th><th>{T('Unit')}</th><th>{T('Amount')}</th></tr>{rows}
<tr><td colspan=3><b>{T('Subtotal')}</b></td><td><b>{money(subtotal)}</b></td></tr></table></div>
<div class="panel"><h2>+ {T('Extra charge')}</h2>
<form method="post" action="/hotelpms/billing/{sid}/extra" style="display:flex;gap:8px">
<input name="description" placeholder="e.g. Laundry" required style="flex:2">
<input name="amount" type="number" min="0" placeholder="Rs" required style="flex:1">
<button class="btn small" type="submit">{T('Add')}</button></form></div>
<div class="panel"><h2>💳 {T('Check-out & invoice')}</h2>
<form method="post" action="/hotelpms/billing/{sid}/checkout">
<label>{T('Payment method (SRB tax auto)')}</label>
<select name="payment_method">
<option value="cash">💵 {T('Cash')} — {s['srb_rate_cash']}% tax</option>
<option value="card">💳 {T('Card/Digital')} — {s['srb_rate_card']}% tax</option>
</select>
<button class="btn green" type="submit">{T('Generate invoice & check-out')}</button></form>
<p style="color:#64748b;font-size:.9rem">FBR mode: <b>{html.escape(s['fbr_mode']).upper()}</b> —
{"⚠️ test invoices are NOT submitted to FBR" if s['fbr_mode']=='test' else "invoices will attempt live FBR submission"}.</p></div>
"""
    return HTMLResponse(_page(T("Folio"), body, u, _lang(request)))


@router.post("/hotelpms/billing/{sid}/extra")
def folio_extra(request: Request, sid: int, description: str = Form(""), amount: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("""INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at, created_by)
            VALUES (?,?,?,?,?,?,?,?)""",
         (sid, "extra", description.strip(), 1, amount, amount, db.now(), u["name"] or u["role"]))
    return RedirectResponse(f"/hotelpms/billing/{sid}", status_code=303)


@router.post("/hotelpms/billing/{sid}/checkout")
def checkout(request: Request, sid: int, payment_method: str = Form("cash")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    st = db.qone("SELECT * FROM stays WHERE id=? AND status='active'", (sid,))
    if not st:
        return RedirectResponse("/hotelpms/frontdesk", status_code=303)
    items = db.qall("SELECT * FROM folio_items WHERE stay_id=? ORDER BY created_at", (sid,))
    lines = [{"description": i["description"], "qty": i["qty"],
              "unit_price": i["unit_price"], "amount": i["amount"]} for i in items]
    inv_id = create_invoice(st["guest_id"], sid, None, lines, payment_method,
                            u["name"] or u["role"])
    db.q("UPDATE stays SET status='closed', check_out_at=? WHERE id=?", (db.now(), sid))
    db.q("UPDATE rooms SET status='dirty' WHERE id=?", (st["room_id"],))
    db.q("""INSERT INTO housekeeping_tasks (room_id, task_type, description, status, created_at)
            VALUES (?,?,?, 'open', ?)""",
         (st["room_id"], "cleaning", "Checkout cleaning — full service", db.now()))
    b = db.qone("SELECT * FROM bookings WHERE id=?", (st["booking_id"],)) if st["booking_id"] else None
    if b:
        db.q("UPDATE bookings SET status='checked_out' WHERE id=?", (b["id"],))
    return RedirectResponse(f"/hotelpms/invoice/{inv_id}", status_code=303)


@router.get("/hotelpms/invoice/{inv_id}", response_class=HTMLResponse)
def invoice_view(request: Request, inv_id: int, stock_warn: str = ""):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    inv = db.qone("SELECT * FROM invoices WHERE id=?", (inv_id,))
    if not inv:
        return RedirectResponse("/hotelpms", status_code=303)
    inv = dict(inv)
    s = db.get_settings()
    g = db.qone("SELECT * FROM guests WHERE id=?", (inv["guest_id"],)) if inv["guest_id"] else None
    lines = json.loads(inv["lines_json"] or "[]")
    lrows = "".join(
        f"<tr><td>{html.escape(l['description'])}</td><td>{l['qty']}</td>"
        f"<td>{money(l['unit_price'])}</td><td>{money(l['amount'])}</td></tr>" for l in lines)
    qr_img = fbr.make_qr_png(inv["fbr_qr_payload"] or fbr.qr_payload_text(inv, s))
    # FBR attempt history (hardening: every attempt logged, shown honestly)
    attempts = db.qall("SELECT * FROM fbr_log WHERE invoice_id=? ORDER BY attempt_no DESC", (inv_id,))
    ahist = "".join(
        f"<tr><td>#{a['attempt_no']}</td><td>{a['http_code'] or '—'}</td>"
        f"<td>{'✅' if a['ok'] else '❌'}</td>"
        f"<td style='font-size:.8rem'>{html.escape((a['response_text'] or '')[:160])}</td>"
        f"<td style='font-size:.8rem'>{time.strftime('%H:%M:%S', time.localtime(a['created_at']))}</td></tr>"
        for a in attempts)
    ahist_block = (f"<details class='noprint'><summary>📡 FBR attempt log ({len(attempts)})</summary>"
                   f"<table><tr><th>Attempt</th><th>HTTP</th><th>OK</th><th>Response</th><th>Time</th></tr>"
                   f"{ahist}</table></details>" if attempts else "")
    fbr_block = ""
    if inv["fbr_status"] == "test":
        fbr_block = ("<div class='alert noprint'>⚠️ <b>FBR TEST MODE</b> — this invoice was NOT "
                     "submitted to FBR. To submit live: Settings → FBR → enter your IRIS credentials "
                     "and switch mode to LIVE (your signup, your action).</div>")
    elif inv["fbr_status"] == "submitted":
        fbr_block = (f"<div class='ok noprint'>✅ <b>Submitted to FBR</b> — FBR invoice no (IRN): "
                     f"<b>{html.escape(inv['fbr_invoice_no'] or '—')}</b><br>"
                     f"<small>Verify: scan the QR or check FBR IRIS portal.</small></div>")
    elif inv["fbr_status"] == "failed":
        fbr_block = (f"<div class='alert noprint'>❌ <b>FBR submission failed</b> (3 attempts, backoff): "
                     f"{html.escape((inv['fbr_response'] or '')[:300])} "
                     f"<form method='post' action='/hotelpms/invoice/{inv_id}/fbr' style='display:inline'>"
                     f"<button class='btn small' type='submit'>Retry</button></form></div>")
    body = f"""
<div class="inv">
{f"<div class='alert noprint'>⚠️ <b>{T('Low stock!')}</b> {html.escape(stock_warn)}</div>" if stock_warn else ""}
<div class="qr"><img src="{qr_img}" width="140"><br><small>FBR QR</small></div>
<h2>{html.escape(s['hotel_name'])}</h2>
<p>{html.escape(s['hotel_address'])}<br>{html.escape(s['hotel_phone'])} ·
NTN: {html.escape(s['ntn'])}</p>
<hr>
<p><b>{T('Invoice')}:</b> {html.escape(inv['invoice_no'])} ·
<b>{T('Date')}:</b> {time.strftime('%d-%b-%Y %H:%M', time.localtime(inv['created_at']))}<br>
<b>{T('Guest')}:</b> {html.escape(g['name'] if g else 'Walk-in Guest')}
{f" · {T('CNIC')}: {html.escape(g['cnic'])}" if g and g['cnic'] else ""}<br>
<b>{T('Payment')}:</b> {html.escape(inv['payment_method']).title()}</p>
<table class="inv-tbl"><tr><th>{T('Description')}</th><th>{T('Qty')}</th><th>{T('Unit')}</th><th>{T('Amount')}</th></tr>{lrows}</table>
<p style="text-align:right">{T('Subtotal')}: <b>{money(inv['subtotal'])}</b><br>
SRB Tax ({inv['tax_rate']}%): <b>{money(inv['tax_amount'])}</b><br>
<span style="font-size:1.3rem">{T('Total')}: <b>{money(inv['total'])}</b></span></p>
{fbr_block}{ahist_block}
<p class="noprint"><button class="btn" onclick="window.print()">🖨️ {T('Print')} (A4)</button>
<a class="btn gray" href="/hotelpms/invoice/{inv_id}/thermal" target="_blank">🧾 {T('Thermal print')} (80mm)</a>
<a class="btn green" href="/hotelpms">{T('Dashboard')}</a>
{f'''<form method="post" action="/hotelpms/invoice/{inv_id}/fbr" style="display:inline">
<button class="btn amber" type="submit">📡 Submit to FBR</button></form>''' if inv['fbr_status'] in ('test','failed') else ''}</p>
</div>
"""
    return HTMLResponse(_page(f"{T('Invoice')} {inv['invoice_no']}", body, u, _lang(request)))


@router.post("/hotelpms/invoice/{inv_id}/fbr")
def invoice_fbr_submit(request: Request, inv_id: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    fbr.submit(inv_id)  # honest: test mode returns test_mode, live attempts real HTTP (3 tries)
    return RedirectResponse(f"/hotelpms/invoice/{inv_id}", status_code=303)


@router.get("/hotelpms/invoice/{inv_id}/thermal", response_class=HTMLResponse)
def invoice_thermal(request: Request, inv_id: int):
    """80mm thermal-printer receipt — the format every small hotel in Pakistan uses."""
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    inv = db.qone("SELECT * FROM invoices WHERE id=?", (inv_id,))
    if not inv:
        return RedirectResponse("/hotelpms", status_code=303)
    inv = dict(inv)
    s = db.get_settings()
    g = db.qone("SELECT * FROM guests WHERE id=?", (inv["guest_id"],)) if inv["guest_id"] else None
    lines = json.loads(inv["lines_json"] or "[]")
    lrows = "".join(
        f"<div class='li'><span>{html.escape(l['description'][:28])}</span>"
        f"<span>{l['qty']}x{money(l['unit_price'])}</span>"
        f"<span class='r'>{money(l['amount'])}</span></div>" for l in lines)
    qr_img = fbr.make_qr_png(inv["fbr_qr_payload"] or fbr.qr_payload_text(inv, s))
    fbr_line = (f"<div class='c'>FBR: {html.escape(inv['fbr_invoice_no'])}</div>"
                if inv["fbr_status"] == "submitted" and inv["fbr_invoice_no"]
                else "<div class='c'>FBR: TEST — not submitted</div>")
    body = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Receipt {html.escape(inv['invoice_no'])}</title>
<style>
body{{font-family:monospace;font-size:12px;margin:0;padding:8px;color:#000}}
.rcpt{{max-width:300px;margin:0 auto}}
.c{{text-align:center}}.r{{text-align:right}}
h3{{margin:4px 0;font-size:14px}}.p{{margin:2px 0}}
.hr{{border-top:1px dashed #000;margin:6px 0}}
.li{{display:flex;justify-content:space-between;gap:4px;margin:2px 0}}
.tot{{display:flex;justify-content:space-between;margin:2px 0}}
.big{{font-size:15px;font-weight:bold}}
img.qr{{width:110px;height:110px}}
@media print{{.noprint{{display:none}}}}
</style></head><body>
<div class="rcpt">
<div class="c"><h3>{html.escape(s['hotel_name'])}</h3>
<div class="p">{html.escape(s['hotel_address'])}</div>
<div class="p">{html.escape(s['hotel_phone'])} · NTN {html.escape(s['ntn'])}</div></div>
<div class="hr"></div>
<div class="p">Bill: <b>{html.escape(inv['invoice_no'])}</b></div>
<div class="p">{time.strftime('%d-%b-%Y %H:%M', time.localtime(inv['created_at']))}</div>
<div class="p">Guest: {html.escape(g['name'] if g else 'Walk-in')}</div>
<div class="p">Pay: {html.escape(inv['payment_method']).title()}</div>
<div class="hr"></div>
{lrows}
<div class="hr"></div>
<div class="tot"><span>Subtotal</span><span>{money(inv['subtotal'])}</span></div>
<div class="tot"><span>Tax ({inv['tax_rate']}%)</span><span>{money(inv['tax_amount'])}</span></div>
<div class="tot big"><span>TOTAL</span><span>{money(inv['total'])}</span></div>
<div class="hr"></div>
{fbr_line}
<div class="c"><img class="qr" src="{qr_img}"></div>
<div class="c p">Shukriya! Phir tashreef laiye ga</div>
<div class="noprint c" style="margin-top:10px">
<button onclick="window.print()" style="padding:10px 24px">🖨️ Print</button></div>
</div></body></html>"""
    return HTMLResponse(body)


# ----------------------------------------------------------------- guests
@router.get("/hotelpms/guests", response_class=HTMLResponse)
def guests(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    rows = db.qall("SELECT * FROM guests ORDER BY repeat_count DESC, name LIMIT 200")
    tbl = "".join(
        f"<tr><td>{html.escape(g['name'])}"
        f"{' <span class=badge style=background:#16a34a>Repeat ⭐</span>' if g['repeat_count'] > 1 else ''}</td>"
        f"<td>{html.escape(g['phone'])}</td><td>{html.escape(g['cnic'])}</td>"
        f"<td>{g['repeat_count']} stays</td><td>{html.escape(g['preferences'] or '—')}</td>"
        f"<td><form method='post' action='/hotelpms/guests/{g['id']}/pref' style='display:flex;gap:4px'>"
        f"<input name='preferences' placeholder='{T('Preferences')}' value='{html.escape(g['preferences'] or '')}' style='margin:0'>"
        f"<button class='btn small' type='submit'>{T('Save')}</button></form></td></tr>"
        for g in rows) or f"<tr><td colspan=6>{T('No guests yet.')}</td></tr>"
    body = f"""
<h1>👥 {T('Guest CRM')}</h1>
<div class="panel"><table>
<tr><th>{T('Name')}</th><th>{T('Phone')}</th><th>{T('CNIC')}</th><th>{T('Visits')}</th><th>{T('Preferences')}</th><th></th></tr>{tbl}</table></div>
"""
    return HTMLResponse(_page(T("Guest CRM"), body, u, _lang(request)))


@router.post("/hotelpms/guests/{gid}/pref")
def guest_pref(request: Request, gid: int, preferences: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("UPDATE guests SET preferences=? WHERE id=?", (preferences.strip(), gid))
    return RedirectResponse("/hotelpms/guests", status_code=303)

# ----------------------------------------------------------------- reports
@router.get("/hotelpms/reports", response_class=HTMLResponse)
def reports(request: Request, month: str = ""):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    m = month or date.today().strftime("%Y-%m")
    y, mo = m.split("-")
    start = int(time.mktime(date(int(y), int(mo), 1).timetuple()))
    end = int(time.mktime((date(int(y), int(mo), 1) + timedelta(days=32)).replace(day=1).timetuple()))
    invs = db.qall("SELECT * FROM invoices WHERE created_at>=? AND created_at<? ORDER BY created_at",
                   (start, end))
    rev = sum(i["total"] for i in invs)
    tax = sum(i["tax_amount"] for i in invs)
    cash_rev = sum(i["total"] for i in invs if i["payment_method"] == "cash")
    card_rev = sum(i["total"] for i in invs if i["payment_method"] == "card")
    room_rev = sum(i["total"] for i in invs if i["stay_id"])
    total_rooms = db.qone("SELECT COUNT(*) c FROM rooms")["c"]
    days_in_month = (date(int(y), int(mo), 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    room_nights_sold = db.qone(
        "SELECT COALESCE(SUM(nights),0) n FROM bookings WHERE status='checked_out' "
        "AND check_in_date>=? AND check_in_date<?", (f"{m}-01", f"{m}-32"))["n"]
    occ = round(room_nights_sold / (total_rooms * days_in_month.day) * 100, 1) if total_rooms else 0
    trows = "".join(
        f"<tr><td>{html.escape(i['invoice_no'])}</td>"
        f"<td>{time.strftime('%d-%b', time.localtime(i['created_at']))}</td>"
        f"<td>{money(i['subtotal'])}</td><td>{i['tax_rate']}%</td><td>{money(i['tax_amount'])}</td>"
        f"<td>{money(i['total'])}</td><td>{i['payment_method']}</td>"
        f"<td>{html.escape(i['fbr_status'])}</td></tr>" for i in invs)
    body = f"""
<h1>📈 {T('Reports')} — {html.escape(m)}</h1>
<form method="get" action="/hotelpms/reports" style="max-width:220px">
<label>{T('Month')}</label><input type="month" name="month" value="{html.escape(m)}" onchange="this.form.submit()"></form>
<div class="cards">
<div class="card"><div class="big">{money(rev)}</div><div class="lbl">{T('Total revenue')}</div></div>
<div class="card"><div class="big">{money(room_rev)}</div><div class="lbl">{T('Room revenue')}</div></div>
<div class="card"><div class="big">{money(tax)}</div><div class="lbl">{T('SRB tax collected')}</div></div>
<div class="card"><div class="big">{occ}%</div><div class="lbl">{T('Occupancy')}</div></div>
<div class="card"><div class="big">{money(cash_rev)}</div><div class="lbl">{T('Cash')} (15% tax)</div></div>
<div class="card"><div class="big">{money(card_rev)}</div><div class="lbl">{T('Card')} (8% tax)</div></div>
</div>
<div class="panel"><h2>🧾 {T('Tax report (SRB/FBR summary)')}</h2>
<table><tr><th>{T('Invoice')}</th><th>{T('Date')}</th><th>{T('Subtotal')}</th><th>{T('Rate')}</th><th>{T('Tax')}</th><th>{T('Total')}</th><th>{T('Pay')}</th><th>{T('FBR')}</th></tr>
{trows or f"<tr><td colspan=8>{T('No invoices this month.')}</td></tr>"}</table>
<p><a class="btn small gray" href="/hotelpms/export/sales.csv?month={m}">⬇ {T('Export')} CSV</a></p>
<p style="color:#64748b">P&L-lite: Revenue {money(rev)} − Tax {money(tax)} = Net {money(rev - tax)} (before expenses).</p></div>
"""
    return HTMLResponse(_page(T("Reports"), body, u, _lang(request)))


# ------------------------------------------------------------------ events
@router.get("/hotelpms/events", response_class=HTMLResponse)
def events(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    rows = db.qall("SELECT * FROM events ORDER BY event_date DESC LIMIT 100")
    tbl = "".join(
        f"<tr><td>{html.escape(e['event_name'])}</td><td>{html.escape(e['client_name'])}<br>{html.escape(e['client_phone'])}</td>"
        f"<td>{e['event_date']}</td><td>{html.escape(e['hall'])}</td><td>{e['guests_count']}</td>"
        f"<td>{money(e['total'])}</td><td>{money(e['advance'])}</td><td>{money(e['balance'])}</td>"
        f"<td><span class='badge b-{e['status']}'>{e['status'].title()}</span></td>"
        f"<td>" + (f"<form method='post' action='/hotelpms/events/{e['id']}/bill' style='display:inline'>"
                    f"<button class='btn small green' type='submit'>{T('Bill balance')}</button></form> "
                    if e['status'] in ('booked', 'confirmed') and e['balance'] > 0 else "") + "</td></tr>"
        for e in rows) or "<tr><td colspan=10>No events.</td></tr>"
    body = f"""
<h1>💒 {T('Marriage Hall / Events')}</h1>
<p><a class="btn" href="/hotelpms/events/new">{T('+ New event booking')}</a></p>
<div class="panel"><table>
<tr><th>{T('Event')}</th><th>{T('Client')}</th><th>{T('Date')}</th><th>{T('Hall')}</th><th>{T('Guests')}</th><th>{T('Total')}</th><th>{T('Advance')}</th><th>{T('Balance')}</th><th>{T('Status')}</th><th></th></tr>
{tbl}</table></div>
"""
    return HTMLResponse(_page(T("Marriage Hall / Events"), body, u, _lang(request)))


@router.get("/hotelpms/events/new", response_class=HTMLResponse)
def event_new(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    d0 = (date.today() + timedelta(days=7)).isoformat()
    body = f"""
<h1>💒 {T('New event booking')}</h1>
<div class="panel"><form method="post" action="/hotelpms/events/create">
<div class="formrow">
<div><label>{T('Event name')}</label><input name="event_name" placeholder="e.g. Walima — Ahmed family" required></div>
<div><label>{T('Client name')}</label><input name="client_name" required></div></div>
<div class="formrow">
<div><label>{T('Client phone')}</label><input name="client_phone"></div>
<div><label>{T('Event date')}</label><input type="date" name="event_date" value="{d0}" required></div></div>
<div class="formrow">
<div><label>{T('Hall')}</label><select name="hall"><option>Main Hall</option><option>Marquee</option><option>Lawn</option></select></div>
<div><label>{T('Guests count')}</label><input type="number" name="guests_count" min="0" value="300"></div></div>
<div class="formrow">
<div><label>{T('Package')}</label><select name="package_name"><option>Standard Dinner</option><option>Deluxe Dinner</option><option>Basic Tea</option></select></div>
<div><label>{T('Per-head rate')}</label><input type="number" name="per_head_rate" min="0" value="1500"></div></div>
<label>{T('Advance (Rs)')}</label><input type="number" name="advance" min="0" value="0" style="max-width:260px">
<button class="btn" type="submit">{T('Book event')}</button></form></div>
"""
    return HTMLResponse(_page(T("New event booking"), body, u, _lang(request)))


@router.post("/hotelpms/events/create")
def event_create(request: Request, event_name: str = Form(""), client_name: str = Form(""),
                 client_phone: str = Form(""), event_date: str = Form(""), hall: str = Form("Main Hall"),
                 guests_count: int = Form(0), package_name: str = Form(""),
                 per_head_rate: float = Form(0), advance: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    total = guests_count * per_head_rate
    db.q("""INSERT INTO events (event_name, client_name, client_phone, event_date, hall, guests_count,
           package_name, per_head_rate, total, advance, balance, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
         (event_name.strip(), client_name.strip(), client_phone.strip(), event_date, hall,
          guests_count, package_name, per_head_rate, total, advance, total - advance,
          "booked", db.now()))
    return RedirectResponse("/hotelpms/events", status_code=303)


@router.post("/hotelpms/events/{eid}/bill")
def event_bill(request: Request, eid: int):
    """Bill the event balance → invoice (cash default; FBR QR included)."""
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    e = db.qone("SELECT * FROM events WHERE id=?", (eid,))
    if not e or e["balance"] <= 0:
        return RedirectResponse("/hotelpms/events", status_code=303)
    g = db.qone("SELECT * FROM guests WHERE phone=? AND phone!=''", (e["client_phone"],))
    gid = g["id"] if g else None
    lines = [
        {"description": f"{e['event_name']} — {e['hall']} ({e['guests_count']} guests, {e['package_name']})",
         "qty": 1, "unit_price": e["total"], "amount": e["total"]},
        {"description": f"Advance paid", "qty": 1, "unit_price": -e["advance"], "amount": -e["advance"]},
    ]
    inv_id = create_invoice(gid, None, eid, lines, "cash", u["name"] or u["role"])
    db.q("UPDATE events SET status='completed', balance=0 WHERE id=?", (eid,))
    return RedirectResponse(f"/hotelpms/invoice/{inv_id}", status_code=303)


# ---------------------------------------------------------------- settings
@router.get("/hotelpms/settings", response_class=HTMLResponse)
def settings(request: Request):
    u = need_owner(request)
    if not u:
        usr = current_user(request)
        if not usr:
            return login_redirect()
        return HTMLResponse(_page("Settings",
            '<div class="alert">⚠️ Settings are owner-only. Staff can use all operational screens.</div>', usr,
            _lang(request)),
            status_code=403)
    s = db.get_settings()
    T = _tr(request)
    users = db.qall("SELECT id, name, email, pin, role, is_active FROM users ORDER BY role, id")
    urows = "".join(
        f"<tr><td>{html.escape(x['name'] or '—')}</td><td>{html.escape(x['email'] or '—')}</td>"
        f"<td>{html.escape(x['role'])}</td><td>{'PIN: ' + html.escape(x['pin']) if x['pin'] else '—'}</td>"
        f"<td>{'active' if x['is_active'] else 'disabled'}</td></tr>" for x in users)
    fbr_note = ("<div class='alert'>⚠️ <b>FBR TEST MODE</b> — invoices are generated with QR codes "
                "but <b>NOT submitted</b> to FBR. Live submission needs the hotel's own IRIS "
                "registration (their signup at iris.fbr.gov.pk, their action). Never paste anyone "
                "else's credentials here.</div>" if s["fbr_mode"] == "test" else
                "<div class='ok'>📡 <b>FBR LIVE MODE</b> — invoices will attempt real submission "
                "(3 attempts, backoff). Every response is logged on the invoice page, honestly.</div>")
    body = f"""
<h1>⚙️ {T('Settings')}</h1>
<div class="panel"><h2>{T('Hotel profile')}</h2>
<form method="post" action="/hotelpms/settings/hotel">
<div class="formrow">
<div><label>{T('Hotel name')}</label><input name="hotel_name" value="{html.escape(s['hotel_name'])}"></div>
<div><label>{T('Phone')}</label><input name="hotel_phone" value="{html.escape(s['hotel_phone'])}"></div></div>
<label>{T('Address')}</label><input name="hotel_address" value="{html.escape(s['hotel_address'])}">
<div class="formrow">
<div><label>NTN</label><input name="ntn" value="{html.escape(s['ntn'])}"></div>
<div><label>STRN</label><input name="strn" value="{html.escape(s['strn'])}"></div></div>
<div><label>{T('Language')} / زبان</label><select name="lang" style="max-width:260px">
<option value="en" {"selected" if (s.get('lang') or 'en')=='en' else ""}>English</option>
<option value="ur" {"selected" if (s.get('lang') or 'en')=='ur' else ""}>اردو (Urdu)</option>
</select></div>
<button class="btn" type="submit">{T('Save')}</button></form></div>
<div class="panel"><h2>{T('Tax rates (SRB — Sindh)')}</h2>
<form method="post" action="/hotelpms/settings/tax"><div class="formrow">
<div><label>{T('Card / Digital %')}</label><input type="number" step="0.1" name="srb_rate_card" value="{s['srb_rate_card']}"></div>
<div><label>{T('Cash %')}</label><input type="number" step="0.1" name="srb_rate_cash" value="{s['srb_rate_cash']}"></div>
</div><button class="btn" type="submit">{T('Save rates')}</button></form></div>
<div class="panel"><h2>📡 FBR Digital Invoicing (SRO 288(I)/2026)</h2>
{fbr_note}
<form method="post" action="/hotelpms/settings/fbr">
<label>Mode</label><select name="fbr_mode">
<option value="test" {"selected" if s['fbr_mode']=='test' else ""}>TEST — build invoices, do not submit</option>
<option value="live" {"selected" if s['fbr_mode']=='live' else ""}>LIVE — attempt real FBR submission (3 tries)</option>
</select>
<label>IRIS username (hotel's own — their signup)</label>
<input name="fbr_iris_user" value="{html.escape(s['fbr_iris_user'])}" autocomplete="off">
<label>IRIS password</label>
<input type="password" name="fbr_iris_pass" placeholder="{'●●●●●●●● (saved)' if s['fbr_iris_pass'] else ''}" autocomplete="off">
<label>FBR API URL</label><input name="fbr_api_url" value="{html.escape(s['fbr_api_url'])}"
placeholder="https://api.fbr.gov.pk/...">
<button class="btn" type="submit">{T('Save')} FBR settings</button></form></div>
<div class="panel"><h2>💾 {T('Backup & export')}</h2>
<p><a class="btn" href="/hotelpms/settings/backup">⬇ {T('Download')} DB ({T('Backup')})</a></p>
<p><a class="btn small gray" href="/hotelpms/export/sales.csv">CSV: {T('Total revenue')}</a>
<a class="btn small gray" href="/hotelpms/export/tax.csv">CSV: {T('Tax report (SRB/FBR summary)')}</a>
<a class="btn small gray" href="/hotelpms/export/guests.csv">CSV: {T('Guest CRM')}</a></p>
<p style="color:#64748b;font-size:.9rem">⚠️ {T('Backup note')}</p></div>
<div class="panel"><h2>👥 {T('Users')}</h2>
<table><tr><th>{T('Name')}</th><th>{T('Email')}</th><th>{T('Role')}</th><th>{T('PIN')}</th><th>{T('Status')}</th></tr>{urows}</table>
<h3 style="margin-top:14px">+ {T('Add staff (PIN login)')}</h3>
<form method="post" action="/hotelpms/settings/staff/add" style="display:flex;gap:8px;flex-wrap:wrap">
<input name="name" placeholder="{T('Name')}" required style="flex:1;min-width:140px">
<input name="pin" placeholder="{T('4-digit PIN')}" required style="flex:1;min-width:110px">
<button class="btn small" type="submit">{T('Add')}</button></form>
<h3 style="margin-top:14px">{T('Change owner password')}</h3>
<form method="post" action="/hotelpms/settings/password" style="display:flex;gap:8px;flex-wrap:wrap">
<input type="password" name="new_password" placeholder="New password (8+ chars)" required style="flex:1;min-width:180px">
<button class="btn small amber" type="submit">{T('Change')}</button></form></div>
"""
    return HTMLResponse(_page(T("Settings"), body, u, _lang(request)))


@router.post("/hotelpms/settings/hotel")
def settings_hotel(request: Request, hotel_name: str = Form(""), hotel_phone: str = Form(""),
                   hotel_address: str = Form(""), ntn: str = Form(""), strn: str = Form(""),
                   lang: str = Form("en")):
    u = need_owner(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    db.q("""UPDATE settings SET hotel_name=?, hotel_phone=?, hotel_address=?, ntn=?, strn=?,
            lang=?, updated_at=? WHERE id=1""",
         (hotel_name.strip(), hotel_phone.strip(), hotel_address.strip(),
          ntn.strip(), strn.strip(), lang if lang in ("en", "ur") else "en", db.now()))
    return RedirectResponse("/hotelpms/settings", status_code=303)


@router.post("/hotelpms/settings/tax")
def settings_tax(request: Request, srb_rate_card: float = Form(8.0), srb_rate_cash: float = Form(15.0)):
    u = need_owner(request)
    if not u:
        return login_redirect()
    db.q("UPDATE settings SET srb_rate_card=?, srb_rate_cash=?, updated_at=? WHERE id=1",
         (srb_rate_card, srb_rate_cash, db.now()))
    return RedirectResponse("/hotelpms/settings", status_code=303)


@router.post("/hotelpms/settings/fbr")
def settings_fbr(request: Request, fbr_mode: str = Form("test"), fbr_iris_user: str = Form(""),
                 fbr_iris_pass: str = Form(""), fbr_api_url: str = Form("")):
    u = need_owner(request)
    if not u:
        return login_redirect()
    cur = db.get_settings()
    pw = fbr_iris_pass.strip() or cur["fbr_iris_pass"]  # blank = keep saved
    db.q("""UPDATE settings SET fbr_mode=?, fbr_iris_user=?, fbr_iris_pass=?, fbr_api_url=?,
            updated_at=? WHERE id=1""",
         ("live" if fbr_mode == "live" else "test", fbr_iris_user.strip(), pw,
          fbr_api_url.strip(), db.now()))
    return RedirectResponse("/hotelpms/settings", status_code=303)


@router.post("/hotelpms/settings/staff/add")
def staff_add(request: Request, name: str = Form(""), pin: str = Form("")):
    u = need_owner(request)
    if not u:
        return login_redirect()
    db.q("INSERT INTO users (name, pin, role, created_at) VALUES (?,?, 'staff', ?)",
         (name.strip(), pin.strip(), db.now()))
    return RedirectResponse("/hotelpms/settings", status_code=303)


@router.post("/hotelpms/settings/password")
def owner_password(request: Request, new_password: str = Form("")):
    u = need_owner(request)
    if not u:
        return login_redirect()
    if len(new_password) < 8:
        return RedirectResponse("/hotelpms/settings", status_code=303)
    db.q("UPDATE users SET password_hash=? WHERE id=?", (auth.hash_password(new_password), u["id"]))
    return RedirectResponse("/hotelpms/settings", status_code=303)


# ------------------------------------------------------- backup & export
@router.get("/hotelpms/settings/backup")
def settings_backup(request: Request):
    """One-click full DB download (owner only)."""
    u = need_owner(request)
    if not u:
        return login_redirect()
    path = db.db_path()
    # checkpoint WAL so the backup file is complete
    try:
        db.get_conn().execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass
    return FileResponse(path, filename=f"hotelpms-backup-{date.today().isoformat()}.db",
                        media_type="application/x-sqlite3")


def _csv_response(filename: str, header: list, rows: list):
    import csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    data = buf.getvalue().encode("utf-8-sig")  # BOM → Excel opens Urdu correctly
    return StreamingResponse(io.BytesIO(data), media_type="text/csv",
                             headers={"Content-Disposition":
                                      f"attachment; filename={filename}"})


@router.get("/hotelpms/export/sales.csv")
def export_sales(request: Request, month: str = ""):
    u = need_login(request)
    if not u:
        return login_redirect()
    m = month or date.today().strftime("%Y-%m")
    y, mo = m.split("-")
    start = int(time.mktime(date(int(y), int(mo), 1).timetuple()))
    end = int(time.mktime((date(int(y), int(mo), 1) + timedelta(days=32)).replace(day=1).timetuple()))
    invs = db.qall("SELECT * FROM invoices WHERE created_at>=? AND created_at<? ORDER BY created_at",
                   (start, end))
    rows = [[i["invoice_no"], time.strftime("%Y-%m-%d %H:%M", time.localtime(i["created_at"])),
             i["subtotal"], i["tax_rate"], i["tax_amount"], i["total"],
             i["payment_method"], i["fbr_status"], i["fbr_invoice_no"] or ""]
            for i in invs]
    return _csv_response(f"sales-{m}.csv",
                         ["invoice_no", "date", "subtotal", "tax_rate", "tax_amount",
                          "total", "payment_method", "fbr_status", "fbr_invoice_no"], rows)


@router.get("/hotelpms/export/tax.csv")
def export_tax(request: Request, month: str = ""):
    u = need_login(request)
    if not u:
        return login_redirect()
    m = month or date.today().strftime("%Y-%m")
    y, mo = m.split("-")
    start = int(time.mktime(date(int(y), int(mo), 1).timetuple()))
    end = int(time.mktime((date(int(y), int(mo), 1) + timedelta(days=32)).replace(day=1).timetuple()))
    invs = db.qall("SELECT * FROM invoices WHERE created_at>=? AND created_at<? ORDER BY created_at",
                   (start, end))
    rows = [[i["invoice_no"], time.strftime("%Y-%m-%d", time.localtime(i["created_at"])),
             i["subtotal"], i["tax_amount"], i["payment_method"]]
            for i in invs]
    return _csv_response(f"tax-report-{m}.csv",
                         ["invoice_no", "date", "taxable_amount", "srb_tax", "payment_method"],
                         rows)


@router.get("/hotelpms/export/guests.csv")
def export_guests(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    guests = db.qall("SELECT * FROM guests ORDER BY name")
    rows = [[g["name"], g["phone"], g["cnic"], g["repeat_count"], g["preferences"] or ""]
            for g in guests]
    return _csv_response("guests.csv",
                         ["name", "phone", "cnic", "visits", "preferences"], rows)


# -------------------------------------------------------------- inventory
def _deduct_stock_for_order(oid: int, by: str) -> list:
    """Auto-deduct recipe ingredients when a restaurant order is billed.
    Returns list of short items (name, needed, have) — billing still proceeds,
    the shortage is surfaced as a warning."""
    shorts = []
    lines = db.qall(
        "SELECT l.qty, l.item_id FROM order_lines l WHERE l.order_id=?", (oid,))
    for ln in lines:
        recipes = db.qall(
            "SELECT r.qty, i.id, i.name, i.qty_on_hand, i.unit FROM menu_recipe r "
            "JOIN inventory_items i ON i.id=r.inv_item_id WHERE r.menu_item_id=?",
            (ln["item_id"],))
        for r in recipes:
            need = r["qty"] * ln["qty"]
            have = r["qty_on_hand"]
            if have < need:
                shorts.append((r["name"], round(need, 2), round(have, 2), r["unit"]))
            db.q("UPDATE inventory_items SET qty_on_hand=qty_on_hand-? WHERE id=?",
                 (need, r["id"]))
            db.q("""INSERT INTO inventory_movements (item_id, kind, qty, note, created_at, created_by)
                    VALUES (?,?,?,?,?,?)""",
                 (r["id"], "use", -need, f"order #{oid}", db.now(), by))
    return shorts


@router.get("/hotelpms/inventory", response_class=HTMLResponse)
def inventory(request: Request):
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    items = db.qall("SELECT * FROM inventory_items WHERE active=1 ORDER BY category, name")
    low = [i for i in items if i["qty_on_hand"] <= i["reorder_level"]]
    rows = "".join(
        f"<tr><td>{html.escape(i['name'])}</td><td>{html.escape(i['category'])}</td>"
        f"<td>{html.escape(i['unit'])}</td>"
        f"<td><b style='color:{'#dc2626' if i['qty_on_hand'] <= i['reorder_level'] else '#16a34a'}'>"
        f"{i['qty_on_hand']}</b></td><td>{i['reorder_level']}</td><td>{money(i['cost_price'])}</td></tr>"
        for i in items)
    movs = db.qall(
        "SELECT m.*, i.name iname FROM inventory_movements m "
        "JOIN inventory_items i ON i.id=m.item_id ORDER BY m.created_at DESC LIMIT 25")
    mrows = "".join(
        f"<tr><td>{html.escape(m['iname'])}</td><td>{m['kind']}</td>"
        f"<td>{'+' if m['qty'] > 0 else ''}{m['qty']}</td>"
        f"<td>{html.escape(m['note'] or '')}</td>"
        f"<td>{time.strftime('%d-%b %H:%M', time.localtime(m['created_at']))}</td></tr>"
        for m in movs)
    opts = "".join(f"<option value='{i['id']}'>{html.escape(i['name'])} ({html.escape(i['unit'])})</option>"
                   for i in items)
    low_banner = (f"<div class='alert'>⚠️ <b>{T('Low stock!')}</b> — "
                  + ", ".join(html.escape(i["name"]) for i in low) + "</div>") if low else ""
    body = f"""
<h1>📦 {T('Inventory / Store')}</h1>
{low_banner}
<div class="panel"><table>
<tr><th>{T('Item')}</th><th>{T('Category')}</th><th>{T('Unit')}</th><th>{T('On hand')}</th>
<th>{T('Reorder at')}</th><th>{T('Cost')}</th></tr>{rows or f"<tr><td colspan=6>—</td></tr>"}</table></div>
<div class="panel"><h2>{T('+ Add item')}</h2>
<form method="post" action="/hotelpms/inventory/add"><div class="formrow">
<div><label>{T('Item')}</label><input name="name" required></div>
<div><label>{T('Category')}</label><select name="category">
<option>Kitchen</option><option>Linen</option><option>Toiletries</option>
<option>Housekeeping</option><option>General</option></select></div></div>
<div class="formrow">
<div><label>{T('Unit')}</label><select name="unit">
<option>pcs</option><option>kg</option><option>litre</option><option>pack</option></select></div>
<div><label>{T('Reorder at')}</label><input type="number" step="0.01" name="reorder_level" value="0"></div></div>
<div><label>{T('Cost')}</label><input type="number" step="0.01" name="cost_price" value="0" style="max-width:260px"></div>
<button class="btn" type="submit">{T('Add')}</button></form></div>
<div class="panel"><h2>{T('Purchase (stock in)')}</h2>
<form method="post" action="/hotelpms/inventory/move" style="display:flex;gap:8px;flex-wrap:wrap">
<select name="item_id" style="flex:2;min-width:160px">{opts}</select>
<input type="hidden" name="kind" value="purchase">
<input type="number" step="0.01" name="qty" min="0" placeholder="{T('Quantity')}" required style="flex:1;min-width:100px">
<input name="note" placeholder="{T('Note')}" style="flex:2;min-width:140px">
<button class="btn green small" type="submit">{T('Record')}</button></form></div>
<div class="panel"><h2>{T('Use / Adjust')}</h2>
<form method="post" action="/hotelpms/inventory/move" style="display:flex;gap:8px;flex-wrap:wrap">
<select name="item_id" style="flex:2;min-width:160px">{opts}</select>
<select name="kind" style="flex:1;min-width:110px">
<option value="use">{T('Use / Adjust')} (−)</option><option value="adjust">{T('Adjust')} (+)</option>
<option value="waste">{T('Waste')} (−)</option></select>
<input type="number" step="0.01" name="qty" min="0" placeholder="{T('Quantity')}" required style="flex:1;min-width:100px">
<input name="note" placeholder="{T('Note')}" style="flex:2;min-width:140px">
<button class="btn amber small" type="submit">{T('Record')}</button></form></div>
<div class="panel"><h2>{T('Recent movements')}</h2>
<table><tr><th>{T('Item')}</th><th>{T('Category')}</th><th>{T('Quantity')}</th><th>{T('Note')}</th><th>{T('Date')}</th></tr>
{mrows or "<tr><td colspan=5>—</td></tr>"}</table></div>
"""
    return HTMLResponse(_page(T("Inventory / Store"), body, u, _lang(request)))


@router.post("/hotelpms/inventory/add")
def inventory_add(request: Request, name: str = Form(""), category: str = Form("General"),
                  unit: str = Form("pcs"), reorder_level: float = Form(0),
                  cost_price: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    db.q("""INSERT INTO inventory_items (name, category, unit, qty_on_hand, reorder_level,
            cost_price, created_at) VALUES (?,?,?,?,?,?,?)""",
         (name.strip(), category, unit, 0, reorder_level, cost_price, db.now()))
    return RedirectResponse("/hotelpms/inventory", status_code=303)


@router.post("/hotelpms/inventory/move")
def inventory_move(request: Request, item_id: int = Form(0), kind: str = Form("purchase"),
                   qty: float = Form(0), note: str = Form("")):
    u = need_login(request)
    if not u:
        return login_redirect()
    if kind not in ("purchase", "use", "adjust", "waste"):
        return RedirectResponse("/hotelpms/inventory", status_code=303)
    signed = qty if kind in ("purchase", "adjust") else -qty
    db.q("UPDATE inventory_items SET qty_on_hand=qty_on_hand+? WHERE id=?", (signed, item_id))
    db.q("""INSERT INTO inventory_movements (item_id, kind, qty, note, created_at, created_by)
            VALUES (?,?,?,?,?,?)""",
         (item_id, kind, signed, note.strip(), db.now(), u["name"] or u["role"]))
    return RedirectResponse("/hotelpms/inventory", status_code=303)


@router.get("/hotelpms/inventory/recipe/{menu_id}", response_class=HTMLResponse)
def recipe_edit(request: Request, menu_id: int):
    """Recipe editor: which stock items does one serving of a menu item consume?"""
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    m = db.qone("SELECT * FROM restaurant_items WHERE id=?", (menu_id,))
    if not m:
        return RedirectResponse("/hotelpms/restaurant", status_code=303)
    recs = db.qall(
        "SELECT r.*, i.name iname, i.unit FROM menu_recipe r "
        "JOIN inventory_items i ON i.id=r.inv_item_id WHERE r.menu_item_id=?", (menu_id,))
    rrows = "".join(
        f"<tr><td>{html.escape(r['iname'])}</td><td>{r['qty']} {html.escape(r['unit'])}</td>"
        f"<td><form method='post' action='/hotelpms/inventory/recipe/{r['id']}/del' style='display:inline'>"
        f"<button class='btn small red' type='submit'>✕</button></form></td></tr>"
        for r in recs) or f"<tr><td colspan=3>{T('None yet.')}</td></tr>"
    inv = db.qall("SELECT * FROM inventory_items WHERE active=1 ORDER BY name")
    opts = "".join(f"<option value='{i['id']}'>{html.escape(i['name'])} ({html.escape(i['unit'])})</option>"
                   for i in inv)
    body = f"""
<h1>🧪 {T('Recipe')} — {html.escape(m['name'])}</h1>
<p style="color:#64748b">{T('per serving')}: {T('Stock')} auto-deducts on billing.</p>
<div class="panel"><table><tr><th>{T('Item')}</th><th>{T('Quantity')}</th><th></th></tr>{rrows}</table>
<form method="post" action="/hotelpms/inventory/recipe/{menu_id}/add" style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
<select name="inv_item_id" style="flex:2;min-width:160px">{opts}</select>
<input type="number" step="0.001" name="qty" min="0" placeholder="{T('Quantity')}" required style="flex:1;min-width:100px">
<button class="btn small" type="submit">{T('Add')}</button></form></div>
<p><a class="btn gray small" href="/hotelpms/restaurant">← {T('Restaurant POS')}</a></p>
"""
    return HTMLResponse(_page(f"{T('Recipe')} — {m['name']}", body, u, _lang(request)))


@router.post("/hotelpms/inventory/recipe/{menu_id}/add")
def recipe_add(request: Request, menu_id: int, inv_item_id: int = Form(0), qty: float = Form(0)):
    u = need_login(request)
    if not u:
        return login_redirect()
    db.q("INSERT INTO menu_recipe (menu_item_id, inv_item_id, qty) VALUES (?,?,?)",
         (menu_id, inv_item_id, qty))
    return RedirectResponse(f"/hotelpms/inventory/recipe/{menu_id}", status_code=303)


@router.post("/hotelpms/inventory/recipe/{rid}/del")
def recipe_del(request: Request, rid: int):
    u = need_login(request)
    if not u:
        return login_redirect()
    r = db.qone("SELECT menu_item_id FROM menu_recipe WHERE id=?", (rid,))
    db.q("DELETE FROM menu_recipe WHERE id=?", (rid,))
    return RedirectResponse(f"/hotelpms/inventory/recipe/{r['menu_item_id'] if r else 0}",
                            status_code=303)


# --------------------------------------------------------------- payroll
@router.get("/hotelpms/payroll", response_class=HTMLResponse)
def payroll(request: Request, month: str = ""):
    """Payroll-lite: staff list, attendance marking, monthly salary sheet."""
    u = need_login(request)
    if not u:
        return login_redirect()
    T = _tr(request)
    m = month or date.today().strftime("%Y-%m")
    staff = db.qall("SELECT * FROM users WHERE is_active=1 ORDER BY role, name")
    today = today_str()
    att_today = {a["user_id"]: a["status"] for a in
                 db.qall("SELECT * FROM attendance WHERE att_date=?", (today,))}
    srows = ""
    for st in staff:
        cur = att_today.get(st["id"], "")
        btns = "".join(
            f"<form method='post' action='/hotelpms/payroll/attendance' style='display:inline'>"
            f"<input type='hidden' name='user_id' value='{st['id']}'>"
            f"<input type='hidden' name='status' value='{v}'>"
            f"<button class='btn small {'green' if cur == v else 'gray'}' type='submit'>{T(lbl)}</button></form> "
            for v, lbl in (("present", "Present"), ("absent", "Absent"),
                           ("leave", "Leave"), ("half", "Half day")))
        srows += (f"<tr><td>{html.escape(st['name'] or st['email'] or '—')}</td>"
                  f"<td>{html.escape(st['role'])}</td>"
                  f"<td><form method='post' action='/hotelpms/payroll/salary' style='display:flex;gap:4px'>"
                  f"<input type='hidden' name='user_id' value='{st['id']}'>"
                  f"<input type='number' name='salary' min='0' value='{st['salary_monthly'] or 0}' style='margin:0;width:110px'>"
                  f"<button class='btn small' type='submit'>{T('Update')}</button></form></td>"
                  f"<td>{btns}</td></tr>")
    # Monthly sheet
    y, mo = m.split("-")
    mdays = db.qall(
        "SELECT user_id, status, COUNT(*) c FROM attendance "
        "WHERE att_date LIKE ? GROUP BY user_id, status", (f"{m}%",))
    agg = {}
    for r in mdays:
        agg.setdefault(r["user_id"], {}).update({r["status"]: r["c"]})
    sheet = ""
    for st in staff:
        a = agg.get(st["id"], {})
        present = a.get("present", 0) + 0.5 * a.get("half", 0)
        base = st["salary_monthly"] or 0
        payable = round(base / 30 * present, 2)
        pay = db.qone("SELECT * FROM staff_pay WHERE user_id=? AND month=?", (st["id"], m))
        paid = pay and pay["paid"]
        sheet += (f"<tr><td>{html.escape(st['name'] or st['email'] or '—')}</td>"
                  f"<td>{money(base)}</td><td>{present}</td><td>{a.get('absent', 0)}</td>"
                  f"<td>{a.get('leave', 0)}</td><td><b>{money(payable)}</b></td>"
                  f"<td>{'✅ ' + T('Paid') if paid else f'''<form method='post' action='/hotelpms/payroll/pay' style='display:inline'>
<input type='hidden' name='user_id' value='{st['id']}'>
<input type='hidden' name='month' value='{m}'>
<input type='hidden' name='net' value='{payable}'>
<input type='hidden' name='base' value='{base}'>
<input type='hidden' name='present' value='{present}'>
<button class='btn small green' type='submit'>{T('Mark paid')}</button></form>'''}</td></tr>")
    body = f"""
<h1>💰 {T('Payroll')}</h1>
<div class="panel"><h2>{T('Staff')} — {T('Mark today')} ({today})</h2>
<table><tr><th>{T('Name')}</th><th>{T('Role')}</th><th>{T('Monthly salary')}</th>
<th>{T('Attendance')}</th></tr>{srows}</table></div>
<div class="panel"><h2>{T('Salary sheet')} — {html.escape(m)}</h2>
<form method="get" action="/hotelpms/payroll" style="max-width:220px">
<label>{T('Month')}</label><input type="month" name="month" value="{html.escape(m)}" onchange="this.form.submit()"></form>
<table><tr><th>{T('Name')}</th><th>{T('Base')}</th><th>{T('Present')}</th><th>{T('Absent')}</th>
<th>{T('Leave')}</th><th>{T('Net pay')}</th><th></th></tr>{sheet}</table>
<p style="color:#64748b;font-size:.9rem">{T('Payroll note')}</p></div>
"""
    return HTMLResponse(_page(T("Payroll"), body, u, _lang(request)))


@router.post("/hotelpms/payroll/attendance")
def payroll_attendance(request: Request, user_id: int = Form(0), status: str = Form("present")):
    u = need_login(request)
    if not u:
        return login_redirect()
    if status not in ("present", "absent", "leave", "half"):
        return RedirectResponse("/hotelpms/payroll", status_code=303)
    db.q("""INSERT INTO attendance (user_id, att_date, status, created_at) VALUES (?,?,?,?)
            ON CONFLICT(user_id, att_date) DO UPDATE SET status=excluded.status""",
         (user_id, today_str(), status, db.now()))
    return RedirectResponse("/hotelpms/payroll", status_code=303)


@router.post("/hotelpms/payroll/salary")
def payroll_salary(request: Request, user_id: int = Form(0), salary: float = Form(0)):
    u = need_owner(request)
    if not u:
        return login_redirect()
    db.q("UPDATE users SET salary_monthly=? WHERE id=?", (max(0, salary), user_id))
    return RedirectResponse("/hotelpms/payroll", status_code=303)


@router.post("/hotelpms/payroll/pay")
def payroll_pay(request: Request, user_id: int = Form(0), month: str = Form(""),
                net: float = Form(0), base: float = Form(0), present: float = Form(0)):
    u = need_owner(request)
    if not u:
        return login_redirect()
    db.q("""INSERT INTO staff_pay (user_id, month, base_salary, present_days, net_pay, paid, created_at)
            VALUES (?,?,?,?,?,1,?)
            ON CONFLICT(user_id, month) DO UPDATE SET net_pay=excluded.net_pay, paid=1,
            base_salary=excluded.base_salary, present_days=excluded.present_days""",
         (user_id, month, base, present, net, db.now()))
    return RedirectResponse(f"/hotelpms/payroll?month={month}", status_code=303)
