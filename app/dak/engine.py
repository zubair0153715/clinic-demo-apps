"""Dak engine — deterministic, testable email-triage logic.

No AI here on purpose: priority scoring, category classification,
deadline extraction, thread parsing, snooze math and the draft
Safety Check are pure functions so tests can verify them exactly.
The AI (gemini.py) only ever *generates* triage summaries, thread
summaries and reply drafts from text the USER pastes; it never
sends anything, and its output is validated by validate_ai_*
before it reaches the page.

Priority score (0-100), hand-verifiable:
  base 30
  +20  urgency word present (urgent / ASAP / deadline / emergency / ...)
  +10  direct request to you (can you / please send / please confirm / ...)
  +15  extracted deadline within 48 hours of the reference date
  +2   per extra message in the thread, capped at +10
  -15  FYI / no-action marker
  promotions are capped at 20 (a sale is never urgent)
  clamped to 0-100.

Bands: >=70 "Abhi karo" (do now), 40-69 "Aaj" (today),
20-39 "Is hafte" (this week), <20 "Baad mein" (later).
"""

import math
import re
from datetime import date, timedelta

WPM = 200

PASTE_MIN_CHARS = 100
PASTE_MAX_CHARS = 12000

LANGUAGES = {"en": "English", "roman": "Roman-Urdu", "ur": "Urdu"}

URGENCY_WORDS = [
    "urgent", "asap", "immediately", "emergency", "deadline",
    "time-sensitive", "time sensitive", "critical", "فوری",
]

REQUEST_WORDS = [
    "can you", "could you", "please send", "please share",
    "please confirm", "please review", "please reply",
    "need your", "kindly", "please let me know",
]

FYI_WORDS = [
    "fyi", "for your information", "for your info", "no action",
    "just sharing", "for info only", "no action needed",
]

CATEGORY_RULES = [
    ("finance", ["invoice", "payment", "bill due", "receipt",
                 "salary", "refund", "pkr ", "rs. ", "rs ",
                 "$", "bank transfer", "fee due"]),
    ("jobs", ["interview", "job application", "offer letter",
              "hiring", "shortlisted", "we are pleased to offer",
              "application status", "resume", "cv attached"]),
    ("meetings", ["meeting", "zoom", "google meet", "teams call",
                  "appointment", "agenda", "reschedule",
                  "conference call", "calendar invite"]),
    ("study", ["assignment", "exam", "lecture", "university",
               "marks", "result announced", "semester",
               "thesis", " Viva", "quiz marks"]),
    ("security", ["password reset", "verify your account", "otp",
                  "one-time password", "security alert",
                  "suspicious login", "reset your password"]),
    ("promotions", ["unsubscribe", "newsletter", "% off", "sale ends",
                    "limited offer", "discount code", "view in browser",
                    "shop now", "offer ends"]),
]

CATEGORIES = {
    "finance": "Finance · Paisa",
    "jobs": "Jobs · Naukri",
    "meetings": "Meetings · Mulaqat",
    "study": "Study · Parhai",
    "security": "Security · Hifazat",
    "promotions": "Promotions · Istehaar",
    "general": "General · Aam",
}

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3,
    "march": 3, "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9,
    "september": 9, "oct": 10, "october": 10, "nov": 11,
    "november": 11, "dec": 12, "december": 12,
}

COMMITMENT_WORDS = [
    "i will", "i'll", "i agree", "agreed", "confirmed", "i promise",
    "i'll do", "i can do", "main kar loonga", "main karunga",
    "i accept", "deal", "i'll pay",
]

MONEY_RE = re.compile(
    r"(rs\.?\s?\d[\d,]*|pkr\s?\d[\d,]*|\$\s?\d[\d,]*|"
    r"\d[\d,]*\s?(rupees|pkr|usd))", re.IGNORECASE)

TIME_RE = re.compile(
    r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.IGNORECASE)
TIME_24_RE = re.compile(r"\b([01]\d|2[0-3]):([0-5]\d)\b")

ATTACH_WORDS = ["attached", "attachment", "attach kar", "see attached",
                "file attached"]


def word_count(text):
    """Number of whitespace-separated words in text."""
    return len((text or "").split())


def reading_minutes(words, wpm=WPM):
    """Honest reading time in whole minutes, minimum 1."""
    return max(1, math.ceil(words / wpm))


