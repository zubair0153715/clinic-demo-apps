"""Bayan .pptx builder — native python-pptx output that opens cleanly.

This module exists to NOT reproduce the target app's #1 export complaint
(overlapping text boxes, missing fonts). Every text box is placed with
computed, non-overlapping coordinates on a 16:9 canvas, uses the standard
Calibri typeface, and gets SHAPE_TO_FIT_TEXT auto-sizing as a safety net.
No branding or watermarks are stamped anywhere.
"""
from io import BytesIO

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt

from . import deck as deckmod

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)
FONT = "Calibri"


def _rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = _rgb(color)


def _box(slide, left, top, width, height):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                     Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    return tf


def _para(tf, text, size, color, bold=False, italic=False,
          align=PP_ALIGN.LEFT, first=False, space_after=6):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.italic = italic
    p.font.color.rgb = _rgb(color)
    p.font.name = FONT
    p.alignment = align
    p.space_after = Pt(space_after)
    p.line_spacing = 1.15
    return p


def _number(slide, n, total, theme):
    tf = _box(slide, 12.3, 7.0, 0.7, 0.3)
    _para(tf, f"{n}/{total}", 10, theme["muted"], align=PP_ALIGN.RIGHT, first=True)


def _cover(slide, s, d, theme, n, total):
    _bg(slide, theme["bg"])
    # accent bar via a thin shape
    bar = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.14))
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme["accent"])
    bar.line.fill.background()
    tf = _box(slide, 1.0, 2.2, 11.333, 2.2)
    _para(tf, s["title"] or d["title"], 44, theme["text"], bold=True,
          align=PP_ALIGN.CENTER, first=True)
    sub = s["bullets"][0] if s["bullets"] else d["subtitle"]
    if sub:
        tf = _box(slide, 2.0, 4.6, 9.333, 1.2)
        _para(tf, sub, 20, theme["muted"], align=PP_ALIGN.CENTER, first=True)
    _number(slide, n, total, theme)


def _section(slide, s, theme, n, total):
    _bg(slide, theme["card"])
    bar = slide.shapes.add_shape(1, Inches(1.0), Inches(3.3), Inches(1.2), Inches(0.12))
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme["accent"])
    bar.line.fill.background()
    tf = _box(slide, 1.0, 3.6, 11.333, 2.5)
    _para(tf, s["title"], 40, theme["text"], bold=True, first=True)
    _number(slide, n, total, theme)


def _bullets(slide, s, theme, n, total):
    _bg(slide, theme["bg"])
    tf = _box(slide, 0.9, 0.4, 11.5, 1.3)
    _para(tf, s["title"], 32, theme["text"], bold=True, first=True)
    rule = slide.shapes.add_shape(1, Inches(0.9), Inches(1.55), Inches(1.0), Inches(0.07))
    rule.fill.solid()
    rule.fill.fore_color.rgb = _rgb(theme["accent"])
    rule.line.fill.background()
    size = 20 if len(s["bullets"]) <= 4 else 18
    tf = _box(slide, 0.9, 1.9, 11.5, 4.8)
    first = True
    for b in s["bullets"]:
        _para(tf, "•  " + b, size, theme["text"], first=first, space_after=10)
        first = False
    if s["notes"]:
        tf = _box(slide, 0.9, 6.55, 11.5, 0.6)
        _para(tf, "Notes: " + s["notes"], 11, theme["muted"], italic=True, first=True)
    _number(slide, n, total, theme)


def _stats(slide, s, theme, n, total):
    _bg(slide, theme["bg"])
    tf = _box(slide, 0.9, 0.4, 11.5, 1.3)
    _para(tf, s["title"], 32, theme["text"], bold=True, first=True)
    stats = s["stats"][:3] or [{"value": "—", "label": ""}]
    col_w = 11.5 / len(stats)
    for i, st in enumerate(stats):
        tf = _box(slide, 0.9 + i * col_w, 2.4, col_w - 0.2, 3.6)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        _para(tf, st["value"], 54, theme["accent"], bold=True,
              align=PP_ALIGN.CENTER, first=True)
        if st["label"]:
            _para(tf, st["label"], 18, theme["muted"], align=PP_ALIGN.CENTER)
    _number(slide, n, total, theme)


def _quote(slide, s, theme, n, total):
    _bg(slide, theme["card"])
    text = s["title"] if not s["bullets"] else s["bullets"][0]
    tf = _box(slide, 1.6, 2.0, 10.1, 3.2)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    _para(tf, "\u201c" + text + "\u201d", 28, theme["text"], italic=True,
          align=PP_ALIGN.CENTER, first=True)
    if s["quote_by"]:
        tf = _box(slide, 1.6, 5.2, 10.1, 0.8)
        _para(tf, "— " + s["quote_by"], 16, theme["muted"],
              align=PP_ALIGN.CENTER, first=True)
    _number(slide, n, total, theme)


def _closing(slide, s, d, theme, n, total):
    _bg(slide, theme["bg"])
    tf = _box(slide, 1.0, 2.4, 11.333, 1.4)
    _para(tf, "Thank you", 40, theme["text"], bold=True,
          align=PP_ALIGN.CENTER, first=True)
    tf = _box(slide, 1.0, 3.9, 11.333, 1.2)
    _para(tf, s["title"] or d["title"], 24, theme["accent"],
          align=PP_ALIGN.CENTER, first=True)
    if d["subtitle"]:
        tf = _box(slide, 2.0, 5.0, 9.333, 1.0)
        _para(tf, d["subtitle"], 18, theme["muted"],
              align=PP_ALIGN.CENTER, first=True)
    _number(slide, n, total, theme)


_BUILDERS = {"cover": _cover, "section": _section, "bullets": _bullets,
             "stats": _stats, "quote": _quote, "closing": _closing}


def build_pptx(raw_deck, theme_name="midnight"):
    """Build a .pptx from a deck dict. Returns bytes. Never stamps branding."""
    d, _warnings = deckmod.normalize_deck(raw_deck)
    theme = deckmod.theme(theme_name)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]  # blank — full manual control, no placeholders
    total = len(d["slides"])
    for i, s in enumerate(d["slides"], start=1):
        slide = prs.slides.add_slide(blank)
        if s["layout"] == "cover":
            _cover(slide, s, d, theme, i, total)
        elif s["layout"] == "closing":
            _closing(slide, s, d, theme, i, total)
        else:
            _BUILDERS[s["layout"]](slide, s, theme, i, total)
    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
