"""LeadForge SaaS database: users, plans, sessions, run history, share links."""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_DB = None

PLANS = {
    "free": {"runs_per_month": 5, "share": False, "label": "Free"},
    "pro": {"runs_per_month": 10**9, "share": True, "label": "Pro"},
    "enterprise": {"runs_per_month": 10**9, "share": True, "label": "Enterprise"},
}


def _path():
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(here, "data")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "leadforge.db")


def _conn():
    global _DB
    with _lock:
        if _DB is None:
            _DB = sqlite3.connect(_path(), check_same_thread=False)
            _DB.row_factory = sqlite3.Row
            _DB.execute("PRAGMA journal_mode=WAL")
            _init(_DB)
        return _DB


def _init(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE,
      password_hash TEXT, role TEXT DEFAULT 'researcher', plan TEXT DEFAULT 'free',
      runs_this_month INTEGER DEFAULT 0, month_key TEXT DEFAULT '',
      is_active INTEGER DEFAULT 1, created_at REAL);
    CREATE TABLE IF NOT EXISTS sessions(
      token TEXT PRIMARY KEY, user_id INTEGER, created_at REAL,
      expires_at REAL, last_seen REAL);
    CREATE TABLE IF NOT EXISTS runs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, target TEXT,
      query_input TEXT, lead_count INTEGER, top_score REAL, top_label TEXT,
      result_json TEXT, elapsed_s REAL, created_at REAL);
    CREATE TABLE IF NOT EXISTS shares(
      token TEXT PRIMARY KEY, run_id INTEGER, created_at REAL, revoked INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT,
      detail TEXT, created_at REAL);
    CREATE TABLE IF NOT EXISTS jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, target TEXT,
      query_input TEXT, top_n INTEGER, dock INTEGER,
      status TEXT DEFAULT 'queued', result_json TEXT,
      created_at REAL, updated_at REAL);
    """)
    c.commit()


def now():
    return time.time()


def q(sql, args=()):
    with _lock:
        c = _conn()
        cur = c.execute(sql, args)
        c.commit()
        return cur


def qone(sql, args=()):
    with _lock:
        c = _conn()
        return c.execute(sql, args).fetchone()


def qall(sql, args=()):
    with _lock:
        c = _conn()
        return c.execute(sql, args).fetchall()


def month_key():
    return time.strftime("%Y-%m")


def audit(user_id, action, detail=""):
    q("INSERT INTO audit (user_id, action, detail, created_at) VALUES (?,?,?,?)",
      (user_id, action, detail[:500], now()))
