"""Bayan AI outline generation via Gemini (free tier).

Same call pattern as app/sehatplate/gemini.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged.
Returns structured deck JSON the UI labels clearly as an AI DRAFT.
"""
import json
import os
import urllib.error
import urllib.request

from . import deck as deckmod

MODEL = "gemini-2.5-flash"
TIMEOUT = 60

TONES = ("formal", "punchy", "academic", "friendly")
TONE_GUIDE = {
    "formal": "Boardroom-formal wording, complete sentences.",
    "punchy": "Short, high-energy phrases suitable for a pitch.",
    "academic": "Precise academic wording, suitable for a class lecture.",
    "friendly": "Warm, plain-English wording, suitable for a general audience.",
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt, max_tokens=1600):
    key = _get_key()
    if not key:
        return None, "AI ke liye GEMINI_API_KEY set nahi hai — rule-based draft use karo."
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


OUTLINE_PROMPT = """You are a presentation outliner. Build a slide-deck outline from the
user's topic and notes. Reply with ONLY this JSON, no markdown fences, no extra text:
{"title":"deck title","subtitle":"one-line subtitle",
 "slides":[{"layout":"cover|section|bullets|stats|quote|closing",
            "title":"slide title","bullets":["point 1","point 2"],
            "notes":"speaker notes, 1-2 sentences",
            "quote_by":"attribution (only for quote slides)",
            "stats":[{"value":"42%%","label":"what it measures"}]}]}

Rules:
- First slide layout "cover", last slide "closing". Aim for exactly %d slides.
- Bullets: max 5 per slide, each under 12 words. Tone: %s
- NEVER invent statistics, dates, names, or citations. Use numbers ONLY if they
  appear in the user's notes; otherwise write qualitative bullets. If the notes
  lack data for a stats slide, do not use the stats layout.
- The user may write in English, Roman Urdu, or mixed — reply in the same language
  mix for titles and bullets.
- This is a DRAFT the user will edit; keep it structured and honest.

Topic: %s
Notes: %s
"""


def generate_outline(topic, notes, slide_count=8, tone="punchy"):
    """AI-generate a deck outline. Returns (deck_dict, warnings, error)."""
    topic = (topic or "").strip()
    if not topic:
        return None, [], "Topic likho to outline banaun."
    slide_count = max(deckmod.MIN_SLIDES, min(deckmod.MAX_SLIDES, int(slide_count or 8)))
    tone = tone if tone in TONES else "punchy"
    prompt = OUTLINE_PROMPT % (slide_count, TONE_GUIDE[tone], topic,
                               (notes or "").strip()[:2000] or "(no notes)")
    data, err = _call(prompt)
    if err:
        return None, [], err
    d, warnings = deckmod.normalize_deck(data, max_slides=slide_count)
    warnings.append("AI draft — facts verify kar lena before presenting.")
    return d, warnings, None


REGEN_PROMPT = """You are a presentation editor. Rewrite ONE slide following the user's
instruction. Reply with ONLY this JSON, no markdown fences, no extra text:
{"layout":"cover|section|bullets|stats|quote|closing","title":"...",
 "bullets":["..."],"notes":"...","quote_by":"...","stats":[{"value":"...","label":"..."}]}

Rules:
- Keep the same layout unless the instruction asks to change it.
- Bullets: max 5, each under 12 words. Tone: %s
- NEVER invent statistics, dates, names, or citations.
- Match the deck's language mix.

Deck title: %s
Current slide: %s
Instruction: %s
"""


def regenerate_slide(deck_title, slide, instruction, tone="punchy"):
    """AI-rewrite a single slide. Returns (slide_dict, error)."""
    instruction = (instruction or "").strip()
    if not instruction:
        return None, "Instruction likho — slide ko kya badalna hai?"
    tone = tone if tone in TONES else "punchy"
    prompt = REGEN_PROMPT % (TONE_GUIDE[tone], (deck_title or "").strip()[:120],
                             json.dumps(slide, ensure_ascii=False)[:1500],
                             instruction[:500])
    data, err = _call(prompt, max_tokens=800)
    if err:
        return None, err
    return deckmod.normalize_slide(data), None
