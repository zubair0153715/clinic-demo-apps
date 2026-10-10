"""Review Booster engine: send review requests, handle rating replies.

Trigger: appointment marked completed, OR 2h past appointment time with
status='confirmed'. One request per appointment max.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.saas import whatsapp

from . import db

log = logging.getLogger("reviews.engine")


def _appt_dt(appt):
    try:
        dt = datetime.fromisoformat(appt["appointment_at"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _lang(clinic, appt):
    return appt.get("language") or clinic.get("language") or "en"


def request_body(clinic: dict, lang: str) -> str:
    if lang == "ar":
        return (f"كيف كانت زيارتك لـ {clinic['name']}؟ ⭐\n"
                "قيّم تجربتك بالرد برقم من 1 إلى 5")
    return (f"How was your visit to {clinic['name']}? ⭐\n"
            "Reply with a rating from 1 to 5")


def due_requests(now_utc: datetime):
    """Yield (clinic, appointment) pairs that should get a review request now."""
    cutoff = now_utc - timedelta(hours=2)
    clinics = db.qall("SELECT * FROM clinics WHERE is_active=1")
    for c in clinics:
        clinic = dict(c)
        appts = db.qall(
            "SELECT a.* FROM appointments a LEFT JOIN review_requests r "
            "ON r.appointment_id=a.id "
            "WHERE a.clinic_id=? AND r.id IS NULL "
            "AND a.status IN ('completed','confirmed')",
            (clinic["id"],))
        for a in appts:
            appt = dict(a)
            dt = _appt_dt(appt)
            if not dt:
                continue
            if appt["status"] == "completed" or dt <= cutoff:
                yield clinic, appt


def send_review_request(clinic: dict, appt: dict) -> bool:
    # dedupe: one request per appointment
    if db.qone("SELECT id FROM review_requests WHERE appointment_id=?",
               (appt["id"],)):
        return False
    body = request_body(clinic, _lang(clinic, appt))
    res = whatsapp.send_text(appt["patient_phone"], body)
    db.q(
        "INSERT INTO review_requests (clinic_id, appointment_id, patient_name,"
        " patient_phone, status, sent_at, created_at) VALUES (?,?,?,?,?,?,?)",
        (clinic["id"], appt["id"], appt["patient_name"], appt["patient_phone"],
         "sent", db.now(), db.now()))
    db.q(
        "INSERT INTO messages (clinic_id, appointment_id, direction, body, status,"
        " created_at) VALUES (?,?,?,?,?,?)",
        (clinic["id"], appt["id"], "out", body,
         "simulated" if res.get("simulated") else ("sent" if res["ok"] else "failed"),
         db.now()))
    log.info("review request sent clinic=%s appt=%s ok=%s", clinic["id"], appt["id"], res["ok"])
    return res["ok"]


def run_once() -> int:
    now_utc = datetime.now(timezone.utc)
    n = 0
    for clinic, appt in due_requests(now_utc):
        try:
            if send_review_request(clinic, appt):
                n += 1
        except Exception:
            log.exception("review request error appt=%s", appt["id"])
    return n


async def loop_forever(interval_s: int = 60):
    while True:
        try:
            run_once()
        except Exception:
            log.exception("review loop error")
        await asyncio.sleep(interval_s)


RATING_WORDS = {
    "1": 1, "one": 1, "واحد": 1,
    "2": 2, "two": 2, "اثنان": 2, "اثنين": 2,
    "3": 3, "three": 3, "ثلاثة": 3,
    "4": 4, "four": 4, "أربعة": 4, "اربعة": 4,
    "5": 5, "five": 5, "خمسة": 5,
}


def parse_rating(text: str):
    t = (text or "").strip().lower()
    if t in RATING_WORDS:
        return RATING_WORDS[t]
    # "5 stars", "rating: 4", "4/5" ...
    for ch in t:
        if ch.isdigit() and 1 <= int(ch) <= 5:
            return int(ch)
    return None


def handle_incoming_by_phone(from_phone: str, text: str) -> dict:
    """Route a patient WhatsApp reply to a pending review request.

    Returns {"handled": bool, ...}. Call BEFORE the No-Show Guard handler.
    """
    row = db.qone(
        "SELECT r.*, c.name AS clinic_name, c.google_review_link, "
        "c.language AS clinic_lang FROM review_requests r "
        "JOIN clinics c ON c.id=r.clinic_id "
        "WHERE r.patient_phone=? AND r.status IN ('sent','awaiting_feedback') "
        "AND c.is_active=1 ORDER BY r.id DESC LIMIT 1",
        (from_phone,))
    if not row:
        return {"handled": False}
    rr = dict(row)
    lang = rr["clinic_lang"] or "en"
    rating = parse_rating(text)

    db.q(
        "INSERT INTO messages (clinic_id, appointment_id, direction, body, created_at)"
        " VALUES (?,?,?,?,?)",
        (rr["clinic_id"], rr["appointment_id"], "in", text or "", db.now()))

    if rating is not None:
        db.q("UPDATE review_requests SET rating=?, status=?, responded_at=? WHERE id=?",
             (rating, "responded" if rating >= 4 else "awaiting_feedback",
              db.now(), rr["id"]))
        if rating >= 4:
            link = (rr["google_review_link"] or "").strip()
            if link:
                reply = ("Thank you! ⭐⭐⭐⭐⭐\n"
                         f"Please share your experience on Google — it helps other patients find us:\n{link}"
                         if lang != "ar" else
                         f"شكراً لك! ⭐⭐⭐⭐⭐\nشارك تجربتك على Google وساعد مرضى آخرين:\n{link}")
            else:
                reply = ("Thank you so much! ⭐ We're thrilled you had a great visit."
                         if lang != "ar" else
                         "شكراً جزيلاً! ⭐ سعداء أن زيارتك كانت رائعة.")
        else:
            reply = ("We're sorry to hear that. Your feedback is private — "
                     "please reply and tell us what went wrong so we can fix it. 🙏"
                     if lang != "ar" else
                     "نأسف لسماع ذلك. ملاحظتك سرية — رد علينا وأخبرنا ما الذي حدث لنصلحه. 🙏")
        whatsapp.send_text(from_phone, reply)
        db.q(
            "INSERT INTO messages (clinic_id, appointment_id, direction, body, created_at)"
            " VALUES (?,?,?,?,?)",
            (rr["clinic_id"], rr["appointment_id"], "out", reply, db.now()))
        return {"handled": True, "rating": rating}
    # non-rating text while we await private feedback -> store it
    if rr["status"] == "awaiting_feedback" and (text or "").strip():
        db.q(
            "INSERT INTO feedback (clinic_id, review_request_id, rating, text,"
            " patient_name, patient_phone, created_at) VALUES (?,?,?,?,?,?,?)",
            (rr["clinic_id"], rr["id"], rr["rating"], text.strip(),
             rr["patient_name"], from_phone, db.now()))
        db.q("UPDATE review_requests SET status='responded', responded_at=? WHERE id=?",
             (db.now(), rr["id"]))
        reply = ("Thank you — we've noted your feedback privately and will work on it. 🙏"
                 if lang != "ar" else
                 "شكراً — سجلنا ملاحظتك بسرية وسنعمل على تحسينها. 🙏")
        whatsapp.send_text(from_phone, reply)
        return {"handled": True, "feedback": True}
    return {"handled": False}
