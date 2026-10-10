"""SQLite persistence for Lead Qualifier.

Separate tenant type (agencies), own DB file: <app>/data/leads.db.
"""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "leads.db")
    return os.environ.get("LEADS_DB_PATH", default)


def get_conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = db_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            _conn = sqlite3.connect(path, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            init_schema(_conn)
        return _conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS agencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    agency_name TEXT DEFAULT '',
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    phone TEXT DEFAULT '',
    city TEXT DEFAULT 'Dubai',
    whatsapp_number TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    is_active INTEGER DEFAULT 1,
    plan TEXT DEFAULT 'trial',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS agency_sessions (
    token TEXT PRIMARY KEY,
    agency_id INTEGER NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id INTEGER NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
    name TEXT DEFAULT '',
    phone TEXT NOT NULL,
    intent TEXT DEFAULT '',
    budget TEXT DEFAULT '',
    location TEXT DEFAULT '',
    bedrooms TEXT DEFAULT '',
    timeline TEXT DEFAULT '',
    stage TEXT DEFAULT 'intent',
    score TEXT DEFAULT 'cold',
    language TEXT DEFAULT 'en',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_leads_agency_phone ON leads(agency_id, phone);
CREATE TABLE IF NOT EXISTS lead_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    direction TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lm_lead ON lead_messages(lead_id, id);
"""


def init_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    conn.commit()


def q(query: str, args=()):
    with _lock:
        cur = get_conn().execute(query, args)
        get_conn().commit()
        return cur


def qone(query: str, args=()):
    with _lock:
        return get_conn().execute(query, args).fetchone()


def qall(query: str, args=()):
    with _lock:
        return get_conn().execute(query, args).fetchall()


def now() -> float:
    return time.time()
