"""MediScribe Pro routes — multi-user clinical safety app.

Research prototype: deterministic drug-safety engine, live FDA/RxNorm data,
Gemini chat proxy. NOT medical advice; flags must be verified with
Lexicomp/Medscape. NOT HIPAA-compliant — do not use with real patient data
outside a supervised test with consent.
"""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from . import db
from . import auth as authmod
from . import engine
from . import dose as dosemod

router = APIRouter()

_HTML = Path(__file__).with_name("app.html").read_text(encoding="utf-8")


@router.get("/mediscribe", response_class=HTMLResponse)
def mediscribe_page():
    return HTMLResponse(content=_HTML)


@router.get("/mediscribe/manifest.json")
def mediscribe_manifest():
    p = Path(__file__).with_name("manifest.json")
    return Response(content=p.read_bytes(), media_type="application/manifest+json")


@router.get("/mediscribe/sw.js")
def mediscribe_sw():
    p = Path(__file__).with_name("sw.js")
    return Response(content=p.read_bytes(), media_type="application/javascript")


@router.get("/mediscribe/icon-192.png")
def mediscribe_icon192():
    p = Path(__file__).with_name("icon-192.png")
    return Response(content=p.read_bytes(), media_type="image/png")


@router.get("/mediscribe/icon-512.png")
def mediscribe_icon512():
    p = Path(__file__).with_name("icon-512.png")
    return Response(content=p.read_bytes(), media_type="image/png")


# ---------------- helpers ----------------
def _token(request: Request):
    t = request.cookies.get("ms_token")
    if t:
        return t
    h = request.headers.get("authorization", "")
    if h.lower().startswith("bearer "):
        return h[7:]
    return ""


def _user(request: Request):
    return authmod.user_from_token(_token(request))


def _need(request: Request, roles=None):
    u = _user(request)
    if not u:
        return None, JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    if roles and u["role"] not in roles:
        return None, JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
    return u, None


def _audit(user, action, entity, entity_id, details=""):
    prev = "GENESIS"
    row = db.qone("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
    if row and row["hash"]:
        prev = row["hash"]
    body = {"ts": db.now(), "uid": user["id"], "user": user["name"], "action": action,
            "entity": entity, "entity_id": str(entity_id), "details": str(details)[:400],
            "prev_hash": prev}
    body["hash"] = hashlib.sha256(
        (prev + json.dumps(body, sort_keys=True)).encode()).hexdigest()
    db.q("INSERT INTO audit_log (ts, user_id, user_name, action, entity, entity_id, details, prev_hash, hash) VALUES (?,?,?,?,?,?,?,?,?)",
         (body["ts"], body["uid"], body["user"], action, entity, str(entity_id),
          body["details"], prev, body["hash"]))


def _patient_dict(row):
    d = dict(row)
    for k in ("conditions", "allergies", "meds"):
        try:
            d[k] = json.loads(d[k] or "[]")
        except (json.JSONDecodeError, TypeError):
            d[k] = []
    return d


# ---------------- auth ----------------
@router.post("/mediscribe/api/signup")
async def api_signup(req: Request):
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    try:
        role = "admin" if authmod.user_count() == 0 else "doctor"
        u = authmod.create_user(b.get("name", ""), b.get("email", ""),
                                b.get("password", ""), role)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    token = authmod.new_session(u["id"])
    _audit(u, "user_signup", "user", u["id"], u["email"])
    resp = JSONResponse({"ok": True, "user": _pub_user(u)})
    resp.set_cookie("ms_token", token, httponly=True, samesite="lax", max_age=8 * 3600)
    return resp


def _pub_user(u):
    return {"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"]}


@router.post("/mediscribe/api/login")
async def api_login(req: Request):
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    u = authmod.authenticate(b.get("email", ""), b.get("password", ""))
    if not u:
        return JSONResponse({"ok": False, "error": "bad_credentials"}, status_code=401)
    token = authmod.new_session(u["id"])
    _audit(u, "user_login", "user", u["id"], "")
    resp = JSONResponse({"ok": True, "user": _pub_user(u)})
    resp.set_cookie("ms_token", token, httponly=True, samesite="lax", max_age=8 * 3600)
    return resp


@router.post("/mediscribe/api/logout")
async def api_logout(req: Request):
    u = _user(req)
    authmod.destroy_session(_token(req))
    if u:
        _audit(u, "user_logout", "user", u["id"], "")
    resp = JSONResponse({"ok": True})
    resp.delete_cookie("ms_token")
    return resp


