"""Conversation engine for the clinic AI receptionist (provider-agnostic).

State machine, bilingual EN/AR, keyword intent detection. No ML, no network —
works on the demo provider and identically on the real Meta provider.
"""
import datetime as dt
import re

# ------------------------------------------------------------------ clinic --
CLINIC = {
    "name": "Pearl Smile Dental Clinic",
    "name_ar": "عيادة بيرل سمايل لطب الأسنان",
    "city": "Dubai",
    "address": "JLT Cluster D, Dubai, UAE",
    "address_ar": "أبراج بحيرات الجميرا، عنقود D، دبي",
    "phone": "+971 4 123 4567",
    "hours_en": "Sat–Thu 9:00 AM – 9:00 PM, Fri 4:00 PM – 9:00 PM",
    "hours_ar": "السبت–الخميس 9 صباحاً – 9 مساءً، الجمعة 4 – 9 مساءً",
}

SERVICES = [
    ("cleaning", "Dental Cleaning", "تنظيف الأسنان", "AED 350"),
    ("whitening", "Teeth Whitening", "تبييض الأسنان", "AED 1,200"),
    ("braces", "Braces / Orthodontics", "تقويم الأسنان", "from AED 9,000"),
    ("implant", "Dental Implant", "زراعة الأسنان", "from AED 3,500"),
    ("rootcanal", "Root Canal", "علاج الجذور", "from AED 1,500"),
    ("filling", "Filling", "حشوة", "AED 400"),
    ("checkup", "General Checkup", "فحص عام", "FREE this month"),
]
SERVICE_KEYS = {s[0]: s for s in SERVICES}

# ------------------------------------------------------------------ i18n ---
AR_RE = re.compile(r"[\u0600-\u06FF]")

T = {
    "greeting": {
        "en": ("Hello! Welcome to {clinic} 😊 I can help you book an appointment, "
               "or answer questions about our treatments, prices and timings. "
               "How can I help you today?"),
        "ar": ("مرحباً بك في {clinic} 😊 يمكنني مساعدتك في حجز موعد أو الإجابة عن "
               "أسئلتك حول العلاجات والأسعار وأوقات الدوام. كيف أقدر أساعدك اليوم؟"),
    },
    "ask_service": {
        "en": "Which treatment do you need?",
        "ar": "ما العلاج الذي تحتاجه؟",
    },
    "ask_day": {
        "en": "Which day works for you? (e.g. tomorrow, Monday, 20/10)",
        "ar": "أي يوم يناسبك؟ (مثال: بكرا، الاثنين، 20/10)",
    },
    "ask_time": {
        "en": "Morning, afternoon or evening — or tell me a time like 10:30 AM?",
        "ar": "صباحاً أم ظهراً أم مساءً — أو حدد الوقت مثل 10:30 صباحاً؟",
    },
    "ask_name": {
        "en": "May I have your name please?",
        "ar": "ممكن اسمك الكريم؟",
    },
    "ask_phone": {
        "en": "And your mobile number so we can confirm the booking?",
        "ar": "ورقم الجوال لتأكيد الحجز؟",
    },
    "confirm": {
        "en": ("Please confirm your booking:\n🦷 {service}\n📅 {date}\n🕙 {time}\n"
               "👤 {name}\n📱 {phone}\n\nReply YES to confirm or NO to change."),
        "ar": ("يرجى تأكيد حجزك:\n🦷 {service}\n📅 {date}\n🕙 {time}\n"
               "👤 {name}\n📱 {phone}\n\nرد بـ نعم للتأكيد أو لا للتعديل."),
    },
    "booked": {
        "en": ("✅ Done! Your appointment is booked. We'll send a WhatsApp reminder "
               "24 hours before. See you soon at {clinic}!"),
        "ar": ("✅ تم! تم حجز موعدك بنجاح. سنرسل لك تذكيراً على واتساب قبل الموعد بـ 24 "
               "ساعة. نراك قريباً في {clinic}!"),
    },
    "restart": {
        "en": "No problem — let's start over. What would you like to do?",
        "ar": "لا مشكلة — لنبدأ من جديد. ماذا تريد أن تفعل؟",
    },
    "hours": {
        "en": "🕙 We're open {hours}.",
        "ar": "🕙 أوقات الدوام: {hours}.",
    },
    "location": {
        "en": "📍 You'll find us at {address}. Call us: {phone}.",
        "ar": "📍 موقعنا: {address}. هاتف: {phone}.",
    },
    "services_list": {
        "en": "🦷 Our treatments:\n{lines}",
        "ar": "🦷 علاجاتنا:\n{lines}",
    },
    "human": {
        "en": ("Of course — I've flagged your request for our front-desk team. "
               "They'll message you here shortly. Anything else I can help with meanwhile?"),
        "ar": ("بالتأكيد — تم تحويل طلبك إلى فريق الاستقبال وسيتواصلون معك هنا قريباً. "
               "هل أقدر أساعدك بشيء ثانٍ؟"),
    },
    "reschedule_ask": {
        "en": "Sure — what's the new day you'd like? (e.g. tomorrow, Friday, 22/10)",
        "ar": "بالتأكيد — ما اليوم الجديد الذي يناسبك؟ (مثال: بكرا، الجمعة، 22/10)",
    },
    "reschedule_done": {
        "en": ("📝 Noted! I've sent your reschedule request to our team — they'll confirm "
               "the new slot with you shortly here on WhatsApp."),
        "ar": ("📝 تم! أرسلت طلب تعديل الموعد إلى فريقنا — سيؤكدون لك الموعد الجديد "
               "قريباً هنا على واتساب."),
    },
    "cancel_done": {
        "en": ("Your appointment has been cancelled. If you'd like to rebook later, "
               "just say 'book'. Take care! 🌸"),
        "ar": ("تم إلغاء موعدك. إذا أردت الحجز مجدداً لاحقاً، فقط قل 'احجز'. مع السلامة! 🌸"),
    },
    "fallback": {
        "en": ("I want to make sure I help you correctly — did you want to *book* an "
               "appointment, ask about *prices*, *timings*, or talk to a *human*?"),
        "ar": ("أريد التأكد من مساعدتك بالشكل الصحيح — هل تريد *حجز* موعد، السؤال عن "
               "*الأسعار*، *أوقات الدوام*، أو التحدث مع *موظف*؟"),
    },
    "price_prefix": {"en": "💰 ", "ar": "💰 "},
}

