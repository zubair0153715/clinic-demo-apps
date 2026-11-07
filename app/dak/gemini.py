"""Dak AI layer — optional Gemini triage, thread summary and drafts.

Same call pattern as the other gap builds (Khulasa/Zubaan/Waqt/
Shajra/Tahqeeq): urllib, key read from the environment AT CALL
TIME only, never stored or logged. The AI only reads text the USER
pastes — it never connects to an inbox, never sends anything.
Every draft the AI writes is screened by engine.safety_check
before it reaches the page, and the page tells the user to verify
before sending. The rule-based triage, demo inbox, snooze and
follow-up lists work at 100% without a key.
"""

import json
import os
import re
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120

LANG_INSTRUCTIONS = {
    "en": "Write in clear, simple English.",
    "roman": ("Write in Roman Urdu — Urdu written in Latin letters, "
              "the way Pakistanis type on WhatsApp. Keep it natural, "
              "not a word-for-word translation."),
    "ur": ("Write in Urdu script (proper Urdu, Nastaliq-style wording). "
           "Keep sentences short and clear."),
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Rule-based "
                      "triage, demo inbox, snooze aur Safety Check phir bhi "
                      "poore kaam karte hain.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2500},
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


def _extract_json(raw):
    """Pull a JSON object out of the model's reply, tolerating
    ```json fences and surrounding prose."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def triage_ai(subject, body, language):
    """AI triage of one pasted email.

    Returns (result_dict, error). result_dict: category (one of
    engine.CATEGORIES), score 0-100, summary (one line), actions
    (1-5 short strings). The rule-based triage in engine is always
    shown next to it, so the user can see where they disagree.
    """
    ok, err = engine.validate_paste(f"{subject or ''}\n{body or ''}")
    if not ok:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    lang_note = LANG_INSTRUCTIONS[language]
    cats = ", ".join(sorted(engine.CATEGORIES))
    prompt = (
        "You are a careful email triage assistant. Triage ONLY the email "
        "below. Do not invent facts, senders, dates or amounts that are "
        "not in the email. If something is unclear, say so in the summary "
        "instead of guessing.\n\n"
        f"Categories (pick exactly one): {cats}.\n{lang_note}\n\n"
        "Reply with ONLY a JSON object, no other text, in exactly this shape:\n"
        '{"category": "jobs", "score": 82, '
        '"summary": "one-line summary, max 25 words", '
        '"actions": ["action 1", "action 2"]}\n\n'
        "Rules: score 0-100 = how urgently this needs the reader's "
        "attention (100 = drop everything). summary = what this email "
        "is and what it wants, in one line. actions = 1-5 concrete next "
        "steps for the reader.\n\n"
        f"SUBJECT: {subject or '(no subject)'}\n\nEMAIL:\n{(body or '').strip()}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    result = _extract_json(raw)
    if result is None:
        return None, "AI ka jawab samajh nahi aaya (JSON nahi mila). Dobara try karein."
    errors = engine.validate_ai_triage(result)
    if errors:
        return None, "AI ka jawab poora nahi tha: " + "; ".join(errors)
    return result, None


def draft_reply(thread_text, tone, language):
    """Draft a reply to a pasted thread, then Safety-Check it.

    tone: short / polite / firm. Returns (result_dict, error).
    result_dict: draft, tone, safety (list of flags from
    engine.safety_check). The draft is NEVER sent by the app — the
    user copies it and sends it themselves.
    """
    ok, err = engine.validate_paste(thread_text)
    if not ok:
        return None, err
    if tone not in ("short", "polite", "firm"):
        return None, "Tone ghalat hai — short, polite ya firm chunein."
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    lang_note = LANG_INSTRUCTIONS[language]
    tone_note = {
        "short": "Keep the reply short — 3-5 sentences, no fluff.",
        "polite": "Keep the reply warm and polite, professional tone.",
        "firm": "Keep the reply firm and direct — clear boundaries, no hedging.",
    }[tone]
    prompt = (
        "You are a careful email writing assistant. Draft a reply to the "
        "email thread below. Use ONLY facts from the thread. Do not invent "
        "dates, amounts, promises or attachments. Do not agree to any "
        "meeting time, payment or commitment unless the thread already "
        "states it clearly. If the thread asks for something unclear, "
        "draft a reply that ASKS for clarification instead of guessing.\n\n"
        f"{tone_note}\n{lang_note}\n\n"
        "Reply with ONLY a JSON object, no other text, in exactly this shape:\n"
        '{"draft": "the full reply text", "tone": "short"}\n\n'
        f"THREAD:\n{thread_text.strip()}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    result = _extract_json(raw)
    if result is None:
        return None, "AI ka jawab samajh nahi aaya (JSON nahi mila). Dobara try karein."
    errors = engine.validate_ai_draft(result)
    if errors:
        return None, "AI ka jawab poora nahi tha: " + "; ".join(errors)
    result["safety"] = engine.safety_check(result["draft"], thread_text)
    return result, None


def summarize_thread(thread_text, language):
    """Summarise a whole pasted thread: summary, decisions, open
    questions, actions with owners.

    Returns (result_dict, error). The model is told to read EVERY
    message in the thread — Superhuman's auto-respond famously only
    reads the latest one.
    """
    ok, err = engine.validate_paste(thread_text)
    if not ok:
        return None, err
    if language not in engine.LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    lang_note = LANG_INSTRUCTIONS[language]
    prompt = (
        "You are a careful email assistant. Read EVERY message in the "
        "thread below — not just the latest one — and summarise it. Do "
        "not invent decisions, dates, owners or amounts. If a point is "
        "unresolved, list it under open_questions instead of guessing.\n\n"
        f"{lang_note}\n\n"
        "Reply with ONLY a JSON object, no other text, in exactly this shape:\n"
        '{"summary": "2-4 sentence summary of the whole thread", '
        '"decisions": ["decision 1"], '
        '"open_questions": ["question 1"], '
        '"actions": [{"text": "action", "owner": "name or \'?\'"}]}\n\n'
        "Rules: summary = the whole thread in 2-4 sentences. decisions "
        "= things already decided in the thread (empty list if none). "
        "open_questions = things still unanswered. actions = concrete "
        "next steps with whoever owns them ('?' if the thread does not say).\n\n"
        f"THREAD:\n{thread_text.strip()}"
    )
    raw, err = _call(prompt)
    if err:
        return None, err
    result = _extract_json(raw)
    if result is None:
        return None, "AI ka jawab samajh nahi aaya (JSON nahi mila). Dobara try karein."
    errors = engine.validate_ai_thread(result)
    if errors:
        return None, "AI ka jawab poora nahi tha: " + "; ".join(errors)
    return result, None
