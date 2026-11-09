"""Sathi AI layer — optional Gemini daily reflection prompt and
weekly reflection.

Same call pattern as the other gap builds (Sukoon/Dak/Khulasa/
Zubaan/Waqt/Shajra/Tahqeeq): urllib, key read from the environment
AT CALL TIME only, never stored or logged. The AI only reads values
the USER types — a mood, a language choice, a short mood summary.
It never sends anything else. Every AI text is validated by
engine.validate_ai_* before it reaches the page, and labelled
"AI-written" on the page. Check-ins, habits, journeys, gratitude,
breathing and the pet work at 100% without a key.
"""

import json
import os
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120

LANG_INSTRUCTIONS = {
    "en": "Write in clear, simple English.",
    "roman": ("Write in Roman Urdu — Urdu written in Latin letters, "
              "the way Pakistanis type on WhatsApp. Keep it natural, "
              "not a word-for-word translation."),
    "ur": ("Write in Urdu script (proper Urdu, Nastaliq-style wording). "
           "Keep sentences short and clear."),
}

MOOD_NOTES = {
    1: "feeling very low today",
    2: "feeling low today",
    3: "feeling okay today",
    4: "feeling good today",
    5: "feeling very good today",
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Check-in, "
                      "habits, journeys, shukrana, saans aur Jugnu phir "
                      "bhi poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None, "AI quota khatam (429). Thodi der baad dobara try karein."
        return None, f"AI error (HTTP {e.code}). Dobara try karein."
    except Exception as exc:  # network, timeout, bad JSON
        return None, f"AI se rabta nahi hua ({exc}). Dobara try karein."
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip(), None
    except (KeyError, IndexError, TypeError):
        return None, "AI ne khaali jawab diya. Dobara try karein."


def daily_prompt(language, mood=None):
    """One fresh reflection prompt for today.

    Returns (result, error). mood is 1-5 or None. The prompt is a
    gentle question to journal on — never a diagnosis, never advice
    about any condition.
    """
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    if mood is not None and (not isinstance(mood, int)
                             or isinstance(mood, bool)
                             or not 1 <= mood <= 5):
        return None, "Mood 1 se 5 ke beech hona chahiye."
    lang_note = LANG_INSTRUCTIONS[language]
    mood_note = (f"The person is {MOOD_NOTES[mood]}. " if mood
                 else "No mood was given today. ")
    prompt = (
        "You are a kind self-care companion. Write ONE gentle journal "
        "prompt for today — a single open question the person can "
        "reflect on for two minutes. It must be warm, practical and "
        "about everyday life (gratitude, rest, a small kindness, a "
        "worry to set down, something they are looking forward to). "
        f"{mood_note}"
        "Do NOT diagnose, treat or mention any medical or mental-health "
        "condition. Do NOT mention any app, brand or subscription. "
        "Length: 40-150 words, in 1-3 short sentences. "
        f"{lang_note} Reply with ONLY the prompt text, no title."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_prompt(raw)
    if err:
        return None, "AI ka prompt theek nahi tha: " + err
    return {"prompt": clean, "words": engine.word_count(clean),
            "language": language, "ai": True}, None


def weekly_reflection(language, mood_summary):
    """A kind weekly summary from the user's own mood log.

    mood_summary is a short string the USER's own numbers produce
    (e.g. "7 entries, average 3.4, trend steady"). Returns
    (result, error). General encouragement only — never a diagnosis.
    """
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    mood_summary = (mood_summary or "").strip()[:200]
    if not mood_summary:
        return None, "Pehle kuch mood entries likhein, phir reflection milegi."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a kind self-care companion. Write a short, warm weekly "
        "reflection from the person's own mood log: "
        f"{mood_summary}. "
        "Celebrate what went well, name one small gentle next step for "
        "the coming week, and remind them that a rest day is not a "
        "failure. Do NOT diagnose, treat or mention any medical or "
        "mental-health condition. Do NOT mention any app, brand or "
        "subscription. Length: 80-250 words, at least 2 sentences. "
        f"{lang_note} Reply with ONLY the reflection text, no title."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_reflection(raw)
    if err:
        return None, "AI ki reflection theek nahi thi: " + err
    return {"reflection": clean, "words": engine.word_count(clean),
            "language": language, "ai": True}, None
