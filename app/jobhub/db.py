"""Auto-Apply Hub — profile vault + matches store (PK / SA / UAE only).

Container-side SQLite cache. The VM-side package (~/workspace/auto-apply-hub/)
holds the source-of-truth JSON; it pushes matches/profile here via the
worker API and pulls profile edits back. A deploy wipes this DB — the VM
re-syncs after every deploy, so nothing is lost.
"""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobhub.db")

DEFAULT_PROFILE = {
    "name": "Zubair Ali",
    "cv_name": "Zubair Ahmed",
    "email": "za0153715@gmail.com",
    "phone": "+92 311 6925020",
    "city": "Larkana",
    "country": "Pakistan",
    "dob": "2002-03-02",
    "degree": "Doctor of Pharmacy (Pharm-D)",
    "institution": "Shaheed Mohtarma Benazir Bhutto Medical University (SMBBMU), Larkana",
    "session": "2024-2025",
    "start_year": 2024,
    "education_status": "currently pursuing",
    "skills": "LangGraph, CrewAI, n8n, Zapier, Make, Python, FastAPI, RAG, RDKit, AutoDock Vina, AlphaFold 3, UniProt, ChEMBL, in silico ADMET, CTD/eCTD, GMP, GDP, GLP, DRAP, FDA, EMA, WHO, ICH",
    "github": "https://github.com/zubair0153715",
    "linkedin": "https://www.linkedin.com/in/zubair-ahmed-ba68a143b/",
    "pharmareg": "https://pharmareg-ai.fastapicloud.dev",
    "leadforge": "https://clinic-demo.fastapicloud.dev/discovery",
    "relocation": "Islamabad, UAE, Saudi Arabia (needs visa sponsorship for UAE/Saudi)",
    "daily_cap": 4,
}

