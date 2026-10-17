"""Chat intent parser for the Content Engine app (/content).

Pattern matching (EN + Roman-Urdu) is the primary brain — it must work with
zero LLM keys. The engine's llm.py is designed for the VM-side render box;
when an in-container LLM hook exists it can be wired in as an optional
enhancer for the 'fallback' case, never as a hard dependency.
"""
import re

_INTENTS = [
    # 1. help
    ("help", re.compile(
        r"\b(help|madad|kaise|kya\s+kar\s*sakt[ea]\s*ho|what\s+can\s+you\s+do)\b", re.I)),
    # 2. list videos — requires a verb, or plural "meri videos";
    # bare "meri video" is ambiguous (usually status), so NOT matched here
    ("list", re.compile(
        r"\b(meri|my)\s+videos\b"
        r"|\bvideos?\s+(dikhao|dekho|list|show)\b"
        r"|\b(meri\s+)?videos?\s+(dikhao|dekho|list|show)\b"
        r"|\b(show|list|display)\s+(me\s+)?(my|all|the)\s+videos?\b"
        r"|\blibrary\b", re.I)),
    # 3. status
    ("status", re.compile(
        r"\b(status|progress|stauts)\b"
        r"|\bmeri\s+video\s+(kahan\s+tak|kab\s+tayar|ban\s*chuk[ei])\b"
        r"|\bvideo\s+(kahan\s+tak|kab\s+tayar|kab\s*milegi?)\b"
        r"|\b(kab\s+tayar|kitni\s+der|how\s+long)\b"
        r"|\bban\s+rah[i]?\s+he?\b", re.I)),
    # 4. set niche
    ("set_niche", re.compile(
        r"\bmeri\s+(niche|neech|theme|topic[- ]?theme)\s+(.+?)\s*(hai|ho|he)?\s*$"
        r"|\bniche\s+(.+?)\s*(hai|ho|he|kar\s*do|rakho|set)\s*$", re.I | re.S)),
    # 5. set language
    ("set_language", re.compile(
        r"\blanguage\s+(english|urdu|en|ur|roman[- ]?urdu)\b"
        r"|\b(english|urdu|roman[- ]?urdu)\s+(mein|me|main)\s+(video|voice|voiceover|banao)?\s*$"
        r"|\b(english|urdu)\s+language\b", re.I)),
    # 6. set voice
    ("set_voice", re.compile(
        r"\bvoice\s+(.+?)\s*(kar\s*do|kardo|rakho|set)?\s*$", re.I)),
]

# new-video check runs BEFORE set_language/set_voice: "urdu mein video banao"
# must queue a video, not flip a setting. set_niche stays first (it is unambiguous).
_NEWVIDEO = [
    # "dental implants pe video bana kar lao"
    re.compile(r"^(?P<topic>.+?)\s+(pe|par|per)\s+video\s+(bana\w*|tayar\s*kar\w*|bnao)\b", re.I | re.S),
    # "dental implants mein video banao" (language-ish phrasing still = new video)
    re.compile(r"^(?P<topic>.+?)\s+(mein|me)\s+video\s+(bana\w*|tayar\s*kar\w*|bnao)\b", re.I | re.S),
    # "video banao: 5 AI tools"
    re.compile(r"^video\s+(bana\w*|tayar\s*kar\w*)\s*:?\s*(?P<topic>.+)$", re.I | re.S),
    # "make a video on 5 AI tools" / "create video about X"
    re.compile(r"\b(make|create|generate|build)\s+(a\s+|the\s+)?video\s+(on|about|of)\s+(?P<topic>.+)$", re.I | re.S),
    # "banao video on X"
    re.compile(r"\b(bana\w*|tayar\s*kar\w*)\s+(a\s+|the\s+)?video\s+(on|about|of)\s+(?P<topic>.+)$", re.I | re.S),
    # "ek video banao X par"
    re.compile(r"\bvideo\s+(bana\w*|tayar\s*kar\w*)\b\s*(?P<topic>.+)$", re.I | re.S),
]


def parse(text: str) -> dict:
    """Return {'intent': ..., ...}. Intent names: help, list, status,
    set_niche, set_language, set_voice, new_video, new_video_ask, fallback."""
    t = (text or "").strip()
    if not t:
        return {"intent": "fallback"}
    # help / list / status / set_niche first (unambiguous)
    for name in ("help", "list", "status", "set_niche"):
        rx = dict(_INTENTS)[name]
        m = rx.search(t)
        if not m:
            continue
        if name == "set_niche":
            topic = _clean((m.group(2) if m.group(2) else m.group(4)) or "")
            return {"intent": "set_niche", "niche": topic} if topic else {"intent": "fallback"}
        return {"intent": name}
    # new-video before set_language/set_voice
    for rx in _NEWVIDEO:
        m = rx.search(t)
        if m:
            topic = _clean(m.group("topic"))
            # language-only topic = language request, e.g. "urdu mein video banao"
            if topic.lower() in ("urdu", "english", "en", "ur", "roman urdu", "roman-urdu"):
                return {"intent": "set_language", "language": _norm_lang(topic)}
            return {"intent": "new_video", "topic": topic} if topic else \
                {"intent": "new_video_ask"}
    # settings
    for name in ("set_language", "set_voice"):
        rx = dict(_INTENTS)[name]
        m = rx.search(t)
        if not m:
            continue
        if name == "set_language":
            return {"intent": "set_language", "language": _norm_lang(t)}
        voice = _clean(m.group(1))
        words = voice.split()
        if (not voice or len(words) > 3
                or any(w.lower() in _VOICE_BAN for w in words)):
            return {"intent": "fallback"}
        return {"intent": "set_voice", "voice": voice[:40]}
    return {"intent": "fallback"}


_VOICE_BAN = {"is", "not", "was", "are", "wasnt", "nhi", "nahi", "nahin", "hai",
               "ka", "ki", "ko", "mein", "main", "the", "a", "an", "good", "bad", "very"}


def _clean(s: str) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    s = re.sub(r"^(please|plz|zara|bas)\s+", "", s, flags=re.I)
    s = re.sub(r"\s+(pe|par|per)$", "", s, flags=re.I)  # "banao chai pe" -> "chai"
    return s[:300]


def _norm_lang(t: str) -> str:
    low = t.lower()
    if "urdu" in low and "roman" not in low:
        return "ur"
    if "roman" in low:
        return "en"  # Roman-Urdu TTS not available; narration in English script
    return "ur" if re.search(r"\bur\b", low) and "urdu" not in low else "en"


def help_text() -> str:
    return ("Mein aapki videos bana sakta hoon 🎬\n"
            "• **Video banao:** 'dental implants pe video bana kar lao'\n"
            "• **Status:** 'meri video kahan tak pahunchi?'\n"
            "• **Videos:** 'meri videos dikhao'\n"
            "• **Settings:** 'meri niche dental clinic hai' · 'language urdu' · 'voice male'")
