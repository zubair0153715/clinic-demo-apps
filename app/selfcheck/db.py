"""SQLite persistence for the PharmaReg Self-Check quiz leads."""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "selfcheck.db")
    return os.environ.get("SELFCHECK_DB_PATH", default)


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
CREATE TABLE IF NOT EXISTS quiz_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT '',
    company TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    answers_json TEXT DEFAULT '[]',
    gaps_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ql_created ON quiz_leads(created_at);
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
