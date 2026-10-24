"""SM-2 spaced-repetition scheduler (SuperMemo 2, public algorithm).

Reference: Wozniak's SM-2 as documented on supermemo.com — the exact learning
loop Coconote lacks. Pure math; verified against hand calculation in
tests/verify.py.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CardState:
    repetitions: int = 0
    interval: int = 0        # days until next review
    ease: float = 2.5        # ease factor


def sm2(state: CardState, quality: int) -> CardState:
    """Advance one card's schedule after a recall graded 0..5.

    q >= 3 = remembered; q < 3 = forgotten (schedule restarts).
    """
    if not 0 <= quality <= 5:
        raise ValueError("quality must be 0..5")
    s = CardState(state.repetitions, state.interval, state.ease)
    if quality >= 3:
        if s.repetitions == 0:
            s.interval = 1
        elif s.repetitions == 1:
            s.interval = 6
        else:
            s.interval = round(s.interval * s.ease)
        s.repetitions += 1
    else:
        s.repetitions = 0
        s.interval = 1
    s.ease = s.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if s.ease < 1.3:
        s.ease = 1.3
    return s


def review_order(cards, today_ordinal: int):
    """Return indices of cards whose next review is due on/before today.

    Each card dict must carry 'due' (ordinal day). Cards never scheduled
    (no 'due' key) are treated as due today.
    """
    due = [i for i, c in enumerate(cards) if c.get("due", 0) <= today_ordinal]
    due.sort(key=lambda i: cards[i].get("due", 0))
    return due
