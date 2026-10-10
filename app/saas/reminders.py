"""Reminder engine: background loop that sends due WhatsApp reminders.

Runs inside the FastAPI lifespan (every 60s). For each active clinic it finds
appointments whose reminder time has arrived and that haven't had that
reminder sent yet, then sends via the WhatsApp provider and logs to messages.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from . import db, whatsapp

log = logging.getLogger("nsg.reminders")

ACTIVE_STATUSES = ("scheduled", "reminder_sent")


def _parse_hours(clinic: dict):
    try:
        hours = json.loads(clinic.get("reminder_hours") or "[24, 2]")
        return sorted([float(h) for h in hours if float(h) > 0], reverse=True)
    except Exception:
        return [24.0, 2.0]


def _appt_dt(appt) -> datetime | None:
    try:
        dt = datetime.fromisoformat(appt["appointment_at"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def due_reminders(now_utc: datetime):
    """Yield (clinic, appointment, hours_before) tuples that are due."""
    clinics = db.qall("SELECT * FROM clinics WHERE is_active=1")
    for c in clinics:
        clinic = dict(c)
        hours_list = _parse_hours(clinic)
        appts = db.qall(
            "SELECT * FROM appointments WHERE clinic_id=? AND status IN (?,?)",
            (clinic["id"], *ACTIVE_STATUSES))
        for a in appts:
            appt = dict(a)
            dt = _appt_dt(appt)
            if not dt or dt <= now_utc:
                continue
            for h in hours_list:
                delta_h = (dt - now_utc).total_seconds() / 3600
                if delta_h <= h:
                    sent = db.qone(
                        "SELECT id FROM messages WHERE appointment_id=? "
                        "AND hours_before=? AND direction='out'",
                        (appt["id"], h))
                    if not sent:
                        yield clinic, appt, h
                    break  # only the nearest due reminder per appointment


def _ctx(clinic: dict, appt: dict) -> dict:
    dt = _appt_dt(appt)
    try:
        tzname = clinic.get("timezone") or "Asia/Dubai"
        from zoneinfo import ZoneInfo
        local = dt.astimezone(ZoneInfo(tzname))
    except Exception:
        local = dt
    return {
        "patient": appt["patient_name"],
        "clinic": clinic["name"],
        "treatment": appt["treatment"] or "appointment",
        "time": local.strftime("%a %d %b, %I:%M %p"),
    }


def send_reminder(clinic: dict, appt: dict, hours_before: float) -> bool:
    lang = appt.get("language") or clinic.get("language") or "en"
    custom = clinic.get("template_24h") if hours_before >= 12 else clinic.get("template_2h")
    template = (custom.strip() if custom and custom.strip()
                else whatsapp.default_template(hours_before, lang))
    body = whatsapp.render(template, _ctx(clinic, appt))
    res = whatsapp.send_text(appt["patient_phone"], body)
    db.q(
        "INSERT INTO messages (clinic_id, appointment_id, direction, body, hours_before,"
        " provider_msg_id, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (clinic["id"], appt["id"], "out", body, hours_before,
         res.get("provider_id", ""),
         "simulated" if res.get("simulated") else ("sent" if res["ok"] else "failed"),
         db.now()))
    if res["ok"]:
        db.q("UPDATE appointments SET status='reminder_sent' WHERE id=? AND status='scheduled'",
             (appt["id"],))
        log.info("reminder sent clinic=%s appt=%s h=%s", clinic["id"], appt["id"], hours_before)
        return True
    log.warning("reminder failed clinic=%s appt=%s: %s", clinic["id"], appt["id"], res.get("error"))
    return False


def run_once() -> int:
    now_utc = datetime.now(timezone.utc)
    n = 0
    for clinic, appt, h in due_reminders(now_utc):
        try:
            if send_reminder(clinic, appt, h):
                n += 1
        except Exception:
            log.exception("reminder error appt=%s", appt["id"])
    return n


async def loop_forever(interval_s: int = 60):
    while True:
        try:
            run_once()
        except Exception:
            log.exception("reminder loop error")
        await asyncio.sleep(interval_s)
