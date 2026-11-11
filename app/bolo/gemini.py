"""Bolo AI layer — optional Gemini polish, Roman-Urdu transliteration
and English-to-Urdu translation of the user's own dictation.

Same call pattern as the other gap builds (Zehn/Sathi/Sukoon/Dak/
Khulasa/Zubaan/Waqt/Shajra/Tahqeeq): urllib, key read from the
environment AT CALL TIME only, never stored or logged. The AI only
reads text the USER dictated, plus a language and a style choice.
Every AI text is validated by engine.validate_ai_* before it reaches
the page, and labelled "AI-written" on the page. Dictation, voice
commands, sessions, stats and export work at 100% without a key.

The AI never claims any accuracy figure and never mentions any app,
brand or subscription.
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

STYLES = {
    "saaf": "Clean it up: fix grammar and punctuation, keep every "
            "fact and the speaker's meaning, do not add new facts.",
    "email": "Format it as a short, polite email: a greeting line, "
             "the message in short paragraphs, and a simple sign-off.",
    "message": "Rewrite it as a short WhatsApp-style message: warm, "
               "direct, no greeting line, no sign-off.",
    "notes": "Turn it into short bullet notes: one fact per line, "
             "each line starting with '- '.",
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Dictation, "
                      "voice commands, sessions aur export phir bhi "
                      "poore kaam karte hain.")
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


def _check_language(language):
    if language not in engine.LANGUAGES:
        return "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    return None


def polish(language, text, style="saaf"):
    """AI polish of the user's dictation in the chosen style.
    Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if style not in STYLES:
        return None, "Style ghalat hai — saaf, email, message ya notes chunein."
    text = (text or "").strip()
    if len(text) < 10:
        return None, "Pehle kuch bolein ya likhein, phir polish milega."
    if len(text) > 1500:
        return None, "Text 1500 characters se zyada hai — chhota karke dobara try karein."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a careful editor. Rewrite the dictated text below. "
        f"{STYLES[style]} "
        "Keep the speaker's words and meaning; do not invent facts, "
        "names, numbers or dates that are not in the text. Do NOT "
        "mention any app, brand or subscription. Length: 40-400 words. "
        f"{lang_note} Reply with ONLY the rewritten text, no title.\n\n"
        f"Text:\n{text}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_polish(raw)
    if err:
        return None, "AI ka polished text theek nahi tha: " + err
    return {"text": clean, "words": engine.word_count(clean),
            "language": language, "style": style, "ai": True}, None


def romanize(text):
    """Transliterate the user's Urdu-script dictation into Roman-Urdu
    letters (the way Pakistanis type on WhatsApp). Returns
    (result, error)."""
    text = (text or "").strip()
    if len(text) < 5:
        return None, "Pehle Urdu me kuch bolein ya likhein, phir Roman-Urdu milega."
    if len(text) > 1500:
        return None, "Text 1500 characters se zyada hai — chhota karke dobara try karein."
    prompt = (
        "Transliterate the Urdu text below into Roman Urdu — Urdu "
        "written in Latin letters, the way Pakistanis type on "
        "WhatsApp. Do NOT translate it into English and do NOT change "
        "the meaning; only change the script. Keep punctuation. Reply "
        "with ONLY the Roman-Urdu text, no title, no explanation.\n\n"
        f"Text:\n{text}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_short(raw)
    if err:
        return None, "AI ka Roman-Urdu text theek nahi tha: " + err
    return {"text": clean, "words": engine.word_count(clean),
            "language": "roman", "ai": True}, None


def translate_to_urdu(text):
    """Translate the user's English dictation into Urdu script.
    Returns (result, error)."""
    text = (text or "").strip()
    if len(text) < 5:
        return None, "Pehle English me kuch bolein ya likhein, phir Urdu tarjuma milega."
    if len(text) > 1500:
        return None, "Text 1500 characters se zyada hai — chhota karke dobara try karein."
    prompt = (
        "Translate the English text below into natural, clear Urdu "
        "script (proper Urdu, Nastaliq-style wording). Keep the "
        "meaning and the facts; do not add anything. Keep it the same "
        "length, roughly. Reply with ONLY the Urdu text, no title, no "
        "explanation.\n\n"
        f"Text:\n{text}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    clean, err = engine.validate_ai_short(raw)
    if err:
        return None, "AI ka Urdu tarjuma theek nahi tha: " + err
    return {"text": clean, "words": engine.word_count(clean),
            "language": "ur", "ai": True}, None