YES = {"yes", "y", "ok", "confirm", "confirmed", "1", "نعم", "اي", "أي", "تم", "اوك", "أوك"}
NO = {"no", "n", "2", "لا", "لأ"}

# --------------------------------------------------------------- intents ---
def detect_lang(text: str) -> str:
    return "ar" if AR_RE.search(text or "") else "en"


def _has(t: str, *words: str) -> bool:
    return any(w in t for w in words)


def detect_intent(text: str) -> str:
    t = (text or "").strip().lower()
    if not t:
        return "fallback"
    if _has(t, "human", "agent", "person", "staff", "someone", "call me",
            "موظف", "انسان", "إنسان", "شخص", "بشر", "اتصل"):
        return "human"
    if _has(t, "reschedul", "postpone", "change appointment", "change my appointment",
            "تأجيل", "تغيير الموعد", "اغير الموعد", "أغير الموعد", "اجل الموعد", "أجل الموعد"):
        return "reschedule"
    if _has(t, "cancel", "إلغاء", "الغاء", "الغي", "ألغي"):
        return "cancel"
    if _has(t, "book", "appointment", "reserve", "slot", "visit",
            "احجز", "حجز", "موعد", "اريد موعد", "أريد موعد", "بدي موعد"):
        return "book"
    if _has(t, "price", "cost", "how much", "charge", "fee",
            "سعر", "أسعار", "اسعار", "تكلفة", "بكم", "كم سعر"):
        return "price"
    if _has(t, "hour", "timing", "open", "close", "when", "working",
            "أوقات", "اوقات", "ساعات", "دوام", "متى تفتح", "مفتوح"):
        return "hours"
    if _has(t, "where", "address", "location", "direction", "map",
            "أين", "اين", "موقع", "عنوان", "وين"):
        return "location"
    if _has(t, "treatment", "service", "offer", "do you do",
            "علاج", "علاجات", "خدمات", "خدمة"):
        return "services"
    if _has(t, "hi", "hello", "hey", "salam", "good morning", "good evening",
            "مرحبا", "أهلا", "اهلا", "هلا", "السلام", "صباح الخير", "مساء الخير"):
        return "greeting"
    return "fallback"


# ------------------------------------------------------------ date/time ---
WEEKDAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday",
               "saturday", "sunday"]
WEEKDAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الاربعاء", "الخميس",
               "الجمعة", "السبت", "الأحد", "الاحد"]


def parse_day(text: str, today: dt.date | None = None):
    """Return a date or None. Handles today/tomorrow, weekday names EN/AR, DD/MM."""
    today = today or dt.date.today()
    t = (text or "").strip().lower()
    if _has(t, "today", "اليوم"):
        return today
    if _has(t, "tomorrow", "غدا", "غداً", "بكرا", "بكره"):
        return today + dt.timedelta(days=1)
    for i, name in enumerate(WEEKDAYS_EN):
        if name in t or name[:3] in t.split():
            delta = (i - today.weekday()) % 7 or 7
            return today + dt.timedelta(days=delta)
    for i, name in enumerate(WEEKDAYS_AR):
        if name in t:
            delta = (i - today.weekday()) % 7 or 7
            return today + dt.timedelta(days=delta)
    m = re.search(r"(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?", t)
    if m:
        d, mo = int(m.group(1)), int(m.group(2))
        yr = int(m.group(3)) if m.group(3) else today.year
        if yr < 100:
            yr += 2000
        try:
            cand = dt.date(yr, mo, d)
        except ValueError:
            return None
        if cand < today:  # assume next year if passed
            try:
                cand = dt.date(yr + 1, mo, d)
            except ValueError:
                return None
        return cand
    return None


