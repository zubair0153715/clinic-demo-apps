"""Waqt scheduling engine — deterministic greedy day planner.

Original clean-room build (Motion gap build). No learning model, no
external calls: tasks are sorted by (deadline, priority, longest
first) and placed into the earliest free slot on or before their
deadline, inside working hours, skipping fixed events, focus blocks
and (optionally) prayer windows. Long tasks split into chunks of at
most ``max_chunk`` minutes with a short break between chunks.

Times are minutes since midnight; dates are ISO strings
("YYYY-MM-DD"). Everything is pure functions so the tests can check
hand-computed placements.
"""
import datetime
import re

MIN_CHUNK = 15          # never place a chunk shorter than this unless it finishes the task
DEFAULT_WORK_START = 9 * 60    # 09:00
DEFAULT_WORK_END = 18 * 60     # 18:00
DEFAULT_BREAK = 10             # minutes between chunks
DEFAULT_MAX_CHUNK = 90         # minutes
DEFAULT_DAYS = 7               # how far ahead the plan looks

# Default prayer windows (minutes since midnight), Pakistan-typical.
# Only the ones inside working hours matter for most users; the list
# is data, not a religious ruling — the user can edit or switch off.
DEFAULT_PRAYER_WINDOWS = [
    (5 * 60, 5 * 60 + 15),        # Fajr 05:00-05:15
    (13 * 60, 13 * 60 + 20),      # Zuhr 13:00-13:20
    (16 * 60 + 30, 16 * 60 + 45),  # Asr 16:30-16:45
    (18 * 60 + 30, 18 * 60 + 45),  # Maghrib 18:30-18:45
    (20 * 60, 20 * 60 + 15),      # Isha 20:00-20:15
]

PRIORITY_LABELS = {1: "Must", 2: "Should", 3: "Nice"}


def parse_date(value):
    """Parse an ISO date string -> datetime.date, or None."""
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(str(value).strip()[:10])
    except (ValueError, TypeError, AttributeError):
        return None


def fmt_time(minutes):
    """Minutes since midnight -> 'HH:MM' (24h)."""
    minutes = int(minutes) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def fmt_dur(minutes):
    """Minutes -> '1h 30m' / '45m'."""
    minutes = int(minutes)
    if minutes < 60:
        return f"{minutes}m"
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if m else f"{h}h"


def merge_intervals(intervals):
    """Merge overlapping/adjacent [start, end) intervals, sorted."""
    out = []
    for s, e in sorted(intervals):
        if e <= s:
            continue
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def free_intervals(work_start, work_end, busy):
    """Free [start, end) slots inside the working window."""
    busy = merge_intervals([(max(s, work_start), min(e, work_end))
                            for s, e in busy if e > work_start and s < work_end])
    free, cursor = [], work_start
    for s, e in busy:
        if s > cursor:
            free.append((cursor, s))
        cursor = max(cursor, e)
    if cursor < work_end:
        free.append((cursor, work_end))
    return free


def validate_task(raw):
    """Return (task dict, error). Task fields: title, minutes,
    deadline (ISO date), priority 1-3, project, splittable."""
    if not isinstance(raw, dict):
        return None, "Task must be an object."
    title = str(raw.get("title", "")).strip()
    if not title:
        return None, "Task title missing."
    try:
        minutes = int(raw.get("minutes", 0))
    except (TypeError, ValueError):
        return None, f"Bad duration for '{title}'."
    if minutes <= 0:
        return None, f"Duration must be positive for '{title}'."
    if minutes > 16 * 60:
        return None, f"'{title}' is over 16 hours — split it first."
    deadline = parse_date(raw.get("deadline"))
    if deadline is None:
        return None, f"Bad deadline for '{title}' (use YYYY-MM-DD)."
    try:
        priority = int(raw.get("priority", 2))
    except (TypeError, ValueError):
        priority = 2
    priority = min(3, max(1, priority))
    return {
        "id": str(raw.get("id") or title.lower().replace(" ", "-")[:40]),
        "title": title[:120],
        "minutes": minutes,
        "deadline": deadline.isoformat(),
        "priority": priority,
        "project": str(raw.get("project", "")).strip()[:60],
        "splittable": bool(raw.get("splittable", True)),
    }, None


