"""Lead qualification conversation engine.

State machine per lead: intent -> budget -> location -> bedrooms -> timeline -> done.
Scores: HOT (budget+timeline clear, wants viewing) / WARM (partial) / COLD (browsing).
On HOT, the agency owner gets a WhatsApp alert summary.
Bilingual EN/AR.
"""
import logging
import re

from app.saas import whatsapp

from . import db

log = logging.getLogger("leads.qualify")

STAGES = ["intent", "budget", "location", "bedrooms", "timeline", "done"]

BUY_WORDS = {"buy", "buying", "purchase", "purchasing", "own", "شراء", "اشتري", "شقة", "فيلا"}
RENT_WORDS = {"rent", "renting", "rental", "lease", "leasing", "إيجار", "ايجار", "استئجار", "للايجار"}
HOT_TIME = {"asap", "urgent", "immediately", "this week", "this month", "today",
            "عاجل", "فورا", "فوراً", "هذا الأسبوع", "هذا الشهر", "بأسرع"}
VIEW_WORDS = {"viewing", "visit", "see it", "tour", "معاينة", "زيارة", "اشوف"}
BROWSE_WORDS = {"just looking", "browsing", "not sure", "maybe later", "أتفرج", "بس اشوف"}


def detect_lang(text: str, default: str = "en") -> str:
    if re.search(r"[\u0600-\u06FF]", text or ""):
        return "ar"
    return default


def _t(lang: str) -> dict:
    if lang == "ar":
        return {
            "greet": "مرحباً! 👋 شكراً لتواصلك مع {agency}. هل تبحث عن *شراء* أم *إيجار*؟",
            "intent": "هل تبحث عن *شراء* أم *إيجار*؟",
            "budget": "ما هي ميزانيتك التقريبية؟ (مثال: 500K درهم)",
            "location": "في أي منطقة أو مدينة تبحث؟ (مثال: دبي مارينا)",
            "bedrooms": "كم عدد غرف النوم التي تحتاجها؟",
            "timeline": "متى تريد الانتقال أو معاينة العقارات؟",
            "done_hot": "ممتاز! 🎯 مستشارنا سيتواصل معك قريباً لترتيب المعاينة.",
            "done": "شكراً! سجلنا طلبك وسنتواصل معك بالعقارات المناسبة. 🏠",
        }
    return {
        "greet": "Hello! 👋 Thanks for contacting {agency}. Are you looking to *BUY* or *RENT*?",
        "intent": "Are you looking to *BUY* or *RENT*?",
        "budget": "What's your approximate budget? (e.g. 500K AED)",
        "location": "Which area or city are you interested in? (e.g. Dubai Marina)",
        "bedrooms": "How many bedrooms do you need?",
        "timeline": "When would you like to move in or view properties?",
        "done_hot": "Excellent! 🎯 Our consultant will contact you shortly to arrange a viewing.",
        "done": "Thanks! We've noted your requirements and will be in touch with matching properties. 🏠",
    }


def parse_intent(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in BUY_WORDS):
        return "buy"
    if any(w in t for w in RENT_WORDS):
        return "rent"
    return ""


def parse_budget(text: str) -> str:
    t = (text or "").lower().replace(",", "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*([kmb])\b", t)
    if m:
        num, suf = float(m.group(1)), m.group(2)
        mult = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}[suf]
        return f"{num:g}{suf.upper()} (~{int(num*mult):,})"
    m = re.search(r"\d{4,}", t)
    if m:
        return m.group(0)
    return ""


def parse_bedrooms(text: str) -> str:
    m = re.search(r"\d+", text or "")
    if m and 1 <= int(m.group(0)) <= 10:
        return m.group(0)
    t = (text or "").lower()
    if "studio" in t or "استوديو" in t:
        return "studio"
    return ""


def timeline_heat(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in HOT_TIME):
        return "hot"
    if any(w in t for w in BROWSE_WORDS):
        return "cold"
    return "warm"


def score_lead(lead: dict, last_text: str = "") -> str:
    filled = sum(1 for f in ("intent", "budget", "location", "bedrooms", "timeline")
                 if lead.get(f))
    heat = timeline_heat(last_text or lead.get("timeline") or "")
    wants_viewing = any(w in (last_text or "").lower() for w in VIEW_WORDS)
    if (lead.get("budget") and heat == "hot") or (filled >= 4 and wants_viewing):
        return "hot"
    if filled >= 2 or heat == "warm":
        return "warm"
    return "cold"


