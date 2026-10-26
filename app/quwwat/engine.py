"""Quwwat engine — original strength-training planner.

Clean-room build. No affiliation with Fitbod or any other fitness app.
All rules are documented here and shown to the user; nothing is a
black-box score.

Rules:
- 1RM estimate: Epley formula, 1RM = weight * (1 + reps / 30).
- 4-week periodized block per goal, with a deload week 4.
- Injury filter: an exercise is removed if it loads any joint the user
  flagged (shoulder / elbow / wrist / knee / lower back -> spine).
- Equipment filter: only exercises the user's kit can actually do.
- Level filter: beginners only get beginner exercises.
- Recovery: a muscle trained on day D is "recovering" on D+1 and
  "ready" again from D+2 (48h rule), computed from the plan itself.
- Loads are prescribed ONLY from a 1RM the user entered. Everything else
  gets sets x reps + an RPE target and the "2 reps in reserve" rule —
  never a made-up number on day one.
"""

# muscle -> display order for the recovery map
MUSCLES = ["chest", "back", "shoulders", "biceps", "triceps", "quads",
            "hamstrings", "glutes", "calves", "core"]

# injury key -> joints it excludes
INJURY_JOINTS = {
    "shoulder": {"shoulder"},
    "elbow": {"elbow"},
    "wrist": {"wrist"},
    "knee": {"knee"},
    "lower_back": {"spine"},
}

EQUIPMENT_PROFILES = {
    "full_gym": {"barbell", "dumbbell", "bodyweight", "machine", "cable",
                 "band", "kettlebell"},
    "dumbbells": {"dumbbell", "bodyweight", "band"},
    "bodyweight": {"bodyweight"},
}

LEVEL_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}

