"""JobHub owner login — single-password gate for the dashboard.

The password comes from the JOBHUB_PASSWORD env secret (set by the owner in
the FastAPI Cloud dashboard). No default password: if the secret is unset,
login is impossible (fail closed). Sessions are random tokens stored in the
jobhub SQLite DB, 30-day expiry, httponly cookie. The worker API is NOT
affected — it stays key-gated via X-Worker-Key.
"""
import hashlib
import hmac
import os
import secrets
import time

from . import db

SESSION_DAYS = 30
COOKIE = "jobhub_session"


def password_set() -> bool:
    return bool(os.environ.get("JOBHUB_PASSWORD", "").strip())


def check_password(password: str) -> bool:
    """Constant-time check against the env secret. False when unset."""
    stored = os.environ.get("JOBHUB_PASSWORD", "")
    if not stored or not password:
        return False
    entered = hashlib.sha256(password.encode()).hexdigest()
    expected = hashlib.sha256(stored.encode()).hexdigest()
    return hmac.compare_digest(entered, expected)


def new_session() -> str:
    token = "jh_" + secrets.token_hex(24)
    expires_at = int(time.time()) + SESSION_DAYS * 86400
    db.add_session(token, expires_at)
    return token


def valid_session(token: str) -> bool:
    if not token:
        return False
    row = db.get_session(token)
    if not row:
        return False
    if int(row["expires_at"]) < int(time.time()):
        db.delete_session(token)
        return False
    return True


def destroy_session(token: str):
    if token:
        db.delete_session(token)
