"""LabLink accounts: students / teachers / admins, pbkdf2 + token sessions."""
import hashlib
import hmac
import secrets
from typing import Optional

from app.lablink import db

SESSION_DAYS = 30
COOKIE = "lablink_session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
        return hmac.compare_digest(salt_hex + "$" + dk.hex(), stored)
    except Exception:
        return False


def new_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    exp = db.now() + SESSION_DAYS * 86400
    db.q("INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?,?,?,?)",
         (token, user_id, db.now(), exp))
    return token


def user_from_token(token: str) -> Optional[dict]:
    if not token:
        return None
    row = db.qone("SELECT * FROM sessions WHERE token=?", (token,))
    if not row or row["expires_at"] < db.now():
        return None
    u = db.qone("SELECT * FROM users WHERE id=? AND is_active=1", (row["user_id"],))
    return dict(u) if u else None


def destroy_session(token: str):
    db.q("DELETE FROM sessions WHERE token=?", (token,))


def authenticate(email: str, password: str) -> Optional[dict]:
    row = db.qone("SELECT * FROM users WHERE email=? AND is_active=1",
                  (email.strip().lower(),))
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


def is_staff(user: dict) -> bool:
    return bool(user) and user.get("role") in ("teacher", "admin")


def is_admin(user: dict) -> bool:
    return bool(user) and user.get("role") == "admin"
