"""MediScribe Dose module — deterministic renal/hepatic dose-adjustment engine.

Pure math + curated rule tables. No LLM involved. Every structured rule traces
to an FDA label section (read via openFDA) or a named published reference
recorded in data/dose_rules.json. Drugs without structured rules fall back to
live FDA label dosage text with an explicit banner (see routes).

Research prototype — NOT medical advice.
"""
import json
import math
import os

_RULES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "data", "dose_rules.json")

_rules_cache = None


def validate_drug_list(drugs):
    """Validate a candidate structured-rule list. Raises ValueError on bad schema."""
    if not isinstance(drugs, list):
        raise ValueError("'drugs' must be a list")
    seen = set()
    for d in drugs:
        for k in ("id", "display", "method", "references"):
            if k not in d:
                raise ValueError(f"drug missing key '{k}': {d.get('id')}")
        if d["id"] in seen:
            raise ValueError(f"duplicate id {d['id']}")
        seen.add(d["id"])
        if not d["references"]:
            raise ValueError(f"{d['id']} has no references (never invent rules)")
        if d.get("method") not in ("bands", "bands_indication", "note", "genta_pct",
                                   "tobra_divscr", "vanco_15x", "digoxin_table",
                                   "apixaban_criteria"):
            raise ValueError(f"{d['id']}: unknown method {d.get('method')}")
        for b in d.get("renal_bands") or []:
            if "min_crcl" not in b or "source" not in b or ("dose" not in b and "pct" not in b):
                raise ValueError(f"{d['id']} band missing min_crcl/(dose|pct)/source")
    return True


