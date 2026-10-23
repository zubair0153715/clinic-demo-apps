"""LabLink (/lablink) — university lab-connect for SMBBMU Larkana Pharm-D.

Teachers & students connect: announcements, experiments library with exact
quantities, lab inventory (chemicals + instruments), library catalog,
weekly timetable and in-app auto-notifications for the day's labs.

Honest limit: real WhatsApp auto-sending needs the university's official
WhatsApp Business API — here the app prepares a ready-to-copy WhatsApp
message; notifications inside the app are automatic.
"""
import datetime
import json
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.lablink import auth, db
from app.lablink.pages import BASE, diagram_box, esc, layout

log = logging.getLogger("lablink.routes")
router = APIRouter(prefix="/lablink")

SUBJECTS = ["Pharmaceutics", "Pharmacology", "Pharmacognosy",
            "Pharmaceutical Chemistry", "Physiology"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ------------------------------------------------------------------ helpers

def current_user(request: Request):
    return auth.user_from_token(request.cookies.get(auth.COOKIE, ""))


def today_info():
    t = datetime.date.today()
    return t, t.strftime("%A")


def ensure_notifications(user):
    """Idempotently create today's-lab notifications for this user."""
    t, day = today_info()
    rows = db.qall("SELECT * FROM timetable WHERE day=? ORDER BY start_time", (day,))
    for r in rows:
        if user["role"] == "student" and r["batch"] != (user.get("batch") or ""):
            continue
        dedupe = f"lab:{user['id']}:{t.isoformat()}:{r['id']}"
        title = f"Today {r['start_time']} — {r['subject']} Lab"
        body = (f"{r['batch']} · {r['lab_room']} · Teacher: {r['teacher']} "
                f"({r['start_time']}–{r['end_time']})")
        db.q("INSERT OR IGNORE INTO notifications (user_id, dedupe, title, body, created_at)"
             " VALUES (?,?,?,?,?)", (user["id"], dedupe, title, body, db.now()))


def unread_count(user):
    if not user:
        return 0
    row = db.qone("SELECT COUNT(*) c FROM notifications WHERE user_id=? AND is_read=0",
                  (user["id"],))
    return row["c"] if row else 0


def page(request, title, active, body, status=200):
    user = current_user(request)
    if user:
        ensure_notifications(user)
    return HTMLResponse(layout(title, user, active, body, unread_count(user)),
                        status_code=status)


def need_login(request):
    """Return (user, redirect_response). Exactly one is not None."""
    user = current_user(request)
    if not user:
        return None, RedirectResponse(f"{BASE}/login", status_code=303)
    return user, None


def fmt_date(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%d %b %Y, %I:%M %p")


def whatsapp_text(rows, day, datestr):
    lines = [f"*LabLink — Labs on {day}, {datestr}*", ""]
    if not rows:
        lines.append("Aaj koi lab schedule nahi hai.")
    for r in rows:
        lines.append(f"• {r['start_time']}–{r['end_time']} — {r['subject']}")
        lines.append(f"  {r['batch']} · {r['lab_room']} · {r['teacher']}")
    lines += ["", "Lab coat + practical notebook lazmi. — LabLink, SMBBMU"]
    return "\n".join(lines)


# --------------------------------------------------------------------- auth

def _auth_page(title, inner):
    return HTMLResponse(layout(title, None, "", f'<div class="auth-wrap">{inner}</div>'))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    if current_user(request):
        return RedirectResponse(f"{BASE}/home", status_code=303)
    return RedirectResponse(f"{BASE}/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, err: str = ""):
    errh = f'<div class="err">{esc(err)}</div>' if err else ""
    inner = f"""
    <div class="card"><h2>🔗 LabLink — Login</h2>
    <p class="muted">SMBBMU Larkana · Pharm-D labs, library &amp; timetable — teachers aur students ek jagah.</p>
    {errh}
    <form method="post" action="{BASE}/login">
      <label>Email</label><input name="email" type="email" required placeholder="you@example.pk">
      <label>Password</label><input name="password" type="password" required>
      <button class="btn" style="width:100%">Login</button>
    </form>
    <p class="muted" style="margin-top:12px">New here? <a href="{BASE}/register">Create an account</a></p>
    <details><summary>Demo accounts (tap to view)</summary>
      <p class="muted">Student: <b>student@demo.pk</b> / demo1234<br>
      Teacher: <b>teacher@demo.pk</b> / demo1234<br>
      Admin: <b>admin@demo.pk</b> / demo1234</p></details>
    </div>"""
    return _auth_page("Login", inner)


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = auth.authenticate(email, password)
    if not user:
        return RedirectResponse(f"{BASE}/login?err=Email+or+password+galat+hai", status_code=303)
    resp = RedirectResponse(f"{BASE}/home", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.new_session(user["id"]),
                    max_age=auth.SESSION_DAYS * 86400, httponly=True, samesite="lax")
    return resp


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, err: str = ""):
    errh = f'<div class="err">{esc(err)}</div>' if err else ""
    batch_opts = "".join(f'<option>{esc(b)}</option>' for b in
                         ["Pharm-D 1st Year Batch A", "Pharm-D 2nd Year Batch A",
                          "Pharm-D 2nd Year Batch B", "Pharm-D 3rd Year Batch A",
                          "Pharm-D 3rd Year Batch B", "Pharm-D 4th Year Batch A",
                          "Pharm-D 5th Year Batch A", "Other"])
    inner = f"""
    <div class="card"><h2>Create account</h2>{errh}
    <form method="post" action="{BASE}/register">
      <label>Full name</label><input name="name" required>
      <label>Email</label><input name="email" type="email" required>
      <label>Password</label><input name="password" type="password" required minlength="6">
      <label>I am a</label><select name="role"><option value="student">Student</option>
      <option value="teacher">Teacher</option></select>
      <label>Batch (students)</label><select name="batch">{batch_opts}</select>
      <label>Phone (optional)</label><input name="phone">
      <button class="btn" style="width:100%">Register</button>
    </form>
    <p class="muted" style="margin-top:12px">Already registered? <a href="{BASE}/login">Login</a></p></div>"""
    return _auth_page("Register", inner)


@router.post("/register")
def register(name: str = Form(...), email: str = Form(...), password: str = Form(...),
             role: str = Form("student"), batch: str = Form(""), phone: str = Form("")):
    email = email.strip().lower()
    if role not in ("student", "teacher"):
        role = "student"
    if db.qone("SELECT id FROM users WHERE email=?", (email,)):
        return RedirectResponse(f"{BASE}/register?err=Ye+email+pehle+se+registered+hai",
                                status_code=303)
    db.q("INSERT INTO users (name, email, password_hash, role, batch, phone, created_at)"
         " VALUES (?,?,?,?,?,?,?)",
         (name.strip(), email, auth.hash_password(password), role,
          batch if role == "student" else "", phone.strip(), db.now()))
    user = auth.authenticate(email, password)
    resp = RedirectResponse(f"{BASE}/home", status_code=303)
    resp.set_cookie(auth.COOKIE, auth.new_session(user["id"]),
                    max_age=auth.SESSION_DAYS * 86400, httponly=True, samesite="lax")
    return resp


@router.get("/logout")
def logout(request: Request):
    auth.destroy_session(request.cookies.get(auth.COOKIE, ""))
    resp = RedirectResponse(f"{BASE}/login", status_code=303)
    resp.delete_cookie(auth.COOKIE)
    return resp


# --------------------------------------------------------------------- home

@router.get("/home", response_class=HTMLResponse)
def home(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    t, day = today_info()
    if user["role"] == "student":
        labs = db.qall("SELECT * FROM timetable WHERE day=? AND batch=? ORDER BY start_time",
                       (day, user.get("batch") or ""))
    else:
        labs = db.qall("SELECT * FROM timetable WHERE day=? ORDER BY start_time", (day,))
    lab_cards = "".join(
        f'<div class="card"><span class="chip blue">{esc(r["start_time"])}–{esc(r["end_time"])}</span>'
        f'<span class="chip">{esc(r["subject"])}</span><h3 style="margin-top:6px">{esc(r["lab_room"])}</h3>'
        f'<p class="muted" style="margin:0">{esc(r["batch"])} · Teacher: {esc(r["teacher"])}</p></div>'
        for r in labs)
    if not labs:
        lab_cards = '<div class="card"><p class="muted" style="margin:0">Aaj (' + esc(day) + ') koi lab schedule nahi hai.</p></div>'

    post_form = ""
    if auth.is_staff(user):
        batch_opts = '<option value="">All batches (sab ke liye)</option>' + "".join(
            f'<option>{esc(b)}</option>' for b in
            sorted({r["batch"] for r in db.qall("SELECT DISTINCT batch FROM timetable")}))
        post_form = f"""
        <div class="card"><h3>📢 New announcement</h3>
        <form method="post" action="{BASE}/announce">
          <input name="title" placeholder="Title" required>
          <textarea name="body" placeholder="Announcement likhein…" required></textarea>
          <label>Target batch</label><select name="target_batch">{batch_opts}</select>
          <button class="btn">Post announcement</button>
        </form></div>"""

    anns = db.qall(
        "SELECT a.*, u.name author FROM announcements a JOIN users u ON u.id=a.author_id"
        " ORDER BY a.id DESC LIMIT 30")
    feed = []
    for a in anns:
        if user["role"] == "student" and a["target_batch"] and a["target_batch"] != user.get("batch"):
            continue
        comments = db.qall(
            "SELECT c.*, u.name author FROM comments c JOIN users u ON u.id=c.author_id"
            " WHERE c.announcement_id=? ORDER BY c.id", (a["id"],))
        ch = "".join(
            f'<div class="comment"><b>{esc(c["author"])}</b> <span class="muted">{esc(fmt_date(c["created_at"]))}</span>'
            f'<br>{esc(c["body"])}</div>' for c in comments)
        target = f'<span class="chip">{esc(a["target_batch"])}</span>' if a["target_batch"] else '<span class="chip">All batches</span>'
        feed.append(f"""
        <div class="card"><div class="rowflex"><h3 style="margin:0">{esc(a["title"])}</h3>{target}</div>
        <p class="muted" style="margin:2px 0 8px">{esc(a["author"])} · {esc(fmt_date(a["created_at"]))}</p>
        <p style="margin:0 0 6px">{esc(a["body"])}</p>
        {ch}
        <form method="post" action="{BASE}/comment" style="margin-top:10px">
          <input type="hidden" name="announcement_id" value="{a['id']}">
          <div class="search"><input name="body" placeholder="Comment…" required>
          <button class="btn small">Post</button></div>
        </form></div>""")
    body = f"""
    <h1 class="pagetitle">Assalam-o-Alaikum, {esc(user['name'].split()[0])} 👋</h1>
    <h3 style="color:#0b3d2e">🧪 Today's Labs — {esc(day)}, {esc(t.strftime('%d %b %Y'))}</h3>
    {lab_cards}
    {post_form}
    <h3 style="color:#0b3d2e">📢 Announcements</h3>
    {''.join(feed) if feed else '<div class="card"><p class="muted">Abhi koi announcement nahi.</p></div>'}"""
    return page(request, "Home", "home", body)


@router.post("/announce")
def announce(request: Request, title: str = Form(...), body: str = Form(...),
             target_batch: str = Form("")):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/home", status_code=303)
    cur = db.q("INSERT INTO announcements (author_id, title, body, target_batch, created_at)"
               " VALUES (?,?,?,?,?)",
               (user["id"], title.strip(), body.strip(), target_batch, db.now()))
    ann_id = cur.lastrowid
    targets = db.qall("SELECT id, batch FROM users WHERE is_active=1")
    for tuser in targets:
        if target_batch and tuser["batch"] != target_batch:
            continue
        db.q("INSERT OR IGNORE INTO notifications (user_id, dedupe, title, body, created_at)"
             " VALUES (?,?,?,?,?)",
             (tuser["id"], f"ann:{tuser['id']}:{ann_id}", f"📢 {title.strip()}",
              body.strip()[:200], db.now()))
    return RedirectResponse(f"{BASE}/home", status_code=303)


@router.post("/comment")
def comment(request: Request, announcement_id: int = Form(...), body: str = Form(...)):
    user, redir = need_login(request)
    if redir:
        return redir
    if body.strip():
        db.q("INSERT INTO comments (announcement_id, author_id, body, created_at) VALUES (?,?,?,?)",
             (announcement_id, user["id"], body.strip(), db.now()))
    return RedirectResponse(f"{BASE}/home", status_code=303)


# --------------------------------------------------------------- experiments

@router.get("/experiments", response_class=HTMLResponse)
def experiments(request: Request, q: str = ""):
    user, redir = need_login(request)
    if redir:
        return redir
    q = q.strip()
    if q:
        like = f"%{q}%"
        rows = db.qall("SELECT * FROM experiments WHERE title LIKE ? OR subject LIKE ?"
                       " OR chemicals LIKE ? OR objective LIKE ? ORDER BY subject, title",
                       (like, like, like, like))
    else:
        rows = db.qall("SELECT * FROM experiments ORDER BY subject, title")
    cards = []
    for e in rows:
        try:
            nchem = len(json.loads(e["chemicals"] or "[]"))
        except Exception:
            nchem = 0
        cards.append(f"""
        <div class="card"><span class="chip">{esc(e['subject'])}</span>
        <span class="chip blue">{nchem} chemicals</span>
        <h3 style="margin:6px 0 4px"><a href="{BASE}/experiments/{e['id']}">{esc(e['title'])}</a></h3>
        <p class="muted" style="margin:0">{esc((e['objective'] or '')[:140])}…</p></div>""")
    add = (f'<a class="btn" href="{BASE}/experiments/new">+ Add experiment</a>'
           if auth.is_staff(user) else "")
    body = f"""
    <h1 class="pagetitle">🧪 Experiments Library</h1>
    <form method="get" action="{BASE}/experiments"><div class="search">
      <input name="q" value="{esc(q)}" placeholder="Search: experiment, subject, chemical (e.g. aspirin, sucrose)…">
      <button class="btn">Search</button></div></form>
    <p class="muted">{len(rows)} experiment(s) mile. {add}</p>
    {''.join(cards) if cards else '<div class="card"><p class="muted">Koi experiment nahi mila.</p></div>'}"""
    return page(request, "Experiments", "experiments", body)


def _exp_form(e=None):
    e = e or {}
    chems = ""
    if e:
        try:
            chems = "\n".join(f"{c.get('name','')} | {c.get('qty','')} | {c.get('unit','')} | {c.get('grade','')}"
                              for c in json.loads(e["chemicals"] or "[]"))
        except Exception:
            chems = ""
    subj_opts = "".join(f'<option {"selected" if e.get("subject")==s else ""}>{s}</option>'
                        for s in SUBJECTS)
    diag_keys = ["", "beaker", "bottle", "flask", "tablet", "funnel", "heart", "microscope"]
    diag_opts = "".join(
        f'<option value="{d}" {"selected" if e.get("diagram")==d else ""}>{d or "— none —"}</option>'
        for d in diag_keys)
    action = f"{BASE}/experiments/{e['id']}/edit" if e else f"{BASE}/experiments/new"
    return f"""
    <div class="card"><form method="post" action="{action}">
      <label>Title</label><input name="title" required value="{esc(e.get('title',''))}">
      <label>Subject</label><select name="subject">{subj_opts}</select>
      <label>Objective / Aim</label><textarea name="objective">{esc(e.get('objective',''))}</textarea>
      <label>Chemicals — one per line: Name | Quantity | Unit | Grade</label>
      <textarea name="chemicals" style="min-height:130px">{esc(chems)}</textarea>
      <label>Apparatus — one per line</label><textarea name="apparatus">{esc(e.get('apparatus',''))}</textarea>
      <label>Procedure — one step per line</label>
      <textarea name="procedure" style="min-height:170px">{esc(e.get('procedure',''))}</textarea>
      <label>Precautions / Safety</label><textarea name="precautions">{esc(e.get('precautions',''))}</textarea>
      <label>Expected observation / result</label><textarea name="observation">{esc(e.get('observation',''))}</textarea>
      <label>Diagram</label><select name="diagram">{diag_opts}</select>
      <button class="btn">Save experiment</button>
    </form></div>"""


def _parse_chems(text):
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        while len(parts) < 4:
            parts.append("")
        out.append({"name": parts[0], "qty": parts[1], "unit": parts[2], "grade": parts[3]})
    return out


def _save_exp(request, exp_id, form):
    user = current_user(request)
    vals = (form["title"].strip(), form["subject"], form["objective"].strip(),
            json.dumps(_parse_chems(form["chemicals"])), form["apparatus"].strip(),
            form["procedure"].strip(), form["precautions"].strip(),
            form["observation"].strip(), form["diagram"])
    if exp_id:
        db.q("UPDATE experiments SET title=?, subject=?, objective=?, chemicals=?, apparatus=?,"
             " procedure=?, precautions=?, observation=?, diagram=? WHERE id=?",
             vals + (exp_id,))
    else:
        db.q("INSERT INTO experiments (title, subject, objective, chemicals, apparatus, procedure,"
             " precautions, observation, diagram, created_by, created_at)"
             " VALUES (?,?,?,?,?,?,?,?,?,?,?)", vals + (user["id"], db.now()))
    return RedirectResponse(f"{BASE}/experiments", status_code=303)


@router.get("/experiments/new", response_class=HTMLResponse)
def exp_new(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    return page(request, "Add experiment", "experiments",
                '<h1 class="pagetitle">Add experiment</h1>' + _exp_form())


@router.post("/experiments/new")
def exp_new_post(request: Request, title: str = Form(...), subject: str = Form(...),
                 objective: str = Form(""), chemicals: str = Form(""),
                 apparatus: str = Form(""), procedure: str = Form(""),
                 precautions: str = Form(""), observation: str = Form(""),
                 diagram: str = Form("")):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    return _save_exp(request, None, dict(title=title, subject=subject, objective=objective,
                                         chemicals=chemicals, apparatus=apparatus,
                                         procedure=procedure, precautions=precautions,
                                         observation=observation, diagram=diagram))


@router.get("/experiments/{exp_id}", response_class=HTMLResponse)
def exp_detail(request: Request, exp_id: int):
    user, redir = need_login(request)
    if redir:
        return redir
    e = db.qone("SELECT * FROM experiments WHERE id=?", (exp_id,))
    if not e:
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    try:
        chems = json.loads(e["chemicals"] or "[]")
    except Exception:
        chems = []
    chem_rows = "".join(
        f"<tr><td>{esc(c.get('name',''))}</td><td><b>{esc(c.get('qty',''))} {esc(c.get('unit',''))}</b></td>"
        f"<td>{esc(c.get('grade',''))}</td></tr>" for c in chems)
    app_list = "".join(f"<li>{esc(x)}</li>" for x in (e["apparatus"] or "").splitlines() if x.strip())
    steps = "".join(f"<li>{esc(x)}</li>" for x in (e["procedure"] or "").splitlines() if x.strip())
    edit = (f'<a class="btn small alt" href="{BASE}/experiments/{e["id"]}/edit">✏️ Edit</a>'
            if auth.is_staff(user) else "")
    body = f"""
    <p><a href="{BASE}/experiments">← All experiments</a></p>
    <div class="card"><span class="chip">{esc(e['subject'])}</span> {edit}
      <h2 style="margin-top:8px">{esc(e['title'])}</h2>
      <p><b>Objective:</b> {esc(e['objective'])}</p>
      {diagram_box(e['diagram'])}
    </div>
    <div class="card"><h3>⚗️ Chemicals required (exact quantities)</h3>
      <table><tr><th>Chemical</th><th>Quantity</th><th>Grade</th></tr>{chem_rows}</table></div>
    <div class="card"><h3>🧰 Apparatus</h3><ul>{app_list}</ul></div>
    <div class="card"><h3>📋 Procedure</h3><ol class="proc">{steps}</ol></div>
    <div class="card"><h3>⚠️ Precautions / Safety</h3><p>{esc(e['precautions'])}</p></div>
    <div class="card"><h3>👁️ Expected observation / result</h3><p>{esc(e['observation'])}</p></div>"""
    return page(request, e["title"], "experiments", body)


@router.get("/experiments/{exp_id}/edit", response_class=HTMLResponse)
def exp_edit(request: Request, exp_id: int):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    e = db.qone("SELECT * FROM experiments WHERE id=?", (exp_id,))
    if not e:
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    return page(request, "Edit experiment", "experiments",
                '<h1 class="pagetitle">Edit experiment</h1>' + _exp_form(dict(e)))


@router.post("/experiments/{exp_id}/edit")
def exp_edit_post(request: Request, exp_id: int, title: str = Form(...),
                  subject: str = Form(...), objective: str = Form(""),
                  chemicals: str = Form(""), apparatus: str = Form(""),
                  procedure: str = Form(""), precautions: str = Form(""),
                  observation: str = Form(""), diagram: str = Form("")):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/experiments", status_code=303)
    return _save_exp(request, exp_id, dict(title=title, subject=subject, objective=objective,
                                           chemicals=chemicals, apparatus=apparatus,
                                           procedure=procedure, precautions=precautions,
                                           observation=observation, diagram=diagram))


@router.post("/experiments/{exp_id}/delete")
def exp_delete(request: Request, exp_id: int):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_admin(user):
        db.q("DELETE FROM experiments WHERE id=?", (exp_id,))
    return RedirectResponse(f"{BASE}/experiments", status_code=303)


# --------------------------------------------------------------------- labs

@router.get("/labs", response_class=HTMLResponse)
def labs(request: Request, q: str = ""):
    user, redir = need_login(request)
    if redir:
        return redir
    staff = auth.is_staff(user)
    q = q.strip()
    like = f"%{q}%"
    chems = db.qall("SELECT * FROM inv_chemicals WHERE name LIKE ? OR lab LIKE ? ORDER BY lab, name",
                    (like, like)) if q else db.qall("SELECT * FROM inv_chemicals ORDER BY lab, name")
    insts = db.qall("SELECT * FROM inv_instruments WHERE name LIKE ? OR lab LIKE ? ORDER BY lab, name",
                    (like, like)) if q else db.qall("SELECT * FROM inv_instruments ORDER BY lab, name")
    chem_rows = []
    for c in chems:
        low = c["threshold"] and c["qty"] < c["threshold"]
        badge = '<span class="chip red">⚠ Low stock</span>' if low else '<span class="chip">In stock</span>'
        upd = ""
        if staff:
            upd = (f'<form method="post" action="{BASE}/labs/chemical/{c["id"]}" style="display:flex;gap:6px">'
                   f'<input name="qty" type="number" step="any" value="{c["qty"]}" style="width:90px;margin:0">'
                   f'<button class="btn small">Update</button></form>')
        chem_rows.append(f"<tr><td><b>{esc(c['name'])}</b><br>{badge}</td><td>{c['qty']:g} {esc(c['unit'])}</td>"
                         f"<td>{esc(c['lab'])}</td><td>{upd}</td></tr>")
    inst_rows = []
    for i in insts:
        badge = ('<span class="chip">✅ Working</span>' if i["status"] == "working"
                 else '<span class="chip amber">🛠 Under maintenance</span>')
        upd = ""
        if staff:
            other = "maintenance" if i["status"] == "working" else "working"
            upd = (f'<form method="post" action="{BASE}/labs/instrument/{i["id"]}">'
                   f'<input type="hidden" name="status" value="{other}">'
                   f'<button class="btn small alt">Mark {other}</button></form>')
        inst_rows.append(f"<tr><td><b>{esc(i['name'])}</b></td><td>{esc(i['lab'])}</td>"
                         f"<td>{badge}</td><td>{upd}</td></tr>")
    add_forms = ""
    if staff:
        add_forms = f"""
        <div class="grid">
        <div class="card"><h3>+ Add chemical</h3><form method="post" action="{BASE}/labs/chemical/add">
          <input name="name" placeholder="Name" required>
          <div class="search"><input name="qty" type="number" step="any" placeholder="Qty" required>
          <input name="unit" placeholder="Unit (g/kg/mL/L)" required></div>
          <input name="lab" placeholder="Lab / room" required style="margin-top:10px">
          <input name="threshold" type="number" step="any" placeholder="Low-stock threshold">
          <button class="btn small">Add</button></form></div>
        <div class="card"><h3>+ Add instrument</h3><form method="post" action="{BASE}/labs/instrument/add">
          <input name="name" placeholder="Name" required>
          <input name="lab" placeholder="Lab / room" required>
          <select name="status"><option value="working">Working</option>
          <option value="maintenance">Under maintenance</option></select>
          <button class="btn small">Add</button></form></div></div>"""
    body = f"""
    <h1 class="pagetitle">🔬 Lab Inventory — kya available hai?</h1>
    <form method="get" action="{BASE}/labs"><div class="search">
      <input name="q" value="{esc(q)}" placeholder="Search chemical, instrument ya lab…">
      <button class="btn">Search</button></div></form>
    <div class="card" style="margin-top:14px"><h3>⚗️ Chemicals ({len(chems)})</h3>
      <table><tr><th>Chemical</th><th>Stock</th><th>Lab</th><th></th></tr>{''.join(chem_rows)}</table></div>
    <div class="card"><h3>🧰 Instruments ({len(insts)})</h3>
      <table><tr><th>Instrument</th><th>Lab</th><th>Status</th><th></th></tr>{''.join(inst_rows)}</table></div>
    {add_forms}"""
    return page(request, "Labs", "labs", body)


@router.post("/labs/chemical/{cid}")
def chem_update(request: Request, cid: int, qty: float = Form(...)):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user):
        db.q("UPDATE inv_chemicals SET qty=? WHERE id=?", (qty, cid))
    return RedirectResponse(f"{BASE}/labs", status_code=303)


@router.post("/labs/chemical/add")
def chem_add(request: Request, name: str = Form(...), qty: float = Form(...),
             unit: str = Form(...), lab: str = Form(...), threshold: float = Form(0)):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user):
        db.q("INSERT INTO inv_chemicals (name, qty, unit, lab, threshold) VALUES (?,?,?,?,?)",
             (name.strip(), qty, unit.strip(), lab.strip(), threshold))
    return RedirectResponse(f"{BASE}/labs", status_code=303)


@router.post("/labs/instrument/{iid}")
def inst_update(request: Request, iid: int, status: str = Form(...)):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user) and status in ("working", "maintenance"):
        db.q("UPDATE inv_instruments SET status=? WHERE id=?", (status, iid))
    return RedirectResponse(f"{BASE}/labs", status_code=303)


@router.post("/labs/instrument/add")
def inst_add(request: Request, name: str = Form(...), lab: str = Form(...),
             status: str = Form("working")):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user):
        db.q("INSERT INTO inv_instruments (name, lab, status) VALUES (?,?,?)",
             (name.strip(), lab.strip(), status if status in ("working", "maintenance") else "working"))
    return RedirectResponse(f"{BASE}/labs", status_code=303)


