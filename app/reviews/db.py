"""Review Booster persistence.

Shares the No-Show Guard SQLite DB (same clinic tenants, same appointments).
Adds review_requests + feedback tables and a google_review_link column on clinics.
"""
from app.saas import db as sdb

SCHEMA = """
CREATE TABLE IF NOT EXISTS review_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    appointment_id INTEGER REFERENCES appointments(id) ON DELETE SET NULL,
    patient_name TEXT DEFAULT '',
    patient_phone TEXT NOT NULL,
    status TEXT DEFAULT 'sent',
    rating INTEGER,
    sent_at REAL NOT NULL,
    responded_at REAL,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rr_appt ON review_requests(appointment_id);
CREATE INDEX IF NOT EXISTS idx_rr_phone_status ON review_requests(patient_phone, status);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clinic_id INTEGER NOT NULL REFERENCES clinics(id) ON DELETE CASCADE,
    review_request_id INTEGER REFERENCES review_requests(id) ON DELETE SET NULL,
    rating INTEGER,
    text TEXT DEFAULT '',
    patient_name TEXT DEFAULT '',
    patient_phone TEXT DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fb_clinic ON feedback(clinic_id, created_at);
"""


def init():
    with sdb._lock:
        conn = sdb.get_conn()
        conn.executescript(SCHEMA)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(clinics)")}
        if "google_review_link" not in cols:
            conn.execute("ALTER TABLE clinics ADD COLUMN google_review_link TEXT DEFAULT ''")
        conn.commit()


# re-export the shared query helpers so callers use one namespace
q = sdb.q
qone = sdb.qone
qall = sdb.qall
now = sdb.now
