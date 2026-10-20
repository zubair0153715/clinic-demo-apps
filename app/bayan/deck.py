"""Bayan deck model: normalization, validation, and themes.

A deck is a plain dict::

    {"title": str, "subtitle": str,
     "slides": [{"layout": str, "title": str, "bullets": [str],
                 "notes": str, "quote_by": str,
                 "stats": [{"value": str, "label": str}]}]}

Layouts: cover, section, bullets, stats, quote, closing.

normalize_deck() enforces every structural guarantee the .pptx builder and the
HTML preview rely on, so neither can emit overlapping or empty slides:
slide-count clamp, bullet-count clamp, per-field length caps, layout allow-list.
"""
import copy

LAYOUTS = ("cover", "section", "bullets", "stats", "quote", "closing")
MIN_SLIDES, MAX_SLIDES = 3, 20
MAX_BULLETS = 6
MAX_TITLE_CHARS = 90
MAX_BULLET_CHARS = 160
MAX_NOTES_CHARS = 400
MAX_STATS = 3

THEMES = {
    "midnight": {"label": "Midnight", "bg": "0F1B2D", "accent": "F2A900",
                 "text": "FFFFFF", "muted": "9FB2CC", "card": "1B2A44"},
    "paper": {"label": "Paper", "bg": "FFFFFF", "accent": "1D4ED8",
              "text": "111827", "muted": "6B7280", "card": "F3F4F6"},
    "forest": {"label": "Forest", "bg": "0C2318", "accent": "7BC47F",
               "text": "FFFFFF", "muted": "A8C3B0", "card": "14301F"},
}
DEFAULT_THEME = "midnight"


def _clip(text, limit):
    text = (text or "").strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def blank_slide(layout="bullets"):
    return {"layout": layout, "title": "", "bullets": [],
            "notes": "", "quote_by": "", "stats": []}


def normalize_slide(raw):
    """Return a sanitized slide dict; never raises on messy AI output."""
    raw = raw or {}
    s = blank_slide()
    layout = str(raw.get("layout", "bullets")).strip().lower()
    s["layout"] = layout if layout in LAYOUTS else "bullets"
    s["title"] = _clip(raw.get("title"), MAX_TITLE_CHARS)
    bullets = raw.get("bullets") or []
    if isinstance(bullets, str):
        bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
    s["bullets"] = [_clip(b, MAX_BULLET_CHARS) for b in bullets
                    if str(b).strip()][:MAX_BULLETS]
    s["notes"] = _clip(raw.get("notes"), MAX_NOTES_CHARS)
    s["quote_by"] = _clip(raw.get("quote_by"), 80)
    stats = raw.get("stats") or []
    clean_stats = []
    for st in stats[:MAX_STATS]:
        if isinstance(st, dict):
            clean_stats.append({"value": _clip(st.get("value"), 24),
                                "label": _clip(st.get("label"), 60)})
    s["stats"] = clean_stats
    # Layout-specific repairs so no slide renders empty or broken.
    if s["layout"] == "cover" and not s["title"]:
        s["title"] = "Untitled deck"
    if s["layout"] == "bullets" and not s["bullets"]:
        s["bullets"] = ["Add your points here — or ask the AI to draft them."]
    if s["layout"] == "stats" and not s["stats"]:
        s["layout"] = "bullets"
        s["bullets"] = ["Add your points here — or ask the AI to draft them."]
    if s["layout"] == "quote" and not s["bullets"] and not s["title"]:
        s["layout"] = "bullets"
        s["bullets"] = ["Add your points here — or ask the AI to draft them."]
    return s