def load_rules():
    """Load + validate the structured rule file. Raises ValueError on bad schema."""
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache
    with open(_RULES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    validate_drug_list(data.get("drugs"))
    _rules_cache = data
    return data


def clear_rules_cache():
    global _rules_cache
    _rules_cache = None


def rules_path():
    return _RULES_PATH


def dose_drugs():
    return load_rules()["drugs"]


def get_dose_drug(drug_id):
    for d in dose_drugs():
        if d["id"] == drug_id:
            return d
    return None


def resolve_dose_drug(text):
    """Match a typed name to a structured-rule drug id (aliases + engine ids)."""
    t = (text or "").strip().lower()
    if not t:
        return None
    for d in dose_drugs():
        names = [d["id"], d["display"].lower()] + [a.lower() for a in d.get("aliases", [])]
        if t in names:
            return d["id"]
    # fall back to main engine ids for the label-fallback path
    try:
        from . import engine as _eng
        mid = _eng.resolve_drug_id(t)
        if mid:
            return "label:" + mid
    except Exception:
        pass
    return None


# ---------------- renal/hepatic formulas (pure math) ----------------
def cockcroft_gault(age, sex, weight_kg, scr_mgdl):
    """Cockcroft-Gault creatinine clearance, mL/min. Label-standard formula."""
    if scr_mgdl <= 0 or weight_kg <= 0 or age <= 0:
        raise ValueError("age/weight/Scr must be positive")
    crcl = ((140 - age) * weight_kg) / (72 * scr_mgdl)
    if (sex or "").lower().startswith("f"):
        crcl *= 0.85
    return round(crcl, 1)


def egfr_ckdepi_2021(age, sex, scr_mgdl):
    """CKD-EPI 2021 race-free eGFR, mL/min/1.73m^2 (FDA 2024 guidance preference)."""
    if scr_mgdl <= 0 or age <= 0:
        raise ValueError("age/Scr must be positive")
    female = (sex or "").lower().startswith("f")
    k = 0.7 if female else 0.9
    a = -0.241 if female else -0.302
    scr_k = scr_mgdl / k
    egfr = (142 * (min(scr_k, 1) ** a) * (max(scr_k, 1) ** -1.200)
            * (0.9938 ** age) * (1.012 if female else 1.0))
    return round(egfr, 1)


def schwartz_pediatric(height_cm, scr_mgdl):
    """Bedside Schwartz 2009: eGFR = 0.413 * height(cm) / Scr(mg/dL)."""
    if scr_mgdl <= 0 or height_cm <= 0:
        raise ValueError("height/Scr must be positive")
    return round(0.413 * height_cm / scr_mgdl, 1)


def ibw_devine(height_cm, sex):
    """Devine ideal body weight, kg."""
    if height_cm <= 0:
        raise ValueError("height must be positive")
    inch = height_cm / 2.54
    base = 50.0 if not (sex or "").lower().startswith("f") else 45.5
    return round(base + 2.3 * max(0, inch - 60), 1)


def adjbw(actual_kg, ibw_kg):
    """Adjusted body weight = IBW + 0.4 * (actual - IBW)."""
    return round(ibw_kg + 0.4 * (actual_kg - ibw_kg), 1)


def dosing_weight(actual_kg, height_cm, sex, weight_rule):
    """Pick dosing weight per rule: 'actual' | 'lean' (IBW) | 'lean_plus40' | 'adjbw_if_obese'.

    Aminoglycosides: obese -> lean/AdjBW per FDA labels (never actual weight).
    """
    ibw = ibw_devine(height_cm, sex) if height_cm else None
    if weight_rule == "lean" and ibw:
        return ibw, f"IBW (lean) {ibw} kg — aminoglycoside label: dose on lean body mass in obesity"
    if weight_rule == "lean_plus40" and ibw:
        w = round(ibw + 0.4 * max(0, actual_kg - ibw), 1)
        return w, f"IBW + 40% excess = {w} kg (tobramycin label method)"
    if weight_rule == "adjbw_if_obese" and ibw:
        if actual_kg > 1.2 * ibw:
            w = adjbw(actual_kg, ibw)
            return w, f"AdjBW {w} kg (actual {actual_kg} kg > 120% of IBW {ibw} kg)"
        return actual_kg, f"actual weight {actual_kg} kg (≤120% of IBW)"
    return actual_kg, f"actual body weight {actual_kg} kg"


def child_pugh(bilirubin_mgdl, albumin_gdl, inr, ascites, encephalopathy):
    """Child-Pugh score + class. ascites/encephalopathy: 1=none,2=mild,3=severe."""
    pts = 0
    pts += 1 if bilirubin_mgdl < 2 else (2 if bilirubin_mgdl <= 3 else 3)
    pts += 1 if albumin_gdl > 3.5 else (2 if albumin_gdl >= 2.8 else 3)
    pts += 1 if inr < 1.7 else (2 if inr <= 2.3 else 3)
    pts += int(ascites)
    pts += int(encephalopathy)
    cls = "A" if pts <= 6 else ("B" if pts <= 9 else "C")
    return {"score": pts, "class": cls,
            "label": f"{pts} points — Child-Pugh class {cls}"}


# ---------------- special calculators ----------------
# Digoxin label Table 3: rows = corrected CrCl, cols = lean body weight (kg)
_DIGOXIN_ROWS = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
_DIGOXIN_COLS = [40, 50, 60, 70, 80, 90, 100]
_DIGOXIN_TABLE = [
    [62.5, 125, 125, 187.5, 187.5, 187.5, 250],
    [125, 125, 125, 187.5, 187.5, 250, 250],
    [125, 125, 187.5, 187.5, 250, 250, 312.5],
    [125, 187.5, 187.5, 250, 250, 312.5, 312.5],
    [125, 187.5, 187.5, 250, 250, 312.5, 312.5],
    [125, 187.5, 250, 250, 312.5, 312.5, 375],
    [187.5, 187.5, 250, 250, 312.5, 375, 375],
    [187.5, 187.5, 250, 312.5, 312.5, 375, 437.5],
    [187.5, 250, 250, 312.5, 375, 437.5, 437.5],
    [187.5, 250, 312.5, 312.5, 375, 437.5, 500],
]


def _nearest(val, options):
    return min(options, key=lambda o: abs(o - val))


def digoxin_dose(crcl, lean_kg):
    r = _nearest(max(10, min(100, crcl)), _DIGOXIN_ROWS)
    c = _nearest(max(40, min(100, lean_kg)), _DIGOXIN_COLS)
    dose = _DIGOXIN_TABLE[_DIGOXIN_ROWS.index(r)][_DIGOXIN_COLS.index(c)]
    return {
        "dose": f"{dose:g} mcg once daily",
        "reason": (f"FDA digoxin label Table 3: corrected CrCl {crcl} mL/min → row {r}; "
                   f"lean body weight {lean_kg} kg → column {c} kg → {dose:g} mcg/day. "
                   f"Increase only every 2 weeks per response/levels/toxicity."),
    }


def _match_band(bands, value):
    for b in bands:
        lo = b["min_crcl"]
        hi = b["max_crcl"]
        if value >= lo and (hi is None or value < hi):
            return b
    # value below all bands -> return the lowest band
    return min(bands, key=lambda b: b["min_crcl"])


# ---------------- main calculation ----------------
def calculate(p):
    """p: dict with drug_id, age, sex, weight_kg, height_cm, scr_mgdl,
    gfr_method ('cockcroft_gault'|'ckdepi_2021'|'schwartz'), indication (optional),
    child_pugh inputs (optional), on_dialysis, pregnant, pediatric_override.

    Returns dict with value, reasoning[], warnings[], result blocks. Raises ValueError.
    """
    drug = get_dose_drug(p.get("drug_id"))
    if not drug:
        raise ValueError("unknown drug")
    age = float(p.get("age") or 0)
    sex = p.get("sex") or ""
    wt = float(p.get("weight_kg") or 0)
    ht = float(p.get("height_cm") or 0)
    scr = float(p.get("scr_mgdl") or 0)
    if not (age > 0 and wt > 0 and scr > 0):
        raise ValueError("age, weight and serum creatinine are required")
    if scr < 0.2:
        raise ValueError("Scr implausibly low — check units (mg/dL)")

    method = p.get("gfr_method") or "cockcroft_gault"
    # metformin bands are eGFR-based per its FDA label
    if drug.get("gfr_method") == "egfr" and method == "cockcroft_gault":
        method = "ckdepi_2021"
    reasoning = []
    if method == "ckdepi_2021":
        gfr = egfr_ckdepi_2021(age, sex, scr)
        gfr_label = f"eGFR (CKD-EPI 2021) = {gfr} mL/min/1.73m²"
    elif method == "schwartz":
        if not ht:
            raise ValueError("height required for Schwartz")
        gfr = schwartz_pediatric(ht, scr)
        gfr_label = f"eGFR (Schwartz) = {gfr} mL/min/1.73m²"
    else:
        gfr = cockcroft_gault(age, sex, wt, scr)
        gfr_label = f"CrCl (Cockcroft-Gault) = {gfr} mL/min"
    reasoning.append(gfr_label + f"  [age {age:g}y, {sex or 'sex n/s'}, {wt:g} kg, Scr {scr} mg/dL]")

    dose_wt, wt_reason = dosing_weight(wt, ht, sex, drug.get("weight_rule") or "actual")
    if dose_wt != wt or (drug.get("weight_rule") not in (None, "actual")):
        reasoning.append("Dosing weight: " + wt_reason)

    warnings = []
    result_lines = []
    sources = list(drug.get("references") or [])

    m = drug.get("method")
    if m == "genta_pct":
        band = _match_band(drug["renal_bands"], gfr)
        mg = round(dose_wt * 1.0 * band["pct"] / 100, 1)
        result_lines.append(f"Give {band['pct']}% of the usual 1 mg/kg q8h dose = {mg:g} mg IV/IM every 8 hours (after the usual initial dose)")
        reasoning.append(
            f"FDA gentamicin label Table 4: CrCl {gfr} mL/min → {band['pct']}% of usual dose. "
            f"{dose_wt:g} kg × 1 mg/kg × {band['pct']}% = {mg:g} mg q8h.")
        reasoning.append("Alternative label method: interval (h) = Scr × 8 with the usual dose.")
        sources.append(band["source"])
    elif m == "tobra_divscr":
        mg = round(dose_wt * 1.0 / scr, 1)
        result_lines.append(f"After 1 mg/kg loading dose: {mg:g} mg IV/IM every 8 hours (= normal 1 mg/kg dose ÷ Scr {scr})")
        reasoning.append(
            f"FDA tobramycin label renal method: reduced q8h dose = normal dose ÷ serum creatinine = "
            f"({dose_wt:g} × 1 mg/kg) ÷ {scr} = {mg:g} mg. Alternative: normal dose every {round(scr*6)}h (Scr × 6).")
    elif m == "vanco_15x":
        daily = round(15 * gfr)
        load = round(15 * dose_wt)
        if gfr < 10:
            result_lines.append(f"Functionally anephric: loading {load:g} mg, then {round(1.9*dose_wt):g} mg per 24h (1.9 mg/kg/24h)")
            reasoning.append("FDA vancomycin label: anephric dosing — 15 mg/kg load, 1.9 mg/kg/24h maintenance.")
        else:
            result_lines.append(f"≈ {daily} mg per 24 hours (15 × CrCl {gfr}), commonly divided q12h; initial dose at least {load:g} mg (15 mg/kg)")
            reasoning.append(
                f"FDA vancomycin label (Moellering table): daily dose ≈ 15 × CrCl = 15 × {gfr} = {daily} mg/24h. "
                f"Initial dose ≥15 mg/kg = {load:g} mg even in renal impairment.")
        reasoning.append("Infuse ≤10 mg/min, ≤5 mg/mL to reduce infusion reactions.")
    elif m == "digoxin_table":
        lean = ibw_devine(ht, sex) if ht else dose_wt
        dd = digoxin_dose(gfr, lean)
        result_lines.append(dd["dose"])
        reasoning.append(dd["reason"])
        reasoning.append(f"Lean body weight used: {lean} kg (digoxin doses by lean weight per label).")
    elif m == "apixaban_criteria":
        ind = (p.get("indication") or "").lower()
        if "dvt" in ind or "pe" in ind or "thromb" in ind or "prophylaxis" in ind:
            result_lines.append("DVT/PE treatment & prophylaxis: NO renal dose adjustment (including ESRD on dialysis)")
            reasoning.append("FDA apixaban label §8.6: no renal adjustment for DVT/PE indications, incl ESRD/HD.")
        else:
            crit = sum([age >= 80, wt <= 60, scr >= 1.5])
            low = crit >= 2
            result_lines.append(
                "AF stroke prevention: 2.5 mg twice daily (≥2 criteria met)" if low
                else "AF stroke prevention: 5 mg twice daily")
            reasoning.append(
                f"Dose-reduction criteria — age≥80 ({age:g}y), weight≤60 kg ({wt:g} kg), Scr≥1.5 mg/dL ({scr}): "
                f"{crit}/3 met → {'2.5 mg' if low else '5 mg'} BID per FDA label §2.1.")
            reasoning.append("ESRD on hemodialysis: usual dose gives ARISTOTLE-like exposure (PK data) — specialist decision.")
        sources.append(drug["references"][0])
    elif m == "bands_indication":
        ind = p.get("indication") or ""
        band = _match_band(drug["renal_bands"], gfr)
        result_lines.append(band["dose"] + (f"  [regimen: {ind}]" if ind else ""))
        reasoning.append(f"CrCl {gfr} mL/min → {band['dose']}")
        reasoning.append("Full label Table 3: 200 mg 5×/day — CrCl >10 no change, 0-10: 200 mg q12h; "
                         "400 mg q12h — CrCl >10 no change, 0-10: 200 mg q12h; "
                         "800 mg 5×/day — CrCl >25 no change, 10-25: 800 mg q8h, 0-10: 800 mg q12h.")
        sources.append(band["source"])
    elif m == "bands":
        band = _match_band(drug["renal_bands"], gfr)
        result_lines.append(band["dose"])
        reasoning.append(f"CrCl/eGFR {gfr} → {band['dose']}")
        sources.append(band["source"])
        if drug.get("renal_note"):
            reasoning.append(drug["renal_note"])
    elif m == "note":
        result_lines.append(drug.get("normal_dose") or "See label — no fixed renal table")
        if drug.get("renal_note"):
            reasoning.append(drug["renal_note"])
    else:
        raise ValueError(f"unknown method {m}")

    # hepatic
    cp = None
    if p.get("cp_bilirubin") not in (None, ""):
        try:
            cp = child_pugh(float(p["cp_bilirubin"]), float(p.get("cp_albumin") or 3.5),
                            float(p.get("cp_inr") or 1.0), int(p.get("cp_ascites") or 1),
                            int(p.get("cp_encephalopathy") or 1))
            reasoning.append("Hepatic: " + cp["label"])
        except (TypeError, ValueError):
            pass
    if drug.get("hepatic_note"):
        reasoning.append("Hepatic: " + drug["hepatic_note"])
    elif cp and cp["class"] in ("B", "C"):
        warnings.append(f"⚠️ Child-Pugh {cp['class']}: no specific label adjustment in our rules — use caution, verify with pharmacist.")

    # safety flags
    if drug.get("nti"):
        warnings.append("⛔ NARROW THERAPEUTIC INDEX — " + drug.get("tdm", "monitor drug levels."))
    elif drug.get("tdm"):
        warnings.append("ℹ️ " + drug["tdm"])
    if p.get("on_dialysis"):
        if drug.get("dialysis_note"):
            warnings.append("🩸 Dialysis: " + drug["dialysis_note"])
        else:
            warnings.append("🩸 On dialysis: no dialysis rule curated — consult nephrology/pharmacist.")
    if age and age > 75:
        warnings.append("👴 Age >75: start low, go slow — reduced muscle mass overestimates CrCl; specialist review advised.")
    if p.get("pregnant"):
        if drug.get("pregnancy_note"):
            warnings.append("🤰 Pregnancy: " + drug["pregnancy_note"])
        else:
            warnings.append("🤰 Pregnancy: not covered by these rules — specialist decision only.")
    if age and age < 12:
        if drug.get("pediatric_note"):
            warnings.append("🧒 Pediatric: " + drug["pediatric_note"])
        else:
            warnings.append("🧒 Pediatric patient: adult rules do NOT apply — use pediatric references/specialist.")
    if drug.get("gfr_method") == "egfr" and method != "ckdepi_2021":
        warnings.append("ℹ️ This drug's cutoffs are eGFR-based per FDA label — eGFR used.")

    return {
        "ok": True,
        "drug": {"id": drug["id"], "display": drug["display"],
                 "class": drug.get("class"), "nti": bool(drug.get("nti"))},
        "gfr": gfr, "gfr_method": method, "gfr_label": gfr_label,
        "dosing_weight_kg": dose_wt,
        "dose": result_lines,
        "reasoning": reasoning,
        "warnings": warnings,
        "sources": sources,
        "disclaimer": ("Educational reference — NOT medical advice. Verify with Lexicomp/Medscape "
                       "and a doctor/pharmacist before any dosing decision."),
    }