def validate_paste(text):
    """Validate text pasted for AI triage/drafting.

    Returns (ok, error). Dak triages the text you paste — it never
    claims to read an inbox it has no connection to.
    """
    text = (text or "").strip()
    if len(text) < PASTE_MIN_CHARS:
        return False, (f"Email text thora sa hai — kam az kam "
                       f"{PASTE_MIN_CHARS} characters paste karein.")
    if len(text) > PASTE_MAX_CHARS:
        return False, (f"Email bohat lambi hai — zyada se zyada "
                       f"{PASTE_MAX_CHARS} characters.")
    return True, ""


def classify_category(subject, body):
    """Rule-based category from subject + body keywords.

    First matching rule wins, in CATEGORY_RULES order. Returns a
    category key from CATEGORIES.
    """
    text = f"{subject or ''} {body or ''}".lower()
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return category
    return "general"


def _next_weekday(ref, target):
    """Next date on weekday `target` (0=Mon), on or after ref."""
    days_ahead = (target - ref.weekday()) % 7
    return ref + timedelta(days=days_ahead)


def extract_deadline(text, ref=None):
    """Extract a deadline date from free text.

    ref: date to resolve relative phrases against (default today).
    Returns (date_or_None, phrase_found_or_None, ambiguous_bool).
    Ambiguous dates (e.g. "31 Feb", "kal" meaning yesterday in
    some usage) are returned as (None, phrase, True) — never
    guessed silently.
    """
    ref = ref or date.today()
    low = (text or "").lower()

    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", low)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)),
                        int(m.group(3))), m.group(0), False
        except ValueError:
            return None, m.group(0), True

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", low)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return date(y, mo, d), m.group(0), False
        except ValueError:
            return None, m.group(0), True

    m = re.search(
        r"\b(\d{1,2})\s+(jan|january|feb|february|mar|march|apr|april|"
        r"may|jun|june|jul|july|aug|august|sep|september|oct|october|"
        r"nov|november|dec|december)\b(?:\s+(\d{4}))?", low)
    if m:
        year = int(m.group(3)) if m.group(3) else ref.year
        month = MONTHS[m.group(2)]
        try:
            d = date(year, month, int(m.group(1)))
        except ValueError:
            return None, m.group(0), True
        if d < ref and not m.group(3):
            try:
                d = date(year + 1, month, int(m.group(1)))
            except ValueError:
                return None, m.group(0), True
        return d, m.group(0), False

    m = re.search(
        r"\b(jan|january|feb|february|mar|march|apr|april|"
        r"may|jun|june|jul|july|aug|august|sep|september|oct|october|"
        r"nov|november|dec|december)\s+(\d{1,2})\b(?:\s+(\d{4}))?", low)
    if m:
        year = int(m.group(3)) if m.group(3) else ref.year
        month = MONTHS[m.group(1)]
        try:
            d = date(year, month, int(m.group(2)))
        except ValueError:
            return None, m.group(0), True
        if d < ref and not m.group(3):
            try:
                d = date(year + 1, month, int(m.group(2)))
            except ValueError:
                return None, m.group(0), True
        return d, m.group(0), False

    if "eod" in low or "end of day" in low:
        return ref, "EOD", False
    if "next week" in low or "agle hafte" in low:
        return ref + timedelta(days=7), "next week", False
    if "tomorrow" in low or re.search(r"\bkal\b", low):
        return ref + timedelta(days=1), "tomorrow", False
    if "today" in low or re.search(r"\baaj\b", low):
        return ref, "today", False
    for name, num in WEEKDAYS.items():
        if re.search(rf"\b{name}\b", low):
            return _next_weekday(ref, num), name, False
    return None, None, False