def schedule(tasks, events=None, settings=None, start_date=None):
    """Greedy schedule.

    tasks: list of raw task dicts (see validate_task).
    events: list of {title, date, start, end} fixed blocks (minutes).
    settings: {work_start, work_end, break_min, max_chunk,
               prayer (bool), prayer_windows, focus: [{start, end}]}
    start_date: ISO date to start planning from (default today).

    Returns (result, error). result: {blocks, unplaced, days, stats}.
    blocks: [{task_id, title, date, start, end, priority, project,
              chunk_of}] sorted by date then start.
    unplaced: [{task_id, title, minutes_left, deadline, reason,
                suggestions: {split, defer_to, shorten_by}}].
    """
    settings = settings or {}
    work_start = int(settings.get("work_start", DEFAULT_WORK_START))
    work_end = int(settings.get("work_end", DEFAULT_WORK_END))
    break_min = int(settings.get("break_min", DEFAULT_BREAK))
    max_chunk = int(settings.get("max_chunk", DEFAULT_MAX_CHUNK))
    prayer_on = bool(settings.get("prayer", True))
    prayer_windows = settings.get("prayer_windows", DEFAULT_PRAYER_WINDOWS)
    focus = settings.get("focus", []) or []
    if work_end <= work_start:
        return None, "Work end must be after work start."
    if max_chunk < MIN_CHUNK:
        return None, f"Max chunk must be at least {MIN_CHUNK} minutes."

    start = parse_date(start_date) if start_date else datetime.date.today()
    if start is None:
        return None, "Bad start date."

    clean_tasks, errors = [], []
    for raw in tasks or []:
        task, err = validate_task(raw)
        if err:
            errors.append(err)
        else:
            clean_tasks.append(task)
    if errors:
        return None, "; ".join(errors)

    # Fixed events, grouped by date; ignore malformed ones.
    fixed = {}
    for ev in events or []:
        d = parse_date((ev or {}).get("date"))
        try:
            s, e = int(ev.get("start")), int(ev.get("end"))
        except (TypeError, ValueError, AttributeError):
            continue
        if d is None or e <= s:
            continue
        fixed.setdefault(d.isoformat(), []).append((s, e))

    focus_intervals = []
    for fb in focus:
        try:
            s, e = int(fb.get("start")), int(fb.get("end"))
        except (TypeError, ValueError, AttributeError):
            continue
        if e > s:
            focus_intervals.append((s, e))

    prayer_intervals = list(prayer_windows) if prayer_on else []

    # Earliest deadline first, then Must before Nice, then longest first.
    ordered = sorted(
        clean_tasks,
        key=lambda t: (t["deadline"], t["priority"], -t["minutes"]))

    placed = {}          # date iso -> list of (start, end) already booked
    blocks, unplaced = [], []
    for task in ordered:
        deadline = parse_date(task["deadline"])
        if deadline < start:
            unplaced.append(_unplaced(
                task, task["minutes"], "deadline guzar gayi",
                {"split": False, "defer_to": None,
                 "shorten_by": 0}))
            continue
        remaining = task["minutes"]
        day = start
        chunk_no = 0
        while remaining > 0 and day <= deadline:
            day_iso = day.isoformat()
            # Place chunks one at a time, recomputing free slots after
            # each chunk so breaks and earlier chunks are respected.
            while remaining > 0:
                busy = list(fixed.get(day_iso, []))
                busy += focus_intervals
                busy += prayer_intervals
                busy += placed.get(day_iso, [])
                done_chunk = False
                for s, e in free_intervals(work_start, work_end, busy):
                    avail = e - s
                    if avail <= 0:
                        continue
                    limit = max_chunk if task["splittable"] else remaining
                    chunk = min(remaining, limit, avail)
                    # Skip a sliver that cannot usefully hold a chunk,
                    # unless it finishes the task.
                    if chunk < MIN_CHUNK and chunk < remaining:
                        continue
                    chunk_no += 1
                    blocks.append({
                        "task_id": task["id"], "title": task["title"],
                        "date": day_iso, "start": s, "end": s + chunk,
                        "priority": task["priority"],
                        "project": task["project"],
                        "chunk_of": chunk_no,
                    })
                    placed.setdefault(day_iso, []).append((s, s + chunk))
                    remaining -= chunk
                    if remaining > 0:
                        # Reserve the break so the next chunk starts
                        # after it (not a block, just busy time).
                        placed[day_iso].append(
                            (s + chunk, s + chunk + break_min))
                    done_chunk = True
                    break
                if not done_chunk:
                    break
            day += datetime.timedelta(days=1)
        if remaining > 0:
            free_before = _free_minutes_before(
                start, deadline, fixed, focus_intervals,
                prayer_intervals, work_start, work_end)
            unplaced.append(_unplaced(
                task, remaining,
                f"deadline {deadline.isoformat()} tak sirf "
                f"{fmt_dur(free_before)} free tha, "
                f"{fmt_dur(remaining)} reh gaya",
                _suggestions(task, remaining, deadline, max_chunk)))

    blocks.sort(key=lambda b: (b["date"], b["start"]))

    # Per-day summary + totals.
    days = {}
    day = start
    last = max([parse_date(b["date"]) for b in blocks] +
               [parse_date(t["deadline"]) for t in clean_tasks] +
               [start])
    while day <= last:
        iso = day.isoformat()
        day_blocks = [b for b in blocks if b["date"] == iso]
        planned = sum(b["end"] - b["start"] for b in day_blocks)
        busy = list(fixed.get(iso, [])) + focus_intervals + prayer_intervals
        busy_m = sum(e - s for s, e in
                     merge_intervals([(max(s, work_start), min(e, work_end))
                                      for s, e in busy
                                      if e > work_start and s < work_end]))
        focus_m = sum(e - s for s, e in focus_intervals)
        days[iso] = {
            "planned": planned,
            "busy": busy_m,
            "focus": focus_m,
            "free": max(0, (work_end - work_start) - busy_m - planned),
            "blocks": len(day_blocks),
        }
        day += datetime.timedelta(days=1)

    stats = {
        "tasks": len(clean_tasks),
        "scheduled": len(clean_tasks) - len(unplaced),
        "unplaced": len(unplaced),
        "planned_min": sum(b["end"] - b["start"] for b in blocks),
        "focus_min": sum(d["focus"] for d in days.values()),
    }
    return {"blocks": blocks, "unplaced": unplaced, "days": days,
            "stats": stats}, None


