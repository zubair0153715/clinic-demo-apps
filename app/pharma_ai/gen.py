"""Answer generation via the owner's free Gemini key (text model).

Same rules as the style module: key read from the environment AT CALL TIME
only, never stored. When the key is missing or the quota is exhausted the
caller gets (None, reason) and must fall back to showing raw passages.
"""
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 60

SYSTEM = (
    "You are PharmaAI, a study assistant for a Pharm-D student. "
    "Answer the question using ONLY the source passages provided below. "
    "Cite every factual claim as [Document title, Section]. "
    "If the passages do not contain the answer, say so clearly instead of guessing. "
    "Keep the answer focused, structured, and in the student's language (English). "
    "This is a study aid, not medical advice."
)

DISCLAIMER = ("Study aid only — not medical advice. "
              "Verify with your textbooks and a qualified pharmacist/doctor.")


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _extract_text(data):
    try:
        obj = json.loads(data)
    except Exception:
        return None, "Gemini se ghalat jawab aaya."
    cands = obj.get("candidates") or []
    parts = []
    for c in cands:
        for p in (c.get("content") or {}).get("parts") or []:
            if p.get("text"):
                parts.append(p["text"])
    if parts:
        return "".join(parts).strip(), None
    err = (obj.get("error") or {}).get("message", "")
    if err:
        return None, f"Gemini error: {err[:160]}"
    return None, "Gemini ne jawab nahi diya."


def generate(question, passages):
    """Generate a grounded answer.

    passages: list of chunk dicts (doc_title, section, page_start, text).
    Returns (answer_text_or_None, None) on success,
    (None, reason_string) when generation is unavailable.
    """
    key = _get_key()
    if not key:
        return None, ("GEMINI_API_KEY set nahi hai — AI jawab ke liye owner ki "
                       "free Gemini key chahiye. Neeche kitab se mile hue "
                       "passages dikhaye gaye hain.")
    src = []
    for i, p in enumerate(passages, 1):
        src.append(
            f"[Passage {i} — {p['doc_title']}, {p['section']}, "
            f"p.{p['page_start']}]\n{p['text'][:1800]}")
    prompt = (SYSTEM + "\n\nSOURCES:\n" + "\n\n".join(src) +
              f"\n\nQUESTION: {question}\n\nANSWER (with citations):")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200}}
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None, ("Gemini quota khatam (HTTP 429) — thori der baad "
                           "dobara try karo. Neeche passages maujood hain.")
        try:
            err_body = e.read().decode()[:200]
        except Exception:
            err_body = ""
        return None, f"Gemini HTTP {e.code}: {err_body or 'koi tafseel nahi'}."
    except Exception as e:
        return None, f"Gemini se rabta nahi ho saka: {type(e).__name__}."
    text, err = _extract_text(body)
    if err:
        return None, err
    return text + "\n\n_" + DISCLAIMER + "_", None
