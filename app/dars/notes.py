"""Rule-based study-notes builder. Extractive only: every output line is a
verbatim substring of the input, so nothing is invented. Urdu/English aware.
"""
from __future__ import annotations

import re

STOP = set("""
the a an and or but of to in on for with as at by from is are was were be been
being have has had do does did will would can could should may might must shall
this that these those it its into over under between through during each other
such no not so than too very just about also only more most some any all both
few than then there their they them he she his her we you your our us me my
mine yours ours theirs what which who whom whose when where why how if because
until while of se ki ke ko mein ne per aur yeh woh jo to se hain hai tha the
""".split())

_SENT_END = re.compile(r"(?<=[.!?۔])\s+")
_WORD = re.compile(r"[A-Za-z\u0600\u06FF]{3,}")
_DEF_PAT = re.compile(
    r"^(.{2,70}?)\s+(is|are|was|were|means?|refers?\s+to|is\s+called|are\s+called)\b\s+(.+)$",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    """Split into sentences, treating each non-empty line as a boundary
    (a heading line must never merge into the next sentence)."""
    out = []
    for ln in split_lines(text):
        for p in _SENT_END.split(ln):
            p = p.strip()
            if len(p) >= 8:
                out.append(p)
    return out


def split_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def detect_headings(text: str) -> list[str]:
    """Lines that look like section titles: short, no sentence-ending
    punctuation, few words — e.g. 'Cell Biology: The Basics'."""
    heads = []
    for ln in split_lines(text):
        if len(ln) > 90:
            continue
        if ln.endswith(":"):
            heads.append(ln[:-1].strip())
        elif ln.isupper() and len(ln.split()) <= 8:
            heads.append(ln.title())
        elif (not ln[-1] in ".!?۔:" and len(ln.split()) <= 10
                and not _DEF_PAT.match(ln)):
            heads.append(ln)
    return heads


def definitions(sentences: list[str]) -> list[dict]:
    """Term → definition sentences via 'X is/are/means/refers to' patterns."""
    out, seen = [], set()
    for s in sentences:
        m = _DEF_PAT.match(s)
        if not m:
            continue
        term = re.sub(r"^(the|a|an)\s+", "", m.group(1).strip(), flags=re.I)
        if len(term.split()) > 6 or term.lower() in seen:
            continue
        seen.add(term.lower())
        out.append({"term": term, "sentence": s.strip()})
    return out


def key_terms(text: str, sentences: list[str], top_n: int = 12) -> list[dict]:
    """Frequent content words (not stopwords) with their best sentence."""
    freq: dict[str, int] = {}
    for w in _WORD.findall(text):
        wl = w.lower()
        if wl not in STOP:
            freq[wl] = freq.get(wl, 0) + 1
    ranked = sorted([w for w, c in freq.items() if c >= 3],
                    key=lambda w: -freq[w])[:top_n]
    out = []
    for w in ranked:
        best = max(sentences, key=lambda s: (w in s.lower(), len(s)))
        if w in best.lower():
            out.append({"term": w, "sentence": best.strip()})
    return out


def extractive_summary(sentences: list[str], terms: list[str], n: int = 5) -> list[str]:
    """Top-n sentences by key-term overlap, kept in original order."""
    termset = {t.lower() for t in terms}
    scored = []
    for i, s in enumerate(sentences):
        words = {w.lower() for w in _WORD.findall(s)}
        score = len(words & termset) / (len(words) or 1)
        scored.append((score, i, s))
    picked = sorted(sorted(scored, key=lambda x: -x[0])[:n], key=lambda x: x[1])
    return [s for _, _, s in picked]


def build_notes(text: str, max_defs: int = 15) -> dict:
    sentences = split_sentences(text)
    if not sentences:
        return {"headings": [], "definitions": [], "key_terms": [],
                "summary": [], "sentence_count": 0}
    defs = definitions(sentences)[:max_defs]
    def_terms = [d["term"] for d in defs]
    kts = key_terms(text, sentences)
    all_terms = def_terms + [k["term"] for k in kts]
    return {
        "headings": detect_headings(text),
        "definitions": defs,
        "key_terms": kts,
        "summary": extractive_summary(sentences, all_terms),
        "sentence_count": len(sentences),
    }
