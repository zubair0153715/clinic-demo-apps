"""Awaaz AI layer — one optional Gemini call: summarise the loaded text.

Same call pattern as the other gap builds: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The summary is
a convenience only — the reader works at 100% without a key, and when
the key is quota-exhausted the page says so instead of failing the
reader (lesson from the 2026-11-01 Tahqeeq deploy, where Deep mode
429'd on the shared deployed key).
"""
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 120
MAX_SUMMARY_CHARS = 12_000


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available() -> bool:
    return bool(_get_key())


def summarize_text(text, language="en"):
    """Summarise text in its own language. Returns (summary, error)."""
    key = _get_key()
    if not key:
        return None, ("AI summary ke liye GEMINI_API_KEY set nahi hai. "
                      "Reader phir bhi poora kaam karta hai.")
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    snippet = text[:MAX_SUMMARY_CHARS]
    prompt = ("Summarise the following text " + lang_note + " in 5-8 "
              "short bullet points. RULES: only use facts already in "
              "the text — do not invent names, numbers, dates or "
              "claims. Keep each point to one line.\n\n" + snippet)
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1500},
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
        text_out = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "Gemini returned an unexpected response."
    return text_out.strip(), None
