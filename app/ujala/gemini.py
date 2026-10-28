"""Ujala AI advice via Gemini (free tier).

Same call pattern as app/ibarat/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The enhancer
always works without a key; AI only suggests preset/slider starting
points from a text description of the goal. Suggestions are validated
and clamped before use — a bad AI reply can never break a photo.
"""

import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 60


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available() -> bool:
    return bool(_get_key())


def _call(prompt, max_tokens=800):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Presets aur sliders phir bhi poore available hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": max_tokens},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"Gemini HTTP {e.code}"
    except Exception as e:
        return None, f"Gemini request failed: {type(e).__name__}"
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "Gemini se jawab nahi mila (empty response)."
    return text, None


def advise(goal: str):
    """Suggest a preset + slider starting point for a goal described in
    plain words. Returns (dict|None, error|None). Values are clamped by
    the caller; unknown presets fall back to 'auto'."""
    prompt = f"""A user wants to enhance a photo. Their goal, in their own
words: "{goal}". Reply with ONLY a JSON object, no other text, with
these keys: preset (one of auto, portrait, product, vivid), brightness,
contrast, color, sharpness, warmth, smooth (numbers; brightness/
contrast/color/sharpness between 0.5 and 1.8, warmth between -0.5 and
0.5, smooth between 0 and 0.5), and reason (one short sentence).
Do not invent anything about the photo itself — you cannot see it."""
    text, err = _call(prompt)
    if err:
        return None, err
    try:
        start, end = text.index("{"), text.rindex("}") + 1
        data = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None, "Gemini ka jawab samajh nahi aaya — preset khud chunein."
    if data.get("preset") not in ("auto", "portrait", "product", "vivid"):
        data["preset"] = "auto"
    for key, lo, hi in (("brightness", 0.5, 1.8), ("contrast", 0.5, 1.8),
                        ("color", 0.5, 1.8), ("sharpness", 0.5, 1.8),
                        ("warmth", -0.5, 0.5), ("smooth", 0.0, 0.5)):
        try:
            data[key] = max(lo, min(hi, float(data.get(key, 1.0))))
        except (TypeError, ValueError):
            data[key] = 1.0 if key != "warmth" and key != "smooth" else 0.0
    return data, None
