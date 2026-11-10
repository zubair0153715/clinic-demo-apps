# -*- coding: utf-8 -*-
"""Zehn engine — free brain-training studio (Lumosity gap build).

Pure, deterministic logic. No network, no storage, no key needed.

Five original games, each a standard cognitive task from the
public literature (sequence recall, Stroop, arithmetic, 2-back,
grid recall — none of them Lumosity's property, and no Lumosity
game name, art, code or asset is used anywhere):

* Yaad (memory) — remember a digit sequence, type it back.
* Rang (attention) — Stroop: the word says one colour, the ink is
  another; pick the INK colour.
* Tez Hisab (speed) — quick arithmetic, difficulty by level.
* Do Peeche (flexibility) — 2-back: does this letter match the one
  two steps back?
* Raasta (memory, spatial) — remember which grid cells lit up.

Adaptive difficulty: level up on accuracy >= 80%, down below 50%.
Zehn Score (0-100 per skill) = 70 * accuracy + 30 * speed factor,
where the speed factor is 1.0 at or under the target time and falls
linearly to 0 at twice the target time. The formula is published on
the page — no black box, no "LPI".

The honest-science rule, stated on the page and enforced by the
validators: these games train the games themselves. Zehn makes no
claim to raise IQ, prevent dementia or treat any condition.
"""

import random

LANGUAGES = ["en", "roman", "ur"]

# --- game catalogue ----------------------------------------------------------
GAMES = {
    "yaad": {"id": "yaad", "skill": "memory",
             "name_en": "Yaad — Memory", "name_roman": "Yaad",
             "name_ur": "یاد",
             "blurb_en": "Remember a digit sequence, then type it back."},
    "rang": {"id": "rang", "skill": "attention",
             "name_en": "Rang — Attention", "name_roman": "Rang",
             "name_ur": "رنگ",
             "blurb_en": "The word says one colour, the ink is another. Pick the INK colour."},
    "hisab": {"id": "hisab", "skill": "speed",
              "name_en": "Tez Hisab — Maths Speed", "name_roman": "Tez Hisab",
              "name_ur": "تیز حساب",
              "blurb_en": "Quick arithmetic against the clock."},
    "peeche": {"id": "peeche", "skill": "flexibility",
               "name_en": "Do Peeche — 2-Back", "name_roman": "Do Peeche",
               "name_ur": "دو پیچھے",
               "blurb_en": "Does this letter match the one two steps back?"},
    "raasta": {"id": "raasta", "skill": "memory",
               "name_en": "Raasta — Spatial Memory", "name_roman": "Raasta",
               "name_ur": "راستہ",
               "blurb_en": "Remember which squares lit up on the grid."},
}

SKILLS = ["memory", "attention", "speed", "flexibility"]

# Target seconds per round, by game — the speed half of the Zehn Score.
TARGET_SECONDS = {"yaad": 8.0, "rang": 3.0, "hisab": 6.0,
                  "peeche": 2.5, "raasta": 10.0}

MIN_LEVEL, MAX_LEVEL = 1, 5


def _rng(seed):
    return random.Random(seed) if seed is not None else random.Random()


def _check_level(level):
    if not isinstance(level, int) or isinstance(level, bool) \
            or not MIN_LEVEL <= level <= MAX_LEVEL:
        return "Level 1 se 5 ke beech hona chahiye."
    return None


def game_list():
    """All five games with skill and target time."""
    return [{**g, "target_seconds": TARGET_SECONDS[g["id"]]}
            for g in GAMES.values()]


# --- Yaad: digit sequence memory --------------------------------------------
def memory_round(level, seed=None):
    """Sequence of 2+level digits (L1=3 ... L5=7). Returns (round, error)."""
    err = _check_level(level)
    if err:
        return None, err
    rng = _rng(seed)
    n = 2 + level
    digits = [rng.randint(0, 9) for _ in range(n)]
    return {"game": "yaad", "level": level, "length": n,
            "digits": digits}, None


def score_memory(digits, answer):
    """Position-by-position scoring. answer: string of digits or list
    of ints. Returns (result, error)."""
    if not isinstance(digits, list) or not digits \
            or not all(isinstance(d, int) and 0 <= d <= 9 for d in digits):
        return None, "Digits ki list ghalat hai."
    if isinstance(answer, str):
        answer = [int(c) for c in answer.strip() if c.isdigit()]
    if not isinstance(answer, list) or not answer:
        return None, "Jawab khaali hai — digits likhein."
    if len(answer) != len(digits):
        return None, (f"Jawab {len(digits)} digits ka hona chahiye, "
                      f"{len(answer)} mile.")
    correct = sum(1 for d, a in zip(digits, answer) if d == a)
    total = len(digits)
    return {"game": "yaad", "correct": correct, "total": total,
            "accuracy": round(correct / total, 3)}, None


