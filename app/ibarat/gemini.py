"""Ibarat AI rewrite via Gemini (free tier).

Same call pattern as app/quwwat/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The rule-based
tools always work without a key; AI only adds a neural rewrite on top.
The prompt forbids inventing facts, citations and DOIs.
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


def _call(prompt, max_tokens=3000):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Rule-based tools phir bhi poore available hain.")
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


def ai_rewrite(text, mode="standard"):
    """Neural rewrite. Prompt rules: preserve meaning, keep technical
    terms and numbers exactly, never invent facts, citations or DOIs,
    never claim the result is plagiarism-free or detector-proof."""
    prompt = f"""Rewrite the text below in {mode} style, preserving its
meaning as closely as possible. Keep all technical terms, names,
numbers and quantities EXACTLY as written — do not swap them for
synonyms. Do NOT invent facts, citations, DOIs or references. Do NOT
add claims that are not in the original. Return ONLY the rewritten
text, no explanation.

TEXT:
{text}"""
    return _call(prompt)