def parse_thread(text):
    """Split pasted email text into messages.

    Splits on common reply separators (From: lines, "On ... wrote:",
    "-----Original Message-----"). Returns a list of dicts with
    keys: sender (or ""), body. The first chunk is the newest
    message. A single message with no separators returns one item.
    """
    text = (text or "").strip()
    if not text:
        return []
    sep_re = re.compile(
        r"(?im)^(?:from:.*$|on .+ wrote:.*$|-{3,}\s*original message\s*-{3,}.*$|"
        r"from:.*\nsent:.*$)",
        re.MULTILINE)
    parts = []
    last = 0
    for m in sep_re.finditer(text):
        chunk = text[last:m.start()].strip()
        if chunk:
            parts.append(chunk)
        last = m.start()
    tail = text[last:].strip()
    if tail:
        parts.append(tail)
    if not parts:
        parts = [text]
    out = []
    for chunk in parts:
        sender = ""
        fm = re.search(r"(?im)^from:\s*(.+)$", chunk)
        if fm:
            sender = fm.group(1).strip()
        else:
            wm = re.search(r"(?i)on .+?,\s*(.+?)\s+wrote:", chunk)
            if wm:
                sender = wm.group(1).strip()
        body = re.sub(r"(?im)^from:.*$", "", chunk).strip()
        body = re.sub(r"(?im)^sent:.*$", "", body).strip()
        body = re.sub(r"(?im)^on .+ wrote:.*$", "", body).strip()
        body = re.sub(r"(?im)^-{3,}\s*original message\s*-{3,}.*$",
                      "", body).strip()
        if not body:
            continue
        out.append({"sender": sender, "body": body})
    return out


def priority_score(subject, body, ref=None, messages=1):
    """Deterministic 0-100 priority score for one email.

    See module docstring for the exact recipe. `messages` is the
    number of messages in the thread (1 = single email).
    """
    ref = ref or date.today()
    text = f"{subject or ''} {body or ''}".lower()
    score = 30
    if any(w in text for w in URGENCY_WORDS):
        score += 20
    if any(w in text for w in REQUEST_WORDS):
        score += 10
    deadline, _, ambiguous = extract_deadline(
        f"{subject or ''} {body or ''}", ref)
    if deadline and not ambiguous and 0 <= (deadline - ref).days <= 2:
        score += 15
    score += min(10, 2 * max(0, (messages or 1) - 1))
    if any(w in text for w in FYI_WORDS):
        score -= 15
    if classify_category(subject, body) == "promotions":
        score = min(score, 20)
    return max(0, min(100, score))


def priority_band(score):
    """Roman-Urdu band label for a priority score."""
    if score >= 70:
        return "Abhi karo"
    if score >= 40:
        return "Aaj"
    if score >= 20:
        return "Is hafte"
    return "Baad mein"


def triage_email(subject, body, ref=None):
    """Full rule-based triage of one email (no key, no network).

    Returns dict: category, category_label, score, band, deadline
    (ISO or None), deadline_phrase, deadline_ambiguous, messages,
    words, minutes.
    """
    ref = ref or date.today()
    messages = parse_thread(body)
    n = len(messages) or 1
    deadline, phrase, ambiguous = extract_deadline(
        f"{subject or ''} {body or ''}", ref)
    score = priority_score(subject, body, ref, messages=n)
    return {
        "category": classify_category(subject, body),
        "category_label": CATEGORIES[classify_category(subject, body)],
        "score": score,
        "band": priority_band(score),
        "deadline": deadline.isoformat() if deadline else None,
        "deadline_phrase": phrase,
        "deadline_ambiguous": ambiguous,
        "messages": n,
        "words": word_count(f"{subject or ''} {body or ''}"),
        "minutes": reading_minutes(
            word_count(f"{subject or ''} {body or ''}")),
    }