# ------------------------------------------------------------------ library

@router.get("/library", response_class=HTMLResponse)
def library(request: Request, q: str = "", msg: str = ""):
    user, redir = need_login(request)
    if redir:
        return redir
    staff = auth.is_staff(user)
    q = q.strip()
    like = f"%{q}%"
    books = db.qall("SELECT * FROM books WHERE title LIKE ? OR author LIKE ? OR subject LIKE ?"
                    " ORDER BY subject, title", (like, like, like)) if q else \
        db.qall("SELECT * FROM books ORDER BY subject, title")
    rows = []
    my_reqs = {r["book_id"] for r in db.qall(
        "SELECT book_id FROM book_requests WHERE user_id=? AND status='pending'", (user["id"],))}
    for b in books:
        avail = b["available_copies"]
        badge = (f'<span class="chip">✅ {avail} available</span>' if avail > 0
                 else '<span class="chip red">❌ All issued</span>')
        action = ""
        if user["role"] == "student":
            if b["id"] in my_reqs:
                action = '<span class="chip amber">Requested</span>'
            elif avail > 0:
                action = (f'<form method="post" action="{BASE}/library/reserve/{b["id"]}">'
                          f'<button class="btn small">Reserve</button></form>')
        rows.append(f"<tr><td><b>{esc(b['title'])}</b><br><span class='muted'>{esc(b['author'])} · {esc(b['edition'])}</span></td>"
                    f"<td>{esc(b['subject'])}</td><td>{b['total_copies']}</td><td>{badge}</td>"
                    f"<td>{esc(b['shelf'])}</td><td>{action}</td></tr>")
    req_section = ""
    if staff:
        reqs = db.qall("SELECT r.*, b.title, u.name student, u.batch FROM book_requests r"
                       " JOIN books b ON b.id=r.book_id JOIN users u ON u.id=r.user_id"
                       " ORDER BY r.id DESC LIMIT 50")
        rr = []
        for r in reqs:
            acts = ""
            if r["status"] == "pending":
                acts = (f'<form method="post" action="{BASE}/library/request/{r["id"]}/issue" style="display:inline">'
                        f'<button class="btn small">Issue</button></form> '
                        f'<form method="post" action="{BASE}/library/request/{r["id"]}/cancel" style="display:inline">'
                        f'<button class="btn small red">Cancel</button></form>')
            elif r["status"] == "issued":
                acts = (f'<form method="post" action="{BASE}/library/request/{r["id"]}/return" style="display:inline">'
                        f'<button class="btn small alt">Mark returned</button></form>')
            rr.append(f"<tr><td>{esc(r['title'])}</td><td>{esc(r['student'])}<br><span class='muted'>{esc(r['batch'])}</span></td>"
                      f"<td>{esc(r['status'])}</td><td>{esc(fmt_date(r['created_at']))}</td><td>{acts}</td></tr>")
        add_book = f"""
        <div class="card"><h3>+ Add book</h3><form method="post" action="{BASE}/library/add">
          <input name="title" placeholder="Title" required>
          <div class="search"><input name="author" placeholder="Author">
          <input name="edition" placeholder="Edition"></div>
          <div class="search" style="margin-top:10px"><input name="subject" placeholder="Subject">
          <input name="shelf" placeholder="Shelf / rack"></div>
          <div class="search" style="margin-top:10px"><input name="total_copies" type="number" value="1" min="0">
          <input name="available_copies" type="number" value="1" min="0"></div>
          <button class="btn small" style="margin-top:10px">Add book</button></form></div>"""
        req_section = f"""
        <div class="card"><h3>📥 Book requests ({len(reqs)})</h3>
        {'<table><tr><th>Book</th><th>Student</th><th>Status</th><th>Date</th><th></th></tr>' + ''.join(rr) + '</table>' if rr else '<p class="muted">Koi request nahi.</p>'}</div>
        {add_book}"""
    msgh = f'<div class="ok">{esc(msg)}</div>' if msg else ""
    body = f"""
    <h1 class="pagetitle">📚 Library — kon si books hain?</h1>
    {msgh}
    <form method="get" action="{BASE}/library"><div class="search">
      <input name="q" value="{esc(q)}" placeholder="Search title, author ya subject (e.g. Katzung, Tripathi)…">
      <button class="btn">Search</button></div></form>
    <div class="card" style="margin-top:14px"><table>
      <tr><th>Book</th><th>Subject</th><th>Copies</th><th>Status</th><th>Shelf</th><th></th></tr>
      {''.join(rows) if rows else '<tr><td colspan="6" class="muted">Koi book nahi mili.</td></tr>'}
    </table></div>
    {req_section}"""
    return page(request, "Library", "library", body)


