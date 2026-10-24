"""Dars AI study pack + grounded chat via Gemini (free tier).

Same call pattern as app/jalsa/gemini.py and app/tukra/gemini.py: urllib,
key read from the environment AT CALL TIME only, never stored or logged.
Prompts carry a grounding rule: outputs must come from the supplied text,
never invented.
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
                      "Rule-based notes use karo — wo hamesha available hain.")
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
        return None, f"Gemini HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except Exception as e:  # network/SSL/proxy on this VM
        return None, f"Gemini request failed: {type(e).__name__}: {e}"
    try:
        text = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None, "Gemini se jawab nahi mila (empty response)."
    return text, None


def _lang_line(lang: str) -> str:
    if lang == "ur":
        return ("Write EVERYTHING in Urdu script (proper Urdu). Keep English "
                "technical terms as-is where natural.")
    if lang == "ru":
        return ("Write EVERYTHING in Roman-Urdu (Urdu written in Latin letters).")
    return "Write EVERYTHING in clear English."


def ai_study_pack(text: str, lang: str = "en"):
    prompt = f"""You are a study assistant. {_lang_line(lang)}
Use ONLY the study text below. Do not invent facts, terms, or examples.
Return ONLY valid JSON (no markdown fences) with exactly these keys:
{{"notes": [{{"heading": "...", "points": ["...", "..."]}}],
  "flashcards": [{{"front": "...", "back": "..."}}],
  "quiz": [{{"question": "...", "options": ["A","B","C","D"], "answer": 0}}]}}
Rules: notes = outline of the text (each point rephrases, never invents);
flashcards: front = a key term from the text, back = its explanation in your
own words from the text; quiz: 8 multiple-choice, answer = index of correct
option, distractors plausible but clearly wrong per the text. 25 headings max,
20 flashcards max.

STUDY TEXT:
{text[:12000]}"""
    raw, err = _call(prompt, max_tokens=4000)
    if err:
        return None, err
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None, "AI jawab JSON nahi tha."
    try:
        pack = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return None, "AI jawab parse nahi ho saka."
    for key in ("notes", "flashcards", "quiz"):
        pack.setdefault(key, [])
    return pack, None


def ai_chat(text: str, question: str, lang: str = "en"):
    prompt = f"""You are a study tutor. {_lang_line(lang)}
Answer the student's question using ONLY the study text below. If the answer
is not in the text, say so plainly and do not guess. Keep it short.

STUDY TEXT:
{text[:12000]}

QUESTION: {question}"""
    return _call(prompt)
