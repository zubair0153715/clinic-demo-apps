"""Sukoon engine — deterministic, testable sleep & calm logic.

No AI here on purpose: breathing schedules, dhikr rounds, wind-down
planning and sleep-duration math are pure functions so tests can
verify them exactly. The AI (gemini.py) only ever *generates* an
original sleep story or a personal wind-down plan from values the
USER types; its output is validated by validate_ai_* before it
reaches the page.

Breathing patterns (seconds per phase, from published practice):
  4-7-8  inhale 4, hold 7, exhale 8   -> 19 s/cycle
  Box    inhale 4, hold 4, exhale 4, hold 4 -> 16 s/cycle
  Coherent inhale 5, exhale 5         -> 10 s/cycle = 6 breaths/min
  4-4-6  inhale 4, hold 4, exhale 6   -> 14 s/cycle

Wind-down blocks (minutes, in order): dhikr, breathing, story,
sounds-until-bedtime. The schedule never runs past bedtime and
never overlaps; a short window shrinks the blocks instead of
overflowing.
"""

import re

WPM = 200

LANGUAGES = {"en": "English", "roman": "Roman-Urdu", "ur": "Urdu"}

# ---------------------------------------------------------------- breathing

BREATHING_PATTERNS = {
    "478": {
        "name": "4-7-8",
        "label": "4-7-8 — neend ke liye (Dr. Andrew Weil ka mashhoor pattern)",
        "phases": [("inhale", 4), ("hold", 7), ("exhale", 8)],
        "note": "4 second saans andar, 7 second roko, 8 second bahar. "
                "4 cycle = ~76 second.",
    },
    "box": {
        "name": "Box breathing",
        "label": "Box breathing — 4-4-4-4 (tension kam karne ke liye)",
        "phases": [("inhale", 4), ("hold", 4), ("exhale", 4), ("hold", 4)],
        "note": "Har phase 4 second. Navy SEALs bhi yahi pattern "
                "stress ke waqt istemal karte hain.",
    },
    "coherent": {
        "name": "Coherent breathing",
        "label": "Coherent — 5-5 (dil ki dharkan sakin karne ke liye)",
        "phases": [("inhale", 5), ("exhale", 5)],
        "note": "5 second andar, 5 second bahar — 6 saans per minute, "
                "jo heart-rate variability research me sakin mana jata hai.",
    },
    "446": {
        "name": "4-4-6",
        "label": "4-4-6 — halki neend, lambi exhale",
        "phases": [("inhale", 4), ("hold", 4), ("exhale", 6)],
        "note": "Exhale inhale se lambi — jism ko 'aaram karo' ka signal.",
    },
}

MIN_CYCLES = 1
MAX_CYCLES = 20

PHASE_LABELS = {
    "inhale": "Saans andar",
    "hold": "Roko",
    "exhale": "Saans bahar",
}


def cycle_seconds(pattern):
    """Seconds in one full breath cycle of the pattern."""
    pat = BREATHING_PATTERNS.get(pattern)
    if pat is None:
        return None
    return sum(sec for _, sec in pat["phases"])


def breaths_per_minute(pattern):
    """Breaths per minute for the pattern (60 / cycle seconds)."""
    cs = cycle_seconds(pattern)
    if not cs:
        return None
    return round(60.0 / cs, 1)


def breathing_schedule(pattern, cycles):
    """Full phase-by-phase schedule for a session.

    Returns (schedule, error). Schedule is a list of dicts:
    {"cycle": n, "phase": "inhale", "label": "Saans andar",
     "seconds": 4, "start": 0, "end": 4} with start/end in seconds
    from session start. Total = cycles * cycle_seconds(pattern).
    """
    if pattern not in BREATHING_PATTERNS:
        return None, "Pattern nahi mila."
    if not isinstance(cycles, int) or not MIN_CYCLES <= cycles <= MAX_CYCLES:
        return None, f"Cycles {MIN_CYCLES}–{MAX_CYCLES} ke beech hone chahiye."
    phases = BREATHING_PATTERNS[pattern]["phases"]
    schedule = []
    t = 0
    for c in range(1, cycles + 1):
        for phase, sec in phases:
            schedule.append({
                "cycle": c, "phase": phase,
                "label": PHASE_LABELS[phase], "seconds": sec,
                "start": t, "end": t + sec,
            })
            t += sec
    return {"pattern": pattern,
            "name": BREATHING_PATTERNS[pattern]["name"],
            "cycles": cycles,
            "cycle_seconds": cycle_seconds(pattern),
            "total_seconds": t,
            "breaths_per_minute": breaths_per_minute(pattern),
            "schedule": schedule}, None


# ------------------------------------------------------------------- dhikr

