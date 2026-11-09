"""Sathi engine — gentle self-care companion (Finch gap build).

Pure, deterministic logic. No network, no storage, no key needed.

The core idea, and the whole point of the app: a self-care loop
that NEVER punishes. Finch's most-loved feature — streaks — is also
its most complained-about one (users: "Now all I do is box ticking
before bed! I really hate these apps with streaks"). So Sathi's
streak is gentle by design:

* a "care day" is any day you checked in or finished a habit;
* ONE rest day in a streak run never breaks it (and never counts);
* a second missed day ends the run — but the run is only a number,
  and the pet grows on TOTAL care days too, so nothing is ever lost;
* streaks can be switched off entirely (the pet still grows).

Care points: check-in 1, each habit done 1, gratitude 1, breathing
1. Daily cap 8 — the pet grows on steady care, not binge-ticking.
"""

from datetime import date, timedelta

LANGUAGES = ["en", "roman", "ur"]

# --- points ----------------------------------------------------------------
CHECKIN_POINTS = 1
HABIT_POINTS = 1
GRATITUDE_POINTS = 1
BREATHING_POINTS = 1
DAILY_POINT_CAP = 8

# --- pet growth: care points -> stage --------------------------------------
# Jugnu the firefly: Egg -> Spark -> Glow -> Bright -> Radiant.
PET_STAGES = [
    {"id": "egg", "min_points": 0,
     "name_en": "Egg", "name_roman": "Anda", "name_ur": "انڈا",
     "glow": 0, "blurb_en": "Jugnu is resting, waiting for your first check-in."},
    {"id": "spark", "min_points": 7,
     "name_en": "Spark", "name_roman": "Chingaari", "name_ur": "چنگاری",
     "glow": 1, "blurb_en": "A tiny light! Jugnu woke up because you showed up."},
    {"id": "glow", "min_points": 21,
     "name_en": "Glow", "name_roman": "Roshni", "name_ur": "روشنی",
     "glow": 2, "blurb_en": "Jugnu glows softly now — three weeks of care."},
    {"id": "bright", "min_points": 46,
     "name_en": "Bright", "name_roman": "Ujala", "name_ur": "اجالا",
     "glow": 3, "blurb_en": "Jugnu lights up the whole evening. Steady care."},
    {"id": "radiant", "min_points": 91,
     "name_en": "Radiant", "name_roman": "Noorani", "name_ur": "نورانی",
     "glow": 4, "blurb_en": "Jugnu shines bright — 13 weeks of looking after yourself."},
]


def pet_stage(points):
    """Stage for a lifetime care-points total. Returns (stage, error)."""
    if not isinstance(points, int) or isinstance(points, bool) or points < 0:
        return None, "Points 0 ya zyada, poora number hona chahiye."
    stage = PET_STAGES[0]
    for s in PET_STAGES:
        if points >= s["min_points"]:
            stage = s
    idx = PET_STAGES.index(stage)
    nxt = PET_STAGES[idx + 1] if idx + 1 < len(PET_STAGES) else None
    return {"id": stage["id"], "points": points,
            "name_en": stage["name_en"], "name_roman": stage["name_roman"],
            "name_ur": stage["name_ur"], "glow": stage["glow"],
            "blurb_en": stage["blurb_en"],
            "next_stage": (nxt["id"] if nxt else None),
            "points_to_next": (nxt["min_points"] - points if nxt else 0),
            "max_stage": nxt is None}, None


def care_points(checkin=False, habits_done=0, gratitude=False, breathing=False):
    """Points earned today for one day of actions, capped at 8.

    Returns (result, error). habits_done is the count of habits
    finished today (0-20). Each action is worth 1 point.
    """
    if not isinstance(habits_done, int) or isinstance(habits_done, bool) \
            or habits_done < 0 or habits_done > 20:
        return None, "Habits 0 se 20 ke beech hone chahiye."
    raw = (CHECKIN_POINTS if checkin else 0) \
        + habits_done * HABIT_POINTS \
        + (GRATITUDE_POINTS if gratitude else 0) \
        + (BREATHING_POINTS if breathing else 0)
    points = min(raw, DAILY_POINT_CAP)
    return {"raw": raw, "points": points, "capped": raw > DAILY_POINT_CAP,
            "checkin": bool(checkin), "habits_done": habits_done,
            "gratitude": bool(gratitude), "breathing": bool(breathing)}, None


