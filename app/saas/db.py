"""SQLite persistence for the No-Show Guard SaaS.

Multi-tenant: every row belongs to a clinic. DB path configurable via
SAAS_DB_PATH env var (default: <app>/data/saas.db).
"""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "saas.db")
    return os.environ.get("SAAS_DB_PATH", default)


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
CREATE TABLE IF NOT EXISTS clinics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    whatsapp_number TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'Asia/Dubai',
    reminder_hours TEXT DEFAULT '[24, 2]',
    template_24h TEXT DEFAULT '',
    template_2h TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    plan TEXT DEFAULT 'trial',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    appointment_at TEXT NOT NULL,
    treatment TEXT DEFAULT '',
    language TEXT DEFAULT 'en',
    status TEXT DEFAULT 'scheduled',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_appt_clinic_time ON appointments(clinic_id, appointment_at);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    direction TEXT NOT NULL,
    body TEXT NOT NULL,
    hours_before REAL,
    provider_msg_id TEXT DEFAULT '',
    status TEXT DEFAULT 'sent',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_msg_appt ON messages(appointment_id, hours_before);
"""


def init_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    # light migrations for older DBs
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(clinics)")}
    for col, ddl in [
        ("plan", "ALTER TABLE clinics ADD COLUMN plan TEXT DEFAULT 'trial'"),
        ("template_24h", "ALTER TABLE clinics ADD COLUMN template_24h TEXT DEFAULT ''"),
        ("template_2h", "ALTER TABLE clinics ADD COLUMN template_2h TEXT DEFAULT ''"),
    ]:
        if col not in cols:
            conn.execute(ddl)
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
