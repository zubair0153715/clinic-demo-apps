"""Khulasa AI layer — optional Gemini summariser for pasted text.

Same call pattern as the other gap builds (Zubaan/Waqt/Shajra/
Tahqeeq): urllib, key read from the environment AT CALL TIME only,
never stored or logged. The AI only summarises text the USER
pastes — it never claims to know a book the user did not paste.
Its JSON output is validated by engine.validate_ai_result before
it reaches the page. The 6-book starter library, quizzes,
flashcards and action plans work at 100% without a key.
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


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Library ki "
                      "6 kitabein, quiz aur flashcards phir bhi poore kaam "
                      "karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2500},
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


def _extract_json(raw):
    """Pull a JSON object out of the model's reply, tolerating
    ```json fences and surrounding prose."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def summarize_text(text, depth, language):
    """Summarise pasted text at a chosen depth and language.

    Returns (result_dict, error). result_dict has keys: summary,
    key_ideas (5 strings), action_plan (4 strings), quiz (3 items:
    q, options[4], answer index, why). The summary is ALWAYS of
    the pasted text — the model is told to use only that text.
    """
    ok, err = engine.validate_paste(text)
    if not ok:
        return None, err
    if depth not in engine.AI_DEPTHS:
        return None, "Depth ghalat hai — Flash, Standard, Deep ya Study chunein."
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    target = engine.AI_DEPTHS[depth]["words"]
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a careful study assistant. Summarise ONLY the text below. "
        "Do not add facts from outside the text. Do not invent quotes, "
        "numbers or claims. If the text is too short or unclear to summarise "
        "a point, say so inside the summary instead of inventing it.\n\n"
        f"Target length for the summary: {target}.\n{lang_note}\n\n"
        "Reply with ONLY a JSON object, no other text, in exactly this shape:\n"
        '{"summary": "...", '
        '"key_ideas": ["idea 1", "idea 2", "idea 3", "idea 4", "idea 5"], '
        '"action_plan": ["step 1", "step 2", "step 3", "step 4"], '
        '"quiz": [{"q": "...", "options": ["a", "b", "c", "d"], "answer": 0, '
        '"why": "..."}, {"q": "...", "options": [...], "answer": 1, "why": "..."}, '
        '{"q": "...", "options": [...], "answer": 2, "why": "..."}]}\n\n'
        "Rules: key_ideas = the 5 most important ideas IN the text. "
        "action_plan = 4 concrete things the reader can DO this week based on the text. "
        "quiz = 3 multiple-choice questions about the text only, 4 options each, "
        "exactly one correct answer, with a one-line 'why' explaining the answer.\n\n"
        f"TEXT TO SUMMARISE:\n{text.strip()}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    result = _extract_json(raw)
    if result is None:
        return None, "AI ka jawab samajh nahi aaya (JSON nahi mila). Dobara try karein."
    errors = engine.validate_ai_result(result)
    if errors:
        return None, "AI ka jawab poora nahi tha: " + "; ".join(errors)
    return result, None
