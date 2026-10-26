"""Quwwat verification suite. Run: python3 tests/verify.py (from repo root
or clinic-demo root). No network, no key needed — engine + routes only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(os.path.expanduser("~"), "workspace", "clinic-demo")):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.quwwat import engine
    from app.quwwat import gemini as gmod
    from app.quwwat.routes import router
except ImportError:
    from quwwat import engine
    from quwwat import gemini as gmod
    from quwwat.routes import router

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name} {detail}")


# ---------- Epley 1RM, hand-calculated ----------
check("epley 100x5", abs(engine.epley_1rm(100, 5) - 116.6666667) < 1e-4)
check("epley 100x1", engine.epley_1rm(100, 1) == 100.0)
check("epley 80x8", abs(engine.epley_1rm(80, 8) - 101.3333333) < 1e-4)
try:
    engine.epley_1rm(0, 5)
    check("epley rejects 0", False)
except ValueError:
    check("epley rejects 0", True)

# ---------- plate rounding ----------
check("plates 72->72.5", engine.round_to_plates(72.0) == 72.5)
check("plates 85->85", engine.round_to_plates(85.0) == 85.0)
check("plates 84->85", engine.round_to_plates(84.0) == 85.0)

# ---------- block tables ----------
check("strength block", engine.BLOCKS["strength"] == [(4, 6, 0.72), (5, 5, 0.78), (5, 3, 0.85), (3, 5, 0.60)])
check("muscle block", engine.BLOCKS["muscle"] == [(3, 12, 0.62), (4, 10, 0.68), (4, 8, 0.74), (2, 10, 0.60)])
check("general block", engine.BLOCKS["general"] == [(3, 10, 0.65), (3, 10, 0.68), (4, 8, 0.72), (2, 8, 0.60)])
check("deload is week 4 everywhere",
      all(engine.BLOCKS[g][3][2] == 0.60 for g in engine.BLOCKS))

# ---------- filters ----------
pool_shoulder = engine.filter_pool("full_gym", ["shoulder"], "advanced")
check("shoulder filter removes all shoulder-joint lifts",
      all("shoulder" not in e["joints"] for e in pool_shoulder))
check("shoulder filter removes overhead press",
      "barbell_overhead_press" not in {e["id"] for e in pool_shoulder})
pool_bw = engine.filter_pool("bodyweight", [], "advanced")
check("bodyweight pool is bodyweight only",
      all(e["equipment"] == "bodyweight" for e in pool_bw) and len(pool_bw) > 10)
pool_beg = engine.filter_pool("full_gym", [], "beginner")
check("beginner pool excludes intermediate+",
      all(e["level"] == "beginner" for e in pool_beg))
check("beginner pool excludes back squat",
      "barbell_back_squat" not in {e["id"] for e in pool_beg})

# ---------- session coverage: full gym, intermediate, upper day ----------
pool = engine.filter_pool("full_gym", [], "intermediate")
picked, missing = engine.build_session("Upper Body", pool)
covered = {m for e in picked for m in e["muscles"]}
check("upper session covers all 5 targets",
      all(m in covered for m in ["chest", "back", "shoulders", "biceps", "triceps"]),
      f"missing={missing} picked={[e['id'] for e in picked]}")
check("upper session has 5-6 exercises", 5 <= len(picked) <= 6)
check("compounds sort first", len(picked[0]["muscles"]) >= 2)

# ---------- full plan: 1RM-driven weight, hand-checked ----------
plan = engine.build_plan(goal="strength", level="intermediate", days=2,
                         equipment="full_gym", injuries=[],
                         lifts={"squat": {"weight": 100, "reps": 5}})
check("plan 1RM stored", plan["one_rep_maxes"]["squat"] == 116.67)
sq = None
for s in plan["weeks"][0]["sessions"]:
    for e in s["exercises"]:
        if e["id"] == "barbell_back_squat":
            sq = e
check("squat week1 weight 85kg (116.67*0.72=84.0 -> plates 85)",
      sq is not None and sq["weight_kg"] == 85.0, f"got={sq}")
check("plan has 4 weeks", len(plan["weeks"]) == 4)
check("week4 flagged deload", plan["weeks"][3]["deload"] is True)
check("week3 strength intensity 0.85", plan["weeks"][2]["intensity"] == 0.85)
# unknown lifts get the RPE note, never a made-up weight
benchless = engine.build_plan(goal="general", level="beginner", days=2,
                              equipment="bodyweight", injuries=[])
any_weight = any(e["weight_kg"] is not None
                 for w in benchless["weeks"] for s in w["sessions"]
                 for e in s["exercises"])
check("no lifts entered -> no prescribed weights", not any_weight)
any_note = any("2 reps left" in e["load_note"]
               for w in benchless["weeks"] for s in w["sessions"]
               for e in s["exercises"])
check("RPE note present without lifts", any_note)

# ---------- injury filter flows into the plan ----------
inj_plan = engine.build_plan(goal="general", level="intermediate", days=4,
                             equipment="full_gym", injuries=["shoulder", "knee"])
bad = [e["id"] for w in inj_plan["weeks"] for s in w["sessions"]
       for e in s["exercises"]
       if engine.BY_ID[e["id"]]["joints"] & {"shoulder", "knee"}]
check("injured joints absent from whole plan", not bad, f"bad={bad}")

# ---------- determinism ----------
p1 = engine.build_plan(goal="muscle", level="intermediate", days=3,
                       equipment="dumbbells", injuries=["wrist"],
                       lifts={"bench": {"weight": 60, "reps": 8}})
p2 = engine.build_plan(goal="muscle", level="intermediate", days=3,
                       equipment="dumbbells", injuries=["wrist"],
                       lifts={"bench": {"weight": 60, "reps": 8}})
check("deterministic plan", p1 == p2)

# ---------- recovery map (48h rule), direct ----------
rec = engine.recovery_map([{"day": 1, "muscles": ["chest"]},
                           {"day": 3, "muscles": ["chest"]}])
check("recovery day1 trained", rec["chest"][0] == "trained")
check("recovery day2 recovering", rec["chest"][1] == "recovering")
check("recovery day3 trained", rec["chest"][2] == "trained")
check("untrained muscle ready", all(v == "ready" for v in rec["calves"]))

# ---------- gemini helper: no key => honest unavailability, no crash ----------
check("gemini key_available is bool", isinstance(gmod.key_available(), bool))

# ---------- route smoke via TestClient ----------
from fastapi.testclient import TestClient
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
c = TestClient(app)
r = c.get("/quwwat")
check("GET /quwwat 200", r.status_code == 200, f"got={r.status_code}")
check("page mentions Quwwat + injury filter",
      "Quwwat" in r.text and "Injuries" in r.text)
r = c.post("/quwwat/api/plan", json={"goal": "strength", "level": "intermediate",
                                      "days": 3, "equipment": "full_gym",
                                      "injuries": ["shoulder"],
                                      "lifts": {"squat": {"weight": 100, "reps": 5}}})
check("POST /quwwat/api/plan 200", r.status_code == 200, f"got={r.status_code}")
if r.status_code == 200:
    j = r.json()
    check("plan api 4 weeks", len(j["weeks"]) == 4)
    check("plan api recovery present", "recovery" in j and "chest" in j["recovery"])
r = c.post("/quwwat/api/one-rep-max", json={"weight": 100, "reps": 5})
check("POST one-rep-max", r.status_code == 200
      and abs(r.json()["one_rep_max_kg"] - 116.67) < 0.01)
r = c.post("/quwwat/api/one-rep-max", json={"weight": 0, "reps": 5})
check("one-rep-max rejects 0", r.status_code == 400)
r = c.get("/quwwat/api/ai-status")
check("ai-status 200 + bool", r.status_code == 200
      and isinstance(r.json()["ai_available"], bool))

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
