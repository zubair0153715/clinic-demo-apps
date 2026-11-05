"""Zubaan AI layer — optional Gemini open roleplay chat.

Same call pattern as the other gap builds (Waqt/Shajra/Tahqeeq):
urllib, key read from the environment AT CALL TIME only, never
stored or logged. The AI only continues a roleplay scene and
corrects the learner's last sentence. All scripted scenarios,
quizzes and dictation work at 100% without a key, and when the
key is quota-exhausted the page says so instead of failing.
"""

import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 120


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Scripted "
                      "scenarios phir bhi poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.5, "maxOutputTokens": 600},
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
        return None, f"AI error (HTTP {e.code}). Scripted scenario use karein."
    except Exception as exc:  # network, timeout, bad JSON
        return None, f"AI se rabta nahi hua ({exc}). Scripted scenario use karein."
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"].strip(), None
    except (KeyError, IndexError, TypeError):
        return None, "AI ne khaali jawab diya. Dobara try karein."


def roleplay_reply(scenario_title, setting, history, learner_text):
    """Continue a roleplay scene.

    history: list of {"who": "you"|"ai", "text": str}. Returns
    (reply_text, error). The reply must: correct the learner's
    sentence briefly if it has a mistake, then continue the scene
    in character, in simple English, max 3 short sentences.
    """
    convo = "\n".join(
        f"{'Learner' if h['who'] == 'you' else 'Partner'}: {h['text']}"
        for h in history[-8:])
    prompt = (
        "You are a friendly English tutor roleplaying a scene. "
        f"Scene: {scenario_title}. Setting: {setting}\n"
        f"Conversation so far:\n{convo}\n"
        f"Learner just said: {learner_text}\n"
        "Reply in character, in SIMPLE English (max 3 short sentences). "
        "If the learner's sentence has a grammar mistake, first give "
        "the corrected sentence in brackets, e.g. [Correction: ...], "
        "then continue the scene. Stay in the scene, never lecture."
    )
    return _call(prompt)
