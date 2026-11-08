"""SehatCheck engine — free public drug-safety lookup via openFDA.

Data sources (both free, no API key required):
- FDA Adverse Event Reporting System (FAERS) via openFDA drug/event.json
- FDA drug labels via openFDA drug/label.json

This module is deliberately NEW and distinct from the unlisted MediScribe
/drugsafety research prototype: SehatCheck is the public, plain-language
version. Differences: a serious-outcome breakdown (death / hospitalisation /
disability, not just one "serious" count), dosage forms + brand names from
the label, plain-language reading of every number, and a JSON API.

Honest limits (shown on every results page):
- FAERS reports are VOLUNTARY. A report is not proof the drug caused the
  event. Serious outcomes are heavily over-reported; mild ones mostly are not.
- Counts are US-centric, 2004 -> today. Correlation is not causation.
- Outcome counts overlap: one report can list death AND hospitalisation, so
  the three outcome counts do not add up to the serious total.
- This is NOT medical advice. Always ask a pharmacist or doctor.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.fda.gov/drug"
_TIMEOUT = 12

# In-memory cache: key -> (expires_at, value), 1-hour TTL
_CACHE = {}
_CACHE_TTL = 3600

# INN (international) -> USAN (US) names, because FDA labels use USAN.
INN_TO_USAN = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "adrenaline": "epinephrine",
    "frusemide": "furosemide",
    "lignocaine": "lidocaine",
    "co-amoxiclav": "amoxicillin",
}

# Common Pakistani / international brand names -> generic.
# Small curated map (not the prototype's full list): only brands a Pakistani
# user is likely to type. Unknown names pass through unchanged.
BRAND_TO_GENERIC = {
    "panadol": "paracetamol",
    "panadol extra": "paracetamol",
    "brufen": "ibuprofen",
    "arinac": "ibuprofen",
    "risek": "omeprazole",
    "augmentin": "amoxicillin",
    "glucophage": "metformin",
    "flagyl": "metronidazole",
    "disprin": "aspirin",
    "ponstan": "mefenamic acid",
    "zyrtec": "cetirizine",
    "cataflam": "diclofenac",
    "voltaren": "diclofenac",
    "lipitor": "atorvastatin",
    "norvasc": "amlodipine",
    "tenormin": "atenolol",
    "lasix": "furosemide",
    "zantac": "ranitidine",
    "strepsils": "amylmetacresol",
}

POPULAR = ["paracetamol", "ibuprofen", "metformin", "amoxicillin",
           "atorvastatin", "omeprazole"]


def _cache_get(key):
    item = _CACHE.get(key)
    if item and item[0] > time.time():
        return item[1]
    _CACHE.pop(key, None)
    return None


def _cache_set(key, value):
    if len(_CACHE) > 500:
        _CACHE.clear()
    _CACHE[key] = (time.time() + _CACHE_TTL, value)


def _get_json(url, params):
    """GET with timeout. Returns parsed JSON, or None on any failure
    (network error, timeout, HTTP error, bad JSON). Never raises."""
    q = dict(params)
    api_key = os.environ.get("OPENFDA_API_KEY")
    if api_key:
        q["api_key"] = api_key
    full = url + "?" + urllib.parse.urlencode(q)
    try:
        req = urllib.request.Request(full, headers={"User-Agent": "SehatCheck/1.0"})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # openFDA answers unknown drugs with HTTP 404 + {"error": {...}}.
        # That is a real answer ("no matches"), not a network failure —
        # return the parsed body so the caller can tell the two apart.
        try:
            return json.loads(e.read().decode("utf-8"))
        except Exception:
            return {"error": {"code": "HTTP_%s" % e.code}}
    except Exception:
        return None


def normalize(query):
    """Map a brand name to its generic and the generic to its USAN form.

    Returns (display, search_name, note):
    - display: what to show, e.g. 'Panadol (paracetamol)'
    - search_name: the name to query openFDA with (USAN)
    - note: brand-mapping note, or '' if the query was already generic
    """
    q = (query or "").strip()
    if not q:
        return "", "", ""
    low = q.lower()
    if low in BRAND_TO_GENERIC:
        generic = BRAND_TO_GENERIC[low]
        usan = INN_TO_USAN.get(generic, generic)
        return (f"{q.title()} ({generic})", usan,
                f"Brand '{q.title()}' mapped to generic '{generic}' — "
                f"showing FAERS data for {usan}.")
    usan = INN_TO_USAN.get(low, low)
    if usan != low:
        return (f"{q} ({usan})", usan,
                f"'{q}' is known as '{usan}' in FDA data.")
    return q, low, ""


# ---------------------------------------------------------------- parsing

def parse_total(payload):
    """Total report count from a limit=1 event query. 0 if unparseable."""
    try:
        return int(payload["meta"]["results"]["total"])
    except (KeyError, TypeError, ValueError):
        return 0


def parse_reactions(payload, limit=10):
    """Top reactions from a count query -> [(term, count), ...].

    Count queries have no meta.results; the list itself is the data.
    """
    if not payload or not isinstance(payload.get("results"), list):
        return []
    out = []
    for r in payload["results"][:limit]:
        term = (r.get("term") or "?").strip()
        try:
            count = int(r.get("count") or 0)
        except (TypeError, ValueError):
            count = 0
        out.append((term, count))
    return out


def parse_label(payload):
    """Pick the most informative label and extract the sections we show.

    Returns dict: boxed_warning, warnings, adverse_reactions,
    dosage_and_administration, brand_names, generic_name,
    manufacturer_name, dosage_forms, product_type, route.
    All strings; empty when the section is absent.
    """
    empty = {"boxed_warning": "", "warnings": "", "adverse_reactions": "",
             "dosage_and_administration": "", "brand_names": [],
             "generic_name": "", "manufacturer_name": "",
             "dosage_forms": [], "product_type": "", "route": ""}
    if not payload or not isinstance(payload.get("results"), list):
        return empty
    best = None
    for r in payload["results"]:
        score = (2 if r.get("boxed_warning") else 0) + \
                (1 if r.get("adverse_reactions") else 0) + \
                (1 if r.get("warnings") else 0)
        if best is None or score > best[0]:
            best = (score, r)
    if best is None:
        return empty
    r = best[1]
    out = dict(empty)
    for k in ("boxed_warning", "warnings", "adverse_reactions",
              "dosage_and_administration"):
        v = r.get(k)
        if v:
            out[k] = "\n".join(v) if isinstance(v, list) else str(v)
    openfda = r.get("openfda") or {}
    for k, dest in (("brand_name", "brand_names"),
                    ("dosage_form", "dosage_forms")):
        v = openfda.get(k)
        if v:
            out[dest] = list(v) if isinstance(v, list) else [str(v)]
    for k in ("generic_name", "manufacturer_name", "product_type", "route"):
        v = openfda.get(k)
        if v:
            out[k] = ", ".join(v) if isinstance(v, list) else str(v)
    return out


def outcome_share(count, total):
    """Share of reports mentioning an outcome, as a percentage (0-100).

    Returns None when the total is 0. This is a share OF REPORTS, not a
    risk of the outcome — the UI must say so.
    """
    if not total:
        return None
    return round(100.0 * count / total, 1)


# ---------------------------------------------------------------- lookup

def lookup(name):
    """Full public safety lookup for one drug name (brand or generic).

    Returns a dict with keys:
      ok (bool), display, search_name, note, total_reports, serious_reports,
      outcomes {death, hospitalization, disability} (counts),
      top_reactions [(term, count)], label (parse_label dict),
      last_updated (openFDA data date, e.g. '2026-10-28'),
      error (str, only when ok is False).
    Never raises; API failure -> ok False with a plain-language error.
    """
    display, search_name, note = normalize(name)
    if not search_name:
        return {"ok": False, "error": "Type a drug name to search."}
    cache_key = f"sehatcheck:{search_name}"
    hit = _cache_get(cache_key)
    if hit is not None:
        return hit

    out = {"ok": False, "display": display, "search_name": search_name,
           "note": note}
    med = f'patient.drug.medicinalproduct:"{search_name}"'

    # 1. Top reactions (also proves the drug has FAERS data at all).
    ev = _get_json(f"{BASE}/event.json", {
        "search": med,
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": 10,
    })
    if not ev or ("results" not in ev and "error" not in ev):
        alt = search_name.title()
        if alt != search_name:
            ev = _get_json(f"{BASE}/event.json", {
                "search": f'patient.drug.medicinalproduct:"{alt}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": 10,
            })
            if ev and "results" in ev:
                search_name = alt
                out["search_name"] = alt
    if ev is None:
        out["error"] = ("openFDA did not answer just now (network or rate "
                        "limit). Please try again in a few minutes — no data "
                        "was invented.")
        _cache_set(cache_key, out)
        return out
    if "results" not in ev:
        out["error"] = (f"No FAERS reports found for '{display}'. Try the "
                        "generic name (e.g. paracetamol instead of Panadol) "
                        "and check the spelling.")
        _cache_set(cache_key, out)
        return out

    # 2. Totals + serious-outcome breakdown (three separate counts;
    #    they overlap — one report can list several outcomes).
    tot = _get_json(f"{BASE}/event.json", {"search": med, "limit": 1})
    total = parse_total(tot) if tot else 0
    last_updated = (tot or {}).get("meta", {}).get("last_updated", "")

    def _outcome_count(field):
        p = _get_json(f"{BASE}/event.json",
                      {"search": f"{med} AND {field}:1", "limit": 1})
        return parse_total(p) if p else 0

    outcomes = {
        "death": _outcome_count("seriousnessdeath"),
        "hospitalization": _outcome_count("seriousnesshospitalization"),
        "disability": _outcome_count("seriousnessdisabling"),
    }
    serious = max(outcomes.values()) if outcomes else 0
    # A tighter serious total when the API answers it; fall back to the max
    # single outcome (never larger than the true serious count is wrong in
    # the safe direction: it can only understate).
    # openFDA serious flag: serious:1 = serious, serious:2 = non-serious.
    # (Verified live 2026-11-08: acetaminophen serious:1 = 426,113,
    # serious:2 = 71,710; the unlisted prototype queried serious:2, which
    # counts NON-serious reports — SehatCheck uses serious:1.)
    ser = _get_json(f"{BASE}/event.json",
                    {"search": f"{med} AND serious:1", "limit": 1})
    if ser:
        serious = parse_total(ser)

    # 3. Label sections.
    lab = _get_json(f"{BASE}/label.json", {
        "search": f'openfda.generic_name:"{search_name}"',
        "limit": 3,
    })
    label = parse_label(lab) if lab else parse_label(None)

    out.update({
        "ok": True,
        "total_reports": total,
        "serious_reports": serious,
        "outcomes": outcomes,
        "top_reactions": parse_reactions(ev, limit=10),
        "label": label,
        "last_updated": last_updated,
    })
    _cache_set(cache_key, out)
    return out
