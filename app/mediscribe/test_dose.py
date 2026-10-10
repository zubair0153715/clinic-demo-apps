#!/usr/bin/env python3
"""Dose module validation — checks computed doses against published reference
cases (FDA label tables read via openFDA 2026-10-09). Reports pass/fail.

Run: cd ~/workspace/clinic-demo && python3 -m app.mediscribe.test_dose
"""
import sys

from app.mediscribe import dose

PASS, FAIL = 0, 0
LOGS = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        LOGS.append(f"  PASS {name} {detail}")
    else:
        FAIL += 1
        LOGS.append(f"  FAIL {name} {detail}")


def calc(drug_id, age, sex, wt, scr, ht=0, **kw):
    p = {"drug_id": drug_id, "age": age, "sex": sex, "weight_kg": wt,
         "scr_mgdl": scr, "height_cm": ht}
    p.update(kw)
    return dose.calculate(p)


print("== formulas ==")
# Cockcroft-Gault: 60y M 70kg Scr 1.0 -> 77.8
check("CG male", abs(dose.cockcroft_gault(60, "Male", 70, 1.0) - 77.8) < 0.1)
# female factor 0.85
check("CG female factor",
      abs(dose.cockcroft_gault(60, "Female", 70, 1.0) - 77.8 * 0.85) < 0.1)
# CKD-EPI 2021: 60y M Scr 1.0 -> ~86
e = dose.egfr_ckdepi_2021(60, "Male", 1.0)
check("CKD-EPI 2021", 84 < e < 88, f"got {e}")
# Schwartz: 0.413*110/0.6 = 75.7
check("Schwartz", abs(dose.schwartz_pediatric(110, 0.6) - 75.7) < 0.1)
# IBW Devine: M 170cm -> 65.9 ; F 160cm -> 52.4
check("IBW male", abs(dose.ibw_devine(170, "Male") - 65.9) < 0.2)
check("IBW female", abs(dose.ibw_devine(160, "Female") - 52.4) < 0.2)
# Child-Pugh: bili 2.5, alb 3.0, INR 1.5, mild ascites, no enceph -> 8 = B
cp = dose.child_pugh(2.5, 3.0, 1.5, 2, 1)
check("Child-Pugh", cp["score"] == 8 and cp["class"] == "B", str(cp))

print("== gentamicin (FDA label Table 4) ==")
# Ref: label Table 4 — CrCl 35-40 -> 40% of usual 1 mg/kg q8h.
# 60y M, Scr 2.0, 70kg -> CrCl 38.9 -> 40%; lean wt (170cm M) = 65.9 -> 26.4 mg
o = calc("gentamicin", 60, "Male", 70, 2.0, ht=170)
check("genta band CrCl~39 -> 40%", "40%" in o["dose"][0] and "26.4 mg" in o["dose"][0], o["dose"][0][:80])
# CrCl >= 100 -> 100%: 30y M 80kg Scr 0.8 -> CrCl 127 -> 100%
o = calc("gentamicin", 30, "Male", 80, 0.8, ht=180)
check("genta normal renal -> 100%", "100%" in o["dose"][0], o["dose"][0][:60])
# CrCl 10-15 -> 15%: pick Scr for CrCl~12: 70y M 70kg Scr 5.5 -> (70*70)/(72*5.5)=12.4
o = calc("gentamicin", 70, "Male", 70, 5.5, ht=170)
check("genta CrCl~12 -> 15%", "15%" in o["dose"][0], o["dose"][0][:60])
# NTI warning present
check("genta TDM warning", any("NARROW THERAPEUTIC INDEX" in w for w in o["warnings"]))

print("== vancomycin (FDA label Moellering table) ==")
# Ref: daily mg ~= 15 x CrCl. 65y M 70kg Scr 1.4 -> CrCl 52.1 -> ~782 mg/24h
o = calc("vancomycin", 65, "Male", 70, 1.4)
check("vanco 15xCrCl", "782 mg per 24 hours" in o["dose"][0], o["dose"][0][:70])
check("vanco initial >=15mg/kg", "1050" in o["dose"][0], "(15 mg/kg x 70 kg)")
# Label table spot: CrCl 50 -> 770 mg/24h. CrCl exactly 50: 55y M 72kg Scr 1.44 -> (85*72)/(72*1.44)=59? compute instead:
# use age 70 M 70kg Scr 1.4 -> (70*70)/(72*1.4) = 48.6 -> 729 mg
o = calc("vancomycin", 70, "Male", 70, 1.4)
check("vanco CrCl~49 -> ~729mg", "729 mg per 24 hours" in o["dose"][0], o["dose"][0][:70])
check("vanco TDM warning", any("NARROW THERAPEUTIC INDEX" in w for w in o["warnings"]))