@router.post("/library/reserve/{book_id}")
def reserve(request: Request, book_id: int):
    user, redir = need_login(request)
    if redir:
        return redir
    b = db.qone("SELECT * FROM books WHERE id=?", (book_id,))
    if b and b["available_copies"] > 0 and not db.qone(
            "SELECT id FROM book_requests WHERE book_id=? AND user_id=? AND status='pending'",
            (book_id, user["id"])):
        db.q("INSERT INTO book_requests (book_id, user_id, created_at) VALUES (?,?,?)",
             (book_id, user["id"], db.now()))
        return RedirectResponse(f"{BASE}/library?msg=Request+bhej+di+gayi+hai", status_code=303)
    return RedirectResponse(f"{BASE}/library", status_code=303)


@router.post("/library/add")
def book_add(request: Request, title: str = Form(...), author: str = Form(""),
             edition: str = Form(""), subject: str = Form(""), shelf: str = Form(""),
             total_copies: int = Form(1), available_copies: int = Form(1)):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user):
        db.q("INSERT INTO books (title, author, edition, subject, total_copies, available_copies, shelf)"
             " VALUES (?,?,?,?,?,?,?)",
             (title.strip(), author.strip(), edition.strip(), subject.strip(),
              total_copies, available_copies, shelf.strip()))
    return RedirectResponse(f"{BASE}/library", status_code=303)


