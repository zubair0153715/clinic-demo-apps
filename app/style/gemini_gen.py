"""Gemini image-edit visualization for Style Advisor.
Reads GEMINI_API_KEY from the environment AT CALL TIME only.
No key anywhere in code, files, or memory. Nothing is stored.
Stateless: photo goes in, edited photo comes back (or a reason why not).
"""
import base64
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash-image"  # "nano banana" image model
TIMEOUT = 60


def _get_key():
    """Read the key at call time. Accepts the exact name plus the common
    case-variant (dashboard typos happen). Never stored anywhere."""
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    """True if a Gemini API key is configured."""
    return bool(_get_key())


def build_prompt(moustache_name, beard_name, hairstyle_name):
    parts = []
    if moustache_name:
        parts.append(f"a {moustache_name}")
    if beard_name and beard_name.lower() not in ("clean shaven", "clean shave"):
        parts.append(f"a {beard_name}")
    if hairstyle_name:
        parts.append(f"{hairstyle_name} hairstyle")
    style_txt = ", ".join(parts) if parts else "a neat, stylish grooming look"
    return (
        f"Edit this photo: give the person in the photo {style_txt}. "
        "IMPORTANT: keep the person's face, identity, facial features, skin tone, "
        "expression, age, background, lighting and overall photo style EXACTLY unchanged. "
        "Only modify the facial hair and hair. The result must be photorealistic, "
        "as if taken with the same camera in the same moment."
    )


def _extract_image(data):
    try:
        obj = json.loads(data)
    except Exception:
        return None, "Gemini se ghalat jawab aaya."
    cands = obj.get("candidates") or []
    for c in cands:
        for p in (c.get("content") or {}).get("parts") or []:
            inline = p.get("inlineData") or p.get("inline_data")
            if inline and inline.get("data"):
                try:
                    return base64.b64decode(inline["data"]), None
                except Exception:
                    return None, "Tasveer decode nahi ho saki."
    err = (obj.get("error") or {}).get("message", "")
    if err:
        return None, f"Gemini error: {err[:160]}"
    return None, "Gemini ne tasveer nahi banayi — dobara try karo."


def visualize(image_bytes, prompt):
    """Apply the style prompt to the photo via Gemini image editing.

    Args:
        image_bytes: original photo bytes (JPEG/PNG)
        prompt: what to change (from build_prompt)

    Returns:
        (png_or_jpeg_bytes, None) on success,
        (None, reason_string) when the key is missing or the call fails.
    """
    key = _get_key()
    if not key:
        return None, ("GEMINI_API_KEY set nahi hai — ye step owner ki free Gemini "
                      "API key add hone ke baad active hoga.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/jpeg",
                                 "data": base64.b64encode(image_bytes).decode()}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode()[:300]
        except Exception:
            err_body = ""
        return None, (f"Gemini HTTP {e.code}: {err_body or 'koi tafseel nahi'}. "
                      "Key ghalat, restricted, ya quota khatam ho sakti hai.")
    except Exception as e:
        return None, f"Gemini se rabta nahi ho saka: {type(e).__name__}."
    return _extract_image(body)
