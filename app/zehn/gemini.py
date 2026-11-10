"""Zehn AI layer — optional Gemini daily training tip and weekly
progress summary.

Same call pattern as the other gap builds (Sathi/Sukoon/Dak/
Khulasa/Zubaan/Waqt/Shajra/Tahqeeq): urllib, key read from the
environment AT CALL TIME only, never stored or logged. The AI only
reads values the USER types — a language choice and a short summary
of the user's own scores. It never sends anything else. Every AI
text is validated by engine.validate_ai_* before it reaches the
page, and labelled "AI-written" on the page. All five games,
workouts, scores and Zen practice work at 100% without a key.

The AI never claims brain games raise IQ, prevent dementia or
treat any condition — the prompt forbids it.
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


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Paanch khel, "
                      "workout, score aur Zen practice phir bhi poore "
                      "kaam karte hain.")
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


def daily_tip(language, score_summary):
    """One practical training tip for today, from the user's own
    scores. Returns (result, error)."""
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    score_summary = (score_summary or "").strip()[:200]
    if not score_summary:
        return None, "Pehle koi game khelein, phir tip milegi."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a friendly brain-training coach. The person played "
        "some short memory, attention and maths games today. Their "
        f"scores: {score_summary}. "
        "Write ONE practical tip for tomorrow's practice — which game "
        "to focus on, one concrete technique (for example chunking "
        "digits, saying the ink colour out loud, or estimating before "
        "calculating), and one encouraging line. Do NOT claim brain "
        "games raise IQ, improve school or work performance, prevent "
        "dementia or treat any condition. Do NOT mention any app, "
        "brand or subscription. Length: 40-150 words, 1-3 short "
        f"sentences. {lang_note} Reply with ONLY the tip text, no title."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_tip(raw)
    if err:
        return None, "AI ka tip theek nahi tha: " + err
    return {"tip": clean, "words": engine.word_count(clean),
            "language": language, "ai": True}, None


def weekly_summary(language, week_summary):
    """A warm weekly summary from the user's own game scores.

    week_summary is a short string the USER's own numbers produce
    (e.g. "12 games, best skill memory 82, weakest speed 54").
    Returns (result, error)."""
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    week_summary = (week_summary or "").strip()[:200]
    if not week_summary:
        return None, "Pehle kuch games khelein, phir summary milegi."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a friendly brain-training coach. Write a short, warm "
        "weekly summary from the person's own game scores: "
        f"{week_summary}. "
        "Celebrate the strongest skill, name the weakest one with one "
        "concrete way to practise it, and remind them that games "
        "train the games themselves — steady, short practice beats "
        "long sessions. Do NOT claim brain games raise IQ, improve "
        "school or work performance, prevent dementia or treat any "
        "condition. Do NOT mention any app, brand or subscription. "
        "Length: 80-250 words, at least 2 sentences. "
        f"{lang_note} Reply with ONLY the summary text, no title."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_summary(raw)
    if err:
        return None, "AI ki summary theek nahi thi: " + err
    return {"summary": clean, "words": engine.word_count(clean),
            "language": language, "ai": True}, None