@router.post("/library/request/{rid}/{action}")
def request_action(request: Request, rid: int, action: str):
    user, redir = need_login(request)
    if redir:
        return redir
    if not auth.is_staff(user):
        return RedirectResponse(f"{BASE}/library", status_code=303)
    r = db.qone("SELECT * FROM book_requests WHERE id=?", (rid,))
    if r:
        if action == "issue" and r["status"] == "pending":
            db.q("UPDATE book_requests SET status='issued' WHERE id=?", (rid,))
            db.q("UPDATE books SET available_copies=MAX(available_copies-1,0) WHERE id=?",
                 (r["book_id"],))
        elif action == "return" and r["status"] == "issued":
            db.q("UPDATE book_requests SET status='returned' WHERE id=?", (rid,))
            db.q("UPDATE books SET available_copies=MIN(available_copies+1,total_copies) WHERE id=?",
                 (r["book_id"],))
        elif action == "cancel":
            db.q("UPDATE book_requests SET status='cancelled' WHERE id=?", (rid,))
    return RedirectResponse(f"{BASE}/library", status_code=303)


# ---------------------------------------------------------------- timetable

@router.get("/timetable", response_class=HTMLResponse)
def timetable(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    t, day = today_info()
    staff = auth.is_staff(user)
    today_rows = db.qall("SELECT * FROM timetable WHERE day=? ORDER BY start_time", (day,))
    wa = esc(whatsapp_text(today_rows, day, t.strftime("%d %b %Y")))
    blocks = []
    for d in DAYS:
        rows = db.qall("SELECT * FROM timetable WHERE day=? ORDER BY start_time", (d,))
        if not rows:
            continue
        items = "".join(
            f"<tr><td><b>{esc(r['start_time'])}–{esc(r['end_time'])}</b></td><td>{esc(r['subject'])}</td>"
            f"<td>{esc(r['batch'])}</td><td>{esc(r['lab_room'])}</td><td>{esc(r['teacher'])}</td></tr>"
            for r in rows)
        mark = ' <span class="chip blue">Today</span>' if d == day else ""
        blocks.append(f'<div class="card dayblock"><h3>{esc(d)}{mark}</h3>'
                      f'<table><tr><th>Time</th><th>Subject</th><th>Batch</th><th>Lab</th><th>Teacher</th></tr>{items}</table></div>')
    add_form = ""
    if staff:
        day_opts = "".join(f'<option>{d}</option>' for d in DAYS[:6])
        add_form = f"""
        <div class="card"><h3>+ Add timetable entry</h3>
        <form method="post" action="{BASE}/timetable/add">
          <label>Day</label><select name="day">{day_opts}</select>
          <div class="search"><input name="start_time" placeholder="Start (10:00 AM)" required>
          <input name="end_time" placeholder="End (12:00 PM)" required></div>
          <input name="batch" placeholder="Batch (e.g. Pharm-D 3rd Year Batch A)" required style="margin-top:10px">
          <div class="search"><input name="subject" placeholder="Subject" required>
          <input name="lab_room" placeholder="Lab room" required></div>
          <input name="teacher" placeholder="Teacher" required style="margin-top:10px">
          <button class="btn small">Add entry</button></form></div>"""
    body = f"""
    <h1 class="pagetitle">🗓️ Lab Timetable</h1>
    <div class="card"><h3>📲 Aaj ka WhatsApp message (ready to copy)</h3>
      <p class="muted">Ye text copy karke class group me bhej dein. <b>Note:</b> automatic WhatsApp
      sending ke liye university ka official WhatsApp Business API chahiye — LabLink abhi
      in-app notifications khud bhejta hai, WhatsApp text sirf ready karke deta hai.</p>
      <textarea id="wa" readonly style="min-height:130px">{wa}</textarea>
      <button class="btn" onclick="navigator.clipboard.writeText(document.getElementById('wa').value);this.textContent='✅ Copied!'">Copy WhatsApp message</button>
    </div>
    {''.join(blocks)}
    {add_form}"""
    return page(request, "Timetable", "timetable", body)


@router.post("/timetable/add")
def tt_add(request: Request, day: str = Form(...), start_time: str = Form(...),
           end_time: str = Form(...), batch: str = Form(...), subject: str = Form(...),
           lab_room: str = Form(...), teacher: str = Form(...)):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_staff(user) and day in DAYS:
        db.q("INSERT INTO timetable (day, start_time, end_time, batch, subject, lab_room, teacher)"
             " VALUES (?,?,?,?,?,?,?)",
             (day, start_time.strip(), end_time.strip(), batch.strip(), subject.strip(),
              lab_room.strip(), teacher.strip()))
    return RedirectResponse(f"{BASE}/timetable", status_code=303)


@router.post("/timetable/{tid}/delete")
def tt_delete(request: Request, tid: int):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_admin(user):
        db.q("DELETE FROM timetable WHERE id=?", (tid,))
    return RedirectResponse(f"{BASE}/timetable", status_code=303)


# ------------------------------------------------------------- notifications

@router.get("/notifications", response_class=HTMLResponse)
def notifications(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    ensure_notifications(user)
    rows = db.qall("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 60",
                   (user["id"],))
    items = "".join(
        f'<div class="card" style="{"opacity:.65" if n["is_read"] else ""}">'
        f'<b>{esc(n["title"])}</b><br><span class="muted">{esc(n["body"])}</span><br>'
        f'<span class="muted">{esc(fmt_date(n["created_at"]))}</span></div>' for n in rows)
    body = f"""
    <h1 class="pagetitle">🔔 Notifications</h1>
    <p class="muted">Lab wale din aap ki batch ko yahan khud-ba-khud message aata hai —
    teacher ki announcements bhi yahin milti hain.</p>
    <form method="post" action="{BASE}/notifications/read" style="margin-bottom:12px">
      <button class="btn small alt">Mark all as read</button></form>
    {items if items else '<div class="card"><p class="muted">Abhi koi notification nahi.</p></div>'}"""
    return page(request, "Notifications", "notifications", body)


@router.post("/notifications/read")
def notifications_read(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    db.q("UPDATE notifications SET is_read=1 WHERE user_id=?", (user["id"],))
    return RedirectResponse(f"{BASE}/notifications", status_code=303)


# ------------------------------------------------------------------ profile

@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    user, redir = need_login(request)
    if redir:
        return redir
    admin_section = ""
    if auth.is_admin(user):
        users = db.qall("SELECT * FROM users ORDER BY role, name")
        rows = []
        for u in users:
            role_opts = "".join(
                f'<option value="{r}" {"selected" if u["role"]==r else ""}>{r}</option>'
                for r in ("student", "teacher", "admin"))
            toggle = "Deactivate" if u["is_active"] else "Activate"
            rows.append(
                f'<tr><td><b>{esc(u["name"])}</b><br><span class="muted">{esc(u["email"])}</span></td>'
                f'<td>{esc(u["batch"])}</td><td>{esc(u["role"])}{"" if u["is_active"] else " (inactive)"}</td>'
                f'<td><form method="post" action="{BASE}/admin/user/{u["id"]}" style="display:flex;gap:6px">'
                f'<select name="role" style="width:auto;margin:0">{role_opts}</select>'
                f'<button class="btn small" name="act" value="role">Set role</button>'
                f'<button class="btn small red" name="act" value="toggle">{toggle}</button></form></td></tr>')
        admin_section = f"""
        <div class="card"><h3>👥 Manage users (admin)</h3>
        <table><tr><th>User</th><th>Batch</th><th>Role</th><th>Actions</th></tr>{''.join(rows)}</table></div>"""
    my_reqs = db.qall("SELECT r.*, b.title FROM book_requests r JOIN books b ON b.id=r.book_id"
                      " WHERE r.user_id=? ORDER BY r.id DESC", (user["id"],))
    req_html = ""
    if my_reqs:
        req_html = '<div class="card"><h3>📚 My book requests</h3>' + "".join(
            f'<p style="margin:4px 0">{esc(r["title"])} — <span class="chip">{esc(r["status"])}</span></p>'
            for r in my_reqs) + "</div>"
    body = f"""
    <h1 class="pagetitle">👤 Profile</h1>
    <div class="card">
      <p><b>Name:</b> {esc(user['name'])}</p>
      <p><b>Email:</b> {esc(user['email'])}</p>
      <p><b>Role:</b> {esc(user['role'].title())}</p>
      {'<p><b>Batch:</b> ' + esc(user['batch']) + '</p>' if user.get('batch') else ''}
      {'<p><b>Phone:</b> ' + esc(user['phone']) + '</p>' if user.get('phone') else ''}
      <a class="btn red" href="{BASE}/logout">Logout</a>
    </div>
    {req_html}
    {admin_section}
    <div class="card"><h3>About LabLink</h3>
    <p class="muted">LabLink — SMBBMU Larkana ke Pharm-D students aur teachers ke liye.
    Experiments, lab inventory, library aur timetable ek jagah.
    Note: demo data har deploy ke baad reset ho sakta hai (SQLite). Real WhatsApp auto-sending
    ke liye university ka official WhatsApp Business API darkar hai.</p></div>"""
    return page(request, "Profile", "profile", body)


@router.post("/admin/user/{uid}")
def admin_user(request: Request, uid: int, role: str = Form("student"), act: str = Form("role")):
    user, redir = need_login(request)
    if redir:
        return redir
    if auth.is_admin(user) and uid != user["id"]:
        if act == "role" and role in ("student", "teacher", "admin"):
            db.q("UPDATE users SET role=? WHERE id=?", (role, uid))
        elif act == "toggle":
            db.q("UPDATE users SET is_active=1-is_active WHERE id=?", (uid,))
    return RedirectResponse(f"{BASE}/profile", status_code=303)


# ---------------------------------------------------------------------- api

@router.get("/api/today")
def api_today(request: Request):
    user = current_user(request)
    if not user:
        return JSONResponse({"error": "login required"}, status_code=401)
    ensure_notifications(user)
    t, day = today_info()
    if user["role"] == "student":
        rows = db.qall("SELECT * FROM timetable WHERE day=? AND batch=? ORDER BY start_time",
                       (day, user.get("batch") or ""))
    else:
        rows = db.qall("SELECT * FROM timetable WHERE day=? ORDER BY start_time", (day,))
    labs = [dict(r) for r in rows]
    return JSONResponse({
        "date": t.isoformat(), "day": day, "batch": user.get("batch") or "",
        "labs": labs, "unread": unread_count(user),
        "whatsapp_message": whatsapp_text(rows, day, t.strftime("%d %b %Y")),
    })
