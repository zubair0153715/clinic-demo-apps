"""Larkana Property — listings store (Larkana city only).

Container-side SQLite. A deploy wipes this DB (known clinic-demo
limitation) — v1 has no persistent store; listings live in the container
DB and a persistent DB is a v2 step. Nothing is seeded: the launch state
is honestly empty until a real seller posts a listing.
"""

import json
import os
import re
import sqlite3
import uuid

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "larkana.db")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

# Real Larkana localities, verified against OLX Larkana area lists, the
# SMEDA Larkana city profile and FBR SRO 1700(I)/2024 (Larkana schedule).
LOCALITIES = [
    "VIP Road", "Station Road", "Sachal Colony", "Allahabad",
    "Bandar Road", "Bank Square", "Jinnah Bagh", "Lahori Mohalla",
    "Pakistani Chowk", "Sabzi Mandi", "Rahmatpur", "Sheikh Zayed Colony",
    "Bakrani Road", "Murad Wahan", "Professors Colony", "Doctors Colony",
    "Peoples Colony", "Faisal Colony", "OPF Colony",
    "Shah Nawaz Bhutto Road", "Shahi Bazar", "Empire Road",
    "College Road", "Airport Road", "Naudero Chowk", "Khaliq Colony",
    "Chandka Staff Colony", "Abro Colony", "Karma Bagh", "Zulfiqar Bagh",
]

PTYPES = ["house", "plot", "shop", "flat", "commercial"]
PURPOSES = ["sale", "wanted"]
SIZE_UNITS = ["sqyd", "marla", "kanal"]
SQYD_PER_UNIT = {"sqyd": 1.0, "marla": 30.25, "kanal": 605.0}

