"""Khulasa engine — deterministic, testable summary logic.

No AI here on purpose: word counts, reading-time estimates,
depth bands, paste validation, quiz scoring, flashcards and the
spaced-repetition schedule are pure functions so tests can verify
them exactly. The AI (gemini.py) only ever *generates* a summary
from text the user pastes; it never grades, and its output is
validated by validate_ai_result before it reaches the page.
"""

import math
import re
from datetime import date, timedelta

# Reading speed used for every time estimate on the page.
WPM = 200

# Authored-library depth bands: (min words, max words, label).
# The page shows the honest reading time (words / 200 wpm),
# never a round "15 minutes" for every book.
DEPTHS = {
    "flash": {"min": 60, "max": 120, "label": "Flash · ~1 min"},
    "standard": {"min": 250, "max": 450, "label": "Standard · ~2 min"},
    "deep": {"min": 600, "max": 900, "label": "Deep · ~4 min"},
}

# AI depths offered for pasted text (the AI writes the long ones;
# the authored library ships flash/standard/deep only).
AI_DEPTHS = {
    "flash": {"words": "~100 words"},
    "standard": {"words": "~300 words"},
    "deep": {"words": "~800 words"},
    "study": {"words": "~1,500 words, section by section"},
}

# Pasted text limits for the AI summariser.
PASTE_MIN_CHARS = 200
PASTE_MAX_CHARS = 8000

# Spaced-repetition intervals in days, by box number.
SRS_INTERVALS = [1, 3, 7, 14, 30]

LANGUAGES = {"en": "English", "roman": "Roman-Urdu", "ur": "Urdu"}


def word_count(text):
    """Number of whitespace-separated words in text."""
    return len((text or "").split())


def reading_minutes(words, wpm=WPM):
    """Honest reading time in whole minutes, minimum 1."""
    return max(1, math.ceil(words / wpm))


def depth_ok(depth, words):
    """True when a summary of `words` words fits its depth band."""
    band = DEPTHS.get(depth)
    if band is None:
        return False
    return band["min"] <= words <= band["max"]


def validate_paste(text):
    """Validate text pasted for AI summarising.

    Returns (ok, error). The app summarises the text you paste —
    it never claims to know a book you did not paste.
    """
    text = (text or "").strip()
    if len(text) < PASTE_MIN_CHARS:
        return False, (f"Text thora sa hai — kam az kam {PASTE_MIN_CHARS} "
                       "characters paste karein (ek chhota chapter ya notes).")
    if len(text) > PASTE_MAX_CHARS:
        return False, (f"Text bohat lamba hai — zyada se zyada "
                       f"{PASTE_MAX_CHARS} characters (lagbhag 1,500 words).")
    return True, ""


def check_quiz(item, choice_index):
    """True when choice_index is the item's answer index."""
    try:
        return int(choice_index) == int(item["answer"])
    except (KeyError, TypeError, ValueError):
        return False


def quiz_score(answers, quiz):
    """Score a whole quiz.

    answers: list of choice indexes (one per question).
    Returns (correct, total).
    """
    total = len(quiz)
    if total == 0:
        return 0, 0
    correct = sum(1 for item, ans in zip(quiz, answers)
                  if check_quiz(item, ans))
    return correct, total


def flashcards(book):
    """Flashcards derived from the book's own key ideas.

    Front = the idea in one line, back = the detail. The deck is
    data, not code: add a key idea and the card appears.
    """
    cards = []
    for idea in book.get("key_ideas", []):
        if idea.get("idea") and idea.get("detail"):
            cards.append({"front": idea["idea"], "back": idea["detail"]})
    return cards


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


def validate_ai_result(result):
    """Validate an AI-generated summary before it reaches the page.

    Returns a list of errors (empty = usable). Shape only — the
    page labels AI output as AI-generated, and the summary is
    always of the text the user pasted.
    """
    errors = []
    if not isinstance(result, dict):
        return ["AI ka jawab samajh nahi aaya (galat format)."]
    summary = (result.get("summary") or "").strip()
    if word_count(summary) < 40:
        errors.append("AI summary bohat chhoti hai — dobara try karein.")
    if word_count(summary) > 2500:
        errors.append("AI summary bohat lambi hai — dobara try karein.")
    ideas = result.get("key_ideas") or []
    if not isinstance(ideas, list) or len(ideas) < 3:
        errors.append("AI se kam az kam 3 key ideas chahiye the.")
    elif len(ideas) > 7:
        errors.append("AI se zyada se zyada 7 key ideas chahiye the.")
    actions = result.get("action_plan") or []
    if not isinstance(actions, list) or len(actions) < 2:
        errors.append("AI se kam az kam 2 action steps chahiye the.")
    quiz = result.get("quiz") or []
    if not isinstance(quiz, list) or len(quiz) != 3:
        errors.append("AI se exactly 3 quiz questions chahiye the.")
    else:
        for i, item in enumerate(quiz):
            opts = item.get("options", [])
            if len(opts) != 4:
                errors.append(f"AI quiz Q{i + 1}: 4 options chahiye the.")
            ans = item.get("answer")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                errors.append(f"AI quiz Q{i + 1}: jawab ka index ghalat hai.")
            if not item.get("why"):
                errors.append(f"AI quiz Q{i + 1}: wazahat (why) missing hai.")
    return errors


def validate_library(library):
    """Validate the whole starter book bank. Returns a list of
    errors (empty = valid). Used by tests and by /api/library."""
    errors = []
    seen = set()
    for book in library.BOOKS:
        bid = book.get("id", "?")
        if bid in seen:
            errors.append(f"book {bid}: duplicate id")
        seen.add(bid)
        for field in ("title", "author", "year", "category", "why",
                      "roman", "gutenberg"):
            if not book.get(field):
                errors.append(f"book {bid}: missing {field}")
        summaries = book.get("summaries", {})
        for depth in ("flash", "standard", "deep"):
            text = summaries.get(depth, "")
            words = word_count(text)
            if not depth_ok(depth, words):
                errors.append(
                    f"book {bid} {depth}: {words} words, "
                    f"band is {DEPTHS[depth]['min']}-"
                    f"{DEPTHS[depth]['max']}")
        ideas = book.get("key_ideas", [])
        if len(ideas) < 5:
            errors.append(f"book {bid}: {len(ideas)} key ideas, need >= 5")
        for idea in ideas:
            if not idea.get("idea") or not idea.get("detail"):
                errors.append(f"book {bid}: key idea missing idea/detail")
        actions = book.get("action_plan", [])
        if len(actions) < 4:
            errors.append(f"book {bid}: {len(actions)} actions, need >= 4")
        quiz = book.get("quiz", [])
        if len(quiz) != 3:
            errors.append(f"book {bid}: {len(quiz)} quiz items, need 3")
        for i, item in enumerate(quiz):
            opts = item.get("options", [])
            if len(opts) != 4:
                errors.append(f"book {bid} Q{i + 1}: needs 4 options")
            ans = item.get("answer")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                errors.append(f"book {bid} Q{i + 1}: bad answer index")
            if not item.get("why"):
                errors.append(f"book {bid} Q{i + 1}: missing why")
            if not item.get("q"):
                errors.append(f"book {bid} Q{i + 1}: missing question")
    return errors
