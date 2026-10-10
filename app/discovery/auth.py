"""LeadForge auth: pbkdf2 users, plans, token sessions.

First signup becomes admin. Plans: free (5 runs/month), pro/enterprise
(unlimited + share links). Billing is manual (WhatsApp) — admin upgrades plans.
Sessions: 8h absolute + 15min inactivity timeout.
"""
import hashlib
import hmac
import secrets

from . import db

SESSION_ABS_HOURS = 8
INACTIVITY_MIN = 15
ROLES = ("admin", "researcher")


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


def user_count():
    return db.qone("SELECT COUNT(*) c FROM users")["c"]


def create_user(name, email, password):
    email = email.strip().lower()
    if db.qone("SELECT id FROM users WHERE email=?", (email,)):
        raise ValueError("email_taken")
    if len(password) < 8:
        raise ValueError("password_short")
    role = "admin" if user_count() == 0 else "researcher"
    plan = "enterprise" if role == "admin" else "free"
    cur = db.q(
        "INSERT INTO users (name, email, password_hash, role, plan, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (name.strip()[:120], email, hash_password(password), role, plan, db.now()))
    u = get_user(cur.lastrowid)
    db.audit(u["id"], "signup", f"role={role}")
    return u


def get_user(uid):
    row = db.qone("SELECT * FROM users WHERE id=?", (uid,))
    return dict(row) if row else None


def get_user_by_email(email):
    row = db.qone("SELECT * FROM users WHERE email=?", (email.strip().lower(),))
    return dict(row) if row else None


def authenticate(email, password):
    u = get_user_by_email(email)
    if not u or not u["is_active"] or not verify_password(password, u["password_hash"]):
        return None
    return u


def new_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    t = db.now()
    db.q("INSERT INTO sessions (token, user_id, created_at, expires_at, last_seen)"
         " VALUES (?,?,?,?,?)", (token, user_id, t, t + SESSION_ABS_HOURS * 3600, t))
    return token


def user_from_token(token: str):
    if not token:
        return None
    row = db.qone("SELECT * FROM sessions WHERE token=?", (token,))
    if not row:
        return None
    t = db.now()
    if t > row["expires_at"]:
        db.q("DELETE FROM sessions WHERE token=?", (token,))
        return None
    if t - row["last_seen"] > INACTIVITY_MIN * 60:
        db.q("DELETE FROM sessions WHERE token=?", (token,))
        return None
    db.q("UPDATE sessions SET last_seen=? WHERE token=?", (t, token))
    u = get_user(row["user_id"])
    if not u or not u["is_active"]:
        return None
    # monthly quota reset
    mk = db.month_key()
    if u["month_key"] != mk:
        db.q("UPDATE users SET month_key=?, runs_this_month=0 WHERE id=?", (mk, u["id"]))
        u["month_key"] = mk
        u["runs_this_month"] = 0
    return u


def logout(token: str):
    db.q("DELETE FROM sessions WHERE token=?", (token,))


def can_run(user) -> tuple:
    """(allowed: bool, reason: str)."""
    plan = db.PLANS.get(user["plan"], db.PLANS["free"])
    if user["runs_this_month"] >= plan["runs_per_month"]:
        return False, "monthly_limit"
    return True, "ok"


def record_run(user):
    db.q("UPDATE users SET runs_this_month=runs_this_month+1 WHERE id=?", (user["id"],))


def set_plan(admin_id, user_id, plan):
    if plan not in db.PLANS:
        raise ValueError("bad_plan")
    db.q("UPDATE users SET plan=? WHERE id=?", (plan, user_id))
    db.audit(admin_id, "set_plan", f"user={user_id} plan={plan}")


def set_active(admin_id, user_id, active: bool):
    db.q("UPDATE users SET is_active=? WHERE id=?", (1 if active else 0, user_id))
    db.audit(admin_id, "set_active", f"user={user_id} active={active}")
