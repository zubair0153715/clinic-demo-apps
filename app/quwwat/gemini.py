"""Quwwat AI notes via Gemini (free tier).

Same call pattern as app/ishtehar/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The planner always
works without a key; AI only adds coaching notes on top of the plan.
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
                      "Plan phir bhi poora ka poora available hai.")
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
                "exercise names as-is.")
    if lang == "ru":
        return "Write EVERYTHING in Roman-Urdu (Urdu written in Latin letters)."
    return "Write EVERYTHING in clear English."


def ai_explain(summary: str, lang: str = "en"):
    """Coaching notes for a generated plan. Never invents loads, never
    gives medical advice — form cues and 'why this split' only."""
    prompt = f"""You are a strength-training coach writing notes for a beginner-to-intermediate lifter. {_lang_line(lang)}
Explain briefly (under 250 words): why this weekly split makes sense, one form cue per main lift mentioned, and how to progress next week. Do NOT invent weights, sets or reps beyond what is in the plan below. Do NOT give medical advice; if the plan mentions an injury filter, remind the reader to stop on sharp pain and see a clinician. No guarantees about results.

PLAN:
{summary}"""
    return _call(prompt)
