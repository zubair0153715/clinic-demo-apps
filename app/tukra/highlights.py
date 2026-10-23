"""Tukra highlight engine — rule-based, explainable clip detection.

Original clean-room code. Given timed segments (from SRT/VTT) or plain
sentences, it finds high-retention windows and scores them with a visible
breakdown of hook features — no black-box "virality score".

A clip is a dict:
  {id, start, end, duration, text, hook, title, score, breakdown,
   timed (bool), ai_pick (bool)}
`breakdown` is a list of {feature, points, reason, evidence} so the UI can
show WHY a moment was picked.
"""
import re

# (key, compiled regex, points, reason shown in UI)
HOOK_FEATURES = [
    ("question",
     re.compile(r"\?"),
     3.0, "Sawal — viewers ruk kar jawab sunte hain"),
    ("number_stat",
     re.compile(r"\d[\d,.]*\s*(%|percent|fisad|million|billion|crore|lakh|hazaar|saal|din)?", re.I),
     2.0, "Number/stat — concrete baat zyada yaqeen dilati hai"),
    ("money",
     re.compile(r"(\$|rs\.?|rupee|dollar|paisa|pese|qeemat)", re.I),
     1.5, "Paise ki baat — sab ka dhyaan khichti hai"),
    ("superlative",
     re.compile(r"\b(best|worst|biggest|first|never|always|secret|raaz|truth|sach|mistake|ghalti|shocking|hairan|kun|dangerous|khatarnak)\b", re.I),
     2.0, "Superlative/secret — curiosity trigger"),
    ("howto",
     re.compile(r"\b(how to|kaise|tarika|tareeqa|steps?|nuskha)\b", re.I),
     2.0, "How-to — seekhne wale viewers sab se loyal hote hain"),
    ("listicle",
     re.compile(r"\b(pehla|pehli|dusra|dusri|teesra|number|no\.?\s*\d|tips?|wajooh|reasons?)\b", re.I),
     2.0, "List format — dekhna aasaan, share karna aasaan"),
    ("emotion",
     re.compile(r"\b(wow|amazing|zabardast|kamal|shandaar|crazy|pagal|love|mohabbat|hate|nafrat|fear|dar|khushi|gham)\b", re.I),
     1.5, "Emotion word — feeling wali baat yaad rehti hai"),
    ("contrast",
     re.compile(r"\b(but|lekin|magar|actually|darasal|asal mein|however|phir bhi)\b", re.I),
     1.0, "Contrast/turn — kahani mein mor aata hai"),
    ("direct_address",
     re.compile(r"\b(you|your|tum|tumhara|tumhein|aap|aapko)\b", re.I),
     1.0, "Direct address — viewer ko lagta hai usi se baat ho rahi hai"),
    ("urgency",
     re.compile(r"\b(abhi|now|today|aaj|foran|immediately|jaldi|akhir)\b", re.I),
     1.0, "Urgency — abhi dekhne ka ehsas"),
]

SENT_SPLIT = re.compile(r"(?<=[.!?؟…])\s+|\n+")

IDEAL_MIN, IDEAL_MAX = 20.0, 60.0   # seconds — sweet spot for Shorts/Reels
ABS_MIN, ABS_MAX = 12.0, 95.0       # hard clip bounds (timed mode)


def split_sentences(text):
    """Split plain text into sentences."""
    parts = [p.strip() for p in SENT_SPLIT.split(text or "") if p.strip()]
    return parts


def _score_text(text):
    """Score a text window. Returns (score, breakdown)."""
    score, breakdown = 0.0, []
    for key, rx, pts, reason in HOOK_FEATURES:
        hits = rx.findall(text)
        if hits:
            # Cap repeat hits so one long number list doesn't dominate.
            n = min(len(hits), 3)
            got = round(pts * (1 + 0.25 * (n - 1)), 2)
            score += got
            ev = hits[0] if isinstance(hits[0], str) else " ".join(hits[0])
            breakdown.append({"feature": key, "points": got,
                              "reason": reason, "evidence": ev[:60]})
    return round(score, 2), breakdown


def _length_adjust(duration):
    """Bonus/penalty for clip length (timed mode)."""
    if duration < ABS_MIN:
        return -2.0, "Bohat chhota — poori baat nahi banegi"
    if duration > ABS_MAX:
        return -2.0, "Bohat lamba — Shorts ke liye kaato"
    if IDEAL_MIN <= duration <= IDEAL_MAX:
        return 1.5, "Ideal Shorts length (20–60s)"
    return 0.0, ""


