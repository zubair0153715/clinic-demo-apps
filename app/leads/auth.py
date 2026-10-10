"""Agency accounts: signup/login with pbkdf2 password hashing + token sessions."""
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


def create_agency(name: str, agency_name: str, email: str, password: str,
                  city: str = "Dubai") -> dict:
    email = email.strip().lower()
    if db.qone("SELECT id FROM agencies WHERE email=?", (email,)):
        raise ValueError("email_taken")
    if len(password) < 8:
        raise ValueError("password_short")
    cur = db.q(
        "INSERT INTO agencies (name, agency_name, email, password_hash, city, created_at)"
        " VALUES (?,?,?,?,?,?)",
        (name.strip(), agency_name.strip(), email, hash_password(password),
         city.strip() or "Dubai", db.now()))
    return get_agency(cur.lastrowid)


def get_agency(agency_id: int) -> Optional[dict]:
    row = db.qone("SELECT * FROM agencies WHERE id=?", (agency_id,))
    return dict(row) if row else None


def get_agency_by_email(email: str) -> Optional[dict]:
    row = db.qone("SELECT * FROM agencies WHERE email=?", (email.strip().lower(),))
    return dict(row) if row else None


def authenticate(email: str, password: str) -> Optional[dict]:
    a = get_agency_by_email(email)
    if not a or not verify_password(password, a["password_hash"]):
        return None
    return a


def new_session(agency_id: int) -> str:
    token = secrets.token_urlsafe(32)
    exp = db.now() + SESSION_DAYS * 86400
    db.q("INSERT INTO agency_sessions (token, agency_id, created_at, expires_at)"
         " VALUES (?,?,?,?)", (token, agency_id, db.now(), exp))
    return token


def agency_from_token(token: str) -> Optional[dict]:
    if not token:
        return None
    row = db.qone("SELECT * FROM agency_sessions WHERE token=?", (token,))
    if not row or row["expires_at"] < db.now():
        return None
    a = get_agency(row["agency_id"])
    if not a or not a["is_active"]:
        return None
    return a


def destroy_session(token: str):
    db.q("DELETE FROM agency_sessions WHERE token=?", (token,))


def update_settings(agency_id: int, fields: dict):
    allowed = {"name", "agency_name", "phone", "city", "whatsapp_number", "language"}
    sets, args = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            args.append(v)
    if sets:
        args.append(agency_id)
        db.q(f"UPDATE agencies SET {', '.join(sets)} WHERE id=?", tuple(args))


def set_active(agency_id: int, active: bool):
    db.q("UPDATE agencies SET is_active=? WHERE id=?", (1 if active else 0, agency_id))
