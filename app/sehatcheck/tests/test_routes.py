"""SehatCheck route tests — home page, results page, JSON API.

Uses FastAPI TestClient against the router only (no full app needed).
engine.lookup is monkeypatched so no network is touched.
"""
import os
import sys

_HERE = os.path.dirname(__file__)
for _base in (os.path.join(_HERE, ".."),
              os.path.join(_HERE, "..", "..")):
    sys.path.insert(0, os.path.abspath(_base))
try:
    from sehatcheck import engine  # noqa: E402
    from sehatcheck.routes import router  # noqa: E402
except ImportError:
    from app.sehatcheck import engine  # noqa: E402
    from app.sehatcheck.routes import router  # noqa: E402

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

FAKE_RES = {
    "ok": True, "display": "Metformin", "search_name": "metformin",
    "note": "", "total_reports": 439327, "serious_reports": 298232,
    "outcomes": {"death": 36501, "hospitalization": 156096,
                 "disability": 11995},
    "top_reactions": [("NAUSEA", 30628), ("DIARRHOEA", 28491)],
    "label": {"boxed_warning": "Lactic acidosis warning text.",
              "warnings": "Some warnings.", "adverse_reactions": "Nausea.",
              "dosage_and_administration": "Take with food.",
              "brand_names": ["Glucophage"], "generic_name": "metformin",
              "manufacturer_name": "ACME", "dosage_forms": ["TABLET"],
              "product_type": "HUMAN PRESCRIPTION DRUG", "route": "ORAL"},
    "last_updated": "2026-10-28",
}


@pytest.fixture
def client(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    monkeypatch.setattr(engine, "lookup", lambda q: dict(FAKE_RES))
    return TestClient(app, raise_server_exceptions=False)


def test_home_page(client):
    r = client.get("/sehatcheck")
    assert r.status_code == 200
    assert "SehatCheck" in r.text
    assert "correlation, not causation" in r.text
    assert "NOT medical advice" in r.text
    assert "paracetamol" in r.text  # popular chip
    assert "openFDA" in r.text


def test_search_page_renders_results(client):
    r = client.get("/sehatcheck/search", params={"q": "metformin"})
    assert r.status_code == 200
    assert "439,327" in r.text
    assert "298,232" in r.text
    assert "36,501" in r.text  # death
    assert "156,096" in r.text  # hospitalisation
    assert "11,995" in r.text  # disability
    assert "Nausea" in r.text  # top reaction, title-cased in the table
    assert "30,628" in r.text
    assert "BOXED WARNING" in r.text
    assert "Lactic acidosis" in r.text
    assert "TABLET" in r.text
    assert "Glucophage" in r.text
    assert "correlation, not causation" in r.text
    assert "2026-10-28" in r.text


def test_search_empty_query(client):
    r = client.get("/sehatcheck/search", params={"q": ""})
    assert r.status_code == 200
    assert "Type a drug name" in r.text


def test_search_no_results(client, monkeypatch):
    monkeypatch.setattr(engine, "lookup",
                        lambda q: {"ok": False,
                                   "error": "No FAERS reports found for 'x'."})
    r = client.get("/sehatcheck/search", params={"q": "zzzqqq"})
    assert r.status_code == 200
    assert "No FAERS reports" in r.text


def test_api_lookup_json(client):
    r = client.get("/sehatcheck/api/lookup", params={"q": "metformin"})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["total_reports"] == 439327
    assert j["outcomes"]["death"] == 36501
    assert j["top_reactions"][0] == {"term": "NAUSEA", "count": 30628}
    assert j["label"]["dosage_forms"] == ["TABLET"]
    assert "correlation, not causation" in j["caveat"]
    assert j["source"].startswith("openFDA")


def test_api_lookup_missing_q(client):
    r = client.get("/sehatcheck/api/lookup")
    assert r.status_code == 400
    assert r.json()["ok"] is False


def test_api_lookup_no_results(client, monkeypatch):
    monkeypatch.setattr(engine, "lookup",
                        lambda q: {"ok": False, "error": "No FAERS reports."})
    r = client.get("/sehatcheck/api/lookup", params={"q": "zzzqqq"})
    assert r.status_code == 200
    assert r.json()["ok"] is False
