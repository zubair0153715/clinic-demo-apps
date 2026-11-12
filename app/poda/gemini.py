# -*- coding: utf-8 -*-
"""Poda AI layer — Gemini vision identification and diagnosis.

Same call pattern as the other gap builds (Bolo/Zehn/Sathi/Sukoon/
Dak/Khulasa): urllib, key read from the environment AT CALL TIME
only, never stored or logged. The AI only reads a photo the USER
uploaded, plus a language choice. Every AI JSON is validated by
engine.validate_ai_* before it reaches the page, and labelled
"AI-written" on the page.

Safety rules enforced here and in the engine:
* The prompt tells the model to refuse non-plants (plastic plant,
  drawing, object, person, animal) with is_plant false.
* The prompt tells the model to NEVER call a plant safe to eat,
  and the validator refuses any payload that does.
* The prompt tells the model to lower confidence and say so when
  two species look alike (neem vs chinaberry/bakain is the classic
  case). Confidence is shown to the user, never hidden.

Without a key, identification and diagnosis are unavailable; the
common-plants table, watering calculator and My Plants still work
fully.
"""

import base64
import json
import os
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120

LANG_INSTRUCTIONS = {
    "en": "Write the description, care text and season note in clear, "
           "simple English.",
    "roman": ("Write the description, care text and season note in "
              "Roman Urdu — Urdu written in Latin letters, the way "
              "Pakistanis type on WhatsApp."),
    "ur": ("Write the description, care text and season note in Urdu "
           "script (proper Urdu, Nastaliq-style wording). Keep "
           "sentences short and clear."),
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call_vision(prompt, image_b64, mime):
    """One Gemini generateContent call with an inline image.
    Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Aam "
                      "podon ki table, paani ka hisaab aur My Plants "
                      "phir bhi poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": mime, "data": image_b64}},
        ]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2000},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return None, "AI quota khatam (429). Thodi der baad dobara try karein."
        return None, f"AI error (HTTP {e.code}). Dobara try karein."
    except Exception as exc:  # network, timeout, bad JSON
        return None, f"AI se rabta nahi hua ({exc}). Dobara try karein."
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip(), None
    except (KeyError, IndexError, TypeError):
        return None, "AI ne khaali jawab diya. Dobara try karein."


def _parse_json(raw):
    """Parse the model's JSON, tolerating ```json fences."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    try:
        data = json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return None, "AI ka jawab JSON nahi tha. Dobara try karein."
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    return data, None


def _check_language(language):
    if language not in engine.LANGUAGES:
        return "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    return None


IDENTIFY_PROMPT = """You are a careful botanist. Identify the living plant in this photo.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "common_name_en": "English common name",
 "name_ur": "Urdu name in Urdu script",
 "name_roman": "Roman-Urdu name in Latin letters",
 "scientific_name": "Genus species",
 "confidence": 0-100,
 "is_plant": true,
 "description": "2-3 sentences about this plant",
 "care": {{"water": "how often to water", "sunlight": "light needs",
           "soil": "soil needs", "temperature": "temperature range"}},
 "toxicity_humans": "toxicity for humans, or 'Not known to be toxic'",
 "toxicity_pets": "toxicity for pets, or 'Not known to be toxic'",
 "safe_to_eat": false,
 "edible_warning": "Do not eat, smoke or use this plant as medicine based on an app identification. Verify with a local botanist or doctor first.",
 "season_note_pk": "How this plant handles Pakistani summer heat and winter, in 1-2 sentences"
}}
Rules:
- If the photo is NOT a real living plant (plastic plant, drawing, painting, object, person, animal, food on a plate), set "is_plant": false, "confidence": 0, and leave the name fields empty. Do NOT invent a plant.
- NEVER say a plant is safe to eat. "safe_to_eat" is ALWAYS false.
- If you are unsure between two similar species (for example neem Azadirachta indica vs chinaberry Melia azedarach, which look alike), say so in the description and set confidence BELOW 60.
- Keep the description under 400 characters."""


def identify(image_b64, mime, language="en"):
    """Identify the plant in the user's photo. Returns
    (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if not image_b64 or not mime:
        return None, "Pehle poday ki photo dein."
    prompt = IDENTIFY_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language])
    raw, err = _call_vision(prompt, image_b64, mime)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_identification(data)
    if err:
        return None, err
    clean["ai"] = True
    clean["language"] = language
    # Attach the verified local care table when the species is one
    # of the 10 common plants — published intervals beat AI guesses.
    table = engine.match_common_plant(clean["scientific_name"])
    if table:
        clean["verified_table"] = {
            "id": table["id"],
            "water_summer": table["water_summer"],
            "water_winter": table["water_winter"],
            "sunlight_en": table["sunlight_en"],
            "sunlight_ur": table["sunlight_ur"],
            "tip_en": table["tip_en"],
            "tip_roman": table["tip_roman"],
            "source": table["source"],
        }
    return clean, None


DIAGNOSE_PROMPT = """You are a careful plant doctor. Look at this photo of a plant that may be sick.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "problem_en": "Short name of the likely problem in English",
 "problem_ur": "Short name of the likely problem in Urdu script",
 "severity": "mild, moderate or severe",
 "confidence": 0-100,
 "likely_causes": ["cause 1", "cause 2"],
 "treatment_steps": ["step 1", "step 2", "step 3"],
 "when_to_seek_help": "When home care is not enough, in 1-2 sentences"
}}
Rules:
- If the plant looks healthy, say so: problem_en "Looks healthy", severity "mild", and give care tips as treatment steps.
- If the photo is NOT a real living plant, set confidence 0 and problem_en "Not a plant".
- A photo cannot confirm every plant-health problem. Say what to check in person (underside of leaves, roots, soil wetness).
- Never prescribe a chemical by brand name; name the type of treatment only (for example "neem oil spray" or "remove affected leaves").
- Keep each list item under 300 characters."""


def diagnose(image_b64, mime, language="en"):
    """Diagnose a possibly sick plant from the user's photo.
    Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if not image_b64 or not mime:
        return None, "Pehle poday ki photo dein."
    prompt = DIAGNOSE_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language])
    raw, err = _call_vision(prompt, image_b64, mime)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_diagnosis(data)
    if err:
        return None, err
    clean["ai"] = True
    clean["language"] = language
    return clean, None


def identify_from_file(image_bytes, mime, language="en"):
    """Convenience wrapper: bytes in, validated result out. Used by
    the route and by tests/live_check.py."""
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        return None, "Photo khaali hai."
    if len(image_bytes) > engine.MAX_IMAGE_BYTES:
        return None, "Photo 5 MB se bari hai — chhoti photo dein."
    b64 = base64.b64encode(bytes(image_bytes)).decode("ascii")
    clean, err = engine.validate_image(
        mime, len(image_bytes), b64)
    if err:
        return None, err
    return identify(b64, mime, language)


def diagnose_from_file(image_bytes, mime, language="en"):
    """Convenience wrapper for diagnosis: bytes in, result out."""
    if not isinstance(image_bytes, (bytes, bytearray)) or not image_bytes:
        return None, "Photo khaali hai."
    if len(image_bytes) > engine.MAX_IMAGE_BYTES:
        return None, "Photo 5 MB se bari hai — chhoti photo dein."
    b64 = base64.b64encode(bytes(image_bytes)).decode("ascii")
    clean, err = engine.validate_image(
        mime, len(image_bytes), b64)
    if err:
        return None, err
    return diagnose(b64, mime, language)
