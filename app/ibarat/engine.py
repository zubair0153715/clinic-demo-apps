"""Ibarat engine — original clean-room writing tools.

Rule-based paraphrasing (curated synonym/phrase tables, fully visible
in this file), extractive summarization, Flesch readability, style
flags, and a citation builder that NEVER invents a DOI, URL or author:
fields the user does not supply are simply omitted.

Honest limits, stated wherever results are shown:
- Rule-based rewrites change wording, they do not understand meaning.
  Always read the output before using it.
- No plagiarism score is offered: without a reference corpus no such
  score would be honest. No AI detector / humanizer ships either.
- Paraphrasing someone else's work without citation is still
  plagiarism; cite the source.
"""
import math
import re
from collections import Counter

MODES = ["standard", "fluency", "formal", "simple", "creative",
         "shorten", "expand"]

# word -> (simple, standard, formal, creative)
# Only common, low-ambiguity words are listed: swapping a word the
# table does not know is worse than leaving it alone.
SYNONYMS = {
    "important": ("big", "significant", "crucial", "huge"),
    "useful": ("handy", "helpful", "beneficial", "super handy"),
    "quick": ("fast", "rapid", "swift", "speedy"),
    "big": ("large", "large", "substantial", "massive"),
    "small": ("little", "minor", "modest", "tiny"),
    "good": ("fine", "good", "excellent", "great"),
    "bad": ("poor", "poor", "adverse", "awful"),
    "show": ("display", "show", "demonstrate", "reveal"),
    "use": ("use", "utilize", "employ", "leverage"),
    "using": ("using", "utilizing", "employing", "leveraging"),
    "help": ("aid", "assist", "facilitate", "lend a hand"),
    "helps": ("aids", "assists", "facilitates", "lends a hand"),
    "many": ("lots of", "numerous", "a large number of", "tons of"),
    "begin": ("start", "begin", "commence", "kick off"),
    "end": ("finish", "conclude", "terminate", "wrap up"),
    "buy": ("get", "purchase", "acquire", "grab"),
    "make": ("create", "produce", "generate", "craft"),
    "get": ("obtain", "obtain", "acquire", "grab"),
    "need": ("require", "require", "necessitate", "cry out for"),
    "needs": ("requires", "requires", "necessitates", "cries out for"),
    "improve": ("better", "improve", "enhance", "supercharge"),
    "improves": ("betters", "improves", "enhances", "supercharges"),
    "reduce": ("cut", "reduce", "decrease", "slash"),
    "increase": ("raise", "increase", "elevate", "boost"),
    "study": ("look at", "examine", "investigate", "dig into"),
    "studies": ("looks at", "examines", "investigates", "digs into"),
    "result": ("outcome", "result", "finding", "payoff"),
    "results": ("outcomes", "results", "findings", "payoffs"),
    "method": ("way", "method", "approach", "recipe"),
    "methods": ("ways", "methods", "approaches", "recipes"),
    "problem": ("issue", "problem", "challenge", "hurdle"),
    "problems": ("issues", "problems", "challenges", "hurdles"),
    "difficult": ("hard", "difficult", "challenging", "tough"),
    "easy": ("simple", "straightforward", "simple", "a breeze"),
    "clear": ("plain", "clear", "evident", "crystal clear"),
    "fast": ("quick", "rapid", "swift", "speedy"),
    "slow": ("gradual", "slow", "gradual", "sluggish"),
    "strong": ("powerful", "strong", "robust", "mighty"),
    "weak": ("feeble", "weak", "limited", "flimsy"),
    "happy": ("glad", "pleased", "delighted", "over the moon"),
    "sad": ("unhappy", "sad", "sorrowful", "down"),
    "try": ("attempt", "attempt", "endeavour", "give it a go"),
    "tries": ("attempts", "attempts", "endeavours", "gives it a go"),
    "ask": ("request", "ask", "inquire", "pose a question"),
    "tell": ("inform", "tell", "notify", "let know"),
    "give": ("provide", "provide", "furnish", "hand over"),
    "gives": ("provides", "provides", "furnishes", "hands over"),
    "take": ("obtain", "take", "acquire", "grab"),
    "find": ("locate", "find", "identify", "uncover"),
    "finds": ("locates", "finds", "identifies", "uncovers"),
    "change": ("alter", "change", "modify", "shake up"),
    "changes": ("alters", "changes", "modifies", "shakes up"),
    "about": ("around", "about", "regarding", "on the subject of"),
    "because": ("since", "because", "as", "thanks to"),
    "also": ("too", "also", "additionally", "on top of that"),
    "however": ("but", "however", "nevertheless", "still"),
    "therefore": ("so", "therefore", "consequently", "as a result"),
}

