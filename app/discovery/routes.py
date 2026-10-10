"""LeadForge AI — SaaS routes: auth, plan-gated runs, history, shares, admin."""
import json
import secrets
import time

from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import auth as A
from . import db
from . import pipeline as P
from . import sources as S
from . import tox as T

router = APIRouter()
COOKIE = "lf_token"
WHATSAPP = "https://wa.me/923116925020?text=" + (
    "Hi! I want LeadForge Pro for our lab. Please activate my account.")


def _html(name):
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), name)
    with open(p, encoding="utf-8") as f:
        return f.read()


def _user(req: Request):
    return A.user_from_token(req.cookies.get(COOKIE))


def _need_login(req: Request):
    u = _user(req)
    if not u:
        return None, JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    return u, None


def _set_session(resp: JSONResponse, user):
    token = A.new_session(user["id"])
    resp.set_cookie(COOKIE, token, httponly=True, samesite="lax", max_age=8 * 3600, path="/")
    return resp


# ---------- pages ----------
@router.get("/discovery", response_class=HTMLResponse)
def page(req: Request):
    u = _user(req)
    if not u:
        return _html("landing.html")
    return _html("discovery.html")


@router.get("/discovery/admin", response_class=HTMLResponse)
def admin_page(req: Request):
    u = _user(req)
    if not u or u["role"] != "admin":
        return RedirectResponse("/discovery", status_code=303)
    return _html("admin.html")


@router.get("/discovery/r/{token}", response_class=HTMLResponse)
def shared_report(token: str):
    row = db.qone("SELECT * FROM shares WHERE token=? AND revoked=0", (token,))
    if not row:
        return HTMLResponse("<h2>Report not found or revoked.</h2>", status_code=404)
    run = db.qone("SELECT * FROM runs WHERE id=?", (row["run_id"],))
    if not run:
        return HTMLResponse("<h2>Report not found.</h2>", status_code=404)
    result = json.loads(run["result_json"])
    result["shared"] = True
    return HTMLResponse(_render_report(result, shared=True))


