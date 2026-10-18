"""SQLite persistence for the receptionist demo (/receptionist).

Tables: conversations (session state), messages (transcripts), leads.
Container SQLite can be wiped on deploy — acceptable for a sales demo;
production deployments should point RECEPTIONIST_DB_PATH at durable storage.
"""
import json
import os
import sqlite3
import threading
import time
import uuid

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "receptionist.db")
    return os.environ.get("RECEPTIONIST_DB_PATH", default)


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
CREATE TABLE IF NOT EXISTS conversations (
    session_id TEXT PRIMARY KEY,
    lang TEXT DEFAULT 'en',
    state_json TEXT NOT NULL,
    created REAL NOT NULL,
    updated REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    name TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    intent TEXT NOT NULL,
    service TEXT DEFAULT '',
    date TEXT DEFAULT '',
    time TEXT DEFAULT '',
    status TEXT DEFAULT 'new',
    created REAL NOT NULL
);
"""


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def new_session_id() -> str:
    return uuid.uuid4().hex[:12]


def load_session(session_id: str):
    c = get_conn()
    row = c.execute("SELECT * FROM conversations WHERE session_id=?",
                    (session_id,)).fetchone()
    if not row:
        return None
    return {"session_id": row["session_id"], "lang": row["lang"],
            "state": json.loads(row["state_json"])}


def save_session(session_id: str, lang: str, state: dict):
    c = get_conn()
    now = time.time()
    blob = json.dumps(state)
    with _lock:
        c.execute("""INSERT INTO conversations(session_id, lang, state_json, created, updated)
                     VALUES(?,?,?,?,?)
                     ON CONFLICT(session_id) DO UPDATE SET
                       lang=excluded.lang, state_json=excluded.state_json,
                       updated=excluded.updated""",
                  (session_id, lang, blob, now, now))
        c.commit()


def add_message(session_id: str, role: str, text: str):
    c = get_conn()
    with _lock:
        c.execute("INSERT INTO messages(session_id, role, text, ts) VALUES(?,?,?,?)",
                  (session_id, role, text, time.time()))
        c.commit()


def transcript(session_id: str):
    c = get_conn()
    rows = c.execute("SELECT role, text, ts FROM messages WHERE session_id=? ORDER BY id",
                     (session_id,)).fetchall()
    return [dict(r) for r in rows]


def add_lead(session_id: str, intent: str, slots: dict) -> int:
    c = get_conn()
    with _lock:
        cur = c.execute("""INSERT INTO leads(session_id, name, phone, intent, service,
                          date, time, status, created)
                          VALUES(?,?,?,?,?,?,?,?,?)""",
                        (session_id, slots.get("name", ""), slots.get("phone", ""),
                         intent, slots.get("service", ""), slots.get("date", ""),
                         slots.get("time", ""), "new", time.time()))
        c.commit()
        return cur.lastrowid


def list_leads(limit: int = 200):
    c = get_conn()
    rows = c.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def count_sessions() -> int:
    c = get_conn()
    return c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
