# -*- coding: utf-8 -*-
"""Bolo engine — free AI dictation studio (Voicy / Otter.ai gap build).

Pure, deterministic logic. No network, no storage, no key needed.

Dictation itself runs in the browser via the Web Speech API (Chrome /
Edge / Safari); this engine does the part that can be tested exactly:

* Voice commands — spoken punctuation in three languages:
  English ("full stop", "new paragraph"), Roman-Urdu ("naya
  paragraph", "sawaal ka nishan") and Urdu script ("نیا پیراگراف",
  "سوالیہ نشان"). No other dictation app ships Urdu voice commands —
  dictation.io itself asks for native speakers to write them.
* Transcript cleanup — spacing, sentence capitalisation (Latin
  scripts only; Urdu script has no capital letters).
* Session stats — words, characters, words-per-minute.
* Export — plain text and Markdown builders.

Nothing here is Voicy's or Otter's property: spoken-punctuation
commands are a generic dictation convention (Dragon, Google Docs
voice typing, dictation.io all publish their own lists), and the
command phrases below were written from scratch for this app.
"""

import re

LANGUAGES = ["en", "roman", "ur"]

# Dictation languages offered on the page. The BCP-47 tag is what the
# browser's SpeechRecognition gets; ur-PK is a published Google
# Cloud Speech-to-Text language (docs.cloud.google.com) and works in
# Chrome's in-browser recogniser. Roman-Urdu has no BCP-47 tag of its
# own: the user speaks Urdu, recognition runs in ur-PK, and the AI
# "Roman-Urdu me likhein" step transliterates the Urdu-script
# transcript. That is stated honestly on the page.
DICTATION_LANGUAGES = [
    {"id": "en", "code": "en-US", "name_en": "English (US)",
     "name_roman": "English (US)", "name_ur": "انگریزی (امریکہ)",
     "note_en": "Recognition in English; voice commands in English."},
    {"id": "roman", "code": "ur-PK", "name_en": "Roman-Urdu",
     "name_roman": "Roman-Urdu", "name_ur": "رومن اردو",
     "note_en": "Speak Urdu; recognition runs in ur-PK, then AI writes "
                 "it in Roman-Urdu letters. Voice commands in Roman-Urdu."},
    {"id": "ur", "code": "ur-PK", "name_en": "Urdu (Pakistan)",
     "name_roman": "Urdu (Pakistan)", "name_ur": "اردو (پاکستان)",
     "note_en": "Recognition in Urdu script (ur-PK); voice commands "
                 "in Urdu script."},
]

# --- voice commands ----------------------------------------------------------
# (phrase words, replacement token). Longest phrases are matched first.
# Tokens: "." "," "?" "!" ":" ";" "—" "“" "”" "\n" "\n\n".
# Urdu punctuation: "۔" (U+06D4 Urdu full stop), "،" (U+060C Urdu comma),
# "؟" (U+061F Urdu question mark).

_COMMANDS = {
    "en": [
        (("new", "paragraph"), "\n\n"),
        (("question", "mark"), "?"),
        (("exclamation", "mark"), "!"),
        (("exclamation", "point"), "!"),
        (("full", "stop"), "."),
        (("open", "quote"), "“"),
        (("close", "quote"), "”"),
        (("new", "line"), "\n"),
        (("semi", "colon"), ";"),
        (("period",), "."),
        (("comma",), ","),
        (("colon",), ":"),
        (("dash",), "—"),
    ],
    "roman": [
        (("naya", "paragraph"), "\n\n"),
        (("sawaal", "ka", "nishan"), "?"),
        (("nayi", "line"), "\n"),
        (("full", "stop"), "."),
        (("naya", "line"), "\n"),
        (("comma",), ","),
        (("colon",), ":"),
        (("dash",), "—"),
    ],
    "ur": [
        (("نیا", "پیراگراف"), "\n\n"),
        (("سوالیہ", "نشان"), "؟"),
        (("نئی", "لائن"), "\n"),
        (("نیا", "پیراگراف"), "\n\n"),
        (("فل", "سٹاپ"), "۔"),
        (("کاما",), "،"),
    ],
}

_END_PUNCT = {".", "!", "?", "۔", "؟"}
_MID_PUNCT = {",", ":", ";", "،"}
_CLOSE_PUNCT = {"”"}
_OPEN_PUNCT = {"“"}


def _norm_token(tok):
    """Lowercase a token, stripping surrounding punctuation, for
    command matching. Urdu-script tokens are compared as-is."""
    return tok.strip(".,;:!?\"'“”()[]").lower()


def _sorted_commands(language):
    cmds = _COMMANDS.get(language, [])
    return sorted(cmds, key=lambda c: -len(c[0]))


