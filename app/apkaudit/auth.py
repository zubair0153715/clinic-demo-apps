"""SecureAPK accounts: signup/login with pbkdf2 password hashing + token sessions."""
import hashlib
import hmac
import os
import secrets
from typing import Optional

from app.apkaudit import db

SESSION_DAYS = 30


def _hash(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + "$" + dk.hex()


def hash_password(password: str) -> str:
    return _hash(password, secrets.token_bytes(16))


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, _ = stored.split("$", 1)
        return hmac.compare_digest(_hash(password, bytes.fromhex(salt_hex)), stored)
    except Exception:
        return False


def create_user(name: str, email: str, password: str) -> dict:
    email = email.strip().lower()
    if db.qone("SELECT id FROM users WHERE email=?", (email,)):
        raise ValueError("email_taken")
    if len(password) < 8:
        raise ValueError("password_short")
    cur = db.q(
        "INSERT INTO users (name, email, password_hash, plan, created_at) VALUES (?,?,?,?,?)",
        (name.strip()[:80], email, hash_password(password), "free", db.now()),
    )
    return get_user(cur.lastrowid)


def get_user(user_id: int) -> Optional[dict]:
    row = db.qone("SELECT * FROM users WHERE id=?", (user_id,))
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[dict]:
    row = db.qone("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
    return dict(row) if row else None


def authenticate(email: str, password: str) -> Optional[dict]:
    u = get_user_by_email(email)
    if not u or not verify_password(password, u["password_hash"]):
        return None
    return u


def new_session(user_id: int) -> str:
    token = "apk_" + secrets.token_hex(24)
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
    u = get_user(row["user_id"])
    if not u or not u["is_active"]:
        return None
    return u


def destroy_session(token: str):
    db.q("DELETE FROM sessions WHERE token=?", (token,))


def set_plan(user_id: int, plan: str):
    if plan not in ("free", "pro"):
        raise ValueError("bad_plan")
    db.q("UPDATE users SET plan=? WHERE id=?", (plan, user_id))


def set_active(user_id: int, active: bool):
    db.q("UPDATE users SET is_active=? WHERE id=?", (1 if active else 0, user_id))


def admin_key_ok(provided: str) -> bool:
    expected = os.environ.get("APK_AUDIT_ADMIN_KEY", "")
    return bool(expected) and hmac.compare_digest(provided or "", expected)


def scans_this_month(user_id: int) -> int:
    row = db.qone("SELECT COUNT(*) c FROM scans WHERE user_id=? AND month=?",
                  (user_id, db.current_month()))
    return row["c"] if row else 0


FREE_SCANS_PER_MONTH = 3


def can_scan(user: dict) -> bool:
    if user["plan"] == "pro":
        return True
    return scans_this_month(user["id"]) < FREE_SCANS_PER_MONTH


def scans_left(user: dict) -> object:
    if user["plan"] == "pro":
        return "unlimited"
    return max(0, FREE_SCANS_PER_MONTH - scans_this_month(user["id"]))


def list_users():
    rows = db.qall("SELECT id, name, email, plan, is_active, created_at FROM users ORDER BY id DESC")
    out = []
    for r in rows:
        d = dict(r)
        d["scans_total"] = db.qone("SELECT COUNT(*) c FROM scans WHERE user_id=?", (r["id"],))["c"]
        d["scans_month"] = scans_this_month(r["id"])
        out.append(d)
    return out
