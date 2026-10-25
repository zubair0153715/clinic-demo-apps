"""Ishtehar AI rewrite via Gemini (free tier).

Same call pattern as app/dars/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The rule engine
always works without a key; AI only polishes wording within the same
platform limits.
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


def _call(prompt, max_tokens=2000):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Rule-based variants use karo — wo hamesha available hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens},
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
        return None, "Gemini se jawab nahi mila (empty response)."
    return text, None


def _lang_line(lang: str) -> str:
    if lang == "ur":
        return ("Write EVERYTHING in Urdu script (proper Urdu). Keep English "
                "brand/product names as-is.")
    if lang == "ru":
        return "Write EVERYTHING in Roman-Urdu (Urdu written in Latin letters)."
    return "Write EVERYTHING in clear English."


def ai_rewrite(fields: dict, platform_label: str, lang: str = "en"):
    """Polish one variant's fields. Must respect the same char limits."""
    limits = ", ".join(f"{k} <= {len(v)} chars" for k, v in fields.items())
    prompt = f"""You are an ad copywriter. {_lang_line(lang)}
Rewrite the ad copy below for {platform_label}. Keep the SAME meaning,
product, benefit, offer and call to action — only improve the wording.
Do NOT add new claims, prices, guarantees or facts. Respect these limits
exactly (never exceed them): {limits}.
Return ONLY valid JSON (no markdown fences) with exactly the same keys:
{json.dumps(fields)}

AD COPY:
{json.dumps(fields)}"""
    raw, err = _call(prompt)
    if err:
        return None, err
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None, "AI jawab JSON nahi tha."
    try:
        out = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None, "AI jawab parse nahi ho saka."
    for key in fields:
        out.setdefault(key, fields[key])
    return out, None