def _hook_sentence(text):
    """First punchy sentence = the hook shown on the clip card."""
    sents = split_sentences(text)
    if not sents:
        return text[:80]
    # Prefer a question or exclamation as the hook.
    for s in sents:
        if "?" in s or "!" in s:
            return s
    return sents[0]


def detect_highlights_timed(segments, max_clips=8):
    """Timed segments: [(start_sec, end_sec, text)]. Returns clip dicts."""
    segs = [(float(s), float(e), (t or "").strip())
            for s, e, t in segments if (t or "").strip()]
    if not segs:
        return []
    n = len(segs)
    candidates = []
    # Sliding windows: 2..6 segments, target 20-60 s.
    for width in range(2, 7):
        for i in range(n - width + 1):
            win = segs[i:i + width]
            start, end = win[0][0], win[-1][1]
            dur = end - start
            if dur > ABS_MAX + 30:
                continue
            text = " ".join(t for _, _, t in win)
            score, breakdown = _score_text(text)
            adj, adj_reason = _length_adjust(dur)
            score = round(score + adj, 2)
            if adj_reason:
                breakdown.append({"feature": "length", "points": adj,
                                  "reason": adj_reason, "evidence": f"{dur:.0f}s"})
            if score <= 0:
                continue
            candidates.append({
                "start": round(start, 2), "end": round(end, 2),
                "duration": round(dur, 2), "text": text,
                "hook": _hook_sentence(text), "title": "",
                "score": score, "breakdown": breakdown,
                "timed": True, "ai_pick": False,
                "sentence_range": [i, i + width - 1],
            })
    return _pick_best(candidates, max_clips)


def detect_highlights_text(text, max_clips=8):
    """Plain text (no timing): windows of 3-8 sentences. No fake timestamps."""
    sents = split_sentences(text)
    if not sents:
        return []
    candidates = []
    for width in (3, 4, 5, 6, 8):
        for i in range(len(sents) - width + 1):
            win = sents[i:i + width]
            joined = " ".join(win)
            score, breakdown = _score_text(joined)
            if score <= 0:
                continue
            candidates.append({
                "start": None, "end": None, "duration": None,
                "text": joined, "hook": _hook_sentence(joined), "title": "",
                "score": score, "breakdown": breakdown,
                "timed": False, "ai_pick": False,
                "sentence_range": [i, i + width - 1],
            })
    return _pick_best(candidates, max_clips)


def _overlap(a, b):
    """Fraction of the shorter clip overlapped (timed) or sentence overlap."""
    if a.get("timed") and b.get("timed"):
        s = max(a["start"], b["start"])
        e = min(a["end"], b["end"])
        inter = max(0.0, e - s)
        shorter = min(a["duration"], b["duration"])
        return inter / shorter if shorter else 0.0
    ra, rb = a.get("sentence_range"), b.get("sentence_range")
    if ra and rb:
        inter = max(0, min(ra[1], rb[1]) - max(ra[0], rb[0]) + 1)
        shorter = min(ra[1] - ra[0] + 1, rb[1] - rb[0] + 1)
        return inter / shorter if shorter else 0.0
    return 0.0


def _pick_best(candidates, max_clips):
    """Greedy by score, dropping windows that overlap a chosen clip > 50%."""
    chosen = []
    for c in sorted(candidates, key=lambda c: -c["score"]):
        if all(_overlap(c, o) <= 0.5 for o in chosen):
            chosen.append(c)
        if len(chosen) >= max_clips:
            break
    for i, c in enumerate(chosen):
        c["id"] = f"clip-{i + 1}"
    return chosen


def apply_ai_picks(clips, ai_picks, boost=5.0):
    """Merge Gemini moment picks: boost score, set title, flag ai_pick."""
    by_range = {}
    for c in clips:
        key = (c.get("sentence_range") or [None, None])[0]
        by_range.setdefault(key, []).append(c)
    for p in ai_picks or []:
        s0 = p.get("start_idx")
        cands = by_range.get(s0, [])
        if not cands:
            continue
        # Closest end match wins.
        best = min(cands, key=lambda c: abs(
            (c.get("sentence_range") or [0, 0])[1] - p.get("end_idx", s0)))
        best["score"] = round(best["score"] + boost, 2)
        best["ai_pick"] = True
        if p.get("title"):
            best["title"] = p["title"][:90]
        if p.get("why"):
            best["breakdown"].append(
                {"feature": "ai", "points": boost,
                 "reason": "AI pick — " + p["why"][:120], "evidence": ""})
    return sorted(clips, key=lambda c: -c["score"])
