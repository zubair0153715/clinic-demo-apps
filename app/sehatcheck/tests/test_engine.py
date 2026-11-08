"""SehatCheck tests — run with the repo venv python:
~/workspace/.venv-fc/bin/python -m pytest tests/ -q
(or plain: python -m pytest). Fixtures are REAL openFDA responses
saved 2026-11-08 (trimmed only for size); nothing is invented.

Live smoke test (test_live_smoke.py) is separate and only runs with
SEHATCHECK_LIVE=1.
"""
import json
import os
import sys

_HERE = os.path.dirname(__file__)
for _base in (os.path.join(_HERE, ".."),
              os.path.join(_HERE, "..", "..")):
    sys.path.insert(0, os.path.abspath(_base))
try:
    from sehatcheck import engine  # standalone repo layout  # noqa: E402
except ImportError:
    from app.sehatcheck import engine  # clinic-demo layout  # noqa: E402

import pytest  # noqa: E402

FIX = os.path.join(_HERE, "fixtures")


def _load(name):
    with open(os.path.join(FIX, name)) as f:
        return json.load(f)


# ---------------------------------------------------------------- normalize

@pytest.mark.parametrize("query,display,search", [
    ("Panadol", "Panadol (paracetamol)", "acetaminophen"),
    ("panadol", "Panadol (paracetamol)", "acetaminophen"),
    ("Brufen", "Brufen (ibuprofen)", "ibuprofen"),
    ("Risek", "Risek (omeprazole)", "omeprazole"),
    ("paracetamol", "paracetamol (acetaminophen)", "acetaminophen"),
    ("salbutamol", "salbutamol (albuterol)", "albuterol"),
    ("metformin", "metformin", "metformin"),
    ("Amoxicillin", "Amoxicillin", "amoxicillin"),
])
def test_normalize(query, display, search):
    d, s, note = engine.normalize(query)
    assert d == display
    assert s == search


def test_normalize_empty():
    assert engine.normalize("") == ("", "", "")
    assert engine.normalize("   ") == ("", "", "")


def test_normalize_unknown_passes_through():
    d, s, note = engine.normalize("zebra-drug-xyz")
    assert s == "zebra-drug-xyz"
    assert note == ""


# ---------------------------------------------------------------- parsing

@pytest.mark.parametrize("drug,total", [
    ("acetaminophen", 497983),
    ("metformin", 439327),
    ("amoxicillin", 116648),
])
def test_parse_total_real(drug, total):
    assert engine.parse_total(_load(f"{drug}-total.json")) == total


def test_parse_total_missing():
    assert engine.parse_total({}) == 0
    assert engine.parse_total(None) == 0


@pytest.mark.parametrize("drug,top_term,top_count", [
    ("acetaminophen", "DRUG DEPENDENCE", 51264),
    ("metformin", "NAUSEA", 30628),
    ("amoxicillin", "DIARRHOEA", 7039),
])
def test_parse_reactions_real(drug, top_term, top_count):
    rxns = engine.parse_reactions(_load(f"{drug}-reactions.json"))
    assert len(rxns) == 10
    assert rxns[0] == (top_term, top_count)
    assert all(isinstance(c, int) and c > 0 for _, c in rxns)


def test_parse_reactions_empty():
    assert engine.parse_reactions({}) == []
    assert engine.parse_reactions({"results": []}) == []
    assert engine.parse_reactions(None) == []


def test_parse_label_metformin_has_boxed_warning():
    lab = engine.parse_label(_load("metformin-label.json"))
    assert "lactic acidosis" in lab["boxed_warning"].lower()
    assert lab["generic_name"]
    assert lab["brand_names"]


def test_parse_label_acetaminophen_has_warnings():
    # OTC pain-reliever label: warnings present, no adverse_reactions
    # section at all — the parser must not invent one.
    lab = engine.parse_label(_load("acetaminophen-label.json"))
    assert "liver" in lab["warnings"].lower()
    assert lab["adverse_reactions"] == ""
    assert lab["brand_names"]


def test_parse_label_amoxicillin_forms():
    lab = engine.parse_label(_load("amoxicillin-label.json"))
    assert lab["brand_names"]
    assert lab["generic_name"].lower().startswith("amoxicillin")


