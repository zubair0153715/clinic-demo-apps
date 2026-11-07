"""Dak routes — free AI email triage studio (Superhuman gap build).

Original clean-room build. Not affiliated with Superhuman / Grammarly.
Stateless: nothing is stored server-side; snooze, follow-ups and
the demo inbox state live in the user's own browser (localStorage).
No account, no card, no trial, no auto-renewal. Dak does not connect
to any inbox and never sends email — it triages text you paste, and
drafts are copied by you, after the Safety Check.
"""

from datetime import date

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini, inbox
from .pages import DAK_HTML

router = APIRouter(prefix="/dak")


@router.get("", response_class=HTMLResponse)
def index():
    return DAK_HTML


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.get("/api/demo-inbox")
def demo_inbox():
    errors = inbox.validate_inbox()
    mails = []
    for mail in inbox.DEMO_EMAILS:
        entry = dict(mail)
        entry["triage"] = engine.triage_email(
            mail["subject"], mail["body"], ref=date.today())
        mails.append(entry)
    return {"emails": mails, "valid": not errors, "errors": errors}


@router.post("/api/triage")
async def triage(subject: str = Form(""), body: str = Form(""),
                 language: str = Form("en")):
    ok, err = engine.validate_paste(f"{subject}\n{body}")
    if not ok:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    rule = engine.triage_email(subject, body, ref=date.today())
    out = {"ok": True, "rule": rule, "ai": None}
    if gemini.key_available():
        result, err = gemini.triage_ai(subject, body, language)
        if err:
            out["ai_error"] = err
        else:
            out["ai"] = result
    else:
        out["ai_error"] = ("AI band hai (GEMINI_API_KEY set nahi). "
                           "Rule-based triage neeche poora dikhaya gaya hai.")
    return out


@router.post("/api/thread")
async def thread_summary(thread: str = Form(""), language: str = Form("en")):
    result, err = gemini.summarize_thread(thread, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    messages = engine.parse_thread(thread)
    return {"ok": True, "result": result, "ai": True,
            "messages_read": len(messages)}


@router.post("/api/draft")
async def draft(thread: str = Form(""), tone: str = Form("polite"),
                language: str = Form("en")):
    result, err = gemini.draft_reply(thread, tone, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=200)
    return {"ok": True, "result": result, "ai": True}


@router.post("/api/safety-check")
async def safety_check(draft: str = Form(""), thread: str = Form("")):
    if not (draft or "").strip():
        return JSONResponse({"ok": False,
                             "error": "Draft khaali hai — pehle draft likhein."},
                            status_code=200)
    flags = engine.safety_check(draft, thread)
    return {"ok": True, "flags": flags, "count": len(flags)}
