"""IQLab — IQ-style assessment + cognitive training. Route: /iq"""
import json
import os
import secrets
import threading
import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.iq import questions as Q
from app.iq import engine as E
from app.iq import db

router = APIRouter()
_lock = threading.RLock()
_PENDING = {}  # token -> {answer, qtype, domain, level, uid, mode, ts}

HTML_PATH = os.path.join(os.path.dirname(__file__), "app.html")

ASSESS_SEQ = [
    ("matrix", 3), ("number_series", 3), ("analogy", 3), ("synonym", 2),
    ("odd_one_out", 3), ("pattern", 3), ("spatial", 3), ("odd_word", 2),
    ("arithmetic", 3), ("digit_span", 3), ("nback", 2), ("stroop", 3),
    ("symbol_coding", 3), ("number_series", 4), ("matrix", 4),
]

def _uid(request: Request):
    uid = request.cookies.get("iq_uid")
    if not uid:
        uid = db.new_uuid()
    db.get_profile(uid)
    return uid

def _client_question(q):
    """Strip answers; keep grading data server-side."""
    out = {"qtype": q["qtype"], "qtype_ur": q["qtype_ur"], "domain": q["domain"],
           "prompt": q["prompt"], "visual": q.get("visual", ""),
           "options": q.get("options", []), "level": q["level"],
           "input": q.get("_input", None)}
    if q["qtype"] == "digit_span":
        out["digits"] = q["_digits"]
        out["backward"] = q["_backward"]
    elif q["qtype"] == "nback":
        out["letters"] = q["_letters"]
        out["n"] = q["_n"]
    elif q["qtype"] == "stroop":
        out["trials"] = [{"word": t["word"], "ink": t["ink"]} for t in q["_trials"]]
    elif q["qtype"] == "symbol_coding":
        out["key"] = q["_key"]
        out["items"] = q["_items"]
    return out

@router.get("/iq", response_class=HTMLResponse)
def iq_home(request: Request):
    uid = _uid(request)
    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()
    resp = HTMLResponse(content=html)
    resp.set_cookie("iq_uid", uid, max_age=365*24*3600)
    return resp

@router.post("/iq/api/question")
async def api_question(request: Request):
    uid = _uid(request)
    body = await request.json()
    mode = body.get("mode", "train")
    if mode == "assess":
        idx = int(body.get("idx", 0))
        if idx >= len(ASSESS_SEQ):
            return JSONResponse({"done": True})
        qtype, level = ASSESS_SEQ[idx]
    else:
        domain = body.get("domain", "fluid")
        qtypes = Q.DOMAIN_QTYPES.get(domain, ["number_series"])
        import random
        qtype = random.choice(qtypes)
        _, _, train_hist = db.domain_stats(uid)
        dh = [(l, 100) for (d, l) in train_hist if d == domain][:5]
        # approximate pct from stored attempts
        level = E.level_for(dh) if dh else 1
        # refine: use real recent pct
        with db._lock, db._conn() as c:
            rows = c.execute("SELECT level, pct FROM attempts WHERE uuid=? AND domain=? AND mode='train' ORDER BY ts DESC LIMIT 8", (uid, domain)).fetchall()
        hist = [(r["level"], r["pct"]) for r in rows]
        level = E.level_for(hist) if hist else 1
    q = Q.generate(qtype, level)
    token = secrets.token_hex(8)
    with _lock:
        _PENDING[token] = {"answer": q["answer"], "qtype": qtype,
                           "domain": q["domain"], "level": level,
                           "uid": uid, "mode": mode, "ts": time.time()}
        # prune old
        old = [t for t, v in _PENDING.items() if time.time() - v["ts"] > 3600]
        for t in old:
            del _PENDING[t]
    out = _client_question(q)
    out["token"] = token
    out["progress"] = {"idx": body.get("idx", 0), "total": len(ASSESS_SEQ)} if mode == "assess" else None
    resp = JSONResponse(out)
    resp.set_cookie("iq_uid", uid, max_age=365*24*3600)
    return resp

