"""Sukoon AI layer — optional Gemini sleep-story generator and
personal wind-down planner.

Same call pattern as the other gap builds (Dak/Khulasa/Zubaan/Waqt/
Shajra/Tahqeeq): urllib, key read from the environment AT CALL TIME
only, never stored or logged. The AI only reads values the USER
types — a theme, a bedtime, a stress level, a worry note. It never
sends anything. Every AI story and plan is validated by
engine.validate_ai_* before it reaches the page, and labelled
"AI-written" on the page. Breathing, bundled stories, sounds, dhikr,
the planner and the diary work at 100% without a key.
"""

import json
import os
import re
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

STORY_THEMES = ["river", "train", "garden", "desert", "rain", "mountains",
                "sea", "village", "forest", "stars"]


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Saans, "
                      "kahani, awaz, dhikr, planner aur diary phir bhi "
                      "poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 3000},
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


def story_ai(theme, language):
    """Generate one ORIGINAL sleep story on a theme.

    Returns (result_dict, error). result_dict: story (validated
    text), words, minutes. The story is invented fresh by the model —
    never a retelling of a known book, film or celebrity narration —
    slow, gentle, and ending in sleep. Labelled AI-written on the page.
    """
    if theme not in STORY_THEMES:
        return None, "Theme ghalat hai — list me se chunein."
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a sleep-story writer. Write ONE completely original, "
        "gentle sleep story (a bedtime story for an adult who cannot "
        "sleep). It must be your own invention — NOT a retelling of any "
        "known book, film, fairy tale or celebrity narration. Slow pace, "
        "soft imagery, no excitement, no danger, no cliffhanger, and it "
        f"must END with the main character drifting peacefully to sleep. "
        f"Theme: {theme}. Length: 300-500 words, at least 3 paragraphs "
        "(separate paragraphs with a blank line). "
        f"{lang_note} Do not mention any app, brand or subscription. "
        "Reply with ONLY the story text, no title, no introduction."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_story(raw)
    if err:
        return None, "AI ki kahani theek nahi thi: " + err
    return {"story": clean, "words": engine.word_count(clean),
            "minutes": engine.reading_minutes(clean),
            "theme": theme, "language": language, "ai": True}, None


def wind_down_ai(bedtime, wake, stress, worry, language):
    """Generate a personal tonight wind-down plan.

    bedtime / wake are 'HH:MM'; stress 1-5; worry is a free-text note
    the user wants to "park till tomorrow". Returns (result, error).
    The plan is a suggestion, not medical advice, and the page says so.
    """
    bed = engine.parse_hhmm(bedtime)
    wk = engine.parse_hhmm(wake)
    if bed is None or wk is None:
        return None, "Waqt 'HH:MM' format me likhein, masalan 23:00."
    if not isinstance(stress, int) or not 1 <= stress <= 5:
        return None, "Stress 1 se 5 ke beech hona chahiye."
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    worry = (worry or "").strip()[:300]
    lang_note = LANG_INSTRUCTIONS[language]
    dur, _ = engine.sleep_duration(bedtime, wake)
    hours = dur["label"] if dur else "unknown"
    prompt = (
        "You are a calm sleep coach. Write a short, practical wind-down "
        "plan for TONIGHT only, for a person in Pakistan. Bedtime "
        f"{bedtime}, wake time {wake} (about {hours} of sleep), stress "
        f"level {stress}/5. "
        + (f"Their worry tonight: \"{worry}\". Give them one concrete way "
           "to write it down and park it until tomorrow. " if worry else "")
        + "Plan: 4-6 short steps from now until bedtime (dhikr or quiet "
          "time, a breathing pattern, screens off, a story or sound). "
          "Keep it kind, realistic and specific to their times. 120-250 "
          f"words. {lang_note} This is general sleep hygiene, not medical "
          "advice — say nothing that diagnoses or treats any condition. "
          "Reply with ONLY the plan text, no title."
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_plan(raw)
    if err:
        return None, "AI ka plan theek nahi tha: " + err
    return {"plan": clean, "words": engine.word_count(clean),
            "bedtime": bedtime, "wake": wake, "stress": stress,
            "ai": True}, None