def parse_time(text: str) -> str | None:
    t = (text or "").strip().lower()
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|صباحا|صباحاً|مساء|مساءً)?", t)
    if m:
        h = int(m.group(1))
        mi = int(m.group(2) or 0)
        ap = m.group(3)
        if ap in ("pm", "مساء", "مساءً"):
            if h < 12:
                h += 12
        elif ap in ("am", "صباحا", "صباحاً"):
            if h == 12:
                h = 0
        elif h > 23:
            return None
        return f"{h:02d}:{mi:02d}"
    if _has(t, "morning", "صباح", "الصبح"):
        return "10:00"
    if _has(t, "afternoon", "ظهر", "بعد الظهر", "العصر"):
        return "14:00"
    if _has(t, "evening", "night", "مساء", "المسا"):
        return "18:00"
    return None


def fmt_date(d: dt.date, lang: str) -> str:
    if lang == "ar":
        days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة",
                "السبت", "الأحد"]
        months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                  "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
        return f"{days[d.weekday()]} {d.day} {months[d.month - 1]}"
    return d.strftime("%A, %d %B %Y")


def fmt_time(hhmm: str, lang: str) -> str:
    h, m = map(int, hhmm.split(":"))
    if lang == "ar":
        ap = "صباحاً" if h < 12 else "مساءً"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {ap}"
    ap = "AM" if h < 12 else "PM"
    return f"{h % 12 or 12}:{m:02d} {ap}"


def match_service(text: str):
    t = (text or "").lower()
    for key, en, ar, price in SERVICES:
        if key in t or en.lower() in t or ar in t:
            return key
    # loose keywords
    if _has(t, "clean", "تنظيف"):
        return "cleaning"
    if _has(t, "whit", "تبييض", "هوليود", "hollywood"):
        return "whitening"
    if _has(t, "brace", "orthodont", "تقويم"):
        return "braces"
    if _has(t, "implant", "زراع", "غرس"):
        return "implant"
    if _has(t, "root canal", "عصب", "جذور"):
        return "rootcanal"
    if _has(t, "fill", "حشو"):
        return "filling"
    if _has(t, "checkup", "check up", "فحص", "كشف"):
        return "checkup"
    return None