def _unplaced(task, left, reason, suggestions):
    return {"task_id": task["id"], "title": task["title"],
            "minutes_left": left, "deadline": task["deadline"],
            "priority": task["priority"], "reason": reason,
            "suggestions": suggestions}


def _suggestions(task, left, deadline, max_chunk):
    return {
        "split": bool(task["splittable"] and task["minutes"] > max_chunk),
        "defer_to": (deadline + datetime.timedelta(days=1)).isoformat(),
        "shorten_by": left,
    }


def _free_minutes_before(start, deadline, fixed, focus, prayer,
                        work_start, work_end):
    """Total free minutes from start..deadline ignoring placed tasks —
    the optimistic capacity the task had."""
    total = 0
    day = start
    while day <= deadline:
        busy = list(fixed.get(day.isoformat(), [])) + focus + prayer
        total += sum(e - s for s, e in
                     free_intervals(work_start, work_end, busy))
        day += datetime.timedelta(days=1)
    return total


# ---------------- quick-add parsing ----------------

_WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
             "friday": 4, "saturday": 5, "sunday": 6,
             "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4,
             "sat": 5, "sun": 6,
             "peer": 0, "mangal": 1, "budh": 2, "jumerat": 3,
             "juma": 4, "hafta": 5, "itwar": 6}


def _parse_deadline_word(word, today):
    """today/tomorrow/weekday/ISO/dd-mm -> date, or None."""
    w = (word or "").strip().lower()
    if w in ("today", "aaj"):
        return today
    if w in ("tomorrow", "kal"):
        return today + datetime.timedelta(days=1)
    if w in ("parson", "parsoon"):
        return today + datetime.timedelta(days=2)
    if w in _WEEKDAYS:
        delta = (_WEEKDAYS[w] - today.weekday()) % 7
        return today + datetime.timedelta(days=delta or 7)
    d = parse_date(w)
    if d:
        return d
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})$", w)
    if m:
        try:
            return datetime.date(today.year, int(m.group(2)),
                                 int(m.group(1)))
        except ValueError:
            return None
    return None


def parse_quick(text, today=None):
    """Parse quick-add lines into task dicts.

    One task per line. Accepted bits (any order, any subset):
      Title | 90m | tomorrow | high
      "Revise pharmacology 90m tomorrow"
      "Read chapter"  -> 30m, today, Should
    Returns (tasks, errors).
    """
    today = today or datetime.date.today()
    tasks, errors = [], []
    _units = {"m": 1, "min": 1, "mins": 1, "minute": 1, "minutes": 1,
              "h": 60, "hr": 60, "hrs": 60, "hour": 60, "hours": 60}
    _prio_words = {"must": 1, "high": 1, "urgent": 1, "zaroori": 1,
                   "should": 2, "medium": 2, "normal": 2,
                   "nice": 3, "low": 3, "optional": 3}
    for lineno, raw_line in enumerate((text or "").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        title_words, minutes, deadline, priority = [], 30, today, 2
        for part in [p.strip() for p in line.split("|")]:
            words = part.split()
            i = 0
            while i < len(words):
                w = words[i]
                low = w.lower().strip(",")
                # "90m" / "2h" attached unit
                m = re.fullmatch(r"(\d+)(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)",
                                 low)
                if m:
                    minutes = int(m.group(1)) * _units[m.group(2)]
                    i += 1
                    continue
                # "90 minutes" split unit
                if low.isdigit() and i + 1 < len(words) and \
                        words[i + 1].lower().strip(",") in _units:
                    minutes = int(low) * _units[words[i + 1].lower().strip(",")]
                    i += 2
                    continue
                if low in _prio_words:
                    priority = _prio_words[low]
                    i += 1
                    continue
                d = _parse_deadline_word(low, today)
                if d is not None:
                    deadline = d
                    i += 1
                    continue
                title_words.append(w)
                i += 1
        title = " ".join(title_words).strip()
        if not title:
            errors.append(f"Line {lineno}: title missing.")
            continue
        task, err = validate_task({
            "title": title, "minutes": minutes,
            "deadline": deadline.isoformat(), "priority": priority})
        if err:
            errors.append(f"Line {lineno}: {err}")
        else:
            tasks.append(task)
    return tasks, errors
