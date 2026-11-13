# -*- coding: utf-8 -*-
"""Daftar AI layer — grounded chat, audio-overview scripts and study
kits from the USER's own sources, via Gemini.

Same call pattern as the other gap builds (Poda/Bolo/Zehn/Sathi):
urllib, key read from the environment AT CALL TIME only, never
stored or logged. Every AI JSON is validated by
engine.validate_ai_* before it reaches the page, and labelled
"AI-written" on the page.

Grounding rules enforced here and in the engine:
* The model is given ONLY the retrieved chunks, never the whole
  library, and is told to answer only from them.
* Every citation quote must appear word-for-word in the cited
  chunk — engine.check_citations rejects invented quotes. This
  is the checkable-grounding gap NotebookLM leaves open.
* If the chunks do not contain the answer, the model must say so
  (not_found true) instead of inventing one.
* The model never adds facts from its own knowledge to a grounded
  answer; anything beyond the sources is labelled as such.

Without a key, chat, audio scripts and the study kit are
unavailable; the library, chunking, PDF extraction and source
search still work fully.
"""

import json
import os
import urllib.error
import urllib.request

from . import engine

MODEL = "gemini-2.5-flash"
TIMEOUT = 120

LANG_INSTRUCTIONS = {
    "en": "Write everything in clear, simple English.",
    "roman": ("Write everything in Roman Urdu — Urdu written in Latin "
              "letters, the way Pakistanis type on WhatsApp."),
    "ur": ("Write everything in Urdu script (proper Urdu). Keep "
           "sentences short and clear."),
}


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available():
    return bool(_get_key())


def _call_text(prompt, max_tokens=4000, temperature=0.3):
    """One Gemini generateContent call with text only.
    Returns (text, error)."""
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. Library, "
                      "chunking, PDF aur source search phir bhi poore "
                      "kaam karte hain.")
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


def _check_language(language):
    if language not in engine.LANGUAGES:
        return "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    return None


def _chunks_block(chunks):
    """Render retrieved chunks for the prompt, with their ids."""
    lines = []
    for ch in chunks:
        lines.append(f"[{ch['id']}] (source: {ch['source_id']})\n{ch['text']}")
    return "\n\n".join(lines)


CHAT_PROMPT = """You are a careful study tutor. Answer the student's question
USING ONLY the source chunks below. Do not use your own knowledge.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "answer": "Your answer, in 2-6 sentences. Every factual sentence must come from the chunks.",
 "not_found": false,
 "citations": [{{"chunk_id": "S1-C2", "quote": "exact words copied word-for-word from that chunk"}}]
}}
Rules:
- "quote" must be copied EXACTLY from the chunk text — same words, same order. Do not paraphrase inside a quote. Keep each quote under 300 characters.
- Cite 1-4 chunks. Every factual claim in the answer needs a citation.
- If the chunks do NOT contain the answer, set "not_found": true, "citations": [], and write the answer as: "Ye jawab in sources mein nahi hai." (in the requested language) — never invent an answer.
- Never add facts from outside the chunks.

QUESTION: {question}

SOURCE CHUNKS:
{chunks}"""


def chat(question, chunks, language="en"):
    """Grounded Q&A over retrieved chunks. Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    question = (question or "").strip()
    if not question:
        return None, "Sawal khaali hai."
    if len(question) > 2000:
        return None, "Sawal 2000 harf se chhota rakhein."
    if not chunks:
        return None, "Pehle sources dein."
    prompt = CHAT_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language], question=question,
        chunks=_chunks_block(chunks))
    raw, err = _call_text(prompt, max_tokens=3000)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_chat(data, chunks)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


AUDIO_PROMPT = """You are writing a podcast-style study discussion between two
hosts, A and B, based ONLY on the source chunks below. Host A asks
and explains, host B adds examples and checks understanding. Do not
use facts from outside the chunks.
{lang_note}
Style: {style_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "style": "{style}",
 "turns": [
   {{"speaker": "A", "text": "Host A speaks, 1-3 sentences.", "chunk_ids": ["S1-C1"]}},
   {{"speaker": "B", "text": "Host B replies, 1-3 sentences.", "chunk_ids": ["S1-C2"]}}
 ]
}}
Rules:
- Speakers MUST alternate: A, B, A, B... never the same host twice in a row.
- Every turn must cite at least one chunk id whose text supports what is said in that turn.
- Total script: brief = 150-400 words, deep = 600-1200 words, revision = 400-800 words, focused on the most exam-relevant points.
- Keep sentences short and speakable — this will be read aloud.
- Never invent facts, dates or numbers that are not in the chunks.

