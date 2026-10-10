"""Drug adverse-effects lookup — openFDA client with caching.

Data sources:
- FDA Adverse Event Reporting System (FAERS) via openFDA drug/event.json
- FDA drug labels via openFDA drug/label.json
Both are free, no API key required (OPENFDA_API_KEY env var optional for
higher rate limits).

Honest limits (shown in UI): FAERS reports are VOLUNTARY — a report is not
proof the drug caused the event; serious events are over-reported; data is
US-centric (2004 ->). Correlation is not causation.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

_HERE = Path(__file__).parent
with open(_HERE / "pk_brands.json") as f:
    PK_BRANDS = json.load(f)
PK_BRANDS.pop("_note", None)

# INN -> USAN for openFDA label lookup (US labels use USAN names)
INN_TO_USAN = {
    "paracetamol": "acetaminophen",
    "salbutamol": "albuterol",
    "adrenaline": "epinephrine",
}

BASE = "https://api.fda.gov/drug"
_TIMEOUT = 10

# In-memory cache: key -> (expires_at, value), 1-hour TTL
_CACHE = {}
_CACHE_TTL = 3600


def _cache_get(key):
    item = _CACHE.get(key)
    if item and item[0] > time.time():
        return item[1]
    _CACHE.pop(key, None)
    return None


def _cache_set(key, value):
    if len(_CACHE) > 500:  # simple bound
        _CACHE.clear()
    _CACHE[key] = (time.time() + _CACHE_TTL, value)


def _get_json(url, params):
    """GET with timeout; returns parsed JSON or None on any failure."""
    q = dict(params)
    api_key = os.environ.get("OPENFDA_API_KEY")
    if api_key:
        q["api_key"] = api_key
    full = url + "?" + urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(full, timeout=_TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def normalize(query):
    """Map a brand name to its generic; return (display, search_generic, note).

    display: what to show the user, e.g. 'Panadol (paracetamol)'
    search_generic: the primary generic ingredient to query FAERS with
    note: brand-mapping note or '' if query was already generic/unknown
    """
    q = (query or "").strip().lower()
    if not q:
        return "", "", ""
    if q in PK_BRANDS:
        generic = PK_BRANDS[q]
        primary = generic.split("+")[0].strip()
        combo = " (combination)" if "+" in generic else ""
        brand = query.strip().title()
        return (f"{brand} ({generic})",
                primary,
                f"Pakistani brand '{brand}' mapped to generic '{generic}'{combo}; "
                f"showing FAERS data for {primary}.")
    return query.strip(), q, ""


def lookup(generic):
    """Full adverse-effect lookup for a generic name.

    Returns dict: ok, total_reports, serious_reports, top_reactions
    [(term, count)], label {boxed_warning, warnings, adverse_reactions},
    error message on failure.
    """
    cache_key = f"lookup:{generic}"
    hit = _cache_get(cache_key)
    if hit is not None:
        return hit
    out = {"ok": False, "generic": generic}
    med = f'patient.drug.medicinalproduct:"{generic}"'

    # 1. Top adverse reactions by count
    ev = _get_json(f"{BASE}/event.json", {
        "search": med,
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": 15,
    })
    if not ev or "results" not in ev:
        # retry once with title-cased name (FAERS is case-sensitive-ish)
        alt = generic.title()
        ev = _get_json(f"{BASE}/event.json", {
            "search": f'patient.drug.medicinalproduct:"{alt}"',
            "count": "patient.reaction.reactionmeddrapt.exact",
            "limit": 15,
        })
        if ev and "results" in ev:
            generic = alt
    if not ev or "results" not in ev:
        out["error"] = ("No FAERS reports found for '%s'. Try the generic name "
                        "(e.g. paracetamol instead of Panadol)." % generic)
        _cache_set(cache_key, out)
        return out

    # 2. Total report count
    tot = _get_json(f"{BASE}/event.json", {"search": med, "limit": 1})
    total = 0
    if tot:
        try:
            total = tot["meta"]["results"]["total"]
        except (KeyError, TypeError):
            total = 0

    # 3. Serious report count
    ser = _get_json(f"{BASE}/event.json",
                    {"search": f"{med} AND serious:2", "limit": 1})
    serious = 0
    if ser:
        try:
            serious = ser["meta"]["results"]["total"]
        except (KeyError, TypeError):
            serious = 0

    reactions = [(r.get("term", "?"), r.get("count", 0))
                 for r in ev.get("results", [])]

    # 4. Label sections (USAN name for US labels)
    label_name = INN_TO_USAN.get(generic.lower(), generic)
    lab = _get_json(f"{BASE}/label.json", {
        "search": f'openfda.generic_name:"{label_name}"',
        "limit": 3,
    })
    label = {"boxed_warning": "", "warnings": "", "adverse_reactions": ""}
    if lab and "results" in lab:
        best = None
        for r in lab["results"]:
            score = (2 if r.get("boxed_warning") else 0) + \
                    (1 if r.get("adverse_reactions") else 0)
            if best is None or score > best[0]:
                best = (score, r)
        if best:
            r = best[1]
            for k in label:
                v = r.get(k)
                if v:
                    label[k] = "\n".join(v) if isinstance(v, list) else str(v)

    out.update({
        "ok": True,
        "total_reports": total,
        "serious_reports": serious,
        "top_reactions": reactions,
        "label": label,
        "label_name": label_name,
    })
    _cache_set(cache_key, out)
    return out
