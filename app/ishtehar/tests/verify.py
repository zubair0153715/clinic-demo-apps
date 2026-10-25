"""Ishtehar verification suite. Run: python3 tests/verify.py (from repo root
or clinic-demo root). No network, no key needed — rule engine only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(os.path.expanduser("~"), "workspace", "clinic-demo")):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from app.ishtehar import engine as copymod
    from app.ishtehar import gemini as gmod
    from app.ishtehar.routes import router
except ImportError:
    from ishtehar import engine as copymod
    from ishtehar import gemini as gmod
    from ishtehar.routes import router

PASS = FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name} {detail}")


BRIEF = {"product": "Herbal Hair Oil", "benefit": "stops hair fall in 4 weeks",
         "audience": "women 25-45 in Lahore",
         "offer": "20% off + free delivery this week",
         "cta": "Order on WhatsApp now", "lang": "en"}
BRIEF_RU = dict(BRIEF, lang="ru")

# ---------- platform limit tables (public platform specs) ----------
check("meta fields", copymod.PLATFORMS["meta"]["fields"][0][2] == 125
      and copymod.PLATFORMS["meta"]["fields"][1][2] == 40
      and copymod.PLATFORMS["meta"]["fields"][2][2] == 30)
check("google RSA limits", copymod.PLATFORMS["google"]["fields"][0][2] == 30
      and copymod.PLATFORMS["google"]["fields"][1][2] == 90)
check("linkedin limits", copymod.PLATFORMS["linkedin"]["fields"][0][2] == 600
      and copymod.PLATFORMS["linkedin"]["fields"][1][2] == 70)
check("whatsapp limit", copymod.PLATFORMS["whatsapp"]["fields"][0][2] == 1000)

# ---------- _fit never exceeds a limit ----------
for limit in (30, 40, 90, 125):
    txt, trunc = copymod._fit("word " * 60, limit)
    check(f"_fit<={limit}", len(txt) <= limit and trunc)
    check(f"_fit ellipsis {limit}", txt.endswith("…"))
txt, trunc = copymod._fit("short", 125)
check("_fit no-op under limit", txt == "short" and not trunc)

# ---------- full generation: every field within limits, both languages ----------
for brief, tag in ((BRIEF, "en"), (BRIEF_RU, "ru")):
    variants = copymod.build_variants(brief)
    check(f"{tag} count 4x6", len(variants) == 24, f"got {len(variants)}")
    bad = [(v["platform"], k, len(t), v["limits"][k])
           for v in variants for k, t in v["fields"].items()
           if len(t) > v["limits"][k]]
    check(f"{tag} all fields within limits", not bad, str(bad[:3]))
    angles = {v["angle"] for v in variants}
    check(f"{tag} all 6 angles", angles == set(copymod.ANGLES), str(angles))

# ---------- scorer hand-calc ----------
SHORT = {"product": "Hair Oil", "benefit": "stops hair fall",
         "audience": "women", "offer": "20% off",
         "cta": "Order now", "lang": "en"}
perfect = copymod.build_variants(SHORT, platforms=["meta"])[0]
check("untruncated variant scores 100", not perfect["truncated"]
      and perfect["score"]["total"] == 100, str(perfect["score"]))
nocta = copymod.score_variant({"primary": "Stops hair fall in 4 weeks."},
                              [], False)
check("missing CTA loses exactly 20 (25+0+20+15+10+0)", nocta["total"] == 70, str(nocta))
check("benefit always counted", nocta["benefit"] == 20)
nodigit = copymod.score_variant(
    {"primary": "Stops hair fall fast. Order now."}, [], False)
check("no digit loses proof 15", nodigit["proof"] == 0)

# ---------- compliance flags ----------
flags = copymod.compliance_flags("guaranteed cure with zero side effects!")
check("guarantee flagged", any("guarantee" in f["message"].lower() for f in flags))
check("cure flagged", any("Cure" in f["message"] for f in flags))
check("clean copy unflagged",
      copymod.compliance_flags("Stops hair fall in 4 weeks. 20% off.") == [])
flagged = copymod.build_variants(
    dict(BRIEF, benefit="guaranteed miracle cure"), platforms=["meta"])
check("flagged variant carries flags + penalty",
      flagged[0]["flags"] and flagged[0]["score"]["total"] < 100,
      str(flagged[0]["score"]))

# ---------- determinism ----------
a = copymod.build_variants(BRIEF, seed=0)
b = copymod.build_variants(BRIEF, seed=0)
check("deterministic same seed", a == b)
c = copymod.build_variants(BRIEF, seed=1)
check("seed rotates angle order",
      [v["angle"] for v in a[:6]] != [v["angle"] for v in c[:6]])

# ---------- summary ----------
s = copymod.platform_summary(copymod.build_variants(BRIEF))
check("summary counts", s["meta"]["count"] == 6 and s["google"]["count"] == 6)

# ---------- routes registered ----------
paths = {r.path for r in router.routes}
for p in ("/ishtehar", "/ishtehar/api/build", "/ishtehar/api/platforms",
          "/ishtehar/api/ai-status", "/ishtehar/api/ai-rewrite",
          "/ishtehar/api/download-csv"):
    check(f"route {p}", p in paths)

# ---------- honest no-key AI behavior ----------
saved = {k: os.environ.pop(k) for k in ("GEMINI_API_KEY", "GEMINI_APIkey")
         if k in os.environ}
try:
    check("no-key reports unavailable", not gmod.key_available())
    out, err = gmod.ai_rewrite({"primary": "x"}, "Meta", "en")
    check("no-key rewrite errors honestly", out is None and err
          and "GEMINI_API_KEY" in err, str(err))
finally:
    os.environ.update(saved)

# ---------- live TestClient smoke (optional, needs fastapi stack) ----------
try:
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    r = client.get("/ishtehar")
    check("GET /ishtehar 200", r.status_code == 200, str(r.status_code))
    r = client.post("/ishtehar/api/build", json=BRIEF)
    check("POST /ishtehar/api/build 200 + 24 variants",
          r.status_code == 200 and len(r.json()["variants"]) == 24,
          str(r.status_code))
    r = client.get("/ishtehar/api/platforms")
    check("GET /ishtehar/api/platforms", r.status_code == 200
          and "meta" in r.json())
    r = client.post("/ishtehar/api/download-csv", json=BRIEF)
    check("POST download-csv attachment", r.status_code == 200
          and "ishtehar-ads.csv" in r.headers.get("content-disposition", ""))
    for sibling in ("/dars", "/bayan", "/jalsa", "/tukra", "/hisab",
                    "/sehatplate"):
        r = client.get(sibling)
        check(f"no regression {sibling}", r.status_code == 200,
              str(r.status_code))
except Exception as e:
    print(f"SKIP TestClient smoke: {type(e).__name__}: {e}")

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