# --- Rang: Stroop attention ---------------------------------------------------
COLOURS = [
    {"id": "laal", "en": "Red", "roman": "Laal", "ur": "لال",
     "hex": "#dc2626"},
    {"id": "neela", "en": "Blue", "roman": "Neela", "ur": "نیلا",
     "hex": "#2563eb"},
    {"id": "sabz", "en": "Green", "roman": "Sabz", "ur": "سبز",
     "hex": "#16a34a"},
    {"id": "peela", "en": "Yellow", "roman": "Peela", "ur": "پیلا",
     "hex": "#ca8a04"},
]


def stroop_round(level, seed=None):
    """10 Stroop trials. ~25% congruent (word == ink). The correct
    answer is always the INK colour. Returns (round, error)."""
    err = _check_level(level)
    if err:
        return None, err
    rng = _rng(seed)
    trials = []
    for _ in range(10):
        word = rng.choice(COLOURS)
        if rng.random() < 0.25:
            ink = word
        else:
            ink = rng.choice([c for c in COLOURS if c["id"] != word["id"]])
        trials.append({"word": word["id"], "word_en": word["en"],
                       "ink": ink["id"], "ink_en": ink["en"],
                       "ink_hex": ink["hex"],
                       "congruent": word["id"] == ink["id"]})
    return {"game": "rang", "level": level, "trials": trials,
            "options": [c["id"] for c in COLOURS]}, None


def score_stroop(trials, answers):
    """answers: list of colour ids, one per trial. Returns (result, error)."""
    if not isinstance(trials, list) or not trials:
        return None, "Trials ki list ghalat hai."
    if not isinstance(answers, list) or len(answers) != len(trials):
        return None, (f"Jawab {len(trials)} trials ke hone chahiye, "
                      f"{len(answers) if isinstance(answers, list) else 0} mile.")
    correct = sum(1 for t, a in zip(trials, answers)
                  if a == t.get("ink"))
    total = len(trials)
    cong = [t for t in trials if t.get("congruent")]
    incong = [t for t in trials if not t.get("congruent")]
    cong_ok = sum(1 for t, a in zip(trials, answers)
                  if t.get("congruent") and a == t.get("ink"))
    incong_ok = sum(1 for t, a in zip(trials, answers)
                    if not t.get("congruent") and a == t.get("ink"))
    return {"game": "rang", "correct": correct, "total": total,
            "accuracy": round(correct / total, 3),
            "congruent_correct": cong_ok, "congruent_total": len(cong),
            "incongruent_correct": incong_ok,
            "incongruent_total": len(incong)}, None


# --- Tez Hisab: maths speed ---------------------------------------------------
def math_question(level, seed=None):
    """One arithmetic question. Returns (question, error).

    L1: +/- within 20 (never negative). L2: +/- within 100.
    L3: x within 12x12, exact division. L4: 2-digit x 1-digit,
    2-digit + 2-digit. L5: 2-digit x 2-digit, 3-digit - 2-digit.
    """
    err = _check_level(level)
    if err:
        return None, err
    rng = _rng(seed)
    if level == 1:
        a, b = rng.randint(0, 20), rng.randint(0, 20)
        op = rng.choice(["+", "-"])
        if op == "-" and b > a:
            a, b = b, a
    elif level == 2:
        a, b = rng.randint(0, 100), rng.randint(0, 100)
        op = rng.choice(["+", "-"])
        if op == "-" and b > a:
            a, b = b, a
    elif level == 3:
        op = rng.choice(["x", "/"])
        if op == "x":
            a, b = rng.randint(2, 12), rng.randint(2, 12)
        else:
            b = rng.randint(2, 12)
            a = b * rng.randint(2, 12)
    elif level == 4:
        op = rng.choice(["x", "+"])
        if op == "x":
            a, b = rng.randint(10, 99), rng.randint(2, 9)
        else:
            a, b = rng.randint(10, 99), rng.randint(10, 99)
    else:
        op = rng.choice(["x", "-"])
        if op == "x":
            a, b = rng.randint(10, 99), rng.randint(10, 99)
        else:
            a = rng.randint(100, 999)
            b = rng.randint(10, 99)
    if op == "+":
        answer = a + b
    elif op == "-":
        answer = a - b
    elif op == "x":
        answer = a * b
    else:
        answer = a // b
    return {"game": "hisab", "level": level, "a": a, "op": op, "b": b,
            "answer": answer,
            "text": f"{a} {op} {b} = ?"}, None


