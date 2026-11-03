"""Tarteeb AI tailoring via Gemini (free tier).

Same call pattern as app/qabil/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The prompt
forbids inventing facts, employers, numbers or results — AI may only
reword what the user already wrote, and only towards the JD's wording.
The deterministic tools always work without a key.

Reply format is PLAIN TEXT (a SUMMARY: line + numbered bullets), not
JSON — model JSON with unescaped quotes/newlines inside strings kept
failing to parse live, while numbered lines parse robustly.
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


def _call(prompt, max_tokens=4000):
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


def _parse_tailored_lines(text, bullets):
    """Parse Gemini's plain-text reply: a numbered list of tailored
    bullets in the SAME order as the input, plus a SUMMARY: section."""
    summary = ""
    m = re.search(r"SUMMARY\s*:\s*(.*?)(?=^\s*\d+[.)]\s|\Z)",
                  text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if m:
        summary = " ".join(m.group(1).split())
    out = []
    for num, tail in re.findall(r"^\s*(\d+)[.)]\s+(.+)$", text,
                                flags=re.MULTILINE):
        idx = int(num) - 1
        tail = tail.strip()
        if 0 <= idx < len(bullets) and tail:
            out.append({"original": bullets[idx], "tailored": tail})
    seen = set()
    clean = []
    for item in sorted(out, key=lambda x: bullets.index(x["original"])):
        if item["original"] not in seen:
            seen.add(item["original"])
            clean.append(item)
    return {"summary": summary, "bullets": clean}


def ai_tailor(resume_text, jd_text, bullets):
    """AI rewrite of the user's own bullets + summary, matched to the JD.

    Returns ({"summary": str, "bullets": [{"original": str, "tailored": str}]}, None)
    or (None, error). Every tailored bullet maps back to one of the
    supplied originals by position; anything unmapped is dropped,
    never invented."""
    numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
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
- Reply in PLAIN TEXT only, no JSON, no markdown, no explanation:
  first a line "SUMMARY: <rewritten summary, 2-3 lines, facts only>",
  then the rewritten bullets as a numbered list in the SAME order as
  below, one per line, "1. <bullet>" etc. Keep every bullet on ONE line.

JOB DESCRIPTION:
{jd_text}

RESUME SUMMARY:
{(resume_text or "")[:2000]}

BULLETS:
{numbered}"""
    text, err = _call(prompt)
    if err:
        return None, err
    data = _parse_tailored_lines(text, bullets)
    if not data["bullets"] and not data["summary"]:
        text2, err2 = _call(prompt + "\n\nRemember: plain text only, "
                             "SUMMARY: line first, then numbered bullets.")
        if err2:
            return None, err2
        data = _parse_tailored_lines(text2, bullets)
    if not data["bullets"] and not data["summary"]:
        return None, ("Gemini se usable tailoring nahi mili — deterministic "
                      "tailoring istemal karein.")
    return data, None