print("== spot checks (other label tables) ==")
# Gabapentin: CrCl 30-59 -> 400-1400 mg/day. 60y M 70kg Scr 1.6 -> CrCl 48.6
o = calc("gabapentin", 60, "Male", 70, 1.6)
check("gabapentin CrCl~49", "400-1400" in o["dose"][0], o["dose"][0][:50])
# Ciprofloxacin: CrCl 30-50 -> q12h. Same patient
o = calc("ciprofloxacin", 60, "Male", 70, 1.6)
check("cipro CrCl~49 -> q12h", "every 12 hours" in o["dose"][0], o["dose"][0][:50])
# Metformin: eGFR auto-selected; 70y M 80kg Scr 1.3 -> eGFR ~59 -> no change
o = calc("metformin", 70, "Male", 80, 1.3)
check("metformin eGFR method", o["gfr_method"] == "ckdepi_2021")
check("metformin eGFR~59 no change", "No dose change" in o["dose"][0])
# Digoxin Table 3: 72y F 65kg Scr 1.2 ht 160 -> CrCl 43.5 -> row 40; lean 52.4 -> col 50 -> 187.5 mcg
o = calc("digoxin", 72, "Female", 65, 1.2, ht=160)
check("digoxin table", o["dose"][0].startswith("187.5 mcg"), o["dose"][0])
# Lithium: CrCl <30 -> avoid. 60y M 70kg Scr 3.0 -> CrCl 25.9
o = calc("lithium", 60, "Male", 70, 3.0)
check("lithium CrCl<30 avoid", "AVOID" in o["dose"][0], o["dose"][0][:50])
# Apixaban criteria: 82y F 58kg Scr 1.6 -> 3/3 -> 2.5mg BID
o = calc("apixaban", 82, "Female", 58, 1.6, indication="AF stroke prevention")
check("apixaban 3 criteria -> 2.5mg", "2.5 mg twice daily" in o["dose"][0], o["dose"][0])
# Apixaban 0 criteria -> 5mg BID
o = calc("apixaban", 60, "Male", 80, 1.0, indication="AF stroke prevention")
check("apixaban 0 criteria -> 5mg", "5 mg twice daily" in o["dose"][0], o["dose"][0])
# Ceftazidime: CrCl 16-30 -> 1g q24h. 65y M 70kg Scr 2.6 -> CrCl 28
o = calc("ceftazidime", 65, "Male", 70, 2.6)
check("ceftazidime CrCl~28 -> 1g q24h", "1 gram every 24 hours" in o["dose"][0], o["dose"][0][:40])
# Atenolol: CrCl <15 -> max 25mg. 70y M 70kg Scr 5.5 -> CrCl 12.4
o = calc("atenolol", 70, "Male", 70, 5.5)
check("atenolol CrCl<15 -> 25mg max", "25 mg" in o["dose"][0], o["dose"][0][:40])
# Elderly flag
o = calc("gabapentin", 80, "Male", 70, 1.0)
check("elderly warning", any("Age >75" in w for w in o["warnings"]))
# Pediatric flag
o = calc("gabapentin", 8, "Male", 25, 0.6, ht=120)
check("pediatric warning", any(w.startswith("🧒 Pediatric") for w in o["warnings"]))
# Dialysis fallback warning when no rule
o = calc("lisinopril", 60, "Male", 70, 1.2, on_dialysis=True)
check("dialysis note/warning", any("dialysis" in w.lower() for w in o["warnings"]))
# Child-Pugh hepatic note surfaced
o = calc("metronidazole", 50, "Male", 70, 1.0, cp_bilirubin=4.0, cp_albumin=2.5,
         cp_inr=2.0, cp_ascites=3, cp_encephalopathy=2)
check("child-pugh computed", any("Child-Pugh class C" in r for r in o["reasoning"]))
check("metronidazole Child-Pugh C note", any("50%" in r for r in o["reasoning"]))

print()
for l in LOGS:
    print(l)
print(f"\nRESULT: {PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
