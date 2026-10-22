"""Hisab AI layer via Gemini (free tier).

- Photo -> math problem text (vision).
- Computed solution -> pedagogical explanation (English or Urdu).
- Follow-up "why?" chat grounded in the computed steps.

Key read from the environment AT CALL TIME only, never stored or logged.
The SymPy engine (solver.py) is the source of truth for answers; Gemini only
reads photos and explains — it never invents the answer.
"""
import base64
import io
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 90


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(parts, max_tokens=1500, temperature=0.2):
    key = _get_key()
    if not key:
        return None, "AI ke liye GEMINI_API_KEY set nahi hai."
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": temperature,
                             "maxOutputTokens": max_tokens},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        return None, f"Gemini HTTP {e.code} — key ya quota check karo."
    except Exception as e:
        return None, f"Gemini se rabta nahi ho saka: {type(e).__name__}."
    try:
        obj = json.loads(body)
        raw = obj["candidates"][0]["content"]["parts"][0]["text"].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.lstrip().startswith("json"):
                raw = raw.lstrip()[4:]
        return raw.strip(), None
    except Exception:
        return None, "Gemini ne samajh nahi aaya jawab diya — dobara try karo."


def _shrink_image(image_bytes):
    """Downscale to <=1024px JPEG for the vision call."""
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((1024, 1024))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


READ_PROMPT = """Look at this photo of a math problem. Extract the math problem as
plain text, using ^ for powers and * for multiplication (example: 2x^2+5x-3=0,
d/dx x^3, ∫ 2x dx, lim x->0 sin(x)/x).

Reply with ONLY this JSON, no markdown fences, no extra text:
{"problem": "the extracted problem text",
 "confidence": "high/medium/low",
 "note": "one short line if anything is unclear, else empty"}

Rules:
- Extract ONLY the main math problem. Ignore watermarks, ads, handwriting that
  is not the problem.
- NEVER solve it here — only extract.
- If no math problem is visible, set problem to empty string.
"""


def read_photo(image_bytes):
    """Vision: photo -> problem text. Returns (dict|None, error|None)."""
    data, mime = _shrink_image(image_bytes)
    b64 = base64.b64encode(data).decode()
    parts = [{"text": READ_PROMPT},
             {"inline_data": {"mime_type": mime, "data": b64}}]
    raw, err = _call(parts, max_tokens=600)
    if err:
        return None, err
    try:
        d = json.loads(raw)
    except Exception:
        return None, "Photo parh li lekin text nikalna mushkil hua — type kar ke try karo."
    if not (d.get("problem") or "").strip():
        return None, "Photo mein koi math masla nazar nahi aaya — saaf photo lo ya type karo."
    return d, None


EXPLAIN_PROMPT = """You are a friendly math tutor. A computer-algebra engine has
SOLVED the problem below — the steps and answer are CORRECT and VERIFIED. Your
job is only to TEACH them, not to re-solve.

Reply with ONLY this JSON, no markdown fences, no extra text:
{"key_idea": "the one concept this problem teaches, one sentence",
 "walkthrough": ["2-5 short paragraphs walking through the steps in plain words"],
 "common_mistake": "the most common mistake students make here, one sentence"}

Rules:
- NEVER change the steps or the answer. NEVER invent new steps, numbers, or
  formulas. If a step confuses you, describe it as given.
- Explain in %s.
- Plain words a school student understands. No condescension, no filler.

Problem: %s
Computed steps:
%s
Verified answer: %s
"""


def explain(solution, lang="en"):
    """Pedagogical explanation of a computed solution. Returns (dict, err)."""
    lang_name = ("Urdu (proper Urdu script)" if lang == "ur" else "English")
    steps_txt = "\n".join(
        f"- {s['title']}: {s['math']} ({s.get('note','')})"
        for s in solution.get("steps", []))
    prompt = EXPLAIN_PROMPT % (lang_name, solution.get("input", ""),
                               steps_txt, solution.get("answer", ""))
    raw, err = _call([{"text": prompt}], max_tokens=1200)
    if err:
        return None, err
    try:
        return json.loads(raw), None
    except Exception:
        return {"key_idea": "", "walkthrough": [raw],
                "common_mistake": ""}, None


CHAT_PROMPT = """You are a math tutor answering a follow-up question. A
computer-algebra engine solved the problem below — its steps and answer are
CORRECT and VERIFIED. Answer the student's question using ONLY these steps.

Reply in %s, under 120 words unless detail is asked for.

Rules:
- NEVER invent new steps, numbers, or formulas. Quote or paraphrase the given
  steps.
- If the question is not about this problem, say so plainly and redirect to
  the problem.
- If you are unsure, say so — do not guess.

Problem: %s
Verified steps:
%s
Verified answer: %s

Student's question: %s
"""


def chat(solution, question, lang="en", history=""):
    """Follow-up Q&A grounded in the computed solution. Returns (str, err)."""
    question = (question or "").strip()[:500]
    if not question:
        return None, "Sawal likho — hal ke baare mein kya poochna hai?"
    lang_name = ("Urdu (proper Urdu script)" if lang == "ur" else "English")
    steps_txt = "\n".join(
        f"- {s['title']}: {s['math']}" for s in solution.get("steps", []))
    if history:
        steps_txt += "\n\nPehli guftagu:\n" + history[-1500:]
    prompt = CHAT_PROMPT % (lang_name, solution.get("input", ""), steps_txt,
                            solution.get("answer", ""), question)
    raw, err = _call([{"text": prompt}], max_tokens=500)
    if err:
        return None, err
    return raw, None
