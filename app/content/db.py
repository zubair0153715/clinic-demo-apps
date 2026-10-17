"""SQLite persistence for the Content Engine app (/content).

Single-user app: no accounts. Tables: videos (render queue + history),
app_settings (one row: niche + weekly automation toggle).

DB path via CONTENT_DB_PATH env var (default: <app>/data/content.db).
Container SQLite can be wiped on deploy; video history loss is acceptable
(results auto-expire after 30 days anyway).
"""
import os
import re
import sqlite3
import threading
import time
import uuid

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "content.db")
    return os.environ.get("CONTENT_DB_PATH", default)


def results_dir(vid: str = "") -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    base = os.environ.get("CONTENT_RESULTS_DIR",
                          os.path.join(os.path.dirname(here), "data", "content_results"))
    d = os.path.join(base, vid) if vid else base
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
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    niche TEXT DEFAULT '',
    auto INTEGER DEFAULT 0,
    status TEXT DEFAULT 'queued',
    stage TEXT DEFAULT '',
    error TEXT DEFAULT '',
    qc_score REAL,
    month TEXT DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    niche TEXT DEFAULT '',
    weekly_auto INTEGER DEFAULT 0,
    language TEXT DEFAULT 'en',
    voice TEXT DEFAULT '',
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,       -- 'user' | 'agent'
    kind TEXT DEFAULT 'text', -- 'text' | 'video' | 'status'
    text TEXT DEFAULT '',
    vid TEXT DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_created ON videos(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(id);
"""


def init_schema(conn: sqlite3.Connection):
    # One-time migration: the SaaS build used a per-user schema (users,
    # sessions, settings, videos with user_id). This app is single-user;
    # drop the SaaS tables and rebuild. Only test data existed.
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if "users" in tables:
        conn.executescript(
            "DROP TABLE IF EXISTS videos;"
            "DROP TABLE IF EXISTS users;"
            "DROP TABLE IF EXISTS sessions;"
            "DROP TABLE IF EXISTS settings;")
    conn.executescript(SCHEMA)
    if not conn.execute("SELECT 1 FROM app_settings WHERE id=1").fetchone():
        conn.execute("INSERT INTO app_settings (id, niche, weekly_auto, language, voice, updated_at)"
                     " VALUES (1, '', 0, 'en', '', ?)", (time.time(),))
    # additive migrations for older rows
    cols = {r[1] for r in conn.execute("PRAGMA table_info(app_settings)")}
    for col, ddl in (("language", "ALTER TABLE app_settings ADD COLUMN language TEXT DEFAULT 'en'"),
                     ("voice", "ALTER TABLE app_settings ADD COLUMN voice TEXT DEFAULT ''")):
        if col not in cols:
            conn.execute(ddl)
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


def new_id() -> str:
    return uuid.uuid4().hex


def current_month() -> str:
    return time.strftime("%Y-%m", time.gmtime(now()))


# ------------------------------------------------------------- app API ---
def get_settings() -> dict:
    row = qone("SELECT * FROM app_settings WHERE id=1")
    if not row:
        return {"niche": "", "weekly_auto": 0, "language": "en", "voice": ""}
    d = dict(row)
    d.setdefault("language", "en")
    d.setdefault("voice", "")
    return d


def save_settings(niche: str = None, weekly_auto: bool = None,
                  language: str = None, voice: str = None):
    cur = get_settings()
    if niche is not None:
        cur["niche"] = niche.strip()[:200]
    if weekly_auto is not None:
        cur["weekly_auto"] = 1 if weekly_auto else 0
    if language is not None:
        cur["language"] = language.strip().lower()[:8] or "en"
    if voice is not None:
        cur["voice"] = voice.strip()[:120]
    q("UPDATE app_settings SET niche=?, weekly_auto=?, language=?, voice=?, updated_at=? WHERE id=1",
      (cur["niche"], cur["weekly_auto"], cur["language"], cur["voice"], now()))


def create_video(topic: str, niche: str, auto: bool = False) -> dict:
    topic = (topic or "").strip()[:300]
    if not topic:
        topic = (niche or "").strip()[:300] or "AI tools"
    vid = new_id()
    t = now()
    q("""INSERT INTO videos (id, topic, niche, auto, status, stage, month, created_at, updated_at)
         VALUES (?,?,?,?, 'queued', '', ?, ?, ?)""",
      (vid, topic, (niche or "").strip()[:200], 1 if auto else 0,
       current_month(), t, t))
    return get_video(vid)


def get_video(vid: str):
    row = qone("SELECT * FROM videos WHERE id=?", (vid,))
    return dict(row) if row else None


def list_videos(limit: int = 100):
    rows = qall("SELECT * FROM videos ORDER BY created_at DESC LIMIT ?", (limit,))
    return [dict(r) for r in rows]


def set_video_status(vid: str, status: str, stage: str = "", error: str = "",
                     qc_score=None):
    if qc_score is None:
        q("UPDATE videos SET status=?, stage=?, error=?, updated_at=? WHERE id=?",
          (status, stage, error[:2000], now(), vid))
    else:
        q("UPDATE videos SET status=?, stage=?, error=?, qc_score=?, updated_at=? WHERE id=?",
          (status, stage, error[:2000], qc_score, now(), vid))


def delete_video(vid: str):
    q("DELETE FROM videos WHERE id=?", (vid,))


# --------------------------------------------------------- chat messages ---
def add_message(role: str, kind: str = "text", text: str = "", vid: str = "") -> dict:
    cur = q("INSERT INTO messages (role, kind, text, vid, created_at) VALUES (?,?,?,?,?)",
            (role, kind, text[:4000], vid, now()))
    row = qone("SELECT * FROM messages WHERE id=?", (cur.lastrowid,))
    return dict(row)


def list_messages(after: int = 0, limit: int = 200):
    rows = qall("SELECT * FROM messages WHERE id>? ORDER BY id ASC LIMIT ?", (after, limit))
    return [dict(r) for r in rows]


def delete_message(mid: int):
    q("DELETE FROM messages WHERE id=?", (mid,))