@router.get("/mediscribe/api/me")
async def api_me(req: Request):
    u = _user(req)
    if not u:
        return JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    return JSONResponse({"ok": True, "user": _pub_user(u),
                         "engine": engine.stats()})


# ---------------- patients ----------------
@router.get("/mediscribe/api/patients")
async def api_patients(req: Request):
    u, err = _need(req)
    if err:
        return err
    rows = db.qall("SELECT * FROM patients ORDER BY updated_at DESC")
    out = []
    for r in rows:
        d = _patient_dict(r)
        d["meds"] = [engine.drug_name(engine.resolve_drug_id(m) or "") or m
                     if isinstance(m, str) else m for m in d["meds"]]
        out.append(d)
    _audit(u, "patient_list", "patient", "-", f"{len(out)} patients")
    return JSONResponse({"ok": True, "patients": out})


@router.post("/mediscribe/api/patients")
async def api_patient_create(req: Request):
    u, err = _need(req, ("admin", "doctor"))
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    name = (b.get("name") or "").strip()[:120]
    if not name:
        return JSONResponse({"ok": False, "error": "name_required"}, status_code=400)
    # normalize meds to canonical drug ids where possible
    meds = []
    for m in b.get("meds") or []:
        mid = engine.resolve_drug_id(m) if isinstance(m, str) else None
        meds.append(mid or m)
    cur = db.q(
        "INSERT INTO patients (mrn, name, age, sex, conditions, allergies, meds, notes, created_by, updated_by, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ((b.get("mrn") or "").strip()[:40], name, int(b.get("age") or 0),
         (b.get("sex") or "").strip()[:10],
         json.dumps((b.get("conditions") or [])[:20]),
         json.dumps((b.get("allergies") or [])[:20]),
         json.dumps(meds[:40]), (b.get("notes") or "").strip()[:2000],
         u["id"], u["id"], db.now(), db.now()))
    pid = cur.lastrowid
    # instant safety check on save (server-side engine)
    p = _patient_dict(db.qone("SELECT * FROM patients WHERE id=?", (pid,)))
    ids = []
    for m in p["meds"]:
        if isinstance(m, str):
            mid = engine.resolve_drug_id(m)
            if mid:
                ids.append(mid)
    flags = engine.safety_check(sorted(set(ids)), engine.derived_conds(p),
                                p["allergies"], None)
    _audit(u, "patient_create", "patient", pid, name)
    return JSONResponse({"ok": True, "patient": p,
                         "safety": {"red": sum(1 for f in flags if f["sev"] == "red"),
                                    "amber": sum(1 for f in flags if f["sev"] == "amber"),
                                    "flags": flags}})


@router.get("/mediscribe/api/patients/{pid}")
async def api_patient_get(pid: int, req: Request):
    u, err = _need(req)
    if err:
        return err
    row = db.qone("SELECT * FROM patients WHERE id=?", (pid,))
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    _audit(u, "patient_view", "patient", pid, row["name"])
    return JSONResponse({"ok": True, "patient": _patient_dict(row)})


@router.put("/mediscribe/api/patients/{pid}")
async def api_patient_update(pid: int, req: Request):
    u, err = _need(req, ("admin", "doctor"))
    if err:
        return err
    row = db.qone("SELECT * FROM patients WHERE id=?", (pid,))
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    meds = []
    for m in b.get("meds") or []:
        mid = engine.resolve_drug_id(m) if isinstance(m, str) else None
        meds.append(mid or m)
    db.q("UPDATE patients SET mrn=?, name=?, age=?, sex=?, conditions=?, allergies=?, meds=?, notes=?, updated_by=?, updated_at=? WHERE id=?",
         ((b.get("mrn") or "").strip()[:40], (b.get("name") or row["name"]).strip()[:120],
          int(b.get("age") or 0), (b.get("sex") or "").strip()[:10],
          json.dumps((b.get("conditions") or [])[:20]),
          json.dumps((b.get("allergies") or [])[:20]), json.dumps(meds[:40]),
          (b.get("notes") or "").strip()[:2000], u["id"], db.now(), pid))
    _audit(u, "patient_update", "patient", pid, b.get("name") or row["name"])
    return JSONResponse({"ok": True, "patient": _patient_dict(
        db.qone("SELECT * FROM patients WHERE id=?", (pid,)))})


