"""Waqt verification — hand-computed expectations, no invented data.

Run: ~/workspace/.venv-fc/bin/python tests/verify.py
(from the repo root, or from clinic-demo with the app layout)
Covers: greedy placement, fixed events, deadline ordering, chunk
splitting + breaks, prayer windows, focus blocks, overload
("fits nahi"), past deadlines, no-overlap invariant, quick-add
parsing, day stats, and the HTTP routes via TestClient.
"""
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
try:
    from waqt import engine
    from waqt.routes import router
except ImportError:  # clinic-demo layout: app/waqt
    sys.path.insert(0, os.path.join(os.path.dirname(__file__),
                                    "..", "..", ".."))
    from app.waqt import engine  # noqa: E402
    from app.waqt.routes import router  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


BASE = {"work_start": 540, "work_end": 1080, "break_min": 10,
        "max_chunk": 90, "prayer": False, "focus": []}
D0 = "2026-11-04"  # Wednesday
D1 = "2026-11-05"
D2 = "2026-11-06"  # Friday


def task(title, minutes, deadline=D0, priority=2, **kw):
    d = {"title": title, "minutes": minutes, "deadline": deadline,
         "priority": priority}
    d.update(kw)
    return d


def test_single_task():
    print("single task")
    res, err = engine.schedule([task("Revise", 60)], settings=BASE,
                               start_date=D0)
    check("no error", err is None, str(err))
    check("one block", len(res["blocks"]) == 1, str(res["blocks"]))
    b = res["blocks"][0]
    check("starts 09:00", b["start"] == 540, str(b))
    check("ends 10:00", b["end"] == 600, str(b))
    check("date today", b["date"] == D0, str(b))
    check("none unplaced", res["unplaced"] == [])
    check("stats planned 60", res["stats"]["planned_min"] == 60)
    check("day planned 60", res["days"][D0]["planned"] == 60)
    check("day free 480", res["days"][D0]["free"] == 480,
          str(res["days"][D0]))


def test_fixed_event():
    print("fixed event blocks placement")
    events = [{"title": "Lecture", "date": D0, "start": 600, "end": 660}]
    res, err = engine.schedule(
        [task("A", 60), task("B", 60)], events=events, settings=BASE,
        start_date=D0)
    check("no error", err is None, str(err))
    got = [(b["start"], b["end"]) for b in res["blocks"]]
    check("A 09:00-10:00, B 11:00-12:00", got == [(540, 600), (660, 720)],
          str(got))


def test_deadline_ordering():
    print("deadline ordering beats priority order in input")
    res, err = engine.schedule(
        [task("Read novel", 60, deadline=D1, priority=3),
         task("Exam prep", 60, deadline=D0, priority=1)],
        settings=BASE, start_date=D0)
    check("no error", err is None, str(err))
    got = [(b["title"], b["start"]) for b in res["blocks"]]
    check("exam prep first at 09:00",
          got == [("Exam prep", 540), ("Read novel", 600)], str(got))


def test_splitting():
    print("long task splits into chunks with breaks")
    res, err = engine.schedule([task("Thesis", 180)], settings=BASE,
                               start_date=D0)
    check("no error", err is None, str(err))
    got = [(b["start"], b["end"]) for b in res["blocks"]]
    # 90m chunk 09:00-10:30, 10m break, 90m chunk 10:40-12:10
    check("two 90m chunks with 10m break",
          got == [(540, 630), (640, 730)], str(got))
    check("chunk numbers", [b["chunk_of"] for b in res["blocks"]] == [1, 2])


def test_prayer_window():
    print("prayer window is never booked")
    settings = dict(BASE, prayer=True, max_chunk=240)
    res, err = engine.schedule([task("Study", 300)], settings=settings,
                               start_date=D0)
    check("no error", err is None, str(err))
    got = [(b["start"], b["end"]) for b in res["blocks"]]
    # chunk1 09:00-13:00 (240m), break overlaps Zuhr so next free slot
    # starts 13:20; chunk2 13:20-14:20 (60m)
    check("chunks avoid Zuhr 13:00-13:20",
          got == [(540, 780), (800, 860)], str(got))
    for s, e in got:
        check(f"block {s}-{e} outside Zuhr",
              not (s < 800 and e > 780), f"{s}-{e}")


