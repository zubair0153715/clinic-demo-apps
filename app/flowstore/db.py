"""SQLite persistence for FlowStore (Automation-as-a-Service storefront).

DB path configurable via FLOWSTORE_DB_PATH env var
(default: <app>/data/flowstore.db).
"""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "flowstore.db")
    return os.environ.get("FLOWSTORE_DB_PATH", default)


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
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    product TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    business TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    whatsapp TEXT NOT NULL DEFAULT '',
    systems TEXT NOT NULL DEFAULT '[]',
    notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'received',
    n8n_url TEXT NOT NULL DEFAULT '',
    n8n_key TEXT NOT NULL DEFAULT '',
    n8n_workflow_id TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_orders_token ON orders(token);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def qall(sql: str, args=()):
    with _lock:
        return get_conn().execute(sql, args).fetchall()


def qone(sql: str, args=()):
    with _lock:
        return get_conn().execute(sql, args).fetchone()


def qexec(sql: str, args=()):
    with _lock:
        conn = get_conn()
        cur = conn.execute(sql, args)
        conn.commit()
        return cur


def now() -> float:
    return time.time()