DHIKR_PRESETS = {
    "subhanallah": {"name": "SubhanAllah", "arabic": "سُبْحَانَ اللَّهِ",
                    "meaning": "Allah paak hai", "target": 33},
    "alhamdulillah": {"name": "Alhamdulillah", "arabic": "الْحَمْدُ لِلَّهِ",
                      "meaning": "Tamam tareef Allah ke liye", "target": 33},
    "allahu_akbar": {"name": "Allahu Akbar", "arabic": "اللَّهُ أَكْبَرُ",
                     "meaning": "Allah sab se bara hai", "target": 34},
    "la_ilaha": {"name": "La ilaha illallah",
                 "arabic": "لَا إِلَهَ إِلَّا اللَّهُ",
                 "meaning": "Allah ke siwa koi mabood nahi", "target": 100},
    "astaghfirullah": {"name": "Astaghfirullah",
                       "arabic": "أَسْتَغْفِرُ اللَّهَ",
                       "meaning": "Main Allah se maghfirat chahta hoon",
                       "target": 100},
    "durood": {"name": "Durood Sharif",
               "arabic": "اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ",
               "meaning": "Aye Allah, Muhammad ﷺ par rehmat bhej",
               "target": 100},
}


def dhikr_progress(key, count):
    """Rounds completed + remainder for a tap count against its target.

    33-target tasbih: 33 taps = 1 round. Returns dict or (None, error).
    """
    preset = DHIKR_PRESETS.get(key)
    if preset is None:
        return None, "Dhikr nahi mila."
    if not isinstance(count, int) or count < 0:
        return None, "Count 0 ya zyada honi chahiye."
    target = preset["target"]
    return {"key": key, "name": preset["name"], "target": target,
            "count": count, "rounds": count // target,
            "remainder": count % target,
            "round_done": count > 0 and count % target == 0}, None


# ---------------------------------------------------------------- wind-down

# (block name, minutes) for a full window (>= 45 min) and a short one.
WIND_DOWN_FULL = [("dhikr", 10), ("breathing", 5), ("story", 20)]
WIND_DOWN_SHORT = [("dhikr", 5), ("breathing", 3), ("story", 10)]
MIN_SOUNDS_MINUTES = 5


def parse_hhmm(value):
    """'22:30' -> 1350 minutes since midnight. None on bad input."""
    if not isinstance(value, str):
        return None
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", value)
    if not m:
        return None
    h, mins = int(m.group(1)), int(m.group(2))
    if not (0 <= h <= 23 and 0 <= mins <= 59):
        return None
    return h * 60 + mins


def minutes_to_hhmm(minutes):
    """1350 -> '22:30'. Wraps past midnight (1500 -> '01:00')."""
    minutes = int(minutes) % 1440
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def build_wind_down(isha, bedtime):
    """Build tonight's wind-down schedule.

    isha / bedtime are 'HH:MM' strings. Bedtime after midnight is
    handled (22:30 -> 01:00 = 150 min window). Returns (plan, error).
    Plan blocks never overlap and the last one ends exactly at
    bedtime. Sounds fill the remainder so the night ends in sound,
    not silence.
    """
    start = parse_hhmm(isha)
    end = parse_hhmm(bedtime)
    if start is None or end is None:
        return None, "Waqt 'HH:MM' format me likhein, masalan 21:30."
    if end <= start:
        end += 1440
    window = end - start
    if window < 10:
        return None, ("Isha aur bedtime ke beech kam se kam 10 minute "
                      "hone chahiye — warna wind-down ka waqt hi nahi.")
    blocks = WIND_DOWN_FULL if window >= 45 else WIND_DOWN_SHORT
    fixed = sum(m for _, m in blocks)
    sounds = window - fixed
    if sounds < MIN_SOUNDS_MINUTES:
        # shrink the story first, then breathing, to protect 5 min sounds
        blocks = [(name, mins) for name, mins in blocks]
        need = MIN_SOUNDS_MINUTES - sounds
        for i in (2, 1, 0):
            if need <= 0:
                break
            name, mins = blocks[i]
            cut = min(need, mins - 1)
            blocks[i] = (name, mins - cut)
            need -= cut
        fixed = sum(m for _, m in blocks)
        sounds = window - fixed
    plan = []
    t = start
    for name, mins in blocks:
        plan.append({"block": name, "minutes": mins,
                     "start": minutes_to_hhmm(t),
                     "end": minutes_to_hhmm(t + mins)})
        t += mins
    plan.append({"block": "sounds", "minutes": sounds,
                 "start": minutes_to_hhmm(t),
                 "end": minutes_to_hhmm(end)})
    return {"isha": minutes_to_hhmm(start),
            "bedtime": minutes_to_hhmm(end % 1440),
            "window_minutes": window, "blocks": plan}, None