# --- dates / gentle streak --------------------------------------------------
def parse_iso(text):
    """'YYYY-MM-DD' -> date, or None."""
    if not isinstance(text, str):
        return None
    try:
        y, m, d = (int(p) for p in text.strip().split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def gentle_streak(care_days, rest_days, today):
    """Gentle care streak ending at (or just before) `today`.

    care_days / rest_days: lists of 'YYYY-MM-DD' strings (duplicates
    and bad values ignored). today: 'YYYY-MM-DD'.

    Rules, exactly as promised on the page:
    * walk backwards from today; if today is not a care/rest day yet,
      start from yesterday (a streak is never "broken" by today
      simply not being over yet);
    * a care day adds 1 to the streak;
    * ONE rest day inside the run is forgiven (adds 0, does not break);
    * a second missed day (neither care nor rest, or a second rest
      day) ends the run;
    * the run must contain at least one care day.

    Returns (result, error). result: streak_days, rest_used (0/1),
    anchor (the date the run ends on), total_care_days.
    """
    anchor = parse_iso(today)
    if anchor is None:
        return None, "Aaj ki tareekh 'YYYY-MM-DD' format me likhein."
    care = {parse_iso(x) for x in (care_days or []) if parse_iso(x)}
    rest = {parse_iso(x) for x in (rest_days or []) if parse_iso(x)}
    # a day cannot be both; care wins
    rest -= care
    day = anchor
    if day not in care and day not in rest:
        day = anchor - timedelta(days=1)
    streak = 0
    rest_used = 0
    while True:
        if day in care:
            streak += 1
        elif day in rest and rest_used == 0:
            rest_used = 1
        else:
            break
        day -= timedelta(days=1)
        # a run cannot be longer than the data; safety cap 3660 days
        if streak + rest_used > 3660:
            break
    return {"streak_days": streak, "rest_used": rest_used,
            "anchor": day + timedelta(days=1) if streak or rest_used
            else anchor.isoformat(),
            "total_care_days": len(care)}, None


# --- mood -------------------------------------------------------------------
MOOD_WORDS = ["bohot kharab", "kharab", "theek", "acha", "bohot acha"]


def mood_average(entries):
    """7-day (or fewer) mood summary from [{date, mood 1-5}].

    Returns (result, error). Average is rounded to 1 decimal.
    Trend compares the last 3 entries with the 3 before them:
    up / down / steady (needs 4+ entries, else 'not-enough-data').
    """
    if not isinstance(entries, list):
        return None, "Entries list honi chahiye."
    clean = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        m = e.get("mood")
        if isinstance(m, bool) or not isinstance(m, int) or not 1 <= m <= 5:
            continue
        d = parse_iso(e.get("date", ""))
        if d is None:
            continue
        clean.append({"date": d, "mood": m})
    if not clean:
        return None, "Koi valid mood entry nahi mili."
    clean.sort(key=lambda x: x["date"])
    recent = clean[-7:]
    avg = round(sum(x["mood"] for x in recent) / len(recent), 1)
    best = max(recent, key=lambda x: x["mood"])
    if len(clean) >= 4:
        last3 = [x["mood"] for x in clean[-3:]]
        prev3 = [x["mood"] for x in clean[-6:-3]] or [x["mood"] for x in clean[:-3]]
        diff = sum(last3) / len(last3) - sum(prev3) / len(prev3)
        trend = "up" if diff >= 0.5 else "down" if diff <= -0.5 else "steady"
    else:
        trend = "not-enough-data"
    return {"count": len(recent), "average": avg,
            "word": MOOD_WORDS[int(round(avg)) - 1],
            "trend": trend,
            "best_day": best["date"].isoformat(), "best_mood": best["mood"]}, None


def validate_gratitude(items):
    """1-3 gratitude items, each 1-140 chars. Returns (items, error)."""
    if not isinstance(items, list) or not 1 <= len(items) <= 3:
        return None, "Shukrana 1 se 3 cheezein honi chahiye."
    clean = []
    for it in items:
        if not isinstance(it, str) or not it.strip() or len(it.strip()) > 140:
            return None, "Har shukrana 1 se 140 harf ka hona chahiye."
        clean.append(it.strip())
    return clean, None


# --- journeys (the organisation Finch paywalls — free here) ------------------
JOURNEYS = {
    "subah": {
        "title_en": "Subah (Morning)", "title_roman": "Subah",
        "title_ur": "صبح",
        "habits": [
            {"id": "fajr", "en": "Fajr prayer", "roman": "Fajr ki namaz",
             "ur": "فجر کی نماز"},
            {"id": "water", "en": "A glass of water", "roman": "Ek glass paani",
             "ur": "ایک گلاس پانی"},
            {"id": "walk", "en": "10-minute walk", "roman": "10 minute walk",
             "ur": "۱۰ منٹ چہل قدمی"},
            {"id": "plan", "en": "Plan the day in 3 lines", "roman": "Din ki 3-line plan",
             "ur": "دن کا ۳ سطری منصوبہ"},
        ]},
    "neend": {
        "title_en": "Neend (Sleep)", "title_roman": "Neend",
        "title_ur": "نیند",
        "habits": [
            {"id": "isha", "en": "Isha prayer", "roman": "Isha ki namaz",
             "ur": "عشا کی نماز"},
            {"id": "screens", "en": "Screens off 30 min before bed",
             "roman": "Sone se 30 min pehle screens band",
             "ur": "سونے سے ۳۰ منٹ پہلے اسکرین بند"},
            {"id": "dhikr", "en": "Dhikr before sleep", "roman": "Sone se pehle dhikr",
             "ur": "سونے سے پہلے ذکر"},
            {"id": "bedtime", "en": "In bed on time", "roman": "Waqt par bistar",
             "ur": "وقت پر بستر"},
        ]},
    "sehat": {
        "title_en": "Sehat (Health)", "title_roman": "Sehat",
        "title_ur": "صحت",
        "habits": [
            {"id": "exercise", "en": "20 minutes of movement",
             "roman": "20 minute harkat", "ur": "۲۰ منٹ حرکت"},
            {"id": "fruit", "en": "A fruit or salad", "roman": "Ek phal ya salad",
             "ur": "ایک پھل یا سلاد"},
            {"id": "water8", "en": "8 glasses of water", "roman": "8 glass paani",
             "ur": "۸ گلاس پانی"},
            {"id": "no-sugar", "en": "No sugary drink today",
             "roman": "Aaj koi meetha drink nahi", "ur": "آج کوئی میٹھا مشروب نہیں"},
        ]},
    "ibadat": {
        "title_en": "Ibadat (Worship)", "title_roman": "Ibadat",
        "title_ur": "عبادت",
        "habits": [
            {"id": "prayers", "en": "All 5 prayers", "roman": "5 waqt ki namaz",
             "ur": "۵ وقت کی نماز"},
            {"id": "quran", "en": "Read a page of Quran",
             "roman": "Quran ka ek safha", "ur": "قرآن کا ایک صفحہ"},
            {"id": "tasbih", "en": "Tasbih 100 times", "roman": "100 martaba tasbih",
             "ur": "۱۰۰ مرتبہ تسبیح"},
            {"id": "dua", "en": "Dua for someone else",
             "roman": "Kisi aur ke liye dua", "ur": "کسی اور کے لیے دعا"},
        ]},
    "kaam": {
        "title_en": "Kaam (Work & Study)", "title_roman": "Kaam",
        "title_ur": "کام",
        "habits": [
            {"id": "focus", "en": "One 25-minute focus block",
             "roman": "25 minute focus", "ur": "۲۵ منٹ توجہ"},
            {"id": "learn", "en": "Learn one new thing",
             "roman": "Ek nayi cheez seekhein", "ur": "ایک نئی چیز سیکھیں"},
            {"id": "tidy", "en": "Tidy the desk for 5 minutes",
             "roman": "5 minute desk saaf", "ur": "۵ منٹ میز صاف"},
            {"id": "review", "en": "Review tomorrow's first task",
             "roman": "Kal ka pehla kaam dekh lein",
             "ur": "کل کا پہلا کام دیکھ لیں"},
        ]},
}


def journey_list():
    """All journeys with habit counts, for the page."""
    out = []
    for jid, j in JOURNEYS.items():
        out.append({"id": jid, "title_en": j["title_en"],
                    "title_roman": j["title_roman"], "title_ur": j["title_ur"],
                    "habits": len(j["habits"])})
    return out


def journey_habits(journey_id):
    """Habits of one journey. Returns (habits, error)."""
    j = JOURNEYS.get(journey_id)
    if j is None:
        return None, "Journey nahi mili — list me se chunein."
    return [{"id": h["id"], "en": h["en"], "roman": h["roman"],
             "ur": h["ur"]} for h in j["habits"]], None


# --- breathing (one gentle pattern: 4-7-8, 19 s per cycle) -------------------
BREATHING = {"pattern": "478", "inhale": 4, "hold": 7, "exhale": 8,
             "cycle_seconds": 19}


def breathing_schedule(cycles):
    """4-7-8 schedule: list of phases with start/end seconds.

    Returns (schedule, error). cycles 1-10.
    """
    if not isinstance(cycles, int) or isinstance(cycles, bool) \
            or not 1 <= cycles <= 10:
        return None, "Cycles 1 se 10 ke beech hone chahiye."
    sched = []
    t = 0
    for c in range(1, cycles + 1):
        for phase, label, secs in (
                ("inhale", "Saans andar", 4),
                ("hold", "Rokein", 7),
                ("exhale", "Saans bahar", 8)):
            sched.append({"cycle": c, "phase": phase, "label": label,
                          "seconds": secs, "start": t, "end": t + secs})
            t += secs
    return {"pattern": "478", "cycles": cycles, "total_seconds": t,
            "breaths_per_minute": round(60 / 19, 1),
            "schedule": sched}, None


def word_count(text):
    return len(text.split())


def validate_ai_prompt(text):
    """Daily reflection prompt: 40-600 chars, at least 1 sentence."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 40:
        return None, "AI ka prompt bohot chhota tha."
    if len(clean) > 600:
        return None, "AI ka prompt bohot lamba tha."
    if "." not in clean and "؟" not in clean and "?" not in clean \
            and "!" not in clean:
        return None, "AI ke prompt me koi jumla nahi tha."
    return clean, None


def validate_ai_reflection(text):
    """Weekly reflection: 80-900 chars, at least 2 sentences."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 80:
        return None, "AI ki reflection bohot chhoti thi."
    if len(clean) > 900:
        return None, "AI ki reflection bohot lambi thi."
    sentences = [s for s in clean.replace("؟", ".").replace("?", ".")
                 .replace("!", ".").split(".") if s.strip()]
    if len(sentences) < 2:
        return None, "AI ki reflection me kam se kam 2 jumle hone chahiye."
    return clean, None