@router.delete("/mediscribe/api/patients/{pid}")
async def api_patient_delete(pid: int, req: Request):
    u, err = _need(req, ("admin", "doctor"))
    if err:
        return err
    row = db.qone("SELECT * FROM patients WHERE id=?", (pid,))
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    db.q("DELETE FROM patients WHERE id=?", (pid,))
    _audit(u, "patient_delete", "patient", pid, row["name"])
    return JSONResponse({"ok": True})

# ---------------- analyze + consultations ----------------
@router.get("/mediscribe/api/drugs")
async def api_drugs(req: Request):
    u, err = _need(req)
    if err:
        return err
    return JSONResponse({"ok": True,
                         "drugs": [{"id": d["id"], "names": d["n"], "class": d["c"]}
                                   for d in engine.DRUGS],
                         "conditions": [{"id": c[0], "label": c[1]}
                                        for c in engine.CONDITIONS]})
@router.post("/mediscribe/api/analyze")
async def api_analyze(req: Request):
    u, err = _need(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    pid = b.get("patient_id")
    row = db.qone("SELECT * FROM patients WHERE id=?", (pid,))
    if not row:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    p = _patient_dict(row)
    transcript = (b.get("transcript") or "")[:20000]
    if len(transcript.strip()) < 5:
        return JSONResponse({"ok": False, "error": "transcript_short"}, status_code=400)
    result = engine.analyze(p, transcript)
    _audit(u, "consult_analyze", "patient", pid, f"{len(result['flags'])} flags")
    return JSONResponse({"ok": True, **result})


@router.post("/mediscribe/api/consultations")
async def api_consult_save(req: Request):
    u, err = _need(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    pid = b.get("patient_id")
    if not db.qone("SELECT id FROM patients WHERE id=?", (pid,)):
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    flags = b.get("flags") or []
    confirmed = [f.get("key") for f in flags if f.get("confirmed")]
    cur = db.q("INSERT INTO consultations (patient_id, transcript, flags_json, confirmed_json, created_by, created_at) VALUES (?,?,?,?,?,?)",
               (pid, (b.get("transcript") or "")[:20000], json.dumps(flags)[:50000],
                json.dumps(confirmed), u["id"], db.now()))
    _audit(u, "consult_save", "consultation", cur.lastrowid, f"patient {pid}")
    return JSONResponse({"ok": True, "id": cur.lastrowid})


@router.get("/mediscribe/api/consultations")
async def api_consult_list(req: Request, patient_id: int = 0):
    u, err = _need(req)
    if err:
        return err
    if patient_id:
        rows = db.qall("SELECT c.*, u.name AS by_name FROM consultations c LEFT JOIN users u ON u.id=c.created_by WHERE c.patient_id=? ORDER BY c.id DESC", (patient_id,))
    else:
        rows = db.qall("SELECT c.*, u.name AS by_name, p.name AS patient_name FROM consultations c LEFT JOIN users u ON u.id=c.created_by LEFT JOIN patients p ON p.id=c.patient_id ORDER BY c.id DESC LIMIT 100")
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["flags"] = json.loads(d.pop("flags_json") or "[]")
        except (json.JSONDecodeError, TypeError):
            d["flags"] = []
        d.pop("confirmed_json", None)
        d.pop("transcript", None)
        out.append(d)
    return JSONResponse({"ok": True, "consultations": out})


# ---------------- validation feedback (hospital test mode) ----------------
@router.post("/mediscribe/api/feedback")
async def api_feedback(req: Request):
    u, err = _need(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    verdict = b.get("verdict")
    if verdict not in ("correct", "incorrect", "unsure"):
        return JSONResponse({"ok": False, "error": "bad_verdict"}, status_code=400)
    db.q("INSERT INTO flag_feedback (consultation_id, flag_key, verdict, note, user_id, created_at) VALUES (?,?,?,?,?,?)",
         (int(b.get("consultation_id") or 0), (b.get("flag_key") or "")[:300], verdict,
          (b.get("note") or "")[:1000], u["id"], db.now()))
    _audit(u, "flag_feedback", "consultation", b.get("consultation_id") or 0,
           f"{verdict}: {(b.get('flag_key') or '')[:80]}")
    return JSONResponse({"ok": True})


@router.get("/mediscribe/api/feedback/stats")
async def api_feedback_stats(req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    rows = db.qall("SELECT verdict, COUNT(*) c FROM flag_feedback GROUP BY verdict")
    return JSONResponse({"ok": True, "stats": {r["verdict"]: r["c"] for r in rows}})


# ---------------- admin ----------------
@router.get("/mediscribe/api/admin/users")
async def api_admin_users(req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    return JSONResponse({"ok": True, "users": authmod.list_users()})


@router.post("/mediscribe/api/admin/users")
async def api_admin_user_create(req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    try:
        nu = authmod.create_user(b.get("name", ""), b.get("email", ""),
                                 b.get("password", ""), b.get("role", "doctor"))
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    _audit(u, "user_create", "user", nu["id"], f"{nu['email']} ({nu['role']})")
    return JSONResponse({"ok": True, "user": _pub_user(nu)})


@router.post("/mediscribe/api/admin/users/{uid}/active")
async def api_admin_user_active(uid: int, req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        b = {}
    if uid == u["id"]:
        return JSONResponse({"ok": False, "error": "cannot_deactivate_self"}, status_code=400)
    authmod.set_user_active(uid, bool(b.get("active", True)))
    _audit(u, "user_active", "user", uid, str(bool(b.get("active", True))))
    return JSONResponse({"ok": True})


@router.post("/mediscribe/api/admin/users/{uid}/password")
async def api_admin_user_password(uid: int, req: Request):
    """Admin-only: reset another user's password (min 8 chars)."""
    u, err = _need(req, ("admin",))
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    newpw = (b.get("password") or "")
    if len(newpw) < 8:
        return JSONResponse({"ok": False, "error": "password_short"}, status_code=400)
    target = authmod.get_user(uid)
    if not target:
        return JSONResponse({"ok": False, "error": "not_found"}, status_code=404)
    authmod.db.q("UPDATE users SET password_hash=? WHERE id=?",
                 (authmod.hash_password(newpw), uid))
    _audit(u, "user_password_reset", "user", uid, target["email"])
    return JSONResponse({"ok": True})


@router.get("/mediscribe/api/admin/audit")
async def api_admin_audit(req: Request, limit: int = 100):
    u, err = _need(req, ("admin",))
    if err:
        return err
    limit = max(1, min(limit, 500))
    rows = db.qall("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    # verify hash chain over returned window
    ok_chain = True
    prev = None
    for r in reversed(list(rows)):
        if prev is not None and r["prev_hash"] != prev:
            ok_chain = False
            break
        h = hashlib.sha256((r["prev_hash"] + json.dumps(
            {"ts": r["ts"], "uid": r["user_id"], "user": r["user_name"], "action": r["action"],
             "entity": r["entity"], "entity_id": r["entity_id"], "details": r["details"],
             "prev_hash": r["prev_hash"]}, sort_keys=True)).encode()).hexdigest()
        if h != r["hash"]:
            ok_chain = False
            break
        prev = r["hash"]
    return JSONResponse({"ok": True, "chain_ok": ok_chain,
                         "entries": [dict(r) for r in rows]})


# ---------------- backup / restore (deploys wipe container storage) ----------------
@router.get("/mediscribe/api/admin/backup")
async def api_admin_backup(req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    dump = {}
    for t in ("users", "patients", "consultations", "audit_log", "flag_feedback"):
        dump[t] = [dict(r) for r in db.qall(f"SELECT * FROM {t}")]
    _audit(u, "backup_export", "system", "-", f"{sum(len(v) for v in dump.values())} rows")
    return JSONResponse({"ok": True, "backup": dump})


@router.post("/mediscribe/api/admin/restore")
async def api_admin_restore(req: Request):
    u, err = _need(req, ("admin",))
    if err:
        return err
    try:
        b = await req.json()
        dump = b.get("backup") or {}
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    with db._lock:
        conn = db.get_conn()
        for t in ("flag_feedback", "audit_log", "consultations", "patients", "sessions", "users"):
            if t in dump and isinstance(dump[t], list):
                conn.execute(f"DELETE FROM {t}")
                for row in dump[t]:
                    cols = [k for k in row.keys()]
                    conn.execute(f"INSERT INTO {t} ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
                                 tuple(row[c] for c in cols))
        conn.commit()
    _audit(u, "backup_restore", "system", "-", "restore completed")
    return JSONResponse({"ok": True})


# ---------------- Dose module (renal/hepatic dose adjustment) ----------------
@router.get("/mediscribe/api/dose/drugs")
async def api_dose_drugs(req: Request):
    u, err = _need(req)
    if err:
        return err
    try:
        drugs = dosemod.dose_drugs()
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"rules_load_failed: {e}"[:200]})
    return JSONResponse({"ok": True, "count": len(drugs), "drugs": [
        {"id": d["id"], "display": d["display"], "class": d.get("class"),
         "nti": bool(d.get("nti")), "indications": d.get("indications") or [],
         "gfr_method": d.get("gfr_method") or "crcl"}
        for d in drugs]})


@router.post("/mediscribe/api/dose/calc")
async def api_dose_calc(req: Request):
    u, err = _need(req)
    if err:
        return err
    try:
        b = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    drug_id = (b.get("drug_id") or "").strip()
    if not drug_id:
        # try resolving a typed name to a structured drug
        rid = dosemod.resolve_dose_drug(b.get("drug_name") or "")
        if rid and not rid.startswith("label:"):
            drug_id = rid
        elif rid:
            return JSONResponse({"ok": True, "fallback": True, "engine_id": rid[6:]})
        else:
            return JSONResponse({"ok": False, "error": "drug_not_found"}, status_code=404)
    params = dict(b)
    params["drug_id"] = drug_id
    try:
        out = dosemod.calculate(params)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": str(e)[:200]}, status_code=400)
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"calc_failed: {e}"[:200]}, status_code=500)
    _audit(u, "dose_calc", "dose", drug_id,
           f"gfr={out['gfr']} dose={('; '.join(out['dose']))[:200]}")
    return JSONResponse(out)


@router.get("/mediscribe/api/dose/label")
async def api_dose_label(req: Request, name: str = Query(..., min_length=2, max_length=60)):
    """Fallback coverage: live FDA label Dosage and Administration text for ANY drug."""
    u, err = _need(req)
    if err:
        return err
    key = name.strip().lower()
    fda_name = FDA_NAME.get(key, key)
    if not fda_name:
        return JSONResponse({"ok": False, "error": "No single FDA label for this entry."})

    def fn():
        params = urllib.parse.urlencode(
            {"search": f'openfda.generic_name:"{fda_name}"', "limit": 1}
        )
        d = _get(f"https://api.fda.gov/drug/label.json?{params}")
        results = d.get("results") or []
        if not results:
            return {"ok": False, "error": "No FDA label found."}
        r = results[0]
        openfda = r.get("openfda") or {}
        da = r.get("dosage_and_administration")
        txt = (" ".join(da) if isinstance(da, list) else str(da or "")).strip()
        return {
            "ok": True,
            "query": name,
            "generic_name": (openfda.get("generic_name") or [name])[0],
            "brand_name": (openfda.get("brand_name") or [])[:4],
            "dosage_text": txt[:6000] if txt else None,
            "banner": ("Structured adjustment rules not yet curated for this drug — "
                       "official FDA label dosage text below. Verify with a pharmacist / Lexicomp."),
            "source": "openFDA drug label API (live, official FDA label)",
        }

    return JSONResponse(_cached("doselabel:" + key, fn))


@router.post("/mediscribe/api/dose/admin/import")
async def api_dose_import(req: Request):
    """Admin-only batch import of structured rules (no code changes needed).

    Body: {"drugs": [ ...rule objects... ], "mode": "merge"|"replace"}.
    Validates every rule (schema + mandatory references) before touching the file.
    """
    u, err = _need(req, ("admin",))
    if err:
        return err
    try:
        b = await req.json()
        incoming = b.get("drugs")
        mode = b.get("mode") or "merge"
    except Exception:
        return JSONResponse({"ok": False, "error": "bad_json"}, status_code=400)
    try:
        dosemod.validate_drug_list(incoming)
    except ValueError as e:
        return JSONResponse({"ok": False, "error": f"validation_failed: {e}"[:300]},
                            status_code=400)
    path = dosemod.rules_path()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if mode == "replace":
        data["drugs"] = incoming
    else:
        by_id = {d["id"]: d for d in data["drugs"]}
        for d in incoming:
            by_id[d["id"]] = d
        data["drugs"] = list(by_id.values())
    try:
        dosemod.validate_drug_list(data["drugs"])
    except ValueError as e:
        return JSONResponse({"ok": False, "error": f"merged_validation_failed: {e}"[:300]},
                            status_code=400)
    import datetime as _dt
    data["version"] = f"import-{_dt.datetime.now().strftime('%Y-%m-%d')}-via-admin"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    dosemod.clear_rules_cache()
    _audit(u, "dose_import", "dose", "-",
           f"{mode} {len(incoming)} rules; total {len(data['drugs'])}")
    return JSONResponse({"ok": True, "imported": len(incoming),
                         "total": len(data["drugs"])})


# ---------------- live drug data (kept from v1) ----------------
_CACHE = {}
_CACHE_TTL = 6 * 3600

FDA_NAME = {
    "hctz": "hydrochlorothiazide",
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "glibenclamide": "glyburide",
    "amoxclav": "amoxicillin and clavulanate potassium",
    "cotrimoxazole": "sulfamethoxazole and trimethoprim",
    "phenelzine": "phenelzine",
    "ocp": None,
}


def _get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "MediScribe-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _cached(key, fn):
    now = time.time()
    if key in _CACHE and now - _CACHE[key][0] < _CACHE_TTL:
        return _CACHE[key][1]
    try:
        payload = fn()
    except Exception as e:
        payload = {"ok": False, "error": str(e)[:200]}
    _CACHE[key] = (now, payload)
    return payload


@router.get("/mediscribe/api/rxcui")
def api_rxcui(name: str = Query(..., min_length=2, max_length=60)):
    q = urllib.parse.quote(name.strip())

    def fn():
        d = _get(f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={q}&search=1")
        ids = (d.get("idGroup") or {}).get("rxnormId") or []
        return {"ok": True, "name": name, "rxcui": ids[0] if ids else None,
                "source": "NLM RxNorm (live)"}

    return JSONResponse(_cached("rxcui:" + name.lower(), fn))


@router.get("/mediscribe/api/label")
def api_label(name: str = Query(..., min_length=2, max_length=60)):
    key = name.strip().lower()
    fda_name = FDA_NAME.get(key, key)
    if not fda_name:
        return JSONResponse({"ok": False, "error": "No single FDA label for this entry."})

    def fn():
        params = urllib.parse.urlencode(
            {"search": f'openfda.generic_name:"{fda_name}"', "limit": 1}
        )
        d = _get(f"https://api.fda.gov/drug/label.json?{params}")
        results = d.get("results") or []
        if not results:
            return {"ok": False, "error": "No FDA label found."}
        r = results[0]
        openfda = r.get("openfda") or {}

        def section(*names):
            for n in names:
                v = r.get(n)
                if v:
                    txt = " ".join(v) if isinstance(v, list) else str(v)
                    return txt[:1500]
            return None

        return {
            "ok": True,
            "query": name,
            "generic_name": (openfda.get("generic_name") or [name])[0],
            "brand_name": (openfda.get("brand_name") or [])[:4],
            "boxed_warning": section("boxed_warning"),
            "contraindications": section("contraindications"),
            "drug_interactions": section("drug_interactions"),
            "warnings": section("warnings", "warnings_and_cautions"),
            "source": "openFDA drug label API (live, official FDA label)",
        }

    return JSONResponse(_cached("label:" + key, fn))


@router.post("/mediscribe/api/chat")
async def api_chat(req: Request):
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Invalid JSON body."}, status_code=400)
    api_key = (body.get("api_key") or "").strip()
    model = (body.get("model") or "gemini-flash-latest").strip()[:80]
    system = (body.get("system") or "")[:4000]
    messages = body.get("messages") or []
    if not api_key:
        return JSONResponse({"ok": False, "error": "API key missing."}, status_code=400)
    if not messages or len(messages) > 30:
        return JSONResponse({"ok": False, "error": "Bad messages."}, status_code=400)

    contents = []
    for m in messages[-20:]:
        role = "model" if m.get("role") == "model" else "user"
        text = str(m.get("text") or "")[:6000]
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    payload = {"contents": contents,
               "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200}}
    if system:
        payload["system_instruction"] = {"parts": [{"text": system}]}

    data = json.dumps(payload).encode("utf-8")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{urllib.parse.quote(model, safe='')}:generateContent?key="
           f"{urllib.parse.quote(api_key, safe='')}")
    try:
        rq = urllib.request.Request(url, data=data,
                                    headers={"Content-Type": "application/json",
                                             "User-Agent": "MediScribe-research/1.0"})
        with urllib.request.urlopen(rq, timeout=60) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            msg = err.get("error", {}).get("message", str(e))[:300]
        except Exception:
            msg = str(e)[:300]
        return JSONResponse({"ok": False, "error": f"Gemini API: {msg}"})
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Request failed: {str(e)[:200]}"})

    try:
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return JSONResponse({"ok": False,
                             "error": "No text in Gemini response (blocked or empty)."})
    return JSONResponse({"ok": True, "text": text, "model": model})
