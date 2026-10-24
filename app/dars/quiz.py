"""Flashcard + quiz builders from the extractive notes output.

Everything stays traceable to the source text: card backs are verbatim
sentences, MCQ stems blank out the true term, distractors are other terms
from the same text.
"""
from __future__ import annotations

import random
import re


def build_flashcards(notes: dict, limit: int = 40) -> list[dict]:
    cards, seen = [], set()
    for d in notes.get("definitions", []):
        key = d["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        cards.append({
            "front": d["term"],
            "back": d["sentence"],
            "kind": "definition",
        })
    for k in notes.get("key_terms", []):
        if len(cards) >= limit:
            break
        key = k["term"].lower()
        if key in seen:
            continue
        seen.add(key)
        cards.append({
            "front": f"What is '{k['term']}'?",
            "back": k["sentence"],
            "kind": "term",
        })
    return cards[:limit]


def _blank_term(sentence: str, term: str) -> str:
    return re.sub(re.escape(term), "_____", sentence, count=1,
                  flags=re.IGNORECASE)


def build_quiz(notes: dict, n: int = 10, seed: int = 7) -> list[dict]:
    """MCQs: stem = definition with term blanked; options = term + distractors.
    Plus term-swap true/false items. 'answer' is the correct option index."""
    rng = random.Random(seed)
    defs = notes.get("definitions", [])
    terms = [d["term"] for d in defs]
    quiz = []
    for d in defs:
        if len(quiz) >= n:
            break
        stem = _blank_term(d["sentence"], d["term"])
        if stem == d["sentence"]:
            continue
        pool = [t for t in terms if t.lower() != d["term"].lower()]
        rng.shuffle(pool)
        options = [d["term"]] + pool[:3]
        if len(options) < 2:
            continue
        rng.shuffle(options)
        quiz.append({
            "type": "mcq",
            "question": stem,
            "options": options,
            "answer": options.index(d["term"]),
        })
    # true/false via term swap (only when terms differ -> false)
    for d in defs[: max(0, n - len(quiz))]:
        others = [t for t in terms if t.lower() != d["term"].lower()]
        if not others:
            continue
        wrong = rng.choice(others)
        swapped = _blank_term(d["sentence"], d["term"]).replace(
            "_____", wrong, 1)
        quiz.append({
            "type": "tf",
            "question": swapped,
            "options": ["True", "False"],
            "answer": 1,
        })
    return quiz[:n]
