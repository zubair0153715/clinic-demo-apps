# -*- coding: utf-8 -*-
"""Kirdar AI layer — in-character chat replies and chat summaries
via Gemini.

Same call pattern as the other gap builds (Daftar/Poda/Bolo):
urllib, key read from the environment AT CALL TIME only, never
stored or logged. Every AI JSON is validated by engine before it
reaches the page.

Rules enforced here and in the engine:
* The model gets the persona, the visible memory card, the running
  summary and the last 10 turns — never a hidden state the user
  cannot see.
* Replies are validated (non-empty, length-capped, remember list
  cleaned to at most 3 short facts).
* The model never claims to be a real person; wholesome only.

Without a key, chat and summaries are unavailable; the roster,
create-your-own, memory card, demo chat and export/import still
work fully.
"""

import json
import os
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call_text(prompt, max_tokens=3000, temperature=0.7):
    """One Gemini generateContent call with text only.
    Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Roster, "
                      "memory card, demo chat aur export/import phir bhi "
                      "poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature,
                             "maxOutputTokens": max_tokens},
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


def chat(character, memory_card, summary, history, message, language="en"):
    """One in-character reply. Returns (result, error) where result is
    {"reply": str, "remember": [facts]}."""
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    message = (message or "").strip()
    if not message:
        return None, "Message khaali hai."
    if len(message) > engine.MAX_MESSAGE:
        return None, "Message 2000 harf se chhota rakhein."
    prompt = engine.build_chat_prompt(
        character, memory_card, summary, history, message, language)
    raw, err = _call_text(prompt, max_tokens=2500, temperature=0.7)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_reply(data)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


SUMMARIZE_PROMPT = """Summarise this chat with {name} ({role}) into a
short memory note, so the character can keep the story straight in
future replies. Write in {lang_word}. Keep it under 800 characters.
Keep: the user's name if given, story facts, decisions made, and
anything promised. Drop: greetings and small talk.

Reply with ONLY a JSON object, no markdown, no extra text:
{{"summary": "The summary text."}}

CHAT:
{turns}"""


def summarize(character, turns, language="en"):
    """Summarise older turns into a running memory note. Returns
    (summary_text, error)."""
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai."
    if not turns:
        return None, "Summarise karne ke liye koi baat-cheet nahi."
    lines = []
    for turn in turns:
        who = "User" if turn.get("role") == "user" else character["name"]
        lines.append(f"{who}: {turn.get('text', '')}")
    lang_word = {"en": "English",
                 "roman": "Roman Urdu",
                 "ur": "Urdu script"}[language]
    prompt = SUMMARIZE_PROMPT.format(
        name=character["name"], role=character["role"],
        lang_word=lang_word, turns="\n".join(lines))
    raw, err = _call_text(prompt, max_tokens=1500, temperature=0.3)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    summary = data.get("summary")
    clean, err = engine.validate_summary(summary)
    if err:
        return None, err
    return clean, None
