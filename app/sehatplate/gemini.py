"""SehatPlate AI meal estimation via Gemini (free tier).

Same call pattern as app/style/gemini_gen.py: urllib, key read from the
environment AT CALL TIME only, never stored or logged.
Returns structured nutrition JSON the UI labels clearly as an AI ESTIMATE.
"""
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 45


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


PROMPT = """You are a nutrition estimator. The user describes a meal in plain words
(may be English, Roman Urdu, or mixed). Estimate its nutrition honestly.

Rules:
- Guess realistic Pakistani/South-Asian portion sizes when not specified
  (1 roti ~40g, 1 plate biryani ~300g, 1 cup chai ~150ml, 1 bowl daal ~200g).
- Break the meal into items. For each item give grams and kcal/protein/carbs/fat.
- If you are unsure about an item, say so in the note and pick the closest match.
- NEVER invent brand nutrition facts. Prefer simple whole-food estimates.
- Reply with ONLY this JSON, no markdown fences, no extra text:
{"items":[{"name":"...","grams":0,"kcal":0,"protein":0,"carbs":0,"fat":0}],
 "totals":{"kcal":0,"protein":0,"carbs":0,"fat":0},
 "confidence":"low|medium|high","note":"one short sentence"}

Meal: """


def estimate_meal(text):
    """Estimate nutrition for free-text meal description.

    Returns (result_dict, None) on success, (None, reason) on failure.
    """
    key = _get_key()
    if not key:
        return None, "AI estimate ke liye GEMINI_API_KEY set nahi hai."
    text = (text or "").strip()[:500]
    if not text:
        return None, "Khana likho to estimate karun — khaali text aaya hai."
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": PROMPT + text}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800},
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
        data = json.loads(raw.strip())
        items = data.get("items") or []
        for it in items:
            for k in ("grams", "kcal", "protein", "carbs", "fat"):
                it[k] = round(float(it.get(k, 0) or 0), 1)
        t = data.get("totals") or {}
        totals = {k: round(float(t.get(k, 0) or 0), 1)
                  for k in ("kcal", "protein", "carbs", "fat")}
        return {"items": items, "totals": totals,
                "confidence": str(data.get("confidence", "medium")),
                "note": str(data.get("note", ""))[:200],
                "ai_estimate": True}, None
    except Exception:
        return None, "Gemini ne samajh nahi aaya jawab diya — dobara try karo."