# ------------------------------------------------------------------ engine --
class Engine:
    """Pure state machine. Session state is a dict the caller persists."""

    def new_session(self, lang: str = "en") -> dict:
        return {"lang": lang, "flow": "idle", "slots": {}, "done": False}

    # -- helpers -----------------------------------------------------------
    def _t(self, key: str, lang: str, **kw) -> str:
        s = T[key][lang]
        ctx = {"clinic": CLINIC["name_ar"] if lang == "ar" else CLINIC["name"],
               "hours": CLINIC["hours_ar"] if lang == "ar" else CLINIC["hours_en"],
               "address": CLINIC["address_ar"] if lang == "ar" else CLINIC["address"],
               "phone": CLINIC["phone"]}
        ctx.update(kw)
        return s.format(**ctx)

    def _quick(self, lang: str, flow: str):
        if flow == "book_service":
            return [s[2] if lang == "ar" else s[1] for s in SERVICES]
        if flow == "book_day":
            return ["Today", "Tomorrow"] if lang == "en" else ["اليوم", "بكرا"]
        if flow == "book_time":
            return (["Morning", "Afternoon", "Evening"] if lang == "en"
                    else ["صباحاً", "ظهراً", "مساءً"])
        if flow == "confirm":
            return ["YES", "NO"] if lang == "en" else ["نعم", "لا"]
        return []

    def _answer_price(self, text: str, lang: str) -> str:
        key = match_service(text)
        lines = []
        targets = [SERVICE_KEYS[key]] if key else SERVICES
        for _, en, ar, price in targets:
            label = ar if lang == "ar" else en
            lines.append(f"• {label}: {price}")
        head = ("Here are our prices:" if lang == "en" else "هذه أسعارنا:")
        tail = ("\n\nWant me to book you in? Just say 'book'."
                if lang == "en" else "\n\nتريد الحجز؟ فقط قل 'احجز'.")
        return head + "\n" + "\n".join(lines) + tail

    # -- main --------------------------------------------------------------
    def handle(self, session: dict, text: str):
        """Returns (reply, quick_replies, event) where event may carry lead data."""
        lang = session.get("lang") or detect_lang(text)
        session["lang"] = lang
        flow = session.get("flow", "idle")
        slots = session.setdefault("slots", {})
        event = None

        # --- in-flow steps -------------------------------------------------
        if flow == "book_service":
            key = match_service(text)
            if key:
                slots["service"] = key
                session["flow"] = "book_day"
                return self._t("ask_day", lang), self._quick(lang, "book_day"), None
            return ((self._t("ask_service", lang)),
                    self._quick(lang, "book_service"), None)

        if flow == "book_day":
            d = parse_day(text)
            if d:
                slots["date"] = d.isoformat()
                session["flow"] = "book_time"
                return self._t("ask_time", lang), self._quick(lang, "book_time"), None
            retry = ("Which day? Try 'tomorrow', 'Friday' or a date like 22/10."
                     if lang == "en" else
                     "أي يوم؟ جرّب 'بكرا' أو 'الجمعة' أو تاريخ مثل 22/10.")
            return retry, self._quick(lang, "book_day"), None

        if flow == "book_time":
            tm = parse_time(text)
            if tm:
                slots["time"] = tm
                session["flow"] = "book_name"
                return self._t("ask_name", lang), [], None
            retry = ("What time? e.g. 10:30 AM, or morning/afternoon/evening."
                     if lang == "en" else
                     "أي وقت؟ مثال: 10:30 صباحاً، أو صباحاً/ظهراً/مساءً.")
            return retry, self._quick(lang, "book_time"), None

        if flow == "book_name":
            name = (text or "").strip()
            if len(name) >= 2:
                slots["name"] = name[:60]
                session["flow"] = "book_phone"
                return self._t("ask_phone", lang), [], None
            return self._t("ask_name", lang), [], None

        if flow == "book_phone":
            digits = re.sub(r"\D", "", text or "")
            if len(digits) >= 7:
                slots["phone"] = digits[-15:]
                session["flow"] = "confirm"
                svc = SERVICE_KEYS[slots["service"]]
                d = dt.date.fromisoformat(slots["date"])
                reply = self._t(
                    "confirm", lang,
                    service=svc[2] if lang == "ar" else svc[1],
                    date=fmt_date(d, lang), time=fmt_time(slots["time"], lang),
                    name=slots["name"], phone=slots["phone"])
                return reply, self._quick(lang, "confirm"), None
            retry = ("Please share a valid mobile number."
                     if lang == "en" else "يرجى مشاركة رقم جوال صحيح.")
            return retry, [], None

        if flow == "confirm":
            t = (text or "").strip().lower()
            if t in YES:
                session["flow"] = "idle"
                session["done"] = True
                event = {"type": "lead", "intent": "book", "slots": dict(slots)}
                return self._t("booked", lang), [], event
            if t in NO:
                session["flow"] = "idle"
                session["slots"] = {}
                return self._t("restart", lang), [], None
            return self._t("confirm", lang,
                           service="", date="", time="", name="", phone=""), \
                self._quick(lang, "confirm"), None

        if flow == "reschedule_day":
            d = parse_day(text)
            if d:
                session["flow"] = "idle"
                event = {"type": "lead", "intent": "reschedule",
                         "slots": {"date": d.isoformat(), "lang": lang}}
                return self._t("reschedule_done", lang), [], event
            return self._t("reschedule_ask", lang), [], None

        # --- idle: intent routing ------------------------------------------
        intent = detect_intent(text)

        if intent == "greeting":
            return self._t("greeting", lang), [], None
        if intent == "book":
            session["flow"] = "book_service"
            return self._t("ask_service", lang), self._quick(lang, "book_service"), None
        if intent == "reschedule":
            session["flow"] = "reschedule_day"
            return self._t("reschedule_ask", lang), [], None
        if intent == "cancel":
            event = {"type": "lead", "intent": "cancel", "slots": {"lang": lang}}
            return self._t("cancel_done", lang), [], event
        if intent == "hours":
            return self._t("hours", lang), [], None
        if intent == "location":
            return self._t("location", lang), [], None
        if intent == "services":
            lines = [f"• {(s[2] if lang == 'ar' else s[1])}: {s[3]}" for s in SERVICES]
            return self._t("services_list", lang, lines="\n".join(lines)), [], None
        if intent == "price":
            return self._answer_price(text, lang), [], None
        if intent == "human":
            event = {"type": "lead", "intent": "handoff",
                     "slots": {"lang": lang, "last_message": (text or "")[:200]}}
            return self._t("human", lang), [], None
        return self._t("fallback", lang), [], None
