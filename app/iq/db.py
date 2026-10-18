"""IQLab SQLite store — profiles, attempts, streaks."""
import json
import os
import sqlite3
import threading
import time
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "iq.db")
_lock = threading.RLock()

def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init():
    with _lock, _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS profiles(
            uuid TEXT PRIMARY KEY, created REAL, target_iq INTEGER DEFAULT 120,
            badges TEXT DEFAULT '[]', last_day TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS attempts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, ts REAL,
            mode TEXT, domain TEXT, qtype TEXT, level INTEGER,
            correct INTEGER, total INTEGER, pct REAL)""")

def get_profile(uid):
    with _lock, _conn() as c:
        r = c.execute("SELECT * FROM profiles WHERE uuid=?", (uid,)).fetchone()
        if not r:
            c.execute("INSERT INTO profiles(uuid, created) VALUES(?, ?)", (uid, time.time()))
            r = c.execute("SELECT * FROM profiles WHERE uuid=?", (uid,)).fetchone()
        return dict(r)

def set_target(uid, target):
    with _lock, _conn() as c:
        c.execute("UPDATE profiles SET target_iq=? WHERE uuid=?", (int(target), uid))

def record_attempt(uid, mode, domain, qtype, level, correct, total):
    pct = round(100.0 * correct / total, 1) if total else 0
    day = time.strftime("%Y-%m-%d")
    with _lock, _conn() as c:
        c.execute("""INSERT INTO attempts(uuid, ts, mode, domain, qtype, level, correct, total, pct)
                     VALUES(?,?,?,?,?,?,?,?,?)""",
                  (uid, time.time(), mode, domain, qtype, level, correct, total, pct))
        p = c.execute("SELECT last_day FROM profiles WHERE uuid=?", (uid,)).fetchone()
        if p and p["last_day"] != day:
            c.execute("UPDATE profiles SET last_day=? WHERE uuid=?", (day, uid))
    return pct

def streak_days(uid):
    with _lock, _conn() as c:
        days = [r[0] for r in c.execute(
            "SELECT DISTINCT date(ts,'unixepoch','localtime') FROM attempts WHERE uuid=? ORDER BY 1 DESC", (uid,))]
    if not days:
        return 0
    import datetime
    today = datetime.date.today()
    streak = 0
    d = today
    dayset = set(days)
    # allow today missing (count from yesterday)
    if d.isoformat() not in dayset:
        d = d - datetime.timedelta(days=1)
    while d.isoformat() in dayset:
        streak += 1
        d = d - datetime.timedelta(days=1)
    return streak

def domain_stats(uid):
    """Returns {domain: {avg_pct, attempts, max_level}} and assessments count."""
    with _lock, _conn() as c:
        rows = c.execute("""SELECT domain, AVG(pct) avgp, COUNT(*) n, MAX(level) ml
                            FROM attempts WHERE uuid=? AND mode='assess' GROUP BY domain""", (uid,)).fetchall()
        out = {r["domain"]: {"avg": round(r["avgp"], 1), "n": r["n"], "max_level": r["ml"]} for r in rows}
        n_assess = c.execute("SELECT COUNT(DISTINCT date(ts,'unixepoch','localtime')) FROM attempts WHERE uuid=? AND mode='assess'", (uid,)).fetchone()[0]
        train = c.execute("SELECT domain, level FROM attempts WHERE uuid=? AND mode='train' ORDER BY ts DESC LIMIT 50", (uid,)).fetchall()
    return out, n_assess or 0, [(r["domain"], r["level"]) for r in train]

def history(uid, limit=20):
    with _lock, _conn() as c:
        rows = c.execute("""SELECT date(ts,'unixepoch','localtime') day, AVG(pct) p, COUNT(*) n
                            FROM attempts WHERE uuid=? GROUP BY day ORDER BY day DESC LIMIT ?""", (uid, limit)).fetchall()
    return [{"day": r["day"], "avg": round(r["p"], 1), "n": r["n"]} for r in rows]

def new_uuid():
    return uuid.uuid4().hex[:16]

init()