def test_focus_block():
    print("focus block is never booked")
    settings = dict(BASE, focus=[{"start": 540, "end": 660}])
    res, err = engine.schedule([task("Email", 60)], settings=settings,
                               start_date=D0)
    check("no error", err is None, str(err))
    check("starts after focus", res["blocks"][0]["start"] == 660,
          str(res["blocks"]))
    check("focus minutes reported", res["days"][D0]["focus"] == 120)


def test_overload():
    print("overload: task bigger than the day")
    res, err = engine.schedule([task("Mega", 600)], settings=BASE,
                               start_date=D0)
    check("no error", err is None, str(err))
    # Day capacity: 540 min work window; chunks of 90 + 10m breaks:
    # 90*5 + 40 = 490 placed, 110 left.
    check("one unplaced", len(res["unplaced"]) == 1, str(res["unplaced"]))
    check("110 min left", res["unplaced"][0]["minutes_left"] == 110,
          str(res["unplaced"]))
    check("490 planned", res["stats"]["planned_min"] == 490,
          str(res["stats"]))
    check("suggest defer tomorrow",
          res["unplaced"][0]["suggestions"]["defer_to"] == D1)
    check("suggest shorten by 110",
          res["unplaced"][0]["suggestions"]["shorten_by"] == 110)


def test_past_deadline():
    print("past deadline is unplaced, not scheduled")
    res, err = engine.schedule(
        [task("Late", 30, deadline="2026-11-03")], settings=BASE,
        start_date=D0)
    check("no error", err is None, str(err))
    check("no blocks", res["blocks"] == [])
    check("reason mentions deadline",
          "guzar" in res["unplaced"][0]["reason"],
          str(res["unplaced"]))


def test_no_overlap_invariant():
    print("no-overlap invariant on a mixed day")
    settings = dict(BASE, prayer=True,
                    focus=[{"start": 960, "end": 1050}])
    tasks = [task("T1", 120, deadline=D0, priority=1),
             task("T2", 45, deadline=D0, priority=2),
             task("T3", 200, deadline=D1, priority=1),
             task("T4", 30, deadline=D2, priority=3),
             task("T5", 90, deadline=D0, priority=2)]
    events = [{"title": "Class", "date": D0, "start": 600, "end": 720},
              {"title": "Lab", "date": D1, "start": 540, "end": 660}]
    res, err = engine.schedule(tasks, events=events, settings=settings,
                               start_date=D0)
    check("no error", err is None, str(err))
    ok = True
    for day in sorted({b["date"] for b in res["blocks"]}):
        day_blocks = sorted([b for b in res["blocks"] if b["date"] == day],
                            key=lambda b: b["start"])
        for b in day_blocks:
            if not (540 <= b["start"] < b["end"] <= 1080):
                ok = False
            if 780 <= b["start"] < 800 or 780 < b["end"] <= 800:
                ok = False  # Zuhr
            if 960 <= b["start"] < 1050 or 960 < b["end"] <= 1050:
                ok = False  # focus
        for x, y in zip(day_blocks, day_blocks[1:]):
            if y["start"] < x["end"]:
                ok = False
        for ev in events:
            if ev["date"] != day:
                continue
            for b in day_blocks:
                if b["start"] < ev["end"] and ev["start"] < b["end"]:
                    ok = False
    check("all blocks in work hours, outside prayer/focus/events, no overlap", ok)
    placed = sum(b["end"] - b["start"] for b in res["blocks"])
    left = sum(u["minutes_left"] for u in res["unplaced"])
    total = sum(t["minutes"] for t in tasks)
    check("placed + left == total", placed + left == total,
          f"{placed}+{left} != {total}")


