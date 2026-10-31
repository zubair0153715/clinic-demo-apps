"""Majlis engine — deterministic meeting-notes structuring.

Original clean-room build. Not affiliated with Granola, Otter,
Fireflies, Fathom or tl;dv. Everything here is rule-based and
works with no AI key and no audio: the user pastes a transcript
(from any recorder or free transcription tool) or types notes
live, and the engine parses turns, extracts decisions, action
items (owner + due date) and open questions, computes talk-share
stats, and renders minutes + a WhatsApp follow-up draft.

No invented facts: every extracted item cites the transcript line
it came from. v1 does NOT record audio and does NOT transcribe
speech — that limit is stated on the page.
"""

import re

MAX_TRANSCRIPT_CHARS = 100_000
MAX_TITLE_CHARS = 200
MAX_LINES = 2000
WORDS_PER_MINUTE = 150

DAYS = ("monday|tuesday|wednesday|thursday|friday|saturday|sunday")
MONTHS = ("jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
          "jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
          "dec(?:ember)?")

SPEAKER_RE = re.compile(
    r"^([A-Za-z][A-Za-z .]{0,30}?)\s*[:\-\u2013\u2014]\s+(.+)$")
DECISION_RE = re.compile(
    r"\b(agreed|decided|approved|resolved|final decision|we all agree)\b",
    re.I)
ACTION_RE = re.compile(
    r"\b(will|shall|need to|needs to|must|going to|has to|have to|"
    r"todo|action:?|i'll|i will)\b", re.I)
DUE_BY_RE = re.compile(
    r"\bby\s+(" + DAYS + r"|tomorrow|today|next week|next month|"
    r"\d{1,2}\s+(?:" + MONTHS + r")|\d{1,2}/\d{1,2})\b", re.I)
DUE_BARE_RE = re.compile(
    r"\b(tomorrow|today|next week|next month|next\s+(?:" + DAYS + r")|"
    r"on\s+\d{1,2}\s+(?:" + MONTHS + r"))\b", re.I)
OWNER_NAME_RE = re.compile(
    r"^([A-Z][a-z]+)\s+(will|shall|needs?\s+to|must|has\s+to)\b")
OWNER_I_RE = re.compile(r"^I\s+(will|shall|need\s+to|must|have\s+to)\b", re.I)
OWNER_WE_RE = re.compile(r"^We\s+(will|shall|need\s+to|must)\b", re.I)

HEADINGS = {
    "en": {"summary": "Summary", "decisions": "Decisions",
           "actions": "Action items", "questions": "Open questions",
           "transcript": "Transcript", "stats": "Meeting stats",
           "followup": "Follow-up message"},
    "roman": {"summary": "Khulasa", "decisions": "Faislay",
              "actions": "Kaam (Action items)",
              "questions": "Khulay sawal", "transcript": "Transcript",
              "stats": "Meeting ki tafseel",
              "followup": "Follow-up message"},
    "ur": {"summary": "خلاصہ", "decisions": "فیصلے",
           "actions": "ذمہ داریاں", "questions": "کھلے سوالات",
           "transcript": "مکمل گفتگو", "stats": "میٹنگ کی تفصیل",
           "followup": "فالو اپ پیغام"},
}

MEETING_TYPES = ("team", "client", "sales", "one-on-one",
                 "brainstorm", "other")


def check_caps(data):
    """Return an error string if any input cap is exceeded, else None."""
    if len(data.get("transcript", "")) > MAX_TRANSCRIPT_CHARS:
        return (f"Transcript is too long "
                f"({len(data['transcript'])} chars, max "
                f"{MAX_TRANSCRIPT_CHARS}). Split it into two meetings.")
    if len(data.get("title", "")) > MAX_TITLE_CHARS:
        return f"Title is too long (max {MAX_TITLE_CHARS} chars)."
    if len(data.get("transcript", "").splitlines()) > MAX_LINES:
        return (f"Too many lines (max {MAX_LINES}). "
                "Split it into two meetings.")
    return None


def parse_turns(text):
    """Split transcript text into speaker turns.

    A line starting with ``Name: ...`` or ``Name - ...`` starts a new
    turn; other lines continue the previous turn. Lines with no
    speaker get speaker "Unknown". Returns a list of dicts with
    speaker, text and the 1-based line number the turn started on.
    """
    turns = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        m = SPEAKER_RE.match(line)
        if m and m.group(1).strip().lower() not in ("decided", "agreed"):
            name = m.group(1).strip().rstrip(".")
            turns.append({"speaker": name, "text": m.group(2).strip(),
                          "line": i})
        elif turns:
            turns[-1]["text"] += " " + line
        else:
            turns.append({"speaker": "Unknown", "text": line, "line": i})
    return turns


