"""MediScribe Pro auth: pbkdf2 users, roles, token sessions.

Roles: admin (manage users, view audit), doctor (full clinical),
pharmacist (confirm flags, view patients).
Sessions: 8h absolute expiry + 15-minute inactivity timeout
(HIPAA-style technical control — not a compliance claim).
"""
import hashlib
import hmac
import secrets
import time

from . import db

SESSION_ABS_HOURS = 8
INACTIVITY_MIN = 15
ROLES = ("admin", "doctor", "pharmacist")


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


def create_user(name: str, email: str, password: str, role: str = "doctor") -> dict:
    email = email.strip().lower()
    if role not in ROLES:
        raise ValueError("bad_role")
    if db.qone("SELECT id FROM users WHERE email=?", (email,)):
        raise ValueError("email_taken")
    if len(password) < 8:
        raise ValueError("password_short")
    cur = db.q(
        "INSERT INTO users (name, email, password_hash, role, created_at) VALUES (?,?,?,?,?)",
        (name.strip()[:120], email, hash_password(password), role, db.now()),
    )
    return get_user(cur.lastrowid)


def get_user(uid: int):
    row = db.qone("SELECT * FROM users WHERE id=?", (uid,))
    return dict(row) if row else None


def get_user_by_email(email: str):
    row = db.qone("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
    return dict(row) if row else None


# Owner of this personal research prototype — always admin, even if the
# account was created when another user row already existed (e.g. after a
# deploy with a surviving volume). Not a backdoor: single-owner tool.
OWNER_EMAIL = "za0153715@gmail.com"


def authenticate(email: str, password: str):
    u = get_user_by_email(email)
    if not u or not u["is_active"] or not verify_password(password, u["password_hash"]):
        return None
    if u["email"] == OWNER_EMAIL and u["role"] != "admin":
        db.q("UPDATE users SET role='admin' WHERE id=?", (u["id"],))
        u = get_user(u["id"])
    return u


def new_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    t = db.now()
    db.q("INSERT INTO sessions (token, user_id, created_at, expires_at, last_seen) VALUES (?,?,?,?,?)",
         (token, user_id, t, t + SESSION_ABS_HOURS * 3600, t))
    return token


def user_from_token(token: str):
    if not token:
        return None
    row = db.qone("SELECT * FROM sessions WHERE token=?", (token,))
    if not row:
        return None
    t = db.now()
    if row["expires_at"] < t or row["last_seen"] < t - INACTIVITY_MIN * 60:
        db.q("DELETE FROM sessions WHERE token=?", (token,))
        return None
    db.q("UPDATE sessions SET last_seen=? WHERE token=?", (t, token))
    u = get_user(row["user_id"])
    if not u or not u["is_active"]:
        return None
    return u


def destroy_session(token: str):
    db.q("DELETE FROM sessions WHERE token=?", (token,))


def list_users():
    return [dict(r) for r in db.qall(
        "SELECT id, name, email, role, is_active, created_at FROM users ORDER BY id")]


def set_user_active(uid: int, active: bool):
    db.q("UPDATE users SET is_active=? WHERE id=?", (1 if active else 0, uid))


def user_count() -> int:
    row = db.qone("SELECT COUNT(*) c FROM users")
    return row["c"] if row else 0