# -------------------------------------------------------------------- sleep

MAX_SLEEP_MINUTES = 16 * 60


def sleep_duration(bed, wake):
    """Minutes slept from bed 'HH:MM' to wake 'HH:MM' (overnight ok)."""
    b = parse_hhmm(bed)
    w = parse_hhmm(wake)
    if b is None or w is None:
        return None, "Waqt 'HH:MM' format me likhein, masalan 23:00."
    if w <= b:
        w += 1440
    mins = w - b
    if mins <= 0 or mins > MAX_SLEEP_MINUTES:
        return None, "Neend 0 se 16 ghante ke beech honi chahiye."
    return {"minutes": mins, "hours": round(mins / 60, 1),
            "label": f"{mins // 60} ghante {mins % 60:02d} minute"}, None


def sleep_average(durations):
    """Mean of a list of sleep-minute values; None when empty."""
    vals = [d for d in durations
            if isinstance(d, (int, float)) and 0 < d <= MAX_SLEEP_MINUTES]
    if not vals:
        return None
    avg = sum(vals) / len(vals)
    return {"nights": len(vals), "average_minutes": round(avg),
            "average_label": f"{int(avg) // 60} ghante {int(avg) % 60:02d} minute"}


# ------------------------------------------------------------------- sounds

# Web Audio API recipes — filtered noise, synthesised live in the
# browser. No audio files, no licences, no streaming. Values are the
# exact filter settings the page's synth uses.
SOUND_RECIPES = {
    "rain": {"label": "Baarish", "kind": "noise", "filter": "bandpass",
             "freq": 1200, "q": 0.7, "gain": 0.35,
             "note": "Halki band-pass filtered noise — baarish jaisi awaz."},
    "brown": {"label": "Brown noise", "kind": "noise", "filter": "lowpass",
              "freq": 400, "q": 0.5, "gain": 0.5,
              "note": "Gehra low-pass noise — dimagh ko sakin karne ke liye."},
    "waves": {"label": "Samandar ki lehrein", "kind": "noise",
              "filter": "lowpass", "freq": 600, "q": 0.6, "gain": 0.4,
              "lfo_hz": 0.1, "lfo_depth": 0.25,
              "note": "Low-pass noise jiska gain 10 second me halke se "
                      "upar-neeche hota hai — lehar ka aana-jaana."},
    "fan": {"label": "Pankha", "kind": "noise", "filter": "lowpass",
            "freq": 300, "q": 0.4, "gain": 0.3, "lfo_hz": 11,
            "lfo_depth": 0.08,
            "note": "Bohat halka low-pass noise, 11 Hz ki halki larzish — "
                    "pankhe ki goonj."},
}

SLEEP_TIMERS = [15, 30, 45, 60, 90]


# ------------------------------------------------------------------ stories

def word_count(text):
    return len((text or "").split())


def reading_minutes(text):
    return max(1, -(-word_count(text) // WPM))  # ceil, min 1


def validate_ai_story(text):
    """Shape checks for an AI-generated sleep story.

    Original text only: 250–1500 words, at least 3 paragraphs, ends
    with sentence punctuation, no links, no mention of Calm or its
    premium products. Returns (clean_text, error).
    """
    if not text or not text.strip():
        return None, "AI ne khaali kahani di."
    clean = text.strip()
    words = word_count(clean)
    if words < 250:
        return None, f"Kahani bohat chhoti hai ({words} alfaz) — kam se kam 250 chahiye."
    if words > 1500:
        return None, f"Kahani bohat lambi hai ({words} alfaz) — zyada se zyada 1500."
    paras = [p for p in clean.split("\n\n") if p.strip()]
    if len(paras) < 3:
        return None, "Kahani me kam se kam 3 paragraphs hone chahiye."
    if clean[-1] not in ".!؟":
        return None, "Kahani kisi jumle par khatam honi chahiye."
    low = clean.lower()
    if "http" in low or "calm.com" in low or "calm premium" in low:
        return None, "Kahani me link ya kisi aur app ka naam nahi hona chahiye."
    return clean, None


def validate_ai_plan(text):
    """Shape checks for an AI wind-down plan: 80–600 words, has steps."""
    if not text or not text.strip():
        return None, "AI ne khaali plan diya."
    clean = text.strip()
    words = word_count(clean)
    if words < 80:
        return None, f"Plan bohat chhota hai ({words} alfaz)."
    if words > 600:
        return None, f"Plan bohat lamba hai ({words} alfaz)."
    if "http" in clean.lower():
        return None, "Plan me link nahi hona chahiye."
    return clean, None