def split_sentences(text):
    """Split a turn's text into sentences, keeping the terminator."""
    parts = re.split(r"(?<=[.?!])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def word_count(text):
    return len(text.split())


def extract_owner(sentence, speaker):
    """Who owes this action sentence? Name, speaker ('I ...'), or Team."""
    m = OWNER_NAME_RE.match(sentence)
    if m:
        return m.group(1)
    if OWNER_I_RE.match(sentence):
        return speaker
    if OWNER_WE_RE.match(sentence):
        return "Team"
    return speaker


def extract_due(sentence):
    """Due phrase from a sentence, e.g. 'Friday', 'tomorrow'."""
    m = DUE_BY_RE.search(sentence)
    if m:
        return m.group(1)
    m = DUE_BARE_RE.search(sentence)
    if m:
        return m.group(1)
    return None


def analyse(turns):
    """Classify every sentence; return decisions/actions/questions."""
    decisions, actions, questions = [], [], []
    for turn in turns:
        for sent in split_sentences(turn["text"]):
            item = {"text": sent, "speaker": turn["speaker"],
                    "line": turn["line"]}
            if sent.endswith("?"):
                questions.append(item)
                continue
            if DECISION_RE.search(sent):
                decisions.append(item)
            if ACTION_RE.search(sent):
                actions.append({
                    "text": sent, "speaker": turn["speaker"],
                    "line": turn["line"],
                    "owner": extract_owner(sent, turn["speaker"]),
                    "due": extract_due(sent),
                })
    return decisions, actions, questions


def stats(turns):
    """Talk-share and size stats, all arithmetic on word counts."""
    total_words = sum(word_count(t["text"]) for t in turns)
    per_speaker = {}
    for t in turns:
        per_speaker[t["speaker"]] = (
            per_speaker.get(t["speaker"], 0) + word_count(t["text"]))
    share = []
    for speaker, words in sorted(per_speaker.items(),
                                 key=lambda kv: -kv[1]):
        pct = round(words * 100 / total_words) if total_words else 0
        share.append({"speaker": speaker, "words": words, "pct": pct})
    minutes = round(total_words / WORDS_PER_MINUTE, 1) if total_words else 0
    return {"words": total_words, "turns": len(turns),
            "speakers": len(per_speaker), "share": share,
            "est_minutes": minutes}


def followup_message(title, date, decisions, actions, language):
    """WhatsApp-ready follow-up draft, built only from extracted items."""
    lang = language if language in HEADINGS else "en"
    if lang == "ur":
        head = f"میٹنگ فالو اپ — {title}" + (f" ({date})" if date else "")
        d_head, a_head = "فیصلے:", "ذمہ داریاں:"
        d_none, a_none = "کوئی فیصلہ درج نہیں ہوا۔", "کوئی ذمہ داری نہیں ملی۔"
        due_word = "تک"
    elif lang == "roman":
        head = f"Meeting follow-up — {title}" + (f" ({date})" if date else "")
        d_head, a_head = "Faislay:", "Kaam:"
        d_none, a_none = "Koi faisla record nahi hua.", "Koi kaam nahi mila."
        due_word = "tak"
    else:
        head = f"Meeting follow-up — {title}" + (f" ({date})" if date else "")
        d_head, a_head = "Decisions:", "Action items:"
        d_none, a_none = "No decisions recorded.", "No action items found."
        due_word = "by"
    lines = [head, "", d_head]
    if decisions:
        lines += [f"- {d['text']}" for d in decisions]
    else:
        lines.append(f"- {d_none}")
    lines += ["", a_head]
    if actions:
        for a in actions:
            due = f", {due_word} {a['due']}" if a["due"] else ""
            lines.append(f"- {a['text']} — {a['owner']}{due}")
    else:
        lines.append(f"- {a_none}")
    return "\n".join(lines)


def to_markdown(title, date, mtype, language, st, decisions, actions,
                questions, turns):
    """Exportable minutes in Markdown, with line cites for every item."""
    lang = language if language in HEADINGS else "en"
    h = HEADINGS[lang]
    lines = [f"# {title or 'Meeting notes'}"]
    if date:
        lines.append(f"Date: {date}")
    lines.append(f"Type: {mtype}")
    lines += ["", f"## {h['stats']}"]
    lines.append(f"- Words: {st['words']} | Turns: {st['turns']} | "
                 f"Speakers: {st['speakers']} | "
                 f"Est. length: {st['est_minutes']} min")
    for s in st["share"]:
        lines.append(f"- {s['speaker']}: {s['words']} words ({s['pct']}%)")
    lines += ["", f"## {h['decisions']}"]
    if decisions:
        lines += [f"- {d['text']} (line {d['line']})" for d in decisions]
    else:
        lines.append("- None recorded.")
    lines += ["", f"## {h['actions']}"]
    if actions:
        for a in actions:
            due = f", due {a['due']}" if a["due"] else ""
            lines.append(f"- [ ] {a['text']} — {a['owner']}{due} "
                         f"(line {a['line']})")
    else:
        lines.append("- None found.")
    lines += ["", f"## {h['questions']}"]
    if questions:
        lines += [f"- {q['text']} (line {q['line']})" for q in questions]
    else:
        lines.append("- None recorded.")
    lines += ["", f"## {h['transcript']}"]
    for t in turns:
        lines.append(f"{t['speaker']}: {t['text']}")
    return "\n".join(lines) + "\n"


def structure_meeting(data):
    """Full pipeline: parse, classify, stats, follow-up, markdown."""
    title = (data.get("title") or "").strip() or "Untitled meeting"
    date = (data.get("date") or "").strip()
    mtype = data.get("mtype") or "other"
    if mtype not in MEETING_TYPES:
        mtype = "other"
    language = data.get("language") or "en"
    if language not in HEADINGS:
        language = "en"
    transcript = data.get("transcript") or ""
    turns = parse_turns(transcript)
    decisions, actions, questions = analyse(turns)
    st = stats(turns)
    followup = followup_message(title, date, decisions, actions, language)
    markdown = to_markdown(title, date, mtype, language, st, decisions,
                           actions, questions, turns)
    return {"ok": True, "title": title, "date": date, "mtype": mtype,
            "language": language, "turns": turns, "stats": st,
            "decisions": decisions, "actions": actions,
            "questions": questions, "followup": followup,
            "markdown": markdown}
