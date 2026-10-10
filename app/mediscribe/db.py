"""MediScribe Pro — SQLite persistence.

Multi-user: users have roles (admin/doctor/pharmacist). Patients and
consultations are shared across the team; every read/write is audit-logged.
"""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "mediscribe.db")
    return os.environ.get("MEDISCRIBE_DB_PATH", default)


def now() -> float:
    return time.time()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'doctor',
    is_active INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    last_seen REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mrn TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    age INTEGER DEFAULT 0,
    sex TEXT DEFAULT '',
    conditions TEXT DEFAULT '[]',
    allergies TEXT DEFAULT '[]',
    meds TEXT DEFAULT '[]',
    notes TEXT DEFAULT '',
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    transcript TEXT DEFAULT '',
    flags_json TEXT DEFAULT '[]',
    confirmed_json TEXT DEFAULT '[]',
    created_by INTEGER REFERENCES users(id),
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    user_id INTEGER REFERENCES users(id),
    user_name TEXT DEFAULT '',
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details TEXT DEFAULT '',
    prev_hash TEXT DEFAULT '',
    hash TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS flag_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER REFERENCES consultations(id) ON DELETE CASCADE,
    flag_key TEXT NOT NULL,
    verdict TEXT NOT NULL,
    note TEXT DEFAULT '',
    user_id INTEGER REFERENCES users(id),
    created_at REAL NOT NULL
);
"""


def get_conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = db_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            _conn = sqlite3.connect(path, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            with _lock:
                _conn.executescript(SCHEMA)
        return _conn


def q(sql, args=()):
    with _lock:
        cur = get_conn().execute(sql, args)
        get_conn().commit()
        return cur


def qone(sql, args=()):
    with _lock:
        return get_conn().execute(sql, args).fetchone()


def qall(sql, args=()):
    with _lock:
        return get_conn().execute(sql, args).fetchall()
