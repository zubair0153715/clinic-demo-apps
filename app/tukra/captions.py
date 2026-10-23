"""Tukra captions — parse SRT/VTT, emit karaoke ASS / SRT / WebVTT.

Word timing: when only line-level timing exists, a line's duration is split
across its words proportionally by character count (documented approximation;
exact when word timestamps come from a transcriber). ASS karaoke uses \\k tags
in centiseconds; libass renders these as the word-by-word highlight style.
"""
import re

TS = re.compile(
    r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def _to_sec(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_timed(text):
    """Parse SRT or WebVTT. Returns [(start, end, text)]. Raises ValueError."""
    cues = []
    # Normalize: strip WEBVTT header / cue settings, keep timestamp lines.
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        # Drop numeric cue ids and the WEBVTT header line.
        lines = [ln for ln in lines
                 if not re.fullmatch(r"\d+", ln) and ln != "WEBVTT"]
        if not lines:
            continue
        m = TS.search(lines[0])
        if not m:
            continue
        start = _to_sec(*m.groups()[:4])
        end = _to_sec(*m.groups()[4:])
        # Strip cue settings after the timestamp (e.g. "align:start").
        body = re.sub(r"\s+[a-z-]+:[^\s]*", "", lines[0][m.end():]).strip()
        words = [body] if body else []
        words += [re.sub(r"<[^>]+>", "", ln) for ln in lines[1:]]
        cue_text = " ".join(w for w in words if w).strip()
        if cue_text and end > start:
            cues.append((round(start, 3), round(end, 3), cue_text))
    if not cues:
        raise ValueError("Koi timed cue nahi mila — SRT ya VTT format check karo.")
    return sorted(cues, key=lambda c: c[0])


def detect_input_format(text):
    t = (text or "").strip()
    if t.upper().startswith("WEBVTT") or "-->" in t:
        return "timed"
    return "text"


def words_for_line(text, start, end):
    """Split a line into words with proportional timing (documented approx)."""
    words = [w for w in (text or "").split() if w]
    if not words:
        return []
    total = sum(len(w) for w in words) or 1
    dur = max(0.0, end - start)
    out, cursor = [], start
    for i, w in enumerate(words):
        share = len(w) / total
        wend = start + dur * sum(len(x) for x in words[:i + 1]) / total
        if i == len(words) - 1:
            wend = end  # last word owns the rounding remainder
        out.append((w, round(cursor, 3), round(wend, 3)))
        cursor = wend
    return out


def clip_words(segments, clip_start, clip_end):
    """Word timings for one clip, shifted so the clip starts at 0."""
    out = []
    for s, e, text in segments:
        if e <= clip_start or s >= clip_end:
            continue
        cs, ce = max(s, clip_start), min(e, clip_end)
        for w, ws, we in words_for_line(text, cs, ce):
            out.append((w, round(ws - clip_start, 3), round(we - clip_start, 3)))
    return out


def ass_time(sec):
    """ASS timestamp H:MM:SS.cc (centiseconds, floor)."""
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int((sec - int(sec)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_time(sec):
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def vtt_time(sec):
    return srt_time(sec).replace(",", ".")


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Tukra,Arial,64,&H00FFFFFF,&H000019FF,&H80000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def to_ass_karaoke(words, max_words_per_line=4):
    """Word list [(word, start, end)] -> ASS with \\k karaoke timing.

    Karaoke chunks are grouped into short lines (max_words_per_line) so the
    caption block stays readable on a 1080x1920 frame.
    """
    if not words:
        raise ValueError("Caption ke liye koi word nahi mila.")
    lines = ["Dialogue: 0,%s,%s,Tukra,,0,0,0,,%s"]
    events = []
    for i in range(0, len(words), max_words_per_line):
        chunk = words[i:i + max_words_per_line]
        parts = []
        for w, ws, we in chunk:
            cs = max(1, int(round((we - ws) * 100)))  # centiseconds, >= 1
            parts.append("{\\k%d}%s" % (cs, w))
        events.append("Dialogue: 0,%s,%s,Tukra,,0,0,0,,%s" % (
            ass_time(chunk[0][1]), ass_time(chunk[-1][2]), " ".join(parts)))
    return ASS_HEADER + "\n".join(events) + "\n"


def to_srt(words, max_words_per_line=4):
    """Word list -> plain SRT (line-level, no karaoke)."""
    if not words:
        raise ValueError("Caption ke liye koi word nahi mila.")
    out = []
    for n, i in enumerate(range(0, len(words), max_words_per_line), 1):
        chunk = words[i:i + max_words_per_line]
        out.append(str(n))
        out.append(f"{srt_time(chunk[0][1])} --> {srt_time(chunk[-1][2])}")
        out.append(" ".join(w for w, _, _ in chunk))
        out.append("")
    return "\n".join(out)


def to_vtt(words, max_words_per_line=4):
    """Word list -> WebVTT for the in-browser preview overlay."""
    if not words:
        raise ValueError("Caption ke liye koi word nahi mila.")
    out = ["WEBVTT", ""]
    for i in range(0, len(words), max_words_per_line):
        chunk = words[i:i + max_words_per_line]
        out.append(f"{vtt_time(chunk[0][1])} --> {vtt_time(chunk[-1][2])}")
        out.append(" ".join(w for w, _, _ in chunk))
        out.append("")
    return "\n".join(out)


def social_caption(hook, lang="en"):
    """Ready-to-post caption: hook + hashtags."""
    tags_en = "#shorts #podcastclips #viralshorts #reels #tukra"
    tags_ur = "#shorts #urdushorts #podcast #reels #tukra"
    tags = tags_ur if lang == "ur" else tags_en
    hook = (hook or "").strip()
    if len(hook) > 140:
        hook = hook[:137].rsplit(" ", 1)[0] + "…"
    return f"{hook}\n\n{tags}" if hook else tags
