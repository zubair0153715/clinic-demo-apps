"""Tarteeb AI tailoring via Gemini (free tier).

Same call pattern as app/qabil/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The prompt
forbids inventing facts, employers, numbers or results — AI may only
reword what the user already wrote, and only towards the JD's wording.
The deterministic tools always work without a key.
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


def _parse_json_response(text):
    """Parse Gemini's reply as JSON, tolerating markdown fences and
    preamble/trailing prose around the object."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(),
                     flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        return json.loads(cleaned[start:end + 1])
    raise json.JSONDecodeError("no JSON object found", cleaned, 0)
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Rule-based tailoring phir bhi poora available hai.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": max_tokens},
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


def ai_tailor(resume_text, jd_text, bullets):
    """AI rewrite of the user's own bullets + summary, matched to the JD.

    Returns ({"summary": str, "bullets": [{"original": str, "tailored": str}]}, None)
    or (None, error). Every tailored bullet must map back to one of the
    supplied originals; anything unmapped is dropped, never invented."""
    prompt = f"""You are tailoring a resume to a job description. Rewrite the
resume bullets and summary below so they speak the job description's
language. STRICT RULES:
- Use ONLY facts already in the original text. Do NOT invent numbers,
  percentages, results, employers, job titles, degrees, skills or
  achievements. Do NOT add any claim that is not in the original.
- Keep all names, numbers, quantities and employers EXACTLY as written.
- Start each bullet with a strong action verb. Prefer the JD's own
  wording for skills the resume already shows (e.g. if the JD says
  "LLM integration" and the resume says "RAG systems", keep the fact
  but use the JD's term only where it means the same thing).
- If a JD requirement is NOT in the resume, do NOT add it — leave it out.
- Return ONLY valid JSON, no markdown fences, no explanation:
{{"summary": "rewritten summary, 2-3 lines, facts only",
  "bullets": [{{"original": "<exact original bullet>",
                "tailored": "<rewritten bullet>"}}]}}
One entry per bullet below, in the same order.

JOB DESCRIPTION:
{jd_text}

RESUME SUMMARY:
{(resume_text or "")[:2000]}

BULLETS:
{chr(10).join("- " + b for b in bullets)}"""
    text, err = _call(prompt)
    if err:
        return None, err
    try:
        data = _parse_json_response(text)
    except json.JSONDecodeError:
        # one retry with a stricter instruction, then give up honestly
        text2, err2 = _call(prompt + "\n\nReturn ONLY the JSON object. "
                            "No preamble, no markdown, no explanation.")
        if err2:
            return None, err2
        try:
            data = _parse_json_response(text2)
        except json.JSONDecodeError:
            return None, ("Gemini ne valid JSON nahi diya — deterministic "
                          "tailoring istemal karein.")
    summary = (data.get("summary") or "").strip()
    out_bullets = []
    originals = {b.strip(): b for b in bullets}
    for item in data.get("bullets") or []:
        orig = (item.get("original") or "").strip()
        tailored = (item.get("tailored") or "").strip()
        if orig in originals and tailored:
            out_bullets.append({"original": originals[orig],
                                "tailored": tailored})
    if not out_bullets and not summary:
        return None, "Gemini se usable tailoring nahi mili — deterministic tailoring istemal karein."
    return {"summary": summary, "bullets": out_bullets}, None
