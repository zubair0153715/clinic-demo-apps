"""MediScribe Pro safety engine (server-side).

Ported from the v1 JS engine; runs on the server so every user shares one
curated, updatable drug database. Deterministic — no LLM involved in flags.
"""
import re

from .engine_data import (
    DRUGS as _DRUGS, GROUPS as _GROUPS, INTERACTIONS as _IX,
    CONTRA as _CONTRA, ALLERGY_RULES as _ARULES,
    COND_LABEL, CONDITIONS as _CONDITIONS, COUNSEL as _COUNSEL,
)
CONDITIONS = _CONDITIONS

# ---------------- v2 additions (textbook-established only) ----------------
EXTRA_DRUGS = [
    {"id": "pantoprazole", "n": ["pantoprazole", "pantocid"], "c": "Proton-pump inhibitor"},
    {"id": "mefenamic", "n": ["mefenamic acid", "ponstan"], "c": "NSAID"},
    {"id": "bisoprolol", "n": ["bisoprolol", "concor"], "c": "Beta-blocker"},
    {"id": "montelukast", "n": ["montelukast", "montika"], "c": "Leukotriene antagonist"},
    {"id": "fluticasone", "n": ["fluticasone", "flixotide"], "c": "Inhaled corticosteroid"},
    {"id": "pyrazinamide", "n": ["pyrazinamide"], "c": "Anti-TB"},
    {"id": "ethambutol", "n": ["ethambutol"], "c": "Anti-TB"},
    {"id": "artemether", "n": ["artemether", "coartem"], "c": "Antimalarial"},
    {"id": "chloroquine", "n": ["chloroquine"], "c": "Antimalarial"},
    {"id": "albendazole", "n": ["albendazole", "zentel"], "c": "Anthelmintic"},
    {"id": "acyclovir", "n": ["acyclovir"], "c": "Antiviral"},
    {"id": "gliclazide", "n": ["gliclazide", "diamicron"], "c": "Sulfonylurea"},
    {"id": "domperidone", "n": ["domperidone", "motilium"], "c": "Prokinetic"},
    {"id": "chlorpheniramine", "n": ["chlorpheniramine", "piriton"], "c": "Antihistamine"},
    {"id": "cetirizine", "n": ["cetirizine", "zyrtec", "rigix"], "c": "Antihistamine"},
    {"id": "antacid", "n": ["antacid", "mucaine", "digene"], "c": "Antacid"},
    {"id": "iron", "n": ["iron", "ferrous sulfate", "fefol"], "c": "Iron supplement"},
]

EXTRA_GROUPS = {
    "ppi": ["omeprazole", "pantoprazole"],
}

# group membership additions for existing groups
GROUP_ADD = {
    "nsaid": ["mefenamic"],
    "bb": ["bisoprolol"],
}

# [drugA, drugB, severity, note] — drug may be id or group
EXTRA_INTERACTIONS = [
    ["nsaid", "steroid", "amber", "GI-bleed risk increased — add GI protection, monitor."],
    ["theophylline", "fluconazole", "red", "Theophylline toxicity — reduce dose, monitor levels."],
    ["carbamazepine", "isoniazid", "amber", "Carbamazepine levels rise — monitor for toxicity."],
    ["phenytoin", "isoniazid", "amber", "Phenytoin toxicity — monitor levels."],
    ["rifampin", "phenytoin", "amber", "Phenytoin levels fall — seizure control may fail; monitor."],
    ["rifampin", "carbamazepine", "amber", "Carbamazepine levels fall — monitor levels."],
    ["doxycycline", "antacid", "amber", "Absorption reduced — separate by 2–3 hours."],
    ["quinolone", "antacid", "amber", "Absorption reduced — separate by 2–3 hours."],
    ["levothyroxine", "antacid", "amber", "Absorption reduced — take thyroxine alone on empty stomach."],
    ["iron", "levothyroxine", "amber", "Absorption reduced — separate iron by 4 hours."],
    ["iron", "doxycycline", "amber", "Absorption reduced — separate by 2–3 hours."],
    ["iron", "quinolone", "amber", "Absorption reduced — separate by 2–3 hours."],
    ["ssri", "codeine", "amber", "Codeine activation may be blocked (CYP2D6) — poor pain relief; choose alternative."],
    ["amiodarone", "statin", "amber", "Statin levels rise — muscle-pain risk; monitor, consider dose cap."],
    ["nondhp", "statin", "amber", "Statin levels rise (CYP3A4) — monitor for muscle pain."],
]