PROFILE_FIELDS = list(DEFAULT_PROFILE.keys())


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS profile
                     (id INTEGER PRIMARY KEY CHECK (id = 1),
                      data TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS matches
                     (id TEXT PRIMARY KEY, data TEXT NOT NULL,
                      status TEXT NOT NULL DEFAULT 'new',
                      fit_score INTEGER NOT NULL DEFAULT 0,
                      updated_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS queue
                     (id TEXT PRIMARY KEY, match_id TEXT NOT NULL,
                      reason TEXT NOT NULL DEFAULT '',
                      action_needed TEXT NOT NULL DEFAULT '',
                      created_at TEXT NOT NULL DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS applications
                     (id TEXT PRIMARY KEY, title TEXT NOT NULL DEFAULT '',
                      company TEXT NOT NULL DEFAULT '',
                      channel TEXT NOT NULL DEFAULT '',
                      status TEXT NOT NULL DEFAULT 'applied',
                      confirmation TEXT NOT NULL DEFAULT '',
                      applied_at TEXT NOT NULL DEFAULT '')""")


def get_profile():
    init_db()
    with _conn() as c:
        row = c.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    if row:
        try:
            merged = dict(DEFAULT_PROFILE)
            merged.update(json.loads(row["data"]))
            return merged
        except Exception:
            return dict(DEFAULT_PROFILE)
    return dict(DEFAULT_PROFILE)


def save_profile(data):
    init_db()
    import datetime
    now = datetime.datetime.utcnow().isoformat() + "Z"
    clean = {k: data.get(k, DEFAULT_PROFILE.get(k, "")) for k in PROFILE_FIELDS}
    with _conn() as c:
        c.execute(
            "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET data = excluded.data, "
            "updated_at = excluded.updated_at",
            (json.dumps(clean), now),
        )
    return clean


def upsert_match(m):
    init_db()
    import datetime
    now = datetime.datetime.utcnow().isoformat() + "Z"
    mid = m.get("id") or ""
    if not mid:
        return None
    status = m.get("status", "new")
    with _conn() as c:
        row = c.execute("SELECT status FROM matches WHERE id = ?", (mid,)).fetchone()
        if row and status == "new":
            status = row["status"]  # never downgrade an applied/held match
        c.execute(
            "INSERT INTO matches (id, data, status, fit_score, updated_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "data = excluded.data, status = excluded.status, "
            "fit_score = excluded.fit_score, updated_at = excluded.updated_at",
            (mid, json.dumps(m), status, int(m.get("fit_score") or 0), now),
        )
    return mid


def get_matches(status=None, limit=200):
    init_db()
    with _conn() as c:
        if status:
            rows = c.execute(
                "SELECT data FROM matches WHERE status = ? "
                "ORDER BY fit_score DESC, updated_at DESC LIMIT ?",
                (status, limit)).fetchall()
        else:
            rows = c.execute(
                "SELECT data FROM matches ORDER BY fit_score DESC, "
                "updated_at DESC LIMIT ?", (limit,)).fetchall()
    out = []
    for r in rows:
        try:
            out.append(json.loads(r["data"]))
        except Exception:
            continue
    return out


def set_match_status(mid, status, confirmation="", applied_at=""):
    init_db()
    with _conn() as c:
        row = c.execute("SELECT data FROM matches WHERE id = ?", (mid,)).fetchone()
        if not row:
            return False
        m = json.loads(row["data"])
        m["status"] = status
        if confirmation:
            m["confirmation"] = confirmation
        if applied_at:
            m["applied_at"] = applied_at
        c.execute("UPDATE matches SET data = ?, status = ? WHERE id = ?",
                  (json.dumps(m), status, mid))
        if status == "applied":
            c.execute(
                "INSERT INTO applications (id, title, company, channel, status, "
                "confirmation, applied_at) VALUES (?, ?, ?, ?, 'applied', ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET confirmation = excluded.confirmation, "
                "applied_at = excluded.applied_at",
                (mid, m.get("title", ""), m.get("company", ""),
                 m.get("channel", ""), confirmation, applied_at))
    return True


def upsert_queue(item):
    init_db()
    qid = item.get("id") or ""
    if not qid:
        return None
    with _conn() as c:
        c.execute(
            "INSERT INTO queue (id, match_id, reason, action_needed, created_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
            "match_id = excluded.match_id, reason = excluded.reason, "
            "action_needed = excluded.action_needed, "
            "created_at = excluded.created_at",
            (qid, item.get("match_id", ""), item.get("reason", ""),
             item.get("action_needed", ""), item.get("created_at", "")))
    return qid


def get_queue():
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, match_id, reason, action_needed, created_at "
            "FROM queue ORDER BY created_at DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]


def get_applications(limit=200):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, title, company, channel, status, confirmation, applied_at "
            "FROM applications ORDER BY applied_at DESC LIMIT ?",
            (limit,)).fetchall()
    return [dict(r) for r in rows]


def counts():
    init_db()
    import datetime
    today = datetime.datetime.utcnow().date().isoformat()
    with _conn() as c:
        total_matches = c.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        new_matches = c.execute(
            "SELECT COUNT(*) FROM matches WHERE status = 'new'").fetchone()[0]
        queued = c.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
        applied_total = c.execute(
            "SELECT COUNT(*) FROM applications").fetchone()[0]
        applied_today = c.execute(
            "SELECT COUNT(*) FROM applications WHERE substr(applied_at, 1, 10) = ?",
            (today,)).fetchone()[0]
    prof = get_profile()
    filled = sum(1 for k in PROFILE_FIELDS if str(prof.get(k, "")).strip())
    return {
        "profile_complete": f"{filled}/{len(PROFILE_FIELDS)}",
        "total_matches": total_matches,
        "new_matches": new_matches,
        "queued": queued,
        "applied_total": applied_total,
        "applied_today": applied_today,
        "daily_cap": int(prof.get("daily_cap") or 4),
        "today": today,
    }
