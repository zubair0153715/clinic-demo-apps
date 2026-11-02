"""Awaaz engine — deterministic text analysis for the read-aloud reader.

Pure functions, no AI, no network, no key: the reader's core never
depends on a server key (lesson from the 2026-11-01 Tahqeeq deploy,
where the shared Gemini key was quota-exhausted). The browser does the
speaking (Web Speech API); this module supplies the structure the
browser renders: sentences with exact char offsets (so word highlighting
lands on the right word), language detection (Urdu script / Roman-Urdu /
English), reading-time estimates and readability stats.
"""
import re

MAX_CHARS = 200_000
BASE_WPM = 180  # average listening speed for estimates

# Words that end with a period but do not end a sentence.
ABBREV = {
    "dr", "mr", "mrs", "ms", "st", "no", "vs", "etc", "e.g", "i.e",
    "u.s", "u.k", "prof", "sr", "jr", "gen", "col", "capt", "lt",
    "sgt", "fig", "eq", "approx", "dept", "univ", "ph.d", "m.d",
    "b.a", "m.a", "rs", "jan", "feb", "mar", "apr", "jun", "jul",
    "aug", "sep", "sept", "oct", "nov", "dec",
}

SENT_END = re.compile(r'[.!?۔؟]+["\'”’)\]]*')
TOKEN_BEFORE = re.compile(r'([A-Za-z][A-Za-z.]*)$')
ARABIC = re.compile(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]')
WORD = re.compile(r"[A-Za-z\u0600-\u06FF\u0750-\u077F]+(?:['’\-][A-Za-z\u0600-\u06FF]+)?")
VOWEL_GROUP = re.compile(r'[aeiouy]+', re.I)

ROMAN_URDU = {
    "hai", "he", "hain", "mein", "mera", "meri", "mere", "aap", "ap",
    "kya", "nahi", "nahin", "aur", "ka", "ki", "ke", "se", "ye", "yeh",
    "wo", "woh", "hum", "tum", "kar", "karo", "raha", "rahi", "rahe",
    "tha", "thi", "the", "boht", "bohat", "acha", "achi", "kyun",
    "kab", "kahan", "kaise", "bhi", "toh", "phir", "ab", "jab", "sab",
    "kuch", "koi", "ek", "do", "teen", "par", "ne", "liye", "baad",
    "hoon", "hoga", "chahiye", "theek", "zaroor", "shukriya", "batao",
    "samajh", "dekho", "suno", "parho",
}


def check_caps(text):
    """Validate input. Returns an error string, or None."""
    if not text or not text.strip():
        return "Pehle kuch text paste karein ya file upload karein."
    if len(text) > MAX_CHARS:
        return (f"Text zyada lamba hai ({len(text):,} characters). "
                f"Limit {MAX_CHARS:,} characters hai — hissa kar ke sunain.")
    return None


def _is_abbrev(text, punct_start):
    m = TOKEN_BEFORE.search(text[:punct_start])
    if not m:
        return False
    return m.group(1).rstrip(".").lower() in ABBREV


def _is_decimal(text, punct_start):
    before = text[punct_start - 1] if punct_start > 0 else ""
    after = text[punct_start + 1] if punct_start + 1 < len(text) else ""
    return before.isdigit() and after.isdigit()


def split_sentences(text):
    """Split text into sentences with exact char offsets.

    Returns a list of {"text", "start", "end"} where [start, end) is
    the sentence including its terminal punctuation, offsets measured
    on the original (unstripped) text. Splits on . ! ? plus the Urdu
    full stop (۔) and question mark (؟); a double newline also ends a
    sentence. Abbreviations (Dr., Rs., e.g., U.S.) and decimals (3.5)
    never split.
    """
    text = text.strip()
    if not text:
        return []
    cuts = []  # (sentence_end, next_sentence_start)
    for m in SENT_END.finditer(text):
        punct_start = m.start()
        # the punctuation run itself is the sentence end
        end = m.end()
        if _is_decimal(text, punct_start) or _is_abbrev(text, punct_start):
            continue
        j = end
        while j < len(text) and text[j] in " \t\r\n":
            j += 1
        if j >= len(text):
            cuts.append((end, j))
            continue
        # No space after the punctuation means it is mid-token
        # ("U.S.", "e.g.", "Ph.D.") — never a sentence end.
        if j == end:
            continue
        nxt = text[j]
        if nxt.isalnum() or nxt in '"“‘([«':
            cuts.append((end, j))
    for m in re.finditer(r'\n\s*\n', text):
        cuts.append((m.start(), m.end()))
    cuts = sorted(set(cuts))
    sentences = []
    start = 0
    for end, nxt in cuts:
        seg = text[start:end].strip()
        if seg:
            s = text.index(seg, start)
            sentences.append({"text": seg, "start": s,
                              "end": s + len(seg)})
        start = nxt
    tail = text[start:].strip()
    if tail:
        s = text.index(tail, start)
        sentences.append({"text": tail, "start": s, "end": s + len(tail)})
    return sentences


def word_count(text):
    return len(WORD.findall(text))


def detect_language(text):
    """'ur' for Urdu script, 'roman' for Roman-Urdu, else 'en'."""
    letters = WORD.findall(text)
    if not letters:
        return "en"
    arabic = len(ARABIC.findall(text))
    total_chars = sum(len(w) for w in letters)
    if total_chars and arabic / total_chars > 0.10:
        return "ur"
    low = [w.lower() for w in letters]
    roman_hits = sum(1 for w in low if w in ROMAN_URDU)
    # "he"/"the" are also English words, so a couple of hits prove
    # nothing — need several hits or a high share of the text.
    if roman_hits >= 4 or (roman_hits >= 2 and low and
                           roman_hits / len(low) >= 0.4):
        return "roman"
    return "en"


def _syllables_en(word):
    """Heuristic syllable count for one English word."""
    w = re.sub(r'[^a-z]', '', word.lower())
    if not w:
        return 0
    groups = len(VOWEL_GROUP.findall(w))
    if w.endswith("e") and groups > 1:
        groups -= 1
    if w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy":
        groups += 1
    return max(groups, 1)


def flesch_reading_ease(text):
    """Flesch Reading Ease for English text; None for non-English.

    Hand-checkable: 'The cat sat on the mat.' -> 6 words, 1 sentence,
    6 syllables -> 206.835 - 1.015*6 - 84.6*1 = 116.1.
    """
    if detect_language(text) != "en":
        return None
    sentences = split_sentences(text)
    words = WORD.findall(text)
    if not sentences or not words:
        return None
    syllables = sum(_syllables_en(w) for w in words)
    score = (206.835 - 1.015 * (len(words) / len(sentences))
             - 84.6 * (syllables / len(words)))
    return round(score, 1)


def find_headings(text):
    """Short punctuation-free lines that open a block = headings."""
    headings = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        s = line.strip()
        if not s or len(s) > 60:
            continue
        if re.search(r'[.!?۔؟:;,]$', s):
            continue
        if len(s.split()) > 8:
            continue
        if i == 0 or not lines[i - 1].strip():
            headings.append({"text": s, "line": i + 1})
    return headings


def analyze(text):
    """Full deterministic analysis for one document."""
    sentences = split_sentences(text)
    words = word_count(text)
    lang = detect_language(text)
    minutes = round(words / BASE_WPM, 1) if words else 0.0
    return {
        "sentences": sentences,
        "sentence_count": len(sentences),
        "words": words,
        "chars": len(text),
        "language": lang,
        "minutes_180wpm": minutes,
        "flesch": flesch_reading_ease(text),
        "headings": find_headings(text),
    }