# [drug/group, condition, severity, note]
EXTRA_CONTRA = [
    ["pyrazinamide", "liver", "amber", "Hepatotoxic — monitor LFTs."],
    ["carbamazepine", "pregnancy", "red", "Teratogenic — avoid in pregnancy."],
    ["phenytoin", "pregnancy", "red", "Teratogenic — avoid; specialist care needed."],
    ["lithium", "breastfeeding", "amber", "Excreted in breast milk — specialist decision only."],
    ["quinolone", "pregnancy", "amber", "Reserve use — cartilage effects in animal studies."],
    ["metformin", "pregnancy", "info", "Insulin preferred in pregnancy — metformin only under specialist care."],
    ["ssri", "pregnancy", "amber", "Neonatal effects possible — specialist decision; do not stop abruptly."],
    ["tramadol", "pregnancy", "amber", "Reserve use — neonatal withdrawal risk."],
    ["nsaid", "breastfeeding", "info", "Ibuprofen preferred — low transfer into milk."],
    ["paracetamol", "pregnancy", "info", "Analgesic of choice in pregnancy at lowest effective dose."],
]

EXTRA_COUNSEL = {
    "pantoprazole": "Take 30–60 min before breakfast.",
    "iron": "Take on empty stomach; separate from thyroxine, antibiotics and antacids.",
    "montelukast": "Take in the evening.",
    "albendazole": "Take with fatty food for better absorption.",
    "artemether": "Complete the full 3-day course even if feeling better.",
    "domperidone": "Take 15–30 min before meals.",
}

# ---------------- merged tables ----------------
DRUGS = list(_DRUGS) + EXTRA_DRUGS
GROUPS = dict(_GROUPS)
GROUPS.update(EXTRA_GROUPS)
for g, members in GROUP_ADD.items():
    GROUPS[g] = list(GROUPS.get(g, [])) + members

INTERACTIONS = list(_IX) + EXTRA_INTERACTIONS
CONTRA = list(_CONTRA) + EXTRA_CONTRA
COUNSEL = dict(_COUNSEL)
COUNSEL.update(EXTRA_COUNSEL)

_BY_ID = {d["id"]: d for d in DRUGS}
ALIASES = []
for d in DRUGS:
    for n in d["n"]:
        ALIASES.append((n, d["id"]))


def _expand(x):
    return list(GROUPS.get(x, [x]))


_IX = {}
for a, b, sev, note in INTERACTIONS:
    for x in _expand(a):
        for y in _expand(b):
            if x == y:
                continue
            key = "|".join(sorted([x, y]))
            if key not in _IX:
                _IX[key] = {"sev": sev, "note": note, "a": x, "b": y}

_CONTRAX = {}
for d, c, sev, note in CONTRA:
    for x in _expand(d):
        _CONTRAX[x + "|" + c] = {"sev": sev, "note": note}


def drug_name(did):
    d = _BY_ID.get(did)
    return d["n"][0] if d else did


def resolve_drug_id(text):
    """Match v1 JS resolveDrugId: exact alias match, else id match."""
    t = (text or "").strip().lower()
    if not t:
        return None
    for name, did in ALIASES:
        if name == t:
            return did
    return t if t in _BY_ID else None