def check_math(question, given):
    """given: int answer. Returns (result, error)."""
    if not isinstance(question, dict) or "answer" not in question:
        return None, "Sawaal ghalat hai."
    if not isinstance(given, int) or isinstance(given, bool):
        return None, "Jawab poora number hona chahiye."
    ok = given == question["answer"]
    return {"game": "hisab", "correct": ok,
            "given": given, "answer": question["answer"]}, None


# --- Do Peeche: 2-back ---------------------------------------------------------
NBACK_LETTERS = ["A", "B", "C", "D", "E", "F"]


def nback_sequence(level, seed=None):
    """Letter sequence, length 12 + 2*level (L1=14 ... L5=22).
    ~30% of positions (from index 2 on) are targets: the letter
    matches the one two steps back. Returns (round, error)."""
    err = _check_level(level)
    if err:
        return None, err
    rng = _rng(seed)
    n = 12 + 2 * level
    letters = []
    for i in range(n):
        if i >= 2 and rng.random() < 0.3:
            letters.append(letters[i - 2])
        else:
            pool = [L for L in NBACK_LETTERS
                    if i < 2 or L != letters[i - 2]]
            letters.append(rng.choice(pool))
    targets = [False, False] + [letters[i] == letters[i - 2]
                                for i in range(2, n)]
    return {"game": "peeche", "level": level, "length": n,
            "letters": letters, "targets": targets,
            "target_count": sum(targets)}, None


def score_nback(targets, answers):
    """targets/answers: lists of bool, same length. Returns
    (result, error) with hits, misses, false alarms, correct
    rejections and accuracy."""
    if not isinstance(targets, list) or not targets \
            or not all(isinstance(t, bool) for t in targets):
        return None, "Targets ki list ghalat hai."
    if not isinstance(answers, list) or len(answers) != len(targets) \
            or not all(isinstance(a, bool) for a in answers):
        return None, (f"Jawab {len(targets)} trials ke hone chahiye, "
                      "haan/naa me.")
    hits = sum(1 for t, a in zip(targets, answers) if t and a)
    misses = sum(1 for t, a in zip(targets, answers) if t and not a)
    false_alarms = sum(1 for t, a in zip(targets, answers) if not t and a)
    correct_rej = sum(1 for t, a in zip(targets, answers) if not t and not a)
    total = len(targets)
    return {"game": "peeche", "hits": hits, "misses": misses,
            "false_alarms": false_alarms,
            "correct_rejections": correct_rej, "total": total,
            "accuracy": round((hits + correct_rej) / total, 3)}, None


# --- Raasta: spatial grid memory -----------------------------------------------
def grid_round(level, seed=None):
    """Grid of 3x3 (levels 1-2) or 4x4 (levels 3-5); 2+level cells lit
    (L1=3 ... L5=7). Returns (round, error)."""
    err = _check_level(level)
    if err:
        return None, err
    rng = _rng(seed)
    size = 3 if level <= 2 else 4
    count = 2 + level
    cells = list(range(size * size))
    rng.shuffle(cells)
    lit = sorted(cells[:count])
    return {"game": "raasta", "level": level, "size": size,
            "lit_count": count, "lit": lit}, None


def score_grid(lit, picked, size):
    """lit/picked: lists of cell indices (0..size*size-1).
    Returns (result, error) with precision, recall and F1."""
    if not isinstance(size, int) or size not in (3, 4):
        return None, "Grid 3x3 ya 4x4 hona chahiye."
    if not isinstance(lit, list) or not lit:
        return None, "Lit cells ki list ghalat hai."
    if not isinstance(picked, list):
        return None, "Picked cells ki list ghalat hai."
    max_cell = size * size - 1
    if any(not isinstance(c, int) or not 0 <= c <= max_cell for c in lit) \
            or any(not isinstance(c, int) or not 0 <= c <= max_cell
                   for c in picked):
        return None, f"Cells 0 se {max_cell} ke beech hone chahiye."
    lit_s, picked_s = set(lit), set(picked)
    tp = len(lit_s & picked_s)
    fp = len(picked_s - lit_s)
    fn = len(lit_s - picked_s)
    precision = tp / len(picked_s) if picked_s else 0.0
    recall = tp / len(lit_s) if lit_s else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall > 0 else 0.0)
    return {"game": "raasta", "true_positives": tp,
            "false_positives": fp, "false_negatives": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3), "f1": round(f1, 3),
            "accuracy": round(f1, 3)}, None