def test_parse_label_empty():
    lab = engine.parse_label(None)
    assert lab["boxed_warning"] == ""
    assert lab["brand_names"] == []
    lab2 = engine.parse_label({"results": []})
    assert lab2["warnings"] == ""


def test_outcome_share():
    assert engine.outcome_share(103026, 497983) == 20.7
    assert engine.outcome_share(0, 100) == 0.0
    assert engine.outcome_share(5, 0) is None


# ---------------------------------------------------------------- lookup (mocked API)

def _fake_get_factory(drug):
    """Return a _get_json stand-in serving saved fixtures for `drug`."""
    data = {
        "reactions": _load(f"{drug}-reactions.json"),
        "total": _load(f"{drug}-total.json"),
        "death": _load(f"{drug}-death.json"),
        "hosp": _load(f"{drug}-hosp.json"),
        "disab": _load(f"{drug}-disab.json"),
        "serious": _load(f"{drug}-serious.json"),
        "label": _load(f"{drug}-label.json"),
    }

    def fake(url, params):
        search = params.get("search", "")
        if "count" in params:
            return data["reactions"]
        if "label.json" in url:
            return data["label"]
        if "seriousnessdeath" in search:
            return data["death"]
        if "seriousnesshospitalization" in search:
            return data["hosp"]
        if "seriousnessdisabling" in search:
            return data["disab"]
        if "serious:1" in search:
            return data["serious"]
        return data["total"]

    return fake


@pytest.mark.parametrize("drug,total,serious,death,hosp,disab", [
    ("acetaminophen", 497983, 426113, 103026, 159923, 26980),
    ("metformin", 439327, 298232, 36501, 156096, 11995),
    ("amoxicillin", 116648, 97080, 8613, 46675, 3416),
])
def test_lookup_full_pipeline(monkeypatch, drug, total, serious,
                              death, hosp, disab):
    monkeypatch.setattr(engine, "_get_json", _fake_get_factory(drug))
    engine._CACHE.clear()
    res = engine.lookup(drug)
    assert res["ok"] is True
    assert res["total_reports"] == total
    assert res["serious_reports"] == serious
    assert res["outcomes"] == {"death": death, "hospitalization": hosp,
                               "disability": disab}
    assert len(res["top_reactions"]) == 10
    assert res["top_reactions"][0][1] > res["top_reactions"][-1][1]
    assert res["last_updated"] == "2026-10-28"


def test_lookup_brand_mapping(monkeypatch):
    monkeypatch.setattr(engine, "_get_json",
                        _fake_get_factory("acetaminophen"))
    engine._CACHE.clear()
    res = engine.lookup("Panadol")
    assert res["ok"] is True
    assert res["total_reports"] == 497983
    assert "Panadol" in res["display"]
    assert res["note"]


def test_lookup_no_results(monkeypatch):
    def fake(url, params):
        return _load("noresults.json")
    monkeypatch.setattr(engine, "_get_json", fake)
    engine._CACHE.clear()
    res = engine.lookup("zebra-drug-xyz")
    assert res["ok"] is False
    assert "No FAERS reports" in res["error"]


def test_lookup_api_down(monkeypatch):
    monkeypatch.setattr(engine, "_get_json", lambda url, params: None)
    engine._CACHE.clear()
    res = engine.lookup("metformin")
    assert res["ok"] is False
    assert "did not answer" in res["error"]


def test_get_json_http_error_returns_body(monkeypatch):
    """openFDA answers unknown drugs with HTTP 404 + error JSON — the
    client must return the parsed body (a real answer), not None."""
    import io
    import urllib.error
    body = json.dumps({"error": {"code": "NOT_FOUND",
                                 "message": "No matches found!"}}).encode()
    err = urllib.error.HTTPError("https://api.fda.gov/drug/event.json",
                                 404, "Not Found", {}, io.BytesIO(body))

    class _Resp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return b"{}"

    def boom(req, timeout=None):
        raise err

    monkeypatch.setattr(engine.urllib.request, "urlopen", boom)
    out = engine._get_json("https://api.fda.gov/drug/event.json", {"limit": 1})
    assert out["error"]["code"] == "NOT_FOUND"


def test_lookup_empty_query():
    res = engine.lookup("")
    assert res["ok"] is False