def derived_conds(patient):
    s = set(patient.get("conditions") or [])
    age = patient.get("age")
    if age is not None:
        try:
            age = int(age)
            if age < 12:
                s.add("child")
            if age > 65:
                s.add("elderly")
        except (TypeError, ValueError):
            pass
    return sorted(s)


def drug_class(did):
    d = _BY_ID.get(did)
    return d["c"] if d else ""


def extract_drugs(text):
    t = " " + re.sub(r"[^a-z0-9+\- ]", " ", text.lower()) + " "
    found = {}
    order = []
    for name, did in ALIASES:
        if re.search(r"\b" + re.escape(name) + r"\b", t) and did not in found:
            found[did] = name
            order.append(did)
    return [{"id": did, "label": drug_name(did), "cls": drug_class(did)} for did in order]


def safety_check(ids, conds, allergies, new_ids=None):
    flags = []
    seen = set()

    def push(sev, title, reason, drugs):
        k = sev + "|" + title
        if k in seen:
            return
        seen.add(k)
        flags.append({"key": k, "sev": sev, "title": title, "reason": reason,
                      "drugs": drugs or []})

    # allergy rules
    for a in allergies or []:
        al = a.lower()
        for key, target, sev, note in _ARULES:
            if key in al:
                for did in _expand(target):
                    if did in ids:
                        push(sev, "⛔ DO NOT GIVE: " + drug_name(did),
                             'Allergy to "%s". %s' % (a, note), [drug_name(did)])
    # contraindications vs conditions
    for did in ids:
        for c in conds or []:
            r = _CONTRAX.get(did + "|" + c)
            if r:
                push(r["sev"],
                     ("⛔ DO NOT GIVE: " if r["sev"] == "red" else "⚠️ CAUTION: ") + drug_name(did),
                     "Condition: %s. %s" % (COND_LABEL.get(c, c), r["note"]),
                     [drug_name(did)])
    # interactions
    ids = list(ids)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            r = _IX.get("|".join(sorted([a, b])))
            if not r:
                continue
            if new_ids is not None:
                both_new = a in new_ids and b in new_ids
                ctx = " (dono transcript me mention huin)" if both_new else " (patient ki current medication ke saath)"
            else:
                ctx = " (current medications ke darmiyan)"
            push(r["sev"],
                 ("⛔ DO NOT GIVE: " if r["sev"] == "red" else "⚠️ CAUTION: ")
                 + drug_name(a) + " + " + drug_name(b),
                 r["note"] + ctx, [drug_name(a), drug_name(b)])
    return flags


def analyze(patient, transcript):
    """patient: dict with age/conditions/allergies/meds (meds = name strings like v1)."""
    mentioned = extract_drugs(transcript or "")
    mids = {m["id"] for m in mentioned}
    cur_ids = set()
    for m in patient.get("meds") or []:
        mid = m.get("id") if isinstance(m, dict) else resolve_drug_id(m)
        if mid:
            cur_ids.add(mid)
    conds = derived_conds(patient)
    flags = safety_check(sorted(mids | cur_ids), conds, patient.get("allergies") or [], mids)
    for m in mentioned:
        if m["id"] in cur_ids:
            flags.append({"key": "info|already|" + m["id"], "sev": "info",
                          "title": "ℹ️ Already on: " + m["label"],
                          "reason": "Patient already takes this — duplicate therapy check karo.",
                          "drugs": [m["label"]]})
        if m["id"] in COUNSEL and COUNSEL[m["id"]]:
            flags.append({"key": "info|counsel|" + m["id"], "sev": "info",
                          "title": "ℹ️ Counseling: " + m["label"],
                          "reason": COUNSEL[m["id"]], "drugs": [m["label"]]})
    return {"mentioned": mentioned, "flags": flags}


def stats():
    return {"drugs": len(DRUGS), "interactions": len(_IX),
            "contra_rules": len(_CONTRAX), "conditions": len(COND_LABEL)}