# id, name, muscles (primary first), pattern, equipment, joints, level
EXERCISES = [
    # barbell compounds
    ("barbell_back_squat", "Barbell Back Squat", ["quads", "glutes"], "squat", "barbell", {"knee", "hip", "spine"}, "intermediate"),
    ("barbell_bench_press", "Barbell Bench Press", ["chest", "triceps", "shoulders"], "push", "barbell", {"shoulder", "elbow"}, "intermediate"),
    ("barbell_deadlift", "Barbell Deadlift", ["hamstrings", "glutes", "back"], "hinge", "barbell", {"hip", "spine", "knee"}, "intermediate"),
    ("barbell_overhead_press", "Barbell Overhead Press", ["shoulders", "triceps"], "push", "barbell", {"shoulder", "elbow"}, "intermediate"),
    ("barbell_row", "Barbell Bent-Over Row", ["back", "biceps"], "pull", "barbell", {"shoulder", "elbow", "spine"}, "intermediate"),
    ("barbell_romanian_deadlift", "Barbell Romanian Deadlift", ["hamstrings", "glutes"], "hinge", "barbell", {"hip", "spine", "knee"}, "intermediate"),
    ("barbell_hip_thrust", "Barbell Hip Thrust", ["glutes", "hamstrings"], "hinge", "barbell", {"hip", "spine"}, "intermediate"),
    ("barbell_front_squat", "Barbell Front Squat", ["quads", "glutes"], "squat", "barbell", {"knee", "hip", "spine"}, "advanced"),
    ("barbell_close_grip_bench", "Barbell Close-Grip Bench Press", ["triceps", "chest"], "push", "barbell", {"shoulder", "elbow"}, "intermediate"),
    ("barbell_curl", "Barbell Curl", ["biceps", "forearms"], "pull", "barbell", {"elbow", "wrist"}, "beginner"),
    # dumbbell
    ("dumbbell_bench_press", "Dumbbell Bench Press", ["chest", "triceps", "shoulders"], "push", "dumbbell", {"shoulder", "elbow"}, "beginner"),
    ("dumbbell_shoulder_press", "Dumbbell Shoulder Press", ["shoulders", "triceps"], "push", "dumbbell", {"shoulder", "elbow"}, "beginner"),
    ("dumbbell_row", "Dumbbell One-Arm Row", ["back", "biceps"], "pull", "dumbbell", {"elbow", "shoulder"}, "beginner"),
    ("dumbbell_goblet_squat", "Dumbbell Goblet Squat", ["quads", "glutes"], "squat", "dumbbell", {"knee", "hip"}, "beginner"),
    ("dumbbell_romanian_deadlift", "Dumbbell Romanian Deadlift", ["hamstrings", "glutes"], "hinge", "dumbbell", {"hip", "knee"}, "beginner"),
    ("dumbbell_lunge", "Dumbbell Lunge", ["quads", "glutes"], "squat", "dumbbell", {"knee", "hip"}, "intermediate"),
    ("dumbbell_lateral_raise", "Dumbbell Lateral Raise", ["shoulders"], "push", "dumbbell", {"shoulder"}, "beginner"),
    ("dumbbell_bicep_curl", "Dumbbell Bicep Curl", ["biceps"], "pull", "dumbbell", {"elbow", "wrist"}, "beginner"),
    ("dumbbell_hammer_curl", "Dumbbell Hammer Curl", ["biceps", "forearms"], "pull", "dumbbell", {"elbow"}, "beginner"),
    ("dumbbell_tricep_kickback", "Dumbbell Tricep Kickback", ["triceps"], "push", "dumbbell", {"elbow"}, "beginner"),
    ("dumbbell_fly", "Dumbbell Fly", ["chest"], "push", "dumbbell", {"shoulder", "elbow"}, "beginner"),
    ("dumbbell_reverse_fly", "Dumbbell Reverse Fly", ["back", "shoulders"], "pull", "dumbbell", {"shoulder"}, "beginner"),
    ("dumbbell_step_up", "Dumbbell Step-Up", ["quads", "glutes"], "squat", "dumbbell", {"knee", "hip"}, "beginner"),
    ("dumbbell_calf_raise", "Dumbbell Calf Raise", ["calves"], "squat", "dumbbell", {"ankle"}, "beginner"),
    ("dumbbell_shrug", "Dumbbell Shrug", ["back"], "pull", "dumbbell", {"shoulder"}, "beginner"),
    # bodyweight
    ("push_up", "Push-Up", ["chest", "triceps", "shoulders"], "push", "bodyweight", {"shoulder", "elbow", "wrist"}, "beginner"),
    ("pull_up", "Pull-Up", ["back", "biceps"], "pull", "bodyweight", {"shoulder", "elbow"}, "intermediate"),
    ("bodyweight_squat", "Bodyweight Squat", ["quads", "glutes"], "squat", "bodyweight", {"knee", "hip"}, "beginner"),
    ("bodyweight_lunge", "Bodyweight Lunge", ["quads", "glutes"], "squat", "bodyweight", {"knee", "hip"}, "beginner"),
    ("dip", "Dip", ["chest", "triceps"], "push", "bodyweight", {"shoulder", "elbow", "wrist"}, "intermediate"),
    ("plank", "Plank", ["core"], "core", "bodyweight", {"wrist"}, "beginner"),
    ("dead_bug", "Dead Bug", ["core"], "core", "bodyweight", set(), "beginner"),
    ("glute_bridge", "Glute Bridge", ["glutes", "hamstrings"], "hinge", "bodyweight", {"hip"}, "beginner"),
    ("inverted_row", "Inverted Row", ["back", "biceps"], "pull", "bodyweight", {"shoulder", "elbow"}, "beginner"),
    ("diamond_push_up", "Diamond Push-Up", ["triceps", "chest"], "push", "bodyweight", {"shoulder", "elbow", "wrist"}, "intermediate"),
    ("pike_push_up", "Pike Push-Up", ["shoulders", "triceps"], "push", "bodyweight", {"shoulder", "elbow", "wrist"}, "intermediate"),
    ("side_plank", "Side Plank", ["core"], "core", "bodyweight", {"wrist"}, "beginner"),
    ("bird_dog", "Bird Dog", ["core", "back"], "core", "bodyweight", {"hip", "spine"}, "beginner"),
    ("superman", "Superman", ["back", "glutes"], "core", "bodyweight", {"spine", "hip"}, "beginner"),
    ("wall_sit", "Wall Sit", ["quads"], "squat", "bodyweight", {"knee", "hip"}, "beginner"),
    # machine / cable (full gym only)
    ("leg_press", "Leg Press", ["quads", "glutes"], "squat", "machine", {"knee", "hip"}, "beginner"),
    ("leg_curl", "Leg Curl", ["hamstrings"], "hinge", "machine", {"knee"}, "beginner"),
    ("leg_extension", "Leg Extension", ["quads"], "squat", "machine", {"knee"}, "beginner"),
    ("lat_pulldown", "Lat Pulldown", ["back", "biceps"], "pull", "cable", {"shoulder", "elbow"}, "beginner"),
    ("cable_row", "Cable Row", ["back", "biceps"], "pull", "cable", {"shoulder", "elbow"}, "beginner"),
    ("cable_fly", "Cable Fly", ["chest"], "push", "cable", {"shoulder", "elbow"}, "beginner"),
    ("cable_tricep_pushdown", "Cable Tricep Pushdown", ["triceps"], "push", "cable", {"elbow"}, "beginner"),
    ("cable_bicep_curl", "Cable Bicep Curl", ["biceps"], "pull", "cable", {"elbow"}, "beginner"),
    ("calf_raise_machine", "Machine Calf Raise", ["calves"], "squat", "machine", {"ankle"}, "beginner"),
    ("chest_press_machine", "Machine Chest Press", ["chest", "triceps"], "push", "machine", {"shoulder", "elbow"}, "beginner"),
    # band
    ("band_pull_apart", "Band Pull-Apart", ["back", "shoulders"], "pull", "band", {"shoulder"}, "beginner"),
    ("band_row", "Band Row", ["back", "biceps"], "pull", "band", {"elbow", "shoulder"}, "beginner"),
    ("band_squat", "Band Squat", ["quads", "glutes"], "squat", "band", {"knee", "hip"}, "beginner"),
    ("band_deadlift", "Band Deadlift", ["hamstrings", "glutes"], "hinge", "band", {"hip", "knee"}, "beginner"),
    # kettlebell
    ("kettlebell_swing", "Kettlebell Swing", ["glutes", "hamstrings"], "hinge", "kettlebell", {"hip", "spine"}, "intermediate"),
    ("kettlebell_goblet_squat", "Kettlebell Goblet Squat", ["quads", "glutes"], "squat", "kettlebell", {"knee", "hip"}, "beginner"),
]

