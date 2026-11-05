"""Zubaan engine — deterministic, testable learning logic.

No AI here on purpose: XP/levels, spaced repetition, keyword
scoring for roleplay turns, and dictation word-overlap are pure
functions so tests can verify them exactly. The AI (gemini.py)
only ever *continues* a roleplay scene; it never grades you.
"""

import re
from datetime import date, timedelta

# XP thresholds: (xp needed, level name). B2 is the top of this
# starter course; the page says plainly it is not native fluency.
LEVELS = [(0, "A1"), (200, "A2"), (600, "B1"), (1200, "B2")]

XP_QUIZ = 10
XP_ROLEPLAY_STEP = 15
XP_DICTATION = 10

# Spaced-repetition intervals in days, by box number.
SRS_INTERVALS = [1, 3, 7, 14, 30]

# Dictation passes when at least this fraction of the target
# words appear in what the learner typed (order-insensitive).
DICTATION_PASS = 0.80


def level_for(xp):
    """Highest level whose threshold xp has reached."""
    level = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    return level


def award_xp(xp, gain):
    """Return (new_xp, new_level, level_changed)."""
    before = level_for(xp)
    new_xp = max(0, xp + gain)
    after = level_for(new_xp)
    return new_xp, after, after != before


def srs_next(box, last):
    """Next review date (ISO string) for a card in `box`,
    last reviewed on date `last` (ISO string or date).

    Box is clamped to the last interval, so a well-known card
    reviews every 30 days, never "never".
    """
    if isinstance(last, str):
        last = date.fromisoformat(last)
    idx = max(0, min(int(box), len(SRS_INTERVALS) - 1))
    return (last + timedelta(days=SRS_INTERVALS[idx])).isoformat()


def _norm(text):
    return re.sub(r"[^a-z0-9 ]", " ", (text or "").lower())


def score_roleplay_step(keywords, user_text):
    """Score one roleplay turn.

    Returns (matched, total, passed). A keyword counts when it
    appears as a word (or phrase) in the learner's normalised
    reply. passed = at least half the keywords covered.
    """
    words = set(_norm(user_text).split())
    flat = " " + _norm(user_text) + " "
    matched = 0
    for kw in keywords:
        kw = _norm(kw).strip()
        if not kw:
            continue
        if " " in kw:
            if " " + kw + " " in flat:
                matched += 1
        elif kw in words:
            matched += 1
    total = len(keywords)
    passed = total > 0 and matched * 2 >= total
    return matched, total, passed


def dictation_score(target, typed):
    """Fraction of the target sentence's words present in `typed`.

    Order-insensitive, punctuation-insensitive, case-insensitive.
    Returns (fraction, passed).
    """
    target_words = _norm(target).split()
    typed_words = set(_norm(typed).split())
    if not target_words:
        return 0.0, False
    hit = sum(1 for w in target_words if w in typed_words)
    frac = hit / len(target_words)
    return frac, frac >= DICTATION_PASS


def check_quiz(item, choice_index):
    """True when choice_index is the item's answer index."""
    try:
        return int(choice_index) == int(item["answer"])
    except (KeyError, TypeError, ValueError):
        return False


def validate_bank(library):
    """Validate the whole content bank. Returns a list of errors
    (empty = valid). Used by tests and by /api/bank."""
    errors = []
    for deck in library.VOCAB:
        seen = set()
        for entry in deck["words"]:
            if not entry.get("en") or not entry.get("roman"):
                errors.append(f"vocab {deck['id']}: missing en/roman")
            if not entry.get("example"):
                errors.append(f"vocab {deck['id']} {entry.get('en')}: no example")
            if entry.get("en") in seen:
                errors.append(f"vocab {deck['id']}: duplicate {entry['en']}")
            seen.add(entry.get("en"))
    for topic in library.GRAMMAR:
        for item in topic["items"]:
            opts = item.get("options", [])
            if len(opts) != 4:
                errors.append(f"grammar {topic['id']}: item needs 4 options")
            ans = item.get("answer")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                errors.append(f"grammar {topic['id']}: bad answer index")
            if not item.get("rule"):
                errors.append(f"grammar {topic['id']}: item missing rule")
            if "____" not in item.get("q", ""):
                errors.append(f"grammar {topic['id']}: item missing blank")
    for scen in library.SCENARIOS:
        if len(scen["steps"]) < 3:
            errors.append(f"scenario {scen['id']}: too few steps")
        for step in scen["steps"]:
            if not step.get("keywords"):
                errors.append(f"scenario {scen['id']}: step without keywords")
            if not step.get("model"):
                errors.append(f"scenario {scen['id']}: step without model answer")
    return errors
