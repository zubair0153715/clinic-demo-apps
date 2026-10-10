"""Clinic accounts: signup/login with pbkdf2 password hashing + token sessions."""
import hashlib
import hmac
import os
import secrets
from typing import Optional

from . import db

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


def create_clinic(name: str, email: str, password: str) -> dict:
    email = email.strip().lower()
    if db.qone("SELECT id FROM clinics WHERE email=?", (email,)):
        raise ValueError("email_taken")
    if len(password) < 8:
        raise ValueError("password_short")
    cur = db.q(
        "INSERT INTO clinics (name, email, password_hash, created_at) VALUES (?,?,?,?)",
        (name.strip(), email, hash_password(password), db.now()),
    )
    return get_clinic(cur.lastrowid)


def get_clinic(clinic_id: int) -> Optional[dict]:
    row = db.qone("SELECT * FROM clinics WHERE id=?", (clinic_id,))
    return dict(row) if row else None


def get_clinic_by_email(email: str) -> Optional[dict]:
    row = db.qone("SELECT * FROM clinics WHERE email=?", (email.strip().lower(),))
    return dict(row) if row else None


def authenticate(email: str, password: str) -> Optional[dict]:
    c = get_clinic_by_email(email)
    if not c or not verify_password(password, c["password_hash"]):
        return None
    return c


def new_session(clinic_id: int) -> str:
    token = secrets.token_urlsafe(32)
    exp = db.now() + SESSION_DAYS * 86400
    db.q("INSERT INTO sessions (token, clinic_id, created_at, expires_at) VALUES (?,?,?,?)",
         (token, clinic_id, db.now(), exp))
    return token


def clinic_from_token(token: str) -> Optional[dict]:
    if not token:
        return None
    row = db.qone("SELECT * FROM sessions WHERE token=?", (token,))
    if not row or row["expires_at"] < db.now():
        return None
    c = get_clinic(row["clinic_id"])
    if not c or not c["is_active"]:
        return None
    return c


def destroy_session(token: str):
    db.q("DELETE FROM sessions WHERE token=?", (token,))


def update_settings(clinic_id: int, fields: dict):
    allowed = {"name", "whatsapp_number", "language", "timezone",
               "reminder_hours", "template_24h", "template_2h"}
    sets, args = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            args.append(v)
    if sets:
        args.append(clinic_id)
        db.q(f"UPDATE clinics SET {', '.join(sets)} WHERE id=?", tuple(args))


def set_active(clinic_id: int, active: bool):
    db.q("UPDATE clinics SET is_active=? WHERE id=?", (1 if active else 0, clinic_id))


def admin_key_ok(provided: str) -> bool:
    expected = os.environ.get("SAAS_ADMIN_KEY", "")
    return bool(expected) and hmac.compare_digest(provided or "", expected)


def list_clinics():
    rows = db.qall(
        "SELECT id, name, email, whatsapp_number, is_active, plan, created_at "
        "FROM clinics ORDER BY id DESC")
    out = []
    for r in rows:
        d = dict(r)
        d["appointments"] = db.qone(
            "SELECT COUNT(*) c FROM appointments WHERE clinic_id=?", (r["id"],))["c"]
        d["reminders"] = db.qone(
            "SELECT COUNT(*) c FROM messages WHERE clinic_id=? AND direction='out'",
            (r["id"],))["c"]
        out.append(d)
    return out
