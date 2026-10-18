"""IQLab engine — scoring, IQ estimation, levels, streaks, badges."""
import time

DOMAIN_NAMES = {"fluid": "Fluid Reasoning", "verbal": "Verbal",
                "memory": "Working Memory", "speed": "Processing Speed",
                "quant": "Quantitative"}

BADGES = [
    ("first_test", "Pehla Qadam", "Pehla assessment mukammal kiya"),
    ("streak_3", "3-Din Streak", "3 din lagatar training"),
    ("streak_7", "Hafta War", "7 din lagatar training"),
    ("streak_30", "Mahina Master", "30 din lagatar training"),
    ("level_5", "Level 5", "Kisi domain me level 5"),
    ("level_8", "Level 8", "Kisi domain me level 8"),
    ("all_domains", "All-Rounder", "5 domains test kiye"),
    ("target_hit", "Target Locked", "Target IQ hit kiya"),
    ("nback_50", "Memory Pro", "N-back me 80%+ accuracy"),
    ("speed_demon", "Speed Demon", "Stroop me 90%+ accuracy"),
]

def estimate_iq(domain_pct):
    """domain_pct: dict domain->0..100. Returns (iq_est, band). Honest estimate."""
    if not domain_pct:
        return None, "—"
    avg = sum(domain_pct.values()) / len(domain_pct)
    iq = int(round(80 + avg * 0.6))  # 0%->80, 100%->140
    iq = max(80, min(145, iq))
    if iq < 90:
        band = "Developing"
    elif iq < 110:
        band = "Average range"
    elif iq < 120:
        band = "Above average"
    elif iq < 130:
        band = "High"
    else:
        band = "Very high"
    return iq, band

def level_for(domain_history):
    """domain_history: list of (level, pct_correct) recent first. Returns current level 1..10."""
    if not domain_history:
        return 1
    lvl = 1
    for (l, pct) in domain_history:
        if pct >= 80 and l >= lvl and lvl < 10:
            lvl = min(10, l + 1)
        elif pct < 40 and lvl > 1:
            lvl = max(1, lvl - 1)
    return lvl

def check_badges(profile, stats):
    """stats: dict with keys. Returns list of newly earned badge ids."""
    earned = set(profile.get("badges", []))
    new = []
    def give(bid, cond):
        if bid not in earned and cond:
            earned.add(bid)
            new.append(bid)
    give("first_test", stats.get("assessments", 0) >= 1)
    give("streak_3", stats.get("streak", 0) >= 3)
    give("streak_7", stats.get("streak", 0) >= 7)
    give("streak_30", stats.get("streak", 0) >= 30)
    give("level_5", stats.get("max_level", 1) >= 5)
    give("level_8", stats.get("max_level", 1) >= 8)
    give("all_domains", stats.get("domains_tested", 0) >= 5)
    give("target_hit", stats.get("target_hit", False))
    give("nback_50", stats.get("nback_best", 0) >= 80)
    give("speed_demon", stats.get("stroop_best", 0) >= 90)
    profile["badges"] = sorted(earned)
    return new

def badge_info(bid):
    for b, name, desc in BADGES:
        if b == bid:
            return {"id": b, "name": name, "desc": desc}
    return {"id": bid, "name": bid, "desc": ""}
