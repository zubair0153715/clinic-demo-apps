"""JobHub login tests — dashboard locked, login/logout flow, worker API untouched.

Run: cd ~/workspace/clinic-demo && python3 -m pytest app/jobhub/tests/test_auth.py -q
"""
import os
import sys

os.environ["JOBHUB_PASSWORD"] = "test-pass-123"
os.environ["JOBHUB_WORKER_KEY"] = "test-worker-key"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.jobhub.routes import router

app = FastAPI()
app.include_router(router)
client = TestClient(app, follow_redirects=False)


def test_dashboard_redirects_to_login_when_anonymous():
    r = client.get("/jobhub")
    assert r.status_code == 303
    assert r.headers["location"] == "/jobhub/login"


def test_profile_and_status_locked_when_anonymous():
    assert client.get("/jobhub/profile").status_code == 303
    r = client.get("/jobhub/api/status")
    assert r.status_code == 401


def test_login_page_renders():
    r = client.get("/jobhub/login")
    assert r.status_code == 200
    assert "Sign in" in r.text


def test_wrong_password_rejected():
    r = client.post("/jobhub/login", data={"password": "nope"})
    assert r.status_code == 200
    assert "Wrong password" in r.text
    assert "jobhub_session" not in r.headers.get("set-cookie", "")


def test_login_logout_flow():
    r = client.post("/jobhub/login", data={"password": "test-pass-123"})
    assert r.status_code == 303
    assert r.headers["location"] == "/jobhub"
    cookie = r.headers["set-cookie"]
    assert "jobhub_session=" in cookie
    assert "HttpOnly" in cookie
    token = cookie.split("jobhub_session=")[1].split(";")[0]
    r = client.get("/jobhub", cookies={"jobhub_session": token})
    assert r.status_code == 200
    assert "Auto-Apply Hub" in r.text
    r = client.get("/jobhub/logout", cookies={"jobhub_session": token})
    assert r.status_code == 303
    r = client.get("/jobhub", cookies={"jobhub_session": token})
    assert r.status_code == 303


def test_worker_api_still_key_gated():
    r = client.get("/jobhub/api/worker/profile")
    assert r.status_code == 401
    r = client.get("/jobhub/api/worker/profile",
                   headers={"X-Worker-Key": "test-worker-key"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
