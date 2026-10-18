"""SQLite persistence for SecureAPK (/apkaudit).

Tables: users, sessions, scans. DB path via APK_AUDIT_DB_PATH env var
(default: <app>/data/apkaudit.db). Container SQLite can be wiped on deploy;
scan history loss is acceptable (APKs auto-expire anyway).
"""
import os
import sqlite3
import threading
import time
import uuid

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "apkaudit.db")
    return os.environ.get("APK_AUDIT_DB_PATH", default)


def uploads_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.environ.get("APK_AUDIT_UPLOADS",
                       os.path.join(os.path.dirname(here), "data", "apkaudit_uploads"))
    os.makedirs(d, exist_ok=True)
    return d


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
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    plan TEXT DEFAULT 'free',
    is_active INTEGER DEFAULT 1,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    package TEXT DEFAULT '',
    app_name TEXT DEFAULT '',
    version TEXT DEFAULT '',
    risk_score INTEGER DEFAULT 0,
    risk_band TEXT DEFAULT 'Low',
    n_high INTEGER DEFAULT 0,
    n_medium INTEGER DEFAULT 0,
    n_low INTEGER DEFAULT 0,
    findings_json TEXT DEFAULT '[]',
    apk_path TEXT DEFAULT '',
    fixzip_path TEXT DEFAULT '',
    month TEXT DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_user ON scans(user_id);
"""


def init_schema(conn: sqlite3.Connection):
    conn.executescript(SCHEMA)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(scans)")}
    if "fixzip_path" not in cols:
        conn.execute("ALTER TABLE scans ADD COLUMN fixzip_path TEXT DEFAULT ''")
    conn.commit()


def q(query, args=()):
    with _lock:
        cur = get_conn().execute(query, args)
        get_conn().commit()
        return cur


def qone(query, args=()):
    with _lock:
        return get_conn().execute(query, args).fetchone()


def qall(query, args=()):
    with _lock:
        return get_conn().execute(query, args).fetchall()


def now() -> float:
    return time.time()


def new_uuid() -> str:
    return uuid.uuid4().hex


def current_month() -> str:
    return time.strftime("%Y-%m", time.gmtime(now()))