SOURCE CHUNKS:
{chunks}"""

STYLE_NOTES = {
    "brief": "BRIEF: a 2-3 minute quick revision — only the 3-4 most important ideas.",
    "deep": "DEEP DIVE: a 8-10 minute thorough discussion — all key ideas, with examples and connections between them.",
    "revision": "REVISION: a 4-6 minute exam-focused recap — key points, likely exam questions, and common mistakes to avoid.",
}


def audio_script(chunks, language="en", style="deep"):
    """Generate a two-host audio-overview script from chunks.
    Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if style not in STYLE_NOTES:
        return None, "Audio style brief, deep ya revision hona chahiye."
    if not chunks:
        return None, "Pehle sources dein."
    prompt = AUDIO_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language], style=style,
        style_note=STYLE_NOTES[style], chunks=_chunks_block(chunks))
    raw, err = _call_text(prompt, max_tokens=6000, temperature=0.5)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_audio(data, chunks)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


FLASHCARDS_PROMPT = """You are making flashcards for a student, using ONLY the
source chunks below. Do not use facts from outside the chunks.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "cards": [
   {{"question": "One clear question", "answer": "Short answer, 1-3 sentences", "chunk_id": "S1-C1"}}
 ]
}}
Rules:
- Make 8-12 cards covering the most important facts, terms and ideas in the chunks.
- Each card's answer must come from its cited chunk. "chunk_id" must be a chunk id from the chunks below.
- Questions must be answerable from the chunks alone.

SOURCE CHUNKS:
{chunks}"""


def flashcards(chunks, language="en"):
    """Generate flashcards from chunks. Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if not chunks:
        return None, "Pehle sources dein."
    prompt = FLASHCARDS_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language],
        chunks=_chunks_block(chunks))
    raw, err = _call_text(prompt, max_tokens=4000)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_flashcards(data, chunks)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


QUIZ_PROMPT = """You are writing a multiple-choice quiz for a student, using
ONLY the source chunks below. Do not use facts from outside the
chunks.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "questions": [
   {{"question": "One clear question", "options": ["option 1", "option 2", "option 3", "option 4"], "correct": 0, "explanation": "Why the correct option is right, in 1-2 sentences", "chunk_id": "S1-C1"}}
 ]
}}
Rules:
- Make 5-8 questions covering the most important facts in the chunks.
- Exactly 4 options per question, all different, exactly one correct ("correct" is the 0-based index).
- Wrong options must be plausible but clearly wrong according to the chunks.
- The explanation must come from the cited chunk.

SOURCE CHUNKS:
{chunks}"""


def quiz(chunks, language="en"):
    """Generate a multiple-choice quiz from chunks.
    Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if not chunks:
        return None, "Pehle sources dein."
    prompt = QUIZ_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language],
        chunks=_chunks_block(chunks))
    raw, err = _call_text(prompt, max_tokens=5000)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_quiz(data, chunks)
    if err:
        return None, err
    clean["language"] = language
    return clean, None


GUIDE_PROMPT = """You are writing a study guide for a student, using ONLY the
source chunks below. Do not use facts from outside the chunks.
{lang_note}
Reply with ONLY a JSON object, no markdown, no extra text:
{{
 "key_points": ["Most important point 1", "point 2"],
 "terms": [{{"term": "Key term", "definition": "Short definition from the chunks", "chunk_id": "S1-C1"}}],
 "timeline": [{{"event": "What happened", "when": "When it happened"}}]
}}
Rules:
- key_points: 5-10 points, the ideas most likely to be examined.
- terms: 5-10 key terms with definitions taken from the chunks.
- timeline: only if the chunks describe a sequence of events or steps; otherwise an empty list [].
- Every term must cite a chunk id whose text supports its definition.

SOURCE CHUNKS:
{chunks}"""


def study_guide(chunks, language="en"):
    """Generate a study guide from chunks. Returns (result, error)."""
    err = _check_language(language)
    if err:
        return None, err
    if not chunks:
        return None, "Pehle sources dein."
    prompt = GUIDE_PROMPT.format(
        lang_note=LANG_INSTRUCTIONS[language],
        chunks=_chunks_block(chunks))
    raw, err = _call_text(prompt, max_tokens=4000)
    if err:
        return None, err
    data, err = _parse_json(raw)
    if err:
        return None, err
    clean, err = engine.validate_ai_guide(data, chunks)
    if err:
        return None, err
    clean["language"] = language
    return clean, None