# Fluency mode swaps only these (light-touch, low drift risk).
FLUENCY_WORDS = {"important", "useful", "quick", "big", "small", "good",
                 "bad", "many", "begin", "end", "also", "however",
                 "therefore", "because", "show", "use"}

# Expand mode uses a longer phrase for these adjectives only
# (adjective phrases stay grammatical in most positions).
EXPAND = {
    "important": "important and highly significant",
    "useful": "useful and of real practical value",
    "quick": "quick and efficient",
    "big": "big in size and scope",
    "clear": "clear and easy to understand",
    "easy": "easy and simple to follow",
    "strong": "strong and reliable",
}

# Shorten mode: phrase -> shorter equivalent (applied first, whole
# phrase, case-insensitive).
SHORTEN_PHRASES = [
    ("in order to", "to"),
    ("due to the fact that", "because"),
    ("a large number of", "many"),
    ("at this point in time", "now"),
    ("in the event that", "if"),
    ("for the purpose of", "for"),
    ("in spite of the fact that", "although"),
    ("on a daily basis", "daily"),
    ("a lot of", "many"),
    ("in the near future", "soon"),
]

FILLERS = {"very", "really", "just", "actually", "basically", "literally"}
BE_VERBS = {"is", "are", "was", "were", "be", "been", "being"}
STOPWORDS = set("""
a an the and or but if then else when at by for with about into through
during before after above below to from up down in out on off over under
again further once here there all any both each few more most other some
such no nor not only own same so than too very can will just should now
of is are was were be been being have has had do does did would could
shall may might must i you he she it we they this that these those am
""".split())

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
TOKEN = re.compile(r"[A-Za-z']+|[^A-Za-z']+")