def _grade(qtype, expected, response):
    if qtype in ("digit_span", "symbol_coding"):
        exp = str(expected).strip().lower().replace(" ", "")
        got = str(response or "").strip().lower().replace(" ", "")
        return (1 if exp == got else 0), 1
    if qtype in ("nback", "stroop"):
        exp = list(expected)
        got = list(response or [])
        n = max(len(exp), len(got))
        correct = sum(1 for a, b in zip(exp, got) if bool(a) == bool(b))
        # penalize missing
        return correct, len(exp)
    # mcq
    try:
        return (1 if int(response) == int(expected) else 0), 1
    except (TypeError, ValueError):
        return 0, 1

@router.post("/iq/api/answer")
async def api_answer(request: Request):
    body = await request.json()
    token = body.get("token", "")
    with _lock:
        p = _PENDING.pop(token, None)
    if not p:
        return JSONResponse({"error": "expired"}, status_code=400)
    correct, total = _grade(p["qtype"], p["answer"], body.get("response"))
    pct = db.record_attempt(p["uid"], p["mode"], p["domain"], p["qtype"], p["level"], correct, total)
    # explain lookup: regenerate cheap explain? store at question time instead
    return JSONResponse({"correct": correct, "total": total, "pct": pct,
                         "is_correct": correct == total})

@router.get("/iq/api/dashboard")
def api_dashboard(request: Request):
    uid = _uid(request)
    prof = db.get_profile(uid)
    dstats, n_assess, train_hist = db.domain_stats(uid)
    domain_pct = {d: v["avg"] for d, v in dstats.items()}
    iq, band = E.estimate_iq(domain_pct)
    streak = db.streak_days(uid)
    max_level = max([v["max_level"] for v in dstats.values()] + [1])
    # nback/stroop best
    with db._lock, db._conn() as c:
        nb = c.execute("SELECT MAX(pct) m FROM attempts WHERE uuid=? AND qtype='nback'", (uid,)).fetchone()[0] or 0
        st = c.execute("SELECT MAX(pct) m FROM attempts WHERE uuid=? AND qtype='stroop'", (uid,)).fetchone()[0] or 0
    # latest assessment iq
    with db._lock, db._conn() as c:
        rows = c.execute("""SELECT AVG(pct) a FROM attempts WHERE uuid=? AND mode='assess'
                            AND ts > (SELECT COALESCE(MAX(ts),0) FROM attempts WHERE uuid=? AND mode='assess') - 3600*3""",
                         (uid, uid)).fetchone()
    latest_pct = rows[0] if rows and rows[0] else None
    latest_iq, _ = E.estimate_iq({"x": latest_pct}) if latest_pct else (None, None)
    target = prof.get("target_iq") or 120
    target_hit = bool(latest_iq and latest_iq >= target)
    stats = {"assessments": n_assess, "streak": streak, "max_level": max_level,
             "domains_tested": len(dstats), "target_hit": target_hit,
             "nback_best": nb, "stroop_best": st}
    # badges column is a JSON string in sqlite; parse to list first
    try:
        _b = prof.get("badges", "[]")
        prof["badges"] = json.loads(_b) if isinstance(_b, str) else list(_b)
    except Exception:
        prof["badges"] = []
    new_badges = E.check_badges(prof, stats)
    if new_badges:
        with db._lock, db._conn() as c:
            c.execute("UPDATE profiles SET badges=? WHERE uuid=?", (json.dumps(prof["badges"]), uid))
    hist = db.history(uid)
    resp = JSONResponse({
        "iq": iq, "band": band, "domains": dstats, "streak": streak,
        "badges": [E.badge_info(b) for b in prof.get("badges", [])],
        "new_badges": [E.badge_info(b) for b in new_badges],
        "target": target, "target_hit": target_hit, "latest_iq": latest_iq,
        "history": hist, "domain_names": E.DOMAIN_NAMES,
    })
    resp.set_cookie("iq_uid", uid, max_age=365*24*3600)
    return resp

@router.post("/iq/api/target")
async def api_target(request: Request):
    uid = _uid(request)
    body = await request.json()
    t = max(90, min(145, int(body.get("target_iq", 120))))
    db.set_target(uid, t)
    return JSONResponse({"target": t})