def _render_report(result, shared=False):
    leads = result.get("leads", [])
    u = (result.get("target") or {}).get("uniprot") or {}
    rows = []
    for l in leads:
        d = l.get("descriptors") or {}
        tox = l.get("tox") or {}
        assays = tox.get("assays") or {}
        flags = [k for k, v in assays.items() if v is not None and v >= 0.5]
        rows.append(
            f"<tr><td><b>#{l['rank']}</b></td><td>{l['label']}</td>"
            f"<td><b>{l['score']}</b></td><td>{l['similarity']}</td>"
            f"<td>{(l.get('known_activity') or {}).get('pchembl') or '—'}</td>"
            f"<td>{'✓' if d.get('lipinski_pass') else '✗'} / {'✓' if d.get('veber_pass') else '✗'}</td>"
            f"<td>{len(l.get('pains') or [])} alerts</td>"
            f"<td>{', '.join(flags[:4]) if flags else 'low'}</td></tr>")
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>LeadForge report</title><style>
body{{font-family:system-ui;background:#0b1220;color:#e8eefc;margin:0}}
.wrap{{max-width:1000px;margin:0 auto;padding:20px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:8px;border-bottom:1px solid #22314f;text-align:left}}
th{{color:#93a4c4}}.note{{font-size:12px;color:#93a4c4;margin-top:16px}}
</style></head><body><div class="wrap">
<h1>🧬 LeadForge report</h1>
<p>Target: <b>{u.get('accession','')}</b> {u.get('gene','')} — {u.get('protein','')}<br>
<small>Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(result.get('created_at', time.time())))}
· {result.get('ligands_found',0)} known ligands screened · {result.get('elapsed_s','?')}s</small></p>
<table><tr><th>#</th><th>Lead</th><th>Score</th><th>Sim</th><th>pChEMBL</th>
<th>Lip/Veber</th><th>PAINS</th><th>Tox flags</th></tr>{''.join(rows)}</table>
<p class="note">Computational triage only — scores are heuristics, not efficacy or safety proof.
Wet-lab validation required. Research use only, never medical advice.</p>
</div></body></html>"""


# ---------- auth ----------
@router.post("/discovery/api/signup")
async def api_signup(req: Request):
    body = await req.json()
    try:
        u = A.create_user(body.get("name", ""), body.get("email", ""),
                          body.get("password", ""))
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    resp = JSONResponse({"ok": True, "role": u["role"], "plan": u["plan"]})
    return _set_session(resp, u)


@router.post("/discovery/api/login")
async def api_login(req: Request):
    body = await req.json()
    u = A.authenticate(body.get("email", ""), body.get("password", ""))
    if not u:
        return JSONResponse({"ok": False, "error": "bad_credentials"}, status_code=401)
    db.audit(u["id"], "login")
    resp = JSONResponse({"ok": True, "role": u["role"], "plan": u["plan"], "name": u["name"]})
    return _set_session(resp, u)


@router.post("/discovery/api/logout")
def api_logout(req: Request):
    A.logout(req.cookies.get(COOKIE))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(COOKIE, path="/")
    return resp


@router.get("/discovery/api/me")
def api_me(req: Request):
    u = _user(req)
    if not u:
        return JSONResponse({"ok": False}, status_code=401)
    plan = db.PLANS.get(u["plan"], db.PLANS["free"])
    return JSONResponse({"ok": True, "name": u["name"], "email": u["email"],
                         "role": u["role"], "plan": u["plan"],
                         "runs_used": u["runs_this_month"],
                         "runs_limit": plan["runs_per_month"] if plan["runs_per_month"] < 10**9 else None,
                         "can_share": plan["share"],
                         "whatsapp": WHATSAPP})


# ---------- pipeline (background jobs) ----------
def _execute_job(job_id: int):
    """Runs the pipeline for a job; updates job + runs tables."""
    job = db.qone("SELECT * FROM jobs WHERE id=?", (job_id,))
    if not job:
        return
    db.q("UPDATE jobs SET status='running', updated_at=? WHERE id=?", (db.now(), job_id))
    body = json.loads(job["query_input"])
    target = body.get("target", "")
    try:
        result = P.run_pipeline(target, query_smiles=body.get("smiles"),
                                query_name=body.get("compound"),
                                top_n=body.get("top_n", 25),
                                dock_top_n=5 if body.get("dock") else 0)
    except Exception as e:
        result = {"ok": False, "error": str(e)[:300]}
    result["elapsed_s"] = round(db.now() - job["created_at"], 1)
    result["created_at"] = db.now()
    if result.get("ok"):
        leads = result.get("leads", [])
        top = leads[0] if leads else {}
        cur = db.q(
            "INSERT INTO runs (user_id, target, query_input, lead_count, top_score,"
            " top_label, result_json, elapsed_s, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (job["user_id"], target[:120], body.get("label", "")[:200],
             len(leads), top.get("score"), str(top.get("label"))[:80],
             json.dumps(result), result["elapsed_s"], db.now()))
        result["run_id"] = cur.lastrowid
        db.audit(job["user_id"], "run", f"target={target[:60]} leads={len(leads)}")
    db.q("UPDATE jobs SET status=?, result_json=?, updated_at=? WHERE id=?",
         ("done" if result.get("ok") else "failed", json.dumps(result), db.now(), job_id))


@router.post("/discovery/api/run")
async def api_run(req: Request, background: BackgroundTasks):
    u, err = _need_login(req)
    if err:
        return err
    ok, reason = A.can_run(u)
    if not ok:
        return JSONResponse({"ok": False, "error": reason,
                             "whatsapp": WHATSAPP}, status_code=402)
    body = await req.json()
    target = (body.get("target") or "").strip()
    q_smiles = (body.get("smiles") or "").strip() or None
    q_name = (body.get("compound") or "").strip() or None
    top_n = max(5, min(50, int(body.get("top_n") or 25)))
    # Docking is VM-side only (free container OOMs on Vina + protein prep).
    # SaaS runs steps 1-6; docking reports are produced on request + emailed.
    dock = False
    if not target:
        return JSONResponse({"ok": False, "error": "target_required"}, status_code=400)
    if q_smiles and len(q_smiles) > 2000:
        return JSONResponse({"ok": False, "error": "smiles_too_long"}, status_code=400)
    A.record_run(u)  # consume quota at submission
    label = q_smiles or q_name or ""
    cur = db.q(
        "INSERT INTO jobs (user_id, target, query_input, top_n, dock, status, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (u["id"], target[:120],
         json.dumps({"target": target, "smiles": q_smiles, "compound": q_name,
                     "top_n": top_n, "dock": dock, "label": label}),
         top_n, 1 if dock else 0, "queued", db.now(), db.now()))
    job_id = cur.lastrowid
    db.audit(u["id"], "run_start", f"target={target[:60]} job={job_id}")
    background.add_task(_execute_job, job_id)
    return JSONResponse({"ok": True, "job_id": job_id, "status": "queued"})


@router.get("/discovery/api/job/{job_id}")
def api_job(job_id: int, req: Request):
    u, err = _need_login(req)
    if err:
        return err
    job = db.qone("SELECT * FROM jobs WHERE id=?", (job_id,))
    if not job or (job["user_id"] != u["id"] and u["role"] != "admin"):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    out = {"ok": True, "job_id": job["id"], "status": job["status"],
           "target": job["target"]}
    if job["status"] in ("done", "failed") and job["result_json"]:
        out["result"] = json.loads(job["result_json"])
    return JSONResponse(out)


@router.get("/discovery/api/history")
def api_history(req: Request):
    u, err = _need_login(req)
    if err:
        return err
    rows = db.qall("SELECT id, target, query_input, lead_count, top_score, top_label,"
                   " elapsed_s, created_at FROM runs WHERE user_id=? ORDER BY id DESC LIMIT 100",
                   (u["id"],))
    return JSONResponse({"ok": True, "runs": [dict(r) for r in rows]})


@router.get("/discovery/api/run/{run_id}")
def api_get_run(run_id: int, req: Request):
    u, err = _need_login(req)
    if err:
        return err
    run = db.qone("SELECT * FROM runs WHERE id=?", (run_id,))
    if not run or (run["user_id"] != u["id"] and u["role"] != "admin"):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    return JSONResponse({"ok": True, "run": json.loads(run["result_json"])})


@router.post("/discovery/api/share/{run_id}")
def api_share(run_id: int, req: Request):
    u, err = _need_login(req)
    if err:
        return err
    if not db.PLANS.get(u["plan"], db.PLANS["free"])["share"]:
        return JSONResponse({"ok": False, "error": "plan_required",
                             "whatsapp": WHATSAPP}, status_code=402)
    run = db.qone("SELECT * FROM runs WHERE id=? AND user_id=?", (run_id, u["id"]))
    if not run:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    token = secrets.token_urlsafe(16)
    db.q("INSERT INTO shares (token, run_id, created_at) VALUES (?,?,?)",
         (token, run_id, time.time()))
    db.audit(u["id"], "share", f"run={run_id}")
    return JSONResponse({"ok": True, "url": f"/discovery/r/{token}"})


# ---------- lookups (login required to protect shared compute) ----------
@router.get("/discovery/api/lookup")
def api_lookup(req: Request, target: str = "", compound: str = ""):
    u, err = _need_login(req)
    if err:
        return err
    out = {}
    if target.strip():
        uni = S.uniprot_target(target.strip())
        out["target"] = uni["data"] if uni["ok"] else {"error": uni.get("error")}
    if compound.strip():
        pc = S.pubchem_by_name(compound.strip())
        out["compound"] = pc["data"] if pc["ok"] else {"error": pc.get("error")}
    return JSONResponse(out)


@router.get("/discovery/api/tox-assays")
def api_tox_assays(req: Request):
    u, err = _need_login(req)
    if err:
        return err
    return JSONResponse({"assays": T.assay_names()})


# ---------- admin ----------
def _need_admin(req: Request):
    u = _user(req)
    if not u or u["role"] != "admin":
        return None, JSONResponse({"ok": False, "error": "admin_required"}, status_code=403)
    return u, None


@router.get("/discovery/api/admin/users")
def admin_users(req: Request):
    _, err = _need_admin(req)
    if err:
        return err
    rows = db.qall("SELECT id, name, email, role, plan, runs_this_month, is_active,"
                   " created_at FROM users ORDER BY id")
    return JSONResponse({"ok": True, "users": [dict(r) for r in rows],
                         "plans": list(db.PLANS.keys()), "whatsapp": WHATSAPP})


@router.post("/discovery/api/admin/plan")
async def admin_plan(req: Request):
    admin, err = _need_admin(req)
    if err:
        return err
    body = await req.json()
    try:
        A.set_plan(admin["id"], int(body.get("user_id")), body.get("plan", ""))
    except (ValueError, TypeError) as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    return JSONResponse({"ok": True})


@router.post("/discovery/api/admin/active")
async def admin_active(req: Request):
    admin, err = _need_admin(req)
    if err:
        return err
    body = await req.json()
    A.set_active(admin["id"], int(body.get("user_id")), bool(body.get("active")))
    return JSONResponse({"ok": True})


@router.post("/discovery/api/admin/make-admin")
async def admin_make_admin(req: Request):
    admin, err = _need_admin(req)
    if err:
        return err
    body = await req.json()
    uid = int(body.get("user_id"))
    db.q("UPDATE users SET role='admin', plan='enterprise' WHERE id=?", (uid,))
    db.audit(admin["id"], "make_admin", f"user={uid}")
    return JSONResponse({"ok": True})


@router.post("/discovery/api/admin/delete-user")
async def admin_delete_user(req: Request):
    admin, err = _need_admin(req)
    if err:
        return err
    body = await req.json()
    uid = int(body.get("user_id"))
    if uid == admin["id"]:
        return JSONResponse({"ok": False, "error": "cannot_delete_self"}, status_code=400)
    # cascade: sessions, runs (+ their shares), then user
    run_ids = [r["id"] for r in db.qall("SELECT id FROM runs WHERE user_id=?", (uid,))]
    for rid in run_ids:
        db.q("DELETE FROM shares WHERE run_id=?", (rid,))
    db.q("DELETE FROM runs WHERE user_id=?", (uid,))
    db.q("DELETE FROM sessions WHERE user_id=?", (uid,))
    db.q("DELETE FROM users WHERE id=?", (uid,))
    db.audit(admin["id"], "delete_user", f"user={uid}")
    return JSONResponse({"ok": True})


@router.get("/discovery/api/admin/runs")
def admin_runs(req: Request):
    _, err = _need_admin(req)
    if err:
        return err
    rows = db.qall("SELECT r.id, r.target, r.query_input, r.lead_count, r.top_score,"
                   " r.created_at, u.email FROM runs r JOIN users u ON u.id=r.user_id"
                   " ORDER BY r.id DESC LIMIT 200")
    return JSONResponse({"ok": True, "runs": [dict(r) for r in rows]})


@router.get("/discovery/api/admin/audit")
def admin_audit(req: Request):
    _, err = _need_admin(req)
    if err:
        return err
    rows = db.qall("SELECT a.id, a.action, a.detail, a.created_at, u.email FROM audit a"
                   " LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 200")
    return JSONResponse({"ok": True, "audit": [dict(r) for r in rows]})