def normalize_deck(raw, max_slides=MAX_SLIDES):
    """Sanitize a full deck dict. Returns (deck, warnings[list])."""
    warnings = []
    raw = raw or {}
    deck = {"title": _clip(raw.get("title"), MAX_TITLE_CHARS) or "Untitled deck",
            "subtitle": _clip(raw.get("subtitle"), 140),
            "slides": []}
    slides = raw.get("slides") or []
    if not isinstance(slides, list):
        slides = []
    for rs in slides[:max_slides]:
        deck["slides"].append(normalize_slide(rs if isinstance(rs, dict) else {}))
    if len(slides) > max_slides:
        warnings.append(f"Slide count clamped to {max_slides}.")
    # Guarantee a cover first and a closing last.
    if not deck["slides"]:
        deck["slides"] = [normalize_slide({"layout": "cover", "title": deck["title"]}),
                          normalize_slide({"layout": "closing", "title": deck["title"]})]
        warnings.append("Empty outline — started a minimal deck for you.")
    else:
        if deck["slides"][0]["layout"] != "cover":
            deck["slides"].insert(0, normalize_slide(
                {"layout": "cover", "title": deck["title"],
                 "bullets": [deck["subtitle"]] if deck["subtitle"] else []}))
        if deck["slides"][-1]["layout"] != "closing":
            deck["slides"].append(normalize_slide(
                {"layout": "closing", "title": deck["title"]}))
    # Final clamp AFTER cover/closing insertion: never exceed max_slides.
    while len(deck["slides"]) > max_slides:
        del deck["slides"][-2]  # drop second-to-last, keep closing last
        if "Slide count clamped to %d." % max_slides not in warnings:
            warnings.append("Slide count clamped to %d." % max_slides)
    if len(deck["slides"]) < MIN_SLIDES:
        warnings.append("Very short deck — consider 5+ slides.")
    return deck, warnings


def rule_based_outline(topic, notes, slide_count=8):
    """Honest no-AI fallback: structure the user's own notes into slides.

    Splits notes into lines; lines ending with ':' become section headers,
    the rest become bullets grouped ~4 per slide. The user's words are never
    rewritten — only arranged. Returns (deck, warnings).
    """
    topic = (topic or "").strip() or "Untitled deck"
    lines = [ln.strip("•-–* ").strip() for ln in (notes or "").splitlines()]
    lines = [ln for ln in lines if ln]
    slide_count = max(MIN_SLIDES, min(MAX_SLIDES, int(slide_count or 8)))
    slides = [{"layout": "cover", "title": topic,
               "bullets": [], "notes": "", "quote_by": "", "stats": []}]
    current = None
    per_slide = 4
    for ln in lines:
        if ln.endswith(":") and len(ln) < 60:
            if current and current["bullets"]:
                slides.append(current)
            current = {"layout": "section", "title": ln[:-1],
                       "bullets": [], "notes": "", "quote_by": "", "stats": []}
            slides.append(current)
            current = None
        else:
            if current is None or len(current["bullets"]) >= per_slide:
                if current is not None:
                    slides.append(current)
                current = {"layout": "bullets",
                           "title": f"{topic} — key points" if len(slides) < 2 else "Details",
                           "bullets": [], "notes": "", "quote_by": "", "stats": []}
            current["bullets"].append(ln)
    if current is not None:
        slides.append(current)
    # Trim or pad to the requested count.
    while len(slides) > slide_count - 1:
        # merge the two smallest bullet slides
        idxs = [i for i, s in enumerate(slides) if s["layout"] == "bullets"]
        if len(idxs) < 2:
            break
        a, b = idxs[0], idxs[1]
        slides[a]["bullets"].extend(slides[b]["bullets"][:MAX_BULLETS])
        del slides[b]
    slides.append({"layout": "closing", "title": topic,
                   "bullets": [], "notes": "", "quote_by": "", "stats": []})
    deck, warnings = normalize_deck({"title": topic, "subtitle": "",
                                     "slides": slides}, max_slides=slide_count)
    warnings.append("Rule-based draft (no AI) — your own words, only arranged.")
    return deck, warnings


def theme(name):
    return copy.deepcopy(THEMES.get(name, THEMES[DEFAULT_THEME]))