EXERCISES = [
    {"id": e[0], "name": e[1], "muscles": e[2], "pattern": e[3],
     "equipment": e[4], "joints": set(e[5]), "level": e[6]}
    for e in EXERCISES
]
BY_ID = {e["id"]: e for e in EXERCISES}

# exercise id -> which entered lift it takes its load from
LIFT_MAP = {
    "barbell_back_squat": "squat",
    "barbell_front_squat": "squat",
    "barbell_bench_press": "bench",
    "barbell_deadlift": "deadlift",
    "barbell_overhead_press": "press",
}

# goal -> 4 weeks of (sets, reps, intensity fraction of 1RM)
BLOCKS = {
    "strength": [(4, 6, 0.72), (5, 5, 0.78), (5, 3, 0.85), (3, 5, 0.60)],
    "muscle": [(3, 12, 0.62), (4, 10, 0.68), (4, 8, 0.74), (2, 10, 0.60)],
    "general": [(3, 10, 0.65), (3, 10, 0.68), (4, 8, 0.72), (2, 8, 0.60)],
}
BLOCK_NOTES = {
    "strength": "Strength block: heavy, low reps. Week 4 is a deload — same lifts, lighter, so you recover before the next block.",
    "muscle": "Muscle block: moderate weight, higher reps. Week 4 is a deload — lighter, so joints and tendons catch up.",
    "general": "General block: balanced sets and reps for overall strength. Week 4 is a deload — lighter week, then repeat or switch goal.",
}

SPLITS = {
    2: ["Full Body A", "Full Body B"],
    3: ["Full Body A", "Full Body B", "Full Body A"],
    4: ["Upper Body", "Lower Body", "Upper Body", "Lower Body"],
    5: ["Push", "Pull", "Legs", "Upper Body", "Lower Body"],
}

SESSION_TARGETS = {
    "Full Body A": ["chest", "back", "quads", "shoulders", "core"],
    "Full Body B": ["hamstrings", "glutes", "back", "chest", "core"],
    "Upper Body": ["chest", "back", "shoulders", "biceps", "triceps"],
    "Lower Body": ["quads", "hamstrings", "glutes", "calves", "core"],
    "Push": ["chest", "shoulders", "triceps"],
    "Pull": ["back", "biceps", "core"],
    "Legs": ["quads", "hamstrings", "glutes", "calves", "core"],
}


def epley_1rm(weight: float, reps: int) -> float:
    """Epley formula. A 1-rep best set IS the 1RM by definition."""
    if weight <= 0 or reps < 1:
        raise ValueError("weight must be > 0 and reps >= 1")
    if reps == 1:
        return float(weight)
    return weight * (1.0 + reps / 30.0)


def round_to_plates(kg: float) -> float:
    """Nearest 2.5 kg — the smallest plate jump in most gyms."""
    return round(kg / 2.5) * 2.5