# --- Zehn Score + adaptive difficulty ------------------------------------------
def zehn_score(accuracy, avg_seconds, target_seconds):
    """0-100: 70 * accuracy + 30 * speed factor. Speed factor is 1.0
    at or under the target time, falling linearly to 0 at twice the
    target. Returns (score, error)."""
    if not isinstance(accuracy, (int, float)) or isinstance(accuracy, bool) \
            or not 0.0 <= accuracy <= 1.0:
        return None, "Accuracy 0 se 1 ke beech honi chahiye."
    if not isinstance(avg_seconds, (int, float)) or avg_seconds < 0 \
            or not isinstance(target_seconds, (int, float)) \
            or target_seconds <= 0:
        return None, "Waqt 0 ya zyada, target 0 se zyada hona chahiye."
    if avg_seconds <= target_seconds:
        speed = 1.0
    else:
        speed = max(0.0, 1.0 - (avg_seconds - target_seconds) / target_seconds)
    score = int(round(70 * accuracy + 30 * speed))
    return {"score": max(0, min(100, score)),
            "accuracy": accuracy, "avg_seconds": avg_seconds,
            "target_seconds": target_seconds,
            "speed_factor": round(speed, 3)}, None


def adaptive_level(level, accuracy, avg_seconds=None, target_seconds=None):
    """Level up on accuracy >= 0.8 (and, if times given, avg time no
    more than 1.2x target); down below 0.5; else stay. Clamped 1-5.
    Returns (result, error)."""
    err = _check_level(level)
    if err:
        return None, err
    if not isinstance(accuracy, (int, float)) or isinstance(accuracy, bool) \
            or not 0.0 <= accuracy <= 1.0:
        return None, "Accuracy 0 se 1 ke beech honi chahiye."
    fast_enough = True
    if avg_seconds is not None and target_seconds is not None:
        if not isinstance(avg_seconds, (int, float)) or avg_seconds < 0 \
                or not isinstance(target_seconds, (int, float)) \
                or target_seconds <= 0:
            return None, "Waqt 0 ya zyada, target 0 se zyada hona chahiye."
        fast_enough = avg_seconds <= 1.2 * target_seconds
    if accuracy >= 0.8 and fast_enough:
        new_level = min(MAX_LEVEL, level + 1)
        change = "up" if new_level > level else "max"
    elif accuracy < 0.5:
        new_level = max(MIN_LEVEL, level - 1)
        change = "down" if new_level < level else "min"
    else:
        new_level, change = level, "stay"
    return {"level": level, "new_level": new_level, "change": change,
            "accuracy": accuracy}, None


# --- daily workout ---------------------------------------------------------------
def workout_plan(day_of_year, weakest=None):
    """A 5-game daily workout. Order rotates by day of year so no two
    days are identical; if a weakest skill is given, its game goes
    first. Deterministic for a given day. Returns (plan, error)."""
    if not isinstance(day_of_year, int) or isinstance(day_of_year, bool) \
            or not 1 <= day_of_year <= 366:
        return None, "Din 1 se 366 ke beech hona chahiye."
    order = list(GAMES.keys())
    rot = day_of_year % len(order)
    order = order[rot:] + order[:rot]
    if weakest is not None:
        if weakest not in SKILLS:
            return None, "Weakest skill ghalat hai."
        first = [g for g in order if GAMES[g]["skill"] == weakest]
        rest = [g for g in order if GAMES[g]["skill"] != weakest]
        order = first + rest
    plan = [{"game": g, "skill": GAMES[g]["skill"],
             "name_en": GAMES[g]["name_en"],
             "target_seconds": TARGET_SECONDS[g]} for g in order]
    return {"day": day_of_year, "weakest": weakest, "games": plan}, None


# --- AI validators -----------------------------------------------------------------
def word_count(text):
    return len(text.split())


def validate_ai_tip(text):
    """Daily training tip: 40-600 chars, at least 1 sentence."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 40:
        return None, "AI ka tip bohot chhota tha."
    if len(clean) > 600:
        return None, "AI ka tip bohot lamba tha."
    if "." not in clean and "؟" not in clean and "?" not in clean \
            and "!" not in clean:
        return None, "AI ke tip me koi jumla nahi tha."
    return clean, None


def validate_ai_summary(text):
    """Weekly progress summary: 80-900 chars, at least 2 sentences."""
    if not isinstance(text, str):
        return None, "AI ka jawab text nahi tha."
    clean = text.strip()
    if len(clean) < 80:
        return None, "AI ki summary bohot chhoti thi."
    if len(clean) > 900:
        return None, "AI ki summary bohot lambi thi."
    sentences = [s for s in clean.replace("؟", ".").replace("?", ".")
                 .replace("!", ".").split(".") if s.strip()]
    if len(sentences) < 2:
        return None, "AI ki summary me kam se kam 2 jumle hone chahiye."
    return clean, None