def apply_voice_commands(text, language="en"):
    """Replace spoken punctuation commands with punctuation.
    Returns (result, error)."""
    if not isinstance(text, str):
        return None, "Text ghalat hai."
    if language not in LANGUAGES:
        return None, "Language ghalat hai — English, Roman-Urdu ya Urdu chunein."
    words = text.split()
    if not words:
        return "", None
    cmds = _sorted_commands(language)
    out = []
    i = 0
    while i < len(words):
        matched = False
        for phrase, repl in cmds:
            n = len(phrase)
            if i + n <= len(words) and all(
                    _norm_token(words[i + k]) == phrase[k]
                    for k in range(n)):
                out.append(repl)
                i += n
                matched = True
                break
        if not matched:
            out.append(words[i])
            i += 1
    joined = _join_tokens(out)
    return clean_transcript(joined, language), None


def _join_tokens(tokens):
    """Join words and punctuation tokens with correct spacing:
    no space before . , ? ! : ; ، ۔ ؟ ”, no space after “,
    newlines stand alone."""
    parts = []
    for tok in tokens:
        if tok in ("\n", "\n\n"):
            if parts and not parts[-1].endswith("\n"):
                parts.append(tok)
            elif not parts:
                continue
            else:
                parts.append(tok)
        elif tok in _END_PUNCT | _MID_PUNCT | _CLOSE_PUNCT:
            parts.append(tok)
        elif tok in _OPEN_PUNCT:
            if parts and not parts[-1].endswith((" ", "\n")):
                parts.append(" ")
            parts.append(tok)
        else:
            if parts and not parts[-1].endswith((" ", "\n")) \
                    and parts[-1] not in _OPEN_PUNCT:
                parts.append(" ")
            parts.append(tok)
    text = "".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_transcript(text, language="en"):
    """Collapse whitespace, fix spacing around punctuation, capitalise
    sentence starts for Latin scripts. Returns cleaned text."""
    if not isinstance(text, str):
        return ""
    text = _join_tokens(text.split()) if "\n" not in text else text
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" ([.,;:!?،۔؟”])", r"\1", text)
    text = re.sub(r"([.,;:!?،۔؟”])([A-Za-z\u0600-\u06FF])", r"\1 \2", text)
    text = text.strip()
    if language in ("en", "roman"):
        text = _capitalise_sentences(text)
    return text


def _capitalise_sentences(text):
    """Capitalise the first letter of the text and after . ! ? and
    blank lines. Latin script only."""
    if not text:
        return text
    out = []
    cap_next = True
    for ch in text:
        if cap_next and ch.isalpha():
            out.append(ch.upper())
            cap_next = False
        else:
            out.append(ch)
        if ch in ".!?":
            cap_next = True
        elif ch == "\n":
            cap_next = True
        elif ch.isalnum():
            cap_next = False
    return "".join(out)


# --- session stats -------------------------------------------------------------
def word_count(text):
    if not isinstance(text, str):
        return 0
    return len(text.split())


def session_stats(text, seconds):
    """Words, characters, minutes and words-per-minute for a dictation
    session. Returns (stats, error)."""
    if not isinstance(text, str):
        return None, "Text ghalat hai."
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) \
            or seconds < 0:
        return None, "Waqt 0 ya zyada hona chahiye."
    words = word_count(text)
    minutes = seconds / 60.0
    wpm = round(words / minutes) if minutes > 0 else 0
    return {"words": words, "characters": len(text),
            "seconds": seconds, "minutes": round(minutes, 1),
            "wpm": wpm}, None


# --- export ---------------------------------------------------------------------
def format_export(text, title, fmt="txt"):
    """Build a downloadable export. txt: plain; md: Markdown with a
    title heading. Returns (content, error)."""
    if not isinstance(text, str) or not text.strip():
        return None, "Export ke liye text khaali hai."
    if fmt not in ("txt", "md"):
        return None, "Format txt ya md hona chahiye."
    title = (title or "Bolo dictation").strip() or "Bolo dictation"
    title = title[:80]
    if fmt == "md":
        content = f"# {title}\n\n{text.strip()}\n"
    else:
        content = f"{title}\n\n{text.strip()}\n"
    return {"format": fmt, "title": title, "content": content,
            "words": word_count(text)}, None


# --- AI validators -----------------------------------------------------------------
def validate_ai_polish(text):
    """Polished text: 40-2000 chars, at least 1 sentence."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 40:
        return None, "AI ka polished text bohot chhota tha."
    if len(clean) > 2000:
        return None, "AI ka polished text bohot lamba tha."
    if "." not in clean and "؟" not in clean and "?" not in clean \
            and "!" not in clean and "۔" not in clean:
        return None, "AI ke text me koi jumla nahi tha."
    return clean, None


def validate_ai_short(text):
    """Roman-Urdu transliteration / Urdu translation: 10-2000 chars."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 10:
        return None, "AI ka jawab bohot chhota tha."
    if len(clean) > 2000:
        return None, "AI ka jawab bohot lamba tha."
    return clean, None


def languages():
    """Dictation languages offered, with BCP-47 codes."""
    return [dict(l) for l in DICTATION_LANGUAGES]