MAX_PHOTOS = 3
MAX_PHOTO_BYTES = 2 * 1024 * 1024
ALLOWED_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS listings
                     (id TEXT PRIMARY KEY, purpose TEXT NOT NULL,
                      ptype TEXT NOT NULL, title TEXT NOT NULL,
                      locality TEXT NOT NULL, address TEXT NOT NULL DEFAULT '',
                      price INTEGER NOT NULL, size_value REAL NOT NULL DEFAULT 0,
                      size_unit TEXT NOT NULL DEFAULT 'sqyd',
                      bedrooms INTEGER NOT NULL DEFAULT 0,
                      description TEXT NOT NULL DEFAULT '',
                      seller_name TEXT NOT NULL, phone TEXT NOT NULL,
                      phone_digits TEXT NOT NULL DEFAULT '',
                      photos TEXT NOT NULL DEFAULT '[]',
                      status TEXT NOT NULL DEFAULT 'pending',
                      created_at TEXT NOT NULL,
                      reviewed_at TEXT NOT NULL DEFAULT '')""")


def normalize_phone(raw):
    """Return (display, wa_digits). wa_digits is '' unless it is a
    Pakistani mobile usable on WhatsApp (92 + 10 digits)."""
    digits = re.sub(r"\D", "", raw or "")
    display = (raw or "").strip()
    wa = ""
    if len(digits) == 11 and digits.startswith("03"):
        wa = "92" + digits[1:]
    elif len(digits) == 12 and digits.startswith("92") and digits[2] == "3":
        wa = digits
    elif len(digits) == 10 and digits.startswith("3"):
        wa = "92" + digits
    return display, wa


def valid_phone(raw):
    digits = re.sub(r"\D", "", raw or "")
    # Pakistani mobile (03XX, 10-11 digits) or Larkana landline (074, 10 digits)
    return (len(digits) == 11 and digits.startswith("03")) or \
           (len(digits) == 10 and digits.startswith("3")) or \
           (len(digits) == 12 and digits.startswith("92")) or \
           (len(digits) == 10 and digits.startswith("074"))


def size_in_sqyd(value, unit):
    try:
        return float(value or 0) * SQYD_PER_UNIT.get(unit, 1.0)
    except Exception:
        return 0.0


def create_listing(data, photo_names):
    """Insert a PENDING listing. Returns the id."""
    init_db()
    import datetime
    now = datetime.datetime.now().isoformat(timespec="seconds")
    lid = uuid.uuid4().hex[:12]
    _, wa = normalize_phone(data["phone"])
    with _conn() as c:
        c.execute(
            "INSERT INTO listings (id, purpose, ptype, title, locality, "
            "address, price, size_value, size_unit, bedrooms, description, "
            "seller_name, phone, phone_digits, photos, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)",
            (lid, data["purpose"], data["ptype"], data["title"],
             data["locality"], data.get("address", ""),
             int(data["price"]), float(data.get("size_value") or 0),
             data.get("size_unit", "sqyd"),
             int(data.get("bedrooms") or 0),
             data.get("description", ""), data["seller_name"],
             data["phone"], wa, json.dumps(photo_names), now))
    return lid


def get_listing(lid):
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM listings WHERE id = ?",
                        (lid,)).fetchone()
    return _row_to_dict(row) if row else None


def _row_to_dict(row):
    d = dict(row)
    try:
        d["photos"] = json.loads(d.get("photos") or "[]")
    except Exception:
        d["photos"] = []
    d["size_sqyd"] = size_in_sqyd(d.get("size_value"), d.get("size_unit"))
    return d


def search_listings(filters, status="approved", limit=100):
    """filters: ptype, purpose, locality, min_price, max_price,
    min_size_sqyd, max_size_sqyd, q (title/locality/description text)."""
    init_db()
    sql = "SELECT * FROM listings WHERE status = ?"
    params = [status]
    if filters.get("ptype"):
        sql += " AND ptype = ?"
        params.append(filters["ptype"])
    if filters.get("purpose"):
        sql += " AND purpose = ?"
        params.append(filters["purpose"])
    if filters.get("locality"):
        sql += " AND locality = ?"
        params.append(filters["locality"])
    if filters.get("min_price"):
        sql += " AND price >= ?"
        params.append(int(filters["min_price"]))
    if filters.get("max_price"):
        sql += " AND price <= ?"
        params.append(int(filters["max_price"]))
    if filters.get("q"):
        sql += " AND (title LIKE ? OR locality LIKE ? OR description LIKE ?)"
        q = "%" + filters["q"] + "%"
        params += [q, q, q]
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with _conn() as c:
        rows = c.execute(sql, params).fetchall()
    out = [_row_to_dict(r) for r in rows]
    lo = filters.get("min_size_sqyd")
    hi = filters.get("max_size_sqyd")
    if lo is not None or hi is not None:
        out = [d for d in out
               if (lo is None or d["size_sqyd"] >= lo)
               and (hi is None or d["size_sqyd"] <= hi)]
    return out


def list_by_status(status, limit=100):
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM listings WHERE status = ? "
            "ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
    return [_row_to_dict(r) for r in rows]


def set_status(lid, status):
    init_db()
    import datetime
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            "UPDATE listings SET status = ?, reviewed_at = ? WHERE id = ?",
            (status, now, lid))
    return cur.rowcount > 0


def delete_listing(lid):
    init_db()
    listing = get_listing(lid)
    with _conn() as c:
        cur = c.execute("DELETE FROM listings WHERE id = ?", (lid,))
    if listing:
        for name in listing.get("photos") or []:
            try:
                os.remove(os.path.join(UPLOAD_DIR, name))
            except Exception:
                pass
    return cur.rowcount > 0


def counts():
    init_db()
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        live = c.execute(
            "SELECT COUNT(*) FROM listings WHERE status = 'approved'"
        ).fetchone()[0]
        pending = c.execute(
            "SELECT COUNT(*) FROM listings WHERE status = 'pending'"
        ).fetchone()[0]
    return {"total": total, "live": live, "pending": pending}
