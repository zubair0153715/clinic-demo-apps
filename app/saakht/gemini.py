"""Saakht AI polish via Gemini (free tier).

Same call pattern as the other gap builds: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The prompt
forbids inventing services, prices, claims or facts — AI may only
reword the tagline/about text the owner already wrote. The
rule-based builder always works without a key.
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


def polish(tagline, about):
    """Reword supplied copy only. Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Rule-based builder phir bhi poora available hai.")
    prompt = ("Reword the following business tagline and about text to "
              "sound more professional, in the same language. RULES: do "
              "not invent any service, price, claim, achievement or fact "
              "that is not already in the text. Keep it the same length "
              "or shorter. Reply with the polished tagline on line 1, "
              "then a blank line, then the polished about text.\n\n"
              f"Tagline: {tagline}\nAbout: {about}")
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
        return None, f"Gemini HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except Exception as e:
        return None, f"Gemini request failed: {type(e).__name__}: {e}"
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "Gemini returned an unexpected response."
    return text.strip(), None
