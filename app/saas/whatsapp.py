"""WhatsApp sending layer with a pluggable provider.

Providers (SAAS_WHATSAPP_PROVIDER env):
  - "demo" (default): no network call; message is logged to the DB with
    status="simulated". Lets the whole product run end-to-end today.
  - "meta": Meta WhatsApp Cloud API. Needs SAAS_WHATSAPP_TOKEN and
    SAAS_WHATSAPP_PHONE_NUMBER_ID env vars. Real messages go out.

Incoming replies are handled by parse_reply() — shared by the Meta webhook
and the dashboard's demo simulator.
"""
import json
import logging
import os
import urllib.request

log = logging.getLogger("nsg.whatsapp")

PROVIDER = os.environ.get("SAAS_WHATSAPP_PROVIDER", "demo").lower()


def default_template(hours_before: float, lang: str) -> str:
    en_24 = ("Hello {patient}! This is {clinic} reminding you of your appointment "
             "tomorrow ({treatment}) at {time}. Reply 1 to CONFIRM, 2 to CANCEL.")
    en_2 = ("Hello {patient}! Reminder: your appointment at {clinic} ({treatment}) "
            "is in 2 hours, at {time}. Reply 1 to CONFIRM, 2 to CANCEL.")
    ar_24 = ("مرحباً {patient}! هذا تذكير من {clinic} بموعدك غداً ({treatment}) "
             "الساعة {time}. رد بـ 1 للتأكيد، 2 للإلغاء.")
    ar_2 = ("مرحباً {patient}! تذكير: موعدك في {clinic} ({treatment}) بعد ساعتين، "
            "الساعة {time}. رد بـ 1 للتأكيد، 2 للإلغاء.")
    if lang == "ar":
        return ar_24 if hours_before >= 12 else ar_2
    return en_24 if hours_before >= 12 else en_2


def render(template: str, ctx: dict) -> str:
    try:
        return template.format(**ctx)
    except Exception:
        return template


def send_text(to_phone: str, body: str) -> dict:
    """Send a WhatsApp text. Returns {'ok': bool, 'provider_id': str, 'simulated': bool}."""
    if PROVIDER == "meta":
        return _send_meta(to_phone, body)
    log.info("[demo-whatsapp] to=%s body=%.80s", to_phone, body)
    return {"ok": True, "provider_id": "", "simulated": True}


def _send_meta(to_phone: str, body: str) -> dict:
    token = os.environ.get("SAAS_WHATSAPP_TOKEN", "")
    pnid = os.environ.get("SAAS_WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not pnid:
        log.error("meta provider selected but SAAS_WHATSAPP_TOKEN/PHONE_NUMBER_ID missing")
        return {"ok": False, "provider_id": "", "simulated": False, "error": "missing_credentials"}
    url = f"https://graph.facebook.com/v21.0/{pnid}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": body},
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        mid = (data.get("messages") or [{}])[0].get("id", "")
        return {"ok": True, "provider_id": mid, "simulated": False}
    except Exception as e:
        log.exception("meta send failed")
        return {"ok": False, "provider_id": "", "simulated": False, "error": str(e)[:200]}


CONFIRM_WORDS = {"1", "yes", "confirm", "confirmed", "ok", "نعم", "تأكيد", "1️⃣"}
CANCEL_WORDS = {"2", "no", "cancel", "cancelled", "canceled", "لا", "إلغاء", "الغاء", "2️⃣"}


def parse_reply(text: str) -> str:
    t = (text or "").strip().lower()
    if t in CONFIRM_WORDS:
        return "confirmed"
    if t in CANCEL_WORDS:
        return "cancelled"
    return "unknown"


def provider_status() -> dict:
    if PROVIDER == "meta":
        ready = bool(os.environ.get("SAAS_WHATSAPP_TOKEN") and
                     os.environ.get("SAAS_WHATSAPP_PHONE_NUMBER_ID"))
        return {"provider": "meta", "ready": ready,
                "note": "Meta Cloud API" + ("" if ready else " — credentials missing")}
    return {"provider": "demo", "ready": True,
            "note": "Demo mode — messages are simulated, no real WhatsApp sending. "
                    "Add Meta API credentials to go live."}