def test_quick_parse():
    print("quick-add parsing")
    today = datetime.date(2026, 11, 4)  # Wednesday
    tasks, errors = engine.parse_quick(
        "Revise pharmacology 90m tomorrow high\n"
        "Read chapter\n"
        "Gym | 1h | friday | low\n"
        "Submit assignment 2h\n", today=today)
    check("no errors", errors == [], str(errors))
    check("4 tasks", len(tasks) == 4, str(tasks))
    t0, t1, t2, t3 = tasks
    check("t0 title", t0["title"] == "Revise pharmacology", str(t0))
    check("t0 90m tomorrow must",
          (t0["minutes"], t0["deadline"], t0["priority"]) == (90, D1, 1),
          str(t0))
    check("t1 defaults 30m today should",
          (t1["minutes"], t1["deadline"], t1["priority"]) == (30, D0, 2),
          str(t1))
    check("t2 gym 60m friday nice",
          (t2["minutes"], t2["deadline"], t2["priority"]) == (60, D2, 3),
          str(t2))
    check("t3 2h = 120m", t3["minutes"] == 120, str(t3))
    _, errors2 = engine.parse_quick(" | 30m\n", today=today)
    check("bad line reported", len(errors2) == 1, str(errors2))


def test_validation():
    print("validation errors")
    _, err = engine.schedule([task("Zero", 0)], settings=BASE,
                             start_date=D0)
    check("zero minutes rejected", err is not None, str(err))
    _, err = engine.schedule(
        [task("Bad", 30, deadline="not-a-date")], settings=BASE,
        start_date=D0)
    check("bad deadline rejected", err is not None, str(err))
    _, err = engine.schedule([task("Huge", 2000)], settings=BASE,
                             start_date=D0)
    check("over-16h rejected", err is not None, str(err))


def test_routes():
    print("HTTP routes via TestClient")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    r = c.get("/waqt")
    check("GET /waqt 200", r.status_code == 200, str(r.status_code))
    check("page mentions Waqt", "Waqt" in r.text)
    check("page mentions honest limits", "Honest limits" in r.text)
    r = c.post("/waqt/api/schedule", data={"payload":
        '{"tasks": [{"title": "Revise", "minutes": 60, "deadline": "2026-11-04", "priority": 1}], "settings": {"prayer": false}, "start_date": "2026-11-04"}'})
    check("POST schedule 200", r.status_code == 200, str(r.status_code))
    j = r.json()
    check("schedule ok", j.get("ok") is True, str(j))
    check("schedule block 09:00-10:00",
          j["blocks"] == [{"task_id": "revise", "title": "Revise",
                           "date": "2026-11-04", "start": 540, "end": 600,
                           "priority": 1, "project": "", "chunk_of": 1}],
          str(j["blocks"]))
    r = c.post("/waqt/api/parse", data={"text": "Gym 45m tomorrow"})
    check("POST parse 200", r.status_code == 200)
    check("parse finds 45m", r.json()["tasks"][0]["minutes"] == 45,
          str(r.json()))
    r = c.get("/waqt/api/ai-status")
    check("ai-status 200", r.status_code == 200)
    check("ai-status has bool",
          isinstance(r.json().get("ai_available"), bool))
    r = c.post("/waqt/api/breakdown",
               data={"title": "Write thesis chapter", "minutes": "120"})
    check("breakdown 200 (fallback ok without key)",
          r.status_code == 200, str(r.status_code))
    check("breakdown returns subtasks",
          len(r.json().get("subtasks", [])) >= 2, str(r.json()))
    check("breakdown minutes sum to 120",
          sum(s["minutes"] for s in r.json()["subtasks"]) == 120,
          str(r.json()))


if __name__ == "__main__":
    test_single_task()
    test_fixed_event()
    test_deadline_ordering()
    test_splitting()
    test_prayer_window()
    test_focus_block()
    test_overload()
    test_past_deadline()
    test_no_overlap_invariant()
    test_quick_parse()
    test_validation()
    test_routes()
    print(f"\n{PASS} passed, {FAIL} failed")
    raise SystemExit(1 if FAIL else 0)
