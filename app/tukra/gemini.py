"""Tukra AI moments + hook titles via Gemini (free tier).

Same call pattern as app/jalsa/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The prompt carries a
grounding rule: moments must quote the transcript, never invent.
"""
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


def _call(prompt, max_tokens=2000):
    key = _get_key()
    if not key:
        return None, "AI ke liye GEMINI_API_KEY set nahi hai — rule-based detection use karo."
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
        return json.loads(raw.strip()), None
    except Exception:
        return None, "Gemini ne samajh nahi aaya jawab diya — dobara try karo."


MOMENTS_PROMPT = """You pick viral short-form clips from a transcript. Reply with ONLY this
JSON, no markdown fences, no extra text:
{"moments":[{"start_idx":0,"end_idx":2,"title":"punchy clip title, max 60 chars",
"why":"one line, plain words"}]}

Rules:
- The transcript is numbered by sentence index [0], [1], ... Use ONLY those
  indices. NEVER invent sentences, numbers, or quotes.
- Pick 3-6 moments. Each moment spans 2-6 consecutive sentences.
- Prefer: questions, surprising numbers, mistakes/confessions, how-tos,
  emotional turns, contrarian claims.
- "title" is a scroll-stopping hook title in %s — plain words, no clickbait
  lies; it must match what is actually said.
- "why" explains in one line why this moment holds attention.

Transcript (sentence indices in brackets):
%s
"""


def _numbered(text, sentences=None):
    if sentences is None:
        from . import highlights as hl
        sentences = hl.split_sentences(text)
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(sentences)), sentences


def pick_moments(transcript, lang="en", max_moments=6):
    """AI-pick clip moments. Returns (moments, error)."""
    transcript = (transcript or "").strip()
    if not transcript:
        return None, "Pehle transcript do — phir AI moments nikal sakta hai."
    numbered, sentences = _numbered(transcript)
    if len(numbered) > 20000:
        numbered = numbered[:20000]
    lang_name = {"ur": "Urdu (proper script)", "roman": "Roman-Urdu"}.get(
        lang, "English")
    data, err = _call(MOMENTS_PROMPT % (lang_name, numbered))
    if err:
        return None, err
    moments = []
    n = len(sentences)
    for m in (data.get("moments") or [])[:max_moments]:
        try:
            s0, s1 = int(m["start_idx"]), int(m["end_idx"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (0 <= s0 <= s1 < n) or s1 - s0 > 8:
            continue  # ignore out-of-range / invented indices
        moments.append({"start_idx": s0, "end_idx": s1,
                        "title": str(m.get("title", ""))[:90],
                        "why": str(m.get("why", ""))[:140]})
    if not moments:
        return None, "AI ne koi valid moment nahi diya — rule-based results use karo."
    return moments, None


SOCIAL_PROMPT = """Write ONE ready-to-post social caption for this short clip.
Reply with ONLY JSON: {"caption":"..."}
Rules: start with the hook (max 25 words, plain %s), then 4-6 hashtags mixing
broad (#shorts #reels) and niche tags. NEVER invent facts not in the clip.
Clip text: %s
"""


def write_social_caption(clip_text, lang="en"):
    """AI social caption for one clip. Returns (caption, error)."""
    clip_text = (clip_text or "").strip()[:1500]
    if not clip_text:
        return None, "Clip text khaali hai."
    lang_name = {"ur": "Urdu", "roman": "Roman-Urdu"}.get(lang, "English")
    data, err = _call(SOCIAL_PROMPT % (lang_name, clip_text), max_tokens=400)
    if err:
        return None, err
    cap = data.get("caption") if isinstance(data, dict) else str(data)
    return (cap or "").strip()[:500], None
