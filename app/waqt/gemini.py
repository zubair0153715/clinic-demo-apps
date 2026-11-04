"""Waqt AI layer — optional Gemini calls: break a big task into
subtasks with durations, or estimate a realistic duration for a
named task.

Same call pattern as the other gap builds (Shajra/Tahqeeq): urllib,
key read from the environment AT CALL TIME only, never stored or
logged. The AI is a convenience only — the deterministic scheduler
and the equal-chunk splitter work at 100% without a key, and when
the key is quota-exhausted the page says so instead of failing the
plan (lesson from the 2026-11-01 Tahqeeq deploy, where Deep mode
429'd on the shared deployed key).
"""
import json
import os
import re
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 120


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available() -> bool:
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Plan phir bhi poora kaam karta hai — scheduler "
                      "deterministic hai, AI sirf andaza aur torna "
                      "ke liye hai.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1000},
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
        return body["candidates"][0]["content"]["parts"][0]["text"], None
    except (KeyError, IndexError, TypeError):
        return None, "Gemini returned an unexpected response."


def breakdown_task(title, minutes, language="en"):
    """Split a task into 2-5 subtasks with minutes that sum to ~minutes.

    Returns (subtasks, error). Subtasks: [{title, minutes}].
    The caller re-validates the sum; a bad AI answer falls back to
    the deterministic equal-chunk split in routes.py.
    """
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    prompt = (
        f"Break this task into 2 to 5 concrete steps {lang_note}. The "
        f"whole task takes about {minutes} minutes. Reply with ONLY one "
        "step per line in the exact format 'Step title - NNm', for "
        "example 'Read chapter 4 - 30m'. The minutes must add up to "
        f"about {minutes}. No numbering, no bullets, no explanation. "
        "Use only realistic steps for this task — do not invent "
        "requirements.\n\nTask: " + title)
    text, err = _call(prompt)
    if err:
        return None, err
    subtasks = []
    for raw in (text or "").splitlines():
        m = re.match(r"^\s*(?:[-*•\d.)\s]+)?(.+?)\s*[-–:]\s*(\d+)\s*m\s*$",
                     raw.strip())
        if not m:
            continue
        step = m.group(1).strip(" -*•")
        mins = int(m.group(2))
        if step and 5 <= mins <= minutes and len(step) <= 80:
            subtasks.append({"title": step, "minutes": mins})
    if len(subtasks) < 2:
        return None, "Gemini ne usable steps nahi diye — dobara try karein."
    total = sum(s["minutes"] for s in subtasks)
    if total <= 0:
        return None, "Gemini ne usable steps nahi diye — dobara try karein."
    # Rescale to the requested total so the plan stays honest.
    scale = minutes / total
    for s in subtasks:
        s["minutes"] = max(5, round(s["minutes"] * scale / 5) * 5)
    drift = minutes - sum(s["minutes"] for s in subtasks)
    subtasks[-1]["minutes"] = max(5, subtasks[-1]["minutes"] + drift)
    return subtasks, None


def estimate_duration(title, language="en"):
    """Suggest a realistic duration in minutes for a named task.

    Returns (minutes, note, error). The number is a suggestion the
    user can edit — never presented as measured fact.
    """
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    prompt = (
        "How long does this task usually take a student or office "
        f"worker, in minutes? Answer {lang_note} with ONLY one line in "
        "the exact format 'NNm - one short reason', for example "
        "'45m - one chapter with notes'. Give a realistic single "
        "number, not a range. Do not invent a study or statistic.\n\n"
        "Task: " + title)
    text, err = _call(prompt)
    if err:
        return None, None, err
    m = re.search(r"(\d+)\s*m", (text or ""))
    if not m:
        return None, None, "Gemini ne usable andaza nahi diya."
    minutes = int(m.group(1))
    if minutes < 5 or minutes > 8 * 60:
        return None, None, "Gemini ka andaza out of range tha."
    note = (text or "").strip().splitlines()[0][:120]
    return minutes, note, None
