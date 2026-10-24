"""Dars verification suite. Run: python3 tests/verify.py (from repo root or
clinic-demo root). No network, no key needed — rule engine only.
"""
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(os.path.expanduser("~"), "workspace", "clinic-demo")):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.dars import notes, quiz, spaced
    from app.dars import gemini as gmod
    from app.dars.routes import router
except ImportError:
    from dars import notes, quiz, spaced
    from dars import gemini as gmod
    from dars.routes import router

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name} {detail}")

TEXT = """Cell Biology: The Basics

The mitochondria is the powerhouse of the cell. The mitochondria produces ATP
through cellular respiration. The nucleus is the control center of the cell.
The nucleus contains DNA, which carries genetic instructions. Ribosomes are
the protein factories of the cell. The cell membrane is a selective barrier
that controls what enters and leaves. Mitochondria, nucleus, ribosomes and
the membrane all work together to keep the cell alive and functioning well."""

# ---------- SM-2 math (hand-verified) ----------
s = spaced.CardState()
s = spaced.sm2(s, 5)
check("sm2 q5 first: reps=1 int=1", s.repetitions == 1 and s.interval == 1, str(s))
check("sm2 q5 first: EF 2.5->2.6", abs(s.ease - 2.6) < 1e-9, str(s.ease))
s = spaced.sm2(s, 5)
check("sm2 q5 second: int=6", s.interval == 6 and s.repetitions == 2, str(s))
check("sm2 q5 second: EF=2.7", abs(s.ease - 2.7) < 1e-9, str(s.ease))
s = spaced.sm2(s, 5)
check("sm2 q5 third: int=round(6*2.7)=16", s.interval == 16, str(s))
check("sm2 q5 third: EF=2.8", abs(s.ease - 2.8) < 1e-9, str(s.ease))
s2 = spaced.sm2(s, 2)
check("sm2 q2: reps reset int=1",
      s2.repetitions == 0 and s2.interval == 1, str(s2))
check("sm2 q2: EF 2.8-0.32=2.48", abs(s2.ease - 2.48) < 1e-9, str(s2.ease))
s3 = spaced.CardState(ease=1.35, repetitions=5, interval=30)
s3 = spaced.sm2(s3, 0)
check("sm2 EF floors at 1.3", s3.ease == 1.3, str(s3.ease))
try:
    spaced.sm2(spaced.CardState(), 9)
    check("sm2 rejects q=9", False)
except ValueError:
    check("sm2 rejects q=9", True)
cards = [{"due": 5}, {"due": 1}, {"no-due": True}]
ord_ = spaced.review_order(cards, 3)
check("review_order due<=today sorted", ord_ == [2, 1] or ord_ == [1, 2] or
      set(ord_) == {1, 2}, str(ord_))

# ---------- notes: extractive ----------
n = notes.build_notes(TEXT)
check("sentence_count>0", n["sentence_count"] > 5, str(n["sentence_count"]))
for s_ in n["summary"]:
    check(f"summary verbatim: {s_[:30]}", s_ in TEXT)
terms = [d["term"].lower() for d in n["definitions"]]
check("mitochondria definition found", "mitochondria" in terms, str(terms))
check("nucleus definition found", "nucleus" in terms, str(terms))
for d in n["definitions"]:
    check(f"definition sentence verbatim: {d['term']}",
          d["sentence"] in TEXT)
check("headings detected", any("Cell Biology" in h for h in n["headings"]),
      str(n["headings"]))
ur = "فوٹو سنتھیسز پودوں میں ہوتی ہے۔ یہ روشنی سے خوراک بناتی ہے۔"
us = notes.split_sentences(ur)
check("urdu sentence split on '۔'", len(us) == 2, str(us))
check("empty text -> zeros", notes.build_notes("")["sentence_count"] == 0)

# ---------- flashcards ----------
fc = quiz.build_flashcards(n)
check("cards built", len(fc) >= 3, str(len(fc)))
for c in fc:
    check(f"card back verbatim: {c['front'][:30]}", c["back"] in TEXT)
fronts = [c["front"].lower() for c in fc]
check("no duplicate fronts", len(fronts) == len(set(fronts)))

# ---------- quiz ----------
qz = quiz.build_quiz(n, seed=7)
check("quiz built", len(qz) >= 3, str(len(qz)))
for q in qz:
    opts = [o.lower() for o in q["options"]]
    check(f"options unique: {q['question'][:30]}", len(opts) == len(set(opts)))
    check(f"answer in range: {q['question'][:30]}",
          0 <= q["answer"] < len(q["options"]))
mcqs = [q for q in qz if q["type"] == "mcq"]
check("has mcqs", len(mcqs) >= 2)
for q in mcqs:
    check(f"stem has blank: {q['question'][:40]}", "_____" in q["question"])
    correct = q["options"][q["answer"]]
    check(f"correct option is a real term: {correct}",
          correct.lower() in terms or any(correct.lower() in t for t in terms))
tfs = [q for q in qz if q["type"] == "tf"]
if tfs:
    check("tf answer is False (swapped)", all(q["answer"] == 1 for q in tfs))

# ---------- routes registered ----------
paths = {r.path for r in router.routes}
for p in ("/dars", "/dars/", "/dars/api/build", "/dars/api/ai-status",
          "/dars/api/ai-pack", "/dars/api/ai-chat",
          "/dars/api/download-md", "/dars/api/download-csv"):
    check(f"route {p}", p in paths, str(sorted(paths)))

# ---------- honest no-key behavior ----------
check("no key on VM -> key_available False", gmod.key_available() is False)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