def split_sentences(text):
    parts = [s.strip() for s in SENT_SPLIT.split(text.strip()) if s.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def words_of(text):
    return re.findall(r"[A-Za-z']+", text.lower())


def _cap(word, replacement):
    if word[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _is_protected(token, protected, sentence_start):
    low = token.lower()
    if low in protected:
        return True
    if any(ch.isdigit() for ch in token):
        return True
    if token.isupper() and len(token) > 1:
        return True  # acronyms / constants
    if token[:1].isupper() and not sentence_start:
        return True  # proper nouns mid-sentence
    return False


def paraphrase(text, mode="standard", protected=None):
    """Deterministic rule-based rewrite. Returns dict with the
    rewritten text, changed-word count and word-set similarity."""
    if mode not in MODES:
        mode = "standard"
    protected = {p.strip().lower() for p in (protected or []) if p.strip()}
    work = text
    if mode == "shorten":
        for src, dst in SHORTEN_PHRASES:
            work = re.sub(r"\b" + re.escape(src) + r"\b", dst, work,
                          flags=re.IGNORECASE)
    idx = {"simple": 0, "standard": 1, "formal": 2, "creative": 3}[mode] \
        if mode in ("simple", "standard", "formal", "creative") else 1
    out_tokens = []
    sentence_start = True
    for tok in TOKEN.findall(work):
        if re.fullmatch(r"[A-Za-z']+", tok or ""):
            low = tok.lower()
            if mode == "shorten" and low in FILLERS:
                out_tokens.append("")
                sentence_start = False
                continue
            if _is_protected(tok, protected, sentence_start):
                out_tokens.append(tok)
            elif mode == "expand" and low in EXPAND:
                out_tokens.append(_cap(tok, EXPAND[low]))
            elif low in SYNONYMS and (mode != "fluency"
                                      or low in FLUENCY_WORDS):
                out_tokens.append(_cap(tok, SYNONYMS[low][idx]))
            else:
                out_tokens.append(tok)
            sentence_start = False
        else:
            out_tokens.append(tok)
            if any(c in tok for c in ".!?"):
                sentence_start = True
    rewritten = re.sub(r" {2,}", " ", "".join(out_tokens)).strip()
    orig_words = words_of(text)
    new_words = words_of(rewritten)
    changed = sum(1 for a, b in zip(orig_words, new_words) if a != b)
    changed += abs(len(orig_words) - len(new_words))
    return {
        "mode": mode,
        "original": text,
        "rewritten": rewritten,
        "words": len(orig_words),
        "changed_words": changed,
        "similarity": round(word_set_similarity(text, rewritten), 3),
        "engine": "rule-based (curated synonym/phrase tables)",
    }


def word_set_similarity(a, b):
    sa, sb = set(words_of(a)), set(words_of(b))
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def summarize(text, sentences=3):
    """Extractive summary: TF-scored sentences, kept in original order.
    No wording is invented."""
    sents = split_sentences(text)
    if len(sents) <= sentences:
        return {"summary": text.strip(), "picked": list(range(len(sents))),
                "total_sentences": len(sents)}
    freq = Counter(w for w in words_of(text) if w not in STOPWORDS)
    scored = []
    for i, s in enumerate(sents):
        ws = [w for w in words_of(s) if w not in STOPWORDS]
        score = sum(freq[w] for w in ws) / (math.sqrt(len(ws)) or 1)
        scored.append((score, i))
    picked = sorted(i for _, i in sorted(scored, reverse=True)[:sentences])
    return {"summary": " ".join(sents[i] for i in picked),
            "picked": picked, "total_sentences": len(sents)}


def _syllables(word):
    word = word.lower().strip("'")
    if not word:
        return 0
    groups = len(re.findall(r"[aeiouy]+", word))
    if word.endswith("e") and groups > 1:
        groups -= 1
    return max(1, groups)


def readability(text):
    sents = split_sentences(text)
    ws = words_of(text)
    if not sents or not ws:
        return {"words": 0, "sentences": 0, "flesch_reading_ease": None,
                "flesch_kincaid_grade": None, "note": "empty text"}
    syl = sum(_syllables(w) for w in ws)
    wps = len(ws) / len(sents)
    spw = syl / len(ws)
    fre = 206.835 - 1.015 * wps - 84.6 * spw
    fk = 0.39 * wps + 11.8 * spw - 15.59
    return {"words": len(ws), "sentences": len(sents),
            "syllables": syl,
            "flesch_reading_ease": round(fre, 2),
            "flesch_kincaid_grade": round(fk, 2),
            "formula": "Flesch Reading Ease = 206.835 - 1.015*(words/sentences)"
                       " - 84.6*(syllables/words); syllables counted by"
                       " vowel-group heuristic (estimate, not exact)"}


def analyze(text):
    """Deterministic style flags — each one is checkable by eye."""
    sents = split_sentences(text)
    flags = []
    for i, s in enumerate(sents):
        ws = words_of(s)
        for j in range(len(ws) - 1):
            if ws[j] == ws[j + 1]:
                flags.append({"type": "repeated_word",
                              "detail": f"Sentence {i + 1}: '{ws[j]}' twice "
                                        "in a row"})
                break
        if len(ws) > 25:
            flags.append({"type": "long_sentence",
                          "detail": f"Sentence {i + 1}: {len(ws)} words "
                                    "(over 25 — consider splitting)"})
        for j, w in enumerate(ws):
            if w in BE_VERBS and j + 1 < len(ws) and (
                    ws[j + 1].endswith("ed") or ws[j + 1].endswith("en")):
                flags.append({"type": "passive_candidate",
                              "detail": f"Sentence {i + 1}: '{w} "
                                        f"{ws[j + 1]}' may be passive voice"})
                break
    filler_hits = Counter(w for w in words_of(text) if w in FILLERS)
    if filler_hits:
        flags.append({"type": "filler_words",
                      "detail": "Fillers found: " + ", ".join(
                          f"{w} x{n}" for w, n in filler_hits.items())})
    read = readability(text)
    return {"readability": read, "flags": flags,
            "flag_count": len(flags)}


def build_citation(style, surname="", initials="", year="", title="",
                  container="", url="", doi=""):
    """Formats a citation ONLY from supplied fields. A missing DOI/URL
    is omitted, never invented — that is the whole point."""
    surname, initials, year = surname.strip(), initials.strip(), year.strip()
    title, container = title.strip(), container.strip()
    url, doi = url.strip(), doi.strip()
    author = ""
    if surname:
        author = surname + (f", {initials}" if initials else "")
    if style == "mla":
        out = ""
        if author:
            out += author + ". "
        if title:
            out += f'"{title}." '
        if container:
            out += f"{container}, "
        if year:
            out += f"{year}, "
        if doi:
            out += f"https://doi.org/{doi.lstrip('https://doi.org/')}"
        elif url:
            out += url
        out = out.strip().rstrip(",") + "."
    elif style == "chicago":
        out = ""
        if author:
            out += author + ". "
        if year:
            out += f"{year}. "
        if title:
            out += f'"{title}." '
        if container:
            out += f"{container}. "
        if doi:
            out += f"https://doi.org/{doi.lstrip('https://doi.org/')}"
        elif url:
            out += url
        out = out.strip()
        if not out.endswith("."):
            out += "."
    else:  # apa (default)
        out = ""
        if author:
            out += author + " "
        if year:
            out += f"({year}). "
        if title:
            out += f"{title}. "
        if container:
            out += f"{container}. "
        if doi:
            out += f"https://doi.org/{doi.lstrip('https://doi.org/')}"
        elif url:
            out += url
        out = out.strip()
    note = ("No DOI or URL supplied — none invented. Add the real DOI "
            "from the publisher's page if you have it." if not doi and not url
            else "")
    return {"style": style, "citation": out, "note": note}