def get_or_create_lead(agency_id: int, phone: str) -> dict:
    row = db.qone("SELECT * FROM leads WHERE agency_id=? AND phone=? "
                  "ORDER BY id DESC LIMIT 1", (agency_id, phone))
    if row:
        return dict(row)
    cur = db.q(
        "INSERT INTO leads (agency_id, phone, stage, score, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?)",
        (agency_id, phone, "intent", "cold", db.now(), db.now()))
    return dict(db.qone("SELECT * FROM leads WHERE id=?", (cur.lastrowid,)))


def log_msg(lead_id: int, direction: str, body: str):
    db.q("INSERT INTO lead_messages (lead_id, direction, body, created_at)"
         " VALUES (?,?,?,?)", (lead_id, direction, body, db.now()))


def alert_owner(agency: dict, lead: dict):
    owner_phone = (agency.get("whatsapp_number") or agency.get("phone") or "").strip()
    if not owner_phone:
        log.warning("HOT lead but agency %s has no owner WhatsApp", agency["id"])
        return
    body = (f"🔥 HOT LEAD for {agency.get('agency_name') or agency['name']}\n"
            f"Phone: {lead['phone']}\n"
            f"Intent: {lead.get('intent') or '-'} | Budget: {lead.get('budget') or '-'}\n"
            f"Location: {lead.get('location') or '-'} | Beds: {lead.get('bedrooms') or '-'}\n"
            f"Timeline: {lead.get('timeline') or '-'}")
    res = whatsapp.send_text(owner_phone, body)
    log.info("hot-lead alert agency=%s ok=%s simulated=%s",
             agency["id"], res["ok"], res.get("simulated"))


def handle_incoming(agency_id: int, from_phone: str, text: str,
                    agency: dict = None) -> dict:
    """Process one incoming WhatsApp message from a lead. Returns reply info."""
    if agency is None:
        from . import auth as _auth
        agency = _auth.get_agency(agency_id)
    if not agency or not agency["is_active"]:
        return {"ok": False}
    lead = get_or_create_lead(agency_id, from_phone)
    lang = detect_lang(text, agency.get("language") or "en")
    if not lead.get("language") or lead["language"] == "en":
        db.q("UPDATE leads SET language=? WHERE id=?", (lang, lead["id"]))
        lead["language"] = lang
    T = _t(lang)
    log_msg(lead["id"], "in", text or "")
    stage = lead.get("stage") or "intent"

    reply = ""
    updates = {}
    if stage == "intent":
        intent = parse_intent(text)
        if intent:
            updates["intent"] = intent
            updates["stage"] = "budget"
            reply = T["budget"]
        else:
            reply = T["greet"].format(agency=agency.get("agency_name") or agency["name"])
    elif stage == "budget":
        b = parse_budget(text)
        if b:
            updates["budget"] = b
        else:
            updates["budget"] = (text or "").strip()[:120]
        updates["stage"] = "location"
        reply = T["location"]
    elif stage == "location":
        updates["location"] = (text or "").strip()[:120]
        updates["stage"] = "bedrooms"
        reply = T["bedrooms"]
    elif stage == "bedrooms":
        br = parse_bedrooms(text)
        updates["bedrooms"] = br or (text or "").strip()[:40]
        updates["stage"] = "timeline"
        reply = T["timeline"]
    elif stage == "timeline":
        updates["timeline"] = (text or "").strip()[:120]
        updates["stage"] = "done"
        lead.update(updates)
        score = score_lead(lead, text)
        updates["score"] = score
        reply = T["done_hot"] if score == "hot" else T["done"]
    else:  # done — re-engage lightly
        score = score_lead(lead, text)
        updates["score"] = score
        reply = T["done_hot"] if score == "hot" else T["done"]

    if updates:
        sets = ", ".join(f"{k}=?" for k in updates)
        db.q(f"UPDATE leads SET {sets}, updated_at=? WHERE id=?",
             (*updates.values(), db.now(), lead["id"]))
        lead.update(updates)

    if lead.get("score") == "hot" and stage == "timeline":
        # just became hot on this message -> alert owner once
        try:
            alert_owner(agency, lead)
        except Exception:
            log.exception("owner alert failed")

    if reply:
        res = whatsapp.send_text(from_phone, reply)
        log_msg(lead["id"], "out", reply)
    return {"ok": True, "lead_id": lead["id"], "stage": lead.get("stage"),
            "score": lead.get("score"), "reply": reply}
