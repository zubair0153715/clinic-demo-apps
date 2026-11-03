"""Tests for Larkana Property — approval queue, filters, WhatsApp link,
phone validation, XSS escaping.

Works in both layouts: standalone repo (package `larkana`) and
clinic-demo (package `app.larkana`).
Run: ~/workspace/.venv-fc/bin/python -m pytest tests/ -q
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _base in (os.path.join(_HERE, "..", ".."),
              os.path.join(_HERE, "..", "..", "..")):
    sys.path.insert(0, os.path.abspath(_base))

try:
    from app.main import app  # noqa: E402  (clinic-demo layout)
    from app.larkana import db  # noqa: E402
except ImportError:
    from fastapi import FastAPI  # noqa: E402
    from larkana.routes import router  # noqa: E402
    from larkana import db  # noqa: E402
    app = FastAPI()
    app.include_router(router)

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)

GOOD = {
    "title": "5 marla house, Sachal Colony",
    "purpose": "sale",
    "ptype": "house",
    "locality": "Sachal Colony",
    "address": "Street 3, near City Hospital",
    "price": "7500000",
    "size_value": "5",
    "size_unit": "marla",
    "bedrooms": "3",
    "description": "Newly built, gas + water available.",
    "seller_name": "Test Seller",
    "phone": "0300-1234567",
}


def _fresh():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init_db()


def _post_listing(**over):
    data = dict(GOOD)
    data.update(over)
    return client.post("/larkana-property/post", data=data,
                       follow_redirects=False)


def test_empty_launch_state():
    _fresh()
    r = client.get("/larkana-property")
    assert r.status_code == 200
    assert "ابھی کوئی منظور شدہ پراپرٹی نہیں ہے" in r.text
    r = client.get("/larkana-property/api/status")
    assert r.json()["live"] == 0


def test_post_goes_to_pending_not_live():
    _fresh()
    r = _post_listing()
    assert r.status_code == 303
    assert r.headers["location"].endswith("/submitted?lang=ur")
    assert db.counts()["pending"] == 1
    assert db.counts()["live"] == 0
    r = client.get("/larkana-property")
    assert "5 marla house" not in r.text


def test_admin_requires_key():
    _fresh()
    _post_listing()
    r = client.get("/larkana-property/api/admin/list")
    assert r.status_code == 401


def test_approve_then_visible_and_whatsapp_link():
    _fresh()
    os.environ["LARKANA_ADMIN_KEY"] = "test-key-123"
    _post_listing()
    pending = db.list_by_status("pending")
    assert len(pending) == 1
    lid = pending[0]["id"]
    r = client.post(f"/larkana-property/api/admin/{lid}/approve",
                    headers={"X-Admin-Key": "test-key-123"})
    assert r.json()["ok"] is True
    assert db.counts()["live"] == 1
    r = client.get("/larkana-property")
    assert "5 marla house" in r.text
    r = client.get(f"/larkana-property/{lid}")
    assert r.status_code == 200
    # WhatsApp link uses normalized 92 number
    assert "https://wa.me/923001234567" in r.text
    assert "0300-1234567" in r.text


def test_reject_hides_listing():
    _fresh()
    os.environ["LARKANA_ADMIN_KEY"] = "test-key-123"
    _post_listing()
    lid = db.list_by_status("pending")[0]["id"]
    r = client.post(f"/larkana-property/api/admin/{lid}/reject",
                    headers={"X-Admin-Key": "test-key-123"})
    assert r.json()["ok"] is True
    assert db.counts()["live"] == 0
    r = client.get(f"/larkana-property/{lid}")
    assert r.status_code == 404


def test_delete_removes_listing_and_photo():
    # Regression: /delete must not be swallowed by the /{action} route.
    _fresh()
    os.environ["LARKANA_ADMIN_KEY"] = "test-key-123"
    _post_listing()
    lid = db.list_by_status("pending")[0]["id"]
    r = client.post(f"/larkana-property/api/admin/{lid}/delete",
                    headers={"X-Admin-Key": "test-key-123"})
    assert r.json() == {"ok": True}
    assert db.counts()["total"] == 0
    assert db.get_listing(lid) is None
    r = client.post(f"/larkana-property/api/admin/{lid}/delete",
                    headers={"X-Admin-Key": "test-key-123"})
    assert r.json() == {"ok": False}


def test_filters():
    _fresh()
    os.environ["LARKANA_ADMIN_KEY"] = "test-key-123"
    _post_listing()
    _post_listing(title="10 marla plot, VIP Road", ptype="plot",
                  locality="VIP Road", price="4500000", size_value="10",
                  bedrooms="0")
    for lid in [d["id"] for d in db.list_by_status("pending")]:
        client.post(f"/larkana-property/api/admin/{lid}/approve",
                    headers={"X-Admin-Key": "test-key-123"})
    r = client.get("/larkana-property?ptype=plot")
    assert "10 marla plot" in r.text
    assert "5 marla house" not in r.text
    r = client.get("/larkana-property?locality=Sachal+Colony")
    assert "5 marla house" in r.text
    assert "10 marla plot" not in r.text
    r = client.get("/larkana-property?min_price=5000000")
    assert "5 marla house" in r.text
    assert "10 marla plot" not in r.text


def test_bad_phone_rejected():
    _fresh()
    r = _post_listing(phone="12345")
    assert r.status_code == 400
    assert db.counts()["total"] == 0


def test_xss_escaped():
    _fresh()
    os.environ["LARKANA_ADMIN_KEY"] = "test-key-123"
    _post_listing(title="<script>alert(1)</script> house",
                  description="<img src=x onerror=alert(2)>")
    lid = db.list_by_status("pending")[0]["id"]
    client.post(f"/larkana-property/api/admin/{lid}/approve",
                headers={"X-Admin-Key": "test-key-123"})
    r = client.get("/larkana-property")
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text
    r = client.get(f"/larkana-property/{lid}")
    assert "<img src=x onerror=alert(2)>" not in r.text


def test_english_toggle():
    _fresh()
    r = client.get("/larkana-property?lang=en")
    assert r.status_code == 200
    assert "Larkana Property" in r.text
    assert "No approved properties yet" in r.text