def safety_check(draft, thread_text=""):
    """Screen a reply draft before the user sends it.

    Returns a list of flags, each {"code", "message"}. Deterministic:
    odd-hour meetings, commitments/promises, money amounts, and
    attachment mentions. An empty list means no flag fired — it does
    NOT mean the draft is safe to send blindly.
    """
    flags = []
    text = (draft or "")
    low = text.lower()
    ctx = f"{thread_text or ''} {text}".lower()

    odd = False
    for m in TIME_RE.finditer(low):
        hour = int(m.group(1))
        meridiem = m.group(3).lower()
        if meridiem == "am" and hour in (12, 1, 2, 3, 4, 5):
            odd = True
        if meridiem == "pm" and hour == 12 and "midnight" in low:
            odd = True
    for m in TIME_24_RE.finditer(low):
        if int(m.group(1)) < 6:
            odd = True
    if "midnight" in low and ("meet" in low or "call" in low):
        odd = True
    if odd and ("meet" in low or "call" in low or "zoom" in low):
        flags.append({
            "code": "odd_hour",
            "message": ("Raat 12–6 ke beech meeting/call ka zikr hai — "
                        "yeh waqt theek hai ya ghalat likha gaya? "
                        "Superhuman ka Auto Draft bhi aise hi aadhi raat "
                        "ki meeting maan leta tha."),
        })

    if any(w in low for w in COMMITMENT_WORDS):
        flags.append({
            "code": "commitment",
            "message": ("Is draft mein vaada/commitment hai ('I will' / "
                        "'I agree' jaisa) — bhejne se pehle confirm karein "
                        "ke aap waqai yeh kar sakte hain."),
        })

    if MONEY_RE.search(text):
        flags.append({
            "code": "money",
            "message": ("Draft mein raqam likhi hai — amount aur currency "
                        "dobara check karein, ghalat raqam bhejna mehenga "
                        "parta hai."),
        })

    if any(w in low for w in ATTACH_WORDS) or any(
            w in ctx for w in ATTACH_WORDS):
        flags.append({
            "code": "attachment",
            "message": ("Attachment ka zikr hai — kya file waqai attach "
                        "ki hai? Bina attachment ke 'attached' likhna "
                        "aam ghalti hai."),
        })

    caps = re.findall(r"\b[A-Z]{4,}\b", text)
    if len(caps) >= 2 or text.count("!") >= 3:
        flags.append({
            "code": "tone",
            "message": ("Lehja tez lag raha hai (caps ya !!!) — gusse "
                        "wala email thanda ho kar dobara parhein, phir "
                        "bhejein."),
        })
    return flags


def snooze_until(days, ref=None):
    """ISO date `days` after ref (default today)."""
    ref = ref or date.today()
    if isinstance(ref, str):
        ref = date.fromisoformat(ref)
    return (ref + timedelta(days=int(days))).isoformat()


def followup_due(sent, days=3):
    """ISO date a follow-up is due: sent date + days."""
    if isinstance(sent, str):
        sent = date.fromisoformat(sent)
    return (sent + timedelta(days=int(days))).isoformat()


def validate_ai_triage(result):
    """Validate an AI triage result before it reaches the page.

    Returns a list of errors (empty = usable). Shape only.
    """
    errors = []
    if not isinstance(result, dict):
        return ["AI ka jawab samajh nahi aaya (galat format)."]
    if result.get("category") not in CATEGORIES:
        errors.append("AI category ghalat hai.")
    if not isinstance(result.get("score"), int) or not (
            0 <= result["score"] <= 100):
        errors.append("AI score 0–100 ke beech hona chahiye.")
    summary = (result.get("summary") or "").strip()
    if word_count(summary) < 5:
        errors.append("AI summary bohat chhoti hai.")
    if word_count(summary) > 120:
        errors.append("AI summary bohat lambi hai.")
    actions = result.get("actions") or []
    if not isinstance(actions, list) or len(actions) < 1:
        errors.append("AI se kam az kam 1 action chahiye tha.")
    elif len(actions) > 5:
        errors.append("AI se zyada se zyada 5 actions chahiye the.")
    return errors


def validate_ai_draft(result):
    """Validate an AI reply draft before it reaches the page."""
    errors = []
    if not isinstance(result, dict):
        return ["AI ka jawab samajh nahi aaya (galat format)."]
    draft = (result.get("draft") or "").strip()
    if word_count(draft) < 5:
        errors.append("AI draft bohat chhota hai.")
    if word_count(draft) > 400:
        errors.append("AI draft bohat lamba hai.")
    if not result.get("tone"):
        errors.append("AI draft ka tone missing hai.")
    return errors


def validate_ai_thread(result):
    """Validate an AI thread summary before it reaches the page."""
    errors = []
    if not isinstance(result, dict):
        return ["AI ka jawab samajh nahi aaya (galat format)."]
    summary = (result.get("summary") or "").strip()
    if word_count(summary) < 20:
        errors.append("AI thread summary bohat chhoti hai.")
    if word_count(summary) > 600:
        errors.append("AI thread summary bohat lambi hai.")
    decisions = result.get("decisions") or []
    questions = result.get("open_questions") or []
    actions = result.get("actions") or []
    for name, value in (("decisions", decisions),
                        ("open_questions", questions),
                        ("actions", actions)):
        if not isinstance(value, list):
            errors.append(f"AI {name} list honi chahiye thi.")
    for item in actions:
        if not isinstance(item, dict) or not item.get("text"):
            errors.append("AI action mein text missing hai.")
    return errors