def filter_pool(equipment: str, injuries, level: str):
    """Apply equipment, injury-joint and level filters, in list order."""
    allowed_eq = EQUIPMENT_PROFILES.get(equipment, EQUIPMENT_PROFILES["full_gym"])
    banned = set()
    for inj in injuries or []:
        banned |= INJURY_JOINTS.get(inj, set())
    max_rank = LEVEL_RANK.get(level, 1)
    pool = []
    for ex in EXERCISES:
        if ex["equipment"] not in allowed_eq:
            continue
        if ex["joints"] & banned:
            continue
        if LEVEL_RANK[ex["level"]] > max_rank:
            continue
        pool.append(ex)
    return pool


def build_session(session_type: str, pool):
    """Deterministic: one exercise per target muscle first (primary-muscle
    match, pool order), then fill to 6. Multi-muscle compounds sort first."""
    targets = SESSION_TARGETS[session_type]
    picked, picked_ids = [], set()

    def take(ex):
        picked.append(ex)
        picked_ids.add(ex["id"])

    for muscle in targets:
        for ex in pool:
            if ex["id"] not in picked_ids and ex["muscles"][0] == muscle:
                take(ex)
                break
    for ex in pool:
        if len(picked) >= 6:
            break
        if ex["id"] not in picked_ids and ex["muscles"][0] in targets:
            take(ex)
    picked.sort(key=lambda e: (-len(e["muscles"]), EXERCISES.index(e)))
    covered = {m for ex in picked for m in ex["muscles"]}
    missing = [m for m in targets if m not in covered]
    return picked, missing


def build_plan(goal="general", level="intermediate", days=3,
               equipment="full_gym", injuries=None, lifts=None):
    """lifts: {squat|bench|deadlift|press: {weight, reps}} (kg)."""
    goal = goal if goal in BLOCKS else "general"
    days = days if days in SPLITS else 3
    pool = filter_pool(equipment, injuries, level)
    one_rms = {}
    for lift, val in (lifts or {}).items():
        try:
            w, r = float(val.get("weight", 0)), int(val.get("reps", 1))
            if w > 0 and r >= 1:
                one_rms[lift] = round(epley_1rm(w, r), 2)
        except (TypeError, ValueError):
            continue
    split = SPLITS[days]
    weeks = []
    for wi, (sets, reps, pct) in enumerate(BLOCKS[goal]):
        week = {"week": wi + 1, "sets": sets, "reps": reps,
                "intensity": pct, "deload": wi == 3, "sessions": []}
        for day_i, session_type in enumerate(split):
            exercises, missing = build_session(session_type, pool)
            items, tonnage, total_reps = [], 0.0, 0
            for ex in exercises:
                weight = None
                lift = LIFT_MAP.get(ex["id"])
                if lift in one_rms:
                    weight = round_to_plates(one_rms[lift] * pct)
                    tonnage += sets * reps * weight
                total_reps += sets * reps
                items.append({
                    "id": ex["id"], "name": ex["name"],
                    "muscles": ex["muscles"], "equipment": ex["equipment"],
                    "sets": sets, "reps": reps,
                    "weight_kg": weight,
                    "load_note": (f"{weight:g} kg ({pct:.0%} of {one_rms[lift]:g} kg 1RM)"
                                  if weight is not None else
                                  "Pick a weight you can lift with 2 reps left in the tank (RPE ~8)"),
                })
            week["sessions"].append({
                "day": day_i + 1, "type": session_type,
                "exercises": items, "missing": missing,
                "tonnage_kg": round(tonnage, 1), "total_reps": total_reps,
                "muscles": sorted({m for ex in exercises for m in ex["muscles"]}),
            })
        weeks.append(week)
    recovery = recovery_map(weeks[0]["sessions"])
    return {
        "goal": goal, "level": level, "days": days, "equipment": equipment,
        "injuries": list(injuries or []), "block_note": BLOCK_NOTES[goal],
        "one_rep_maxes": one_rms, "weeks": weeks, "recovery": recovery,
        "pool_size": len(pool),
    }


def recovery_map(sessions):
    """Per muscle, per plan day: trained / recovering (<48h) / ready (>=48h).
    Day numbers are 1-based positions in the weekly split."""
    trained_days = {}
    for s in sessions:
        for m in s["muscles"]:
            trained_days.setdefault(m, set()).add(s["day"])
    n_days = max((s["day"] for s in sessions), default=0)
    out = {}
    for muscle in MUSCLES:
        days = sorted(trained_days.get(muscle, set()))
        row = []
        for d in range(1, n_days + 1):
            if d in days:
                row.append("trained")
            else:
                prev = [x for x in days if x < d]
                row.append("recovering" if prev and d - prev[-1] < 2 else "ready")
        out[muscle] = row
    return out
