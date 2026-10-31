"""Majlis AI polish via Gemini (free tier).

Same call pattern as the other gap builds: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The prompt
forbids inventing decisions, action items, owners, dates or facts
that are not already in the transcript — AI may only reword the
deterministic summary the engine already produced. The rule-based
structuring always works without a key.
"""

import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 120


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available() -> bool:
    return bool(_get_key())


def polish_summary(summary_text, language="en"):
    """Reword the structured summary only. Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Rule-based minutes phir bhi pooray available hain.")
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    prompt = ("Rewrite the following meeting summary to read more "
              "clearly and professionally, " + lang_note + ". RULES: do "
              "not invent any decision, action item, owner, date, number "
              "or fact that is not already in the text. Do not drop any "
              "decision or action item. Keep the same sections and the "
              "same length or shorter.\n\n" + summary_text)
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 3000},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"Gemini HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except Exception as e:
        return None, f"Gemini request failed: {type(e).__name__}: {e}"
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "Gemini returned an unexpected response."
    return text.strip(), None
