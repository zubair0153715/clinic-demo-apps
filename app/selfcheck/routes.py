"""PharmaReg Self-Check: public DRAP audit-readiness quiz (free lead-gen tool)."""
import logging
import urllib.parse

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from typing import List, Optional

from app.saas import whatsapp

from . import db, quiz
from pathlib import Path
from .pages import QUIZ_HTML

log = logging.getLogger("selfcheck.routes")
router = APIRouter(prefix="/selfcheck")

OWNER_PHONE = "+923116925020"
OWNER_WA = "https://wa.me/923116925020"


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def quiz_page():
    return HTMLResponse(QUIZ_HTML)


# ---------- PWA (installable) ----------
_PWA_DIR = Path(__file__).with_name("manifest.json").parent


@router.get("/manifest.json")
def pwa_manifest():
    return Response(content=(_PWA_DIR / "manifest.json").read_bytes(),
                    media_type="application/manifest+json")


@router.get("/sw.js")
def pwa_sw():
    return Response(content=(_PWA_DIR / "sw.js").read_bytes(),
                    media_type="application/javascript")


@router.get("/icon-192.png")
def pwa_icon192():
    return Response(content=(_PWA_DIR / "icon-192.png").read_bytes(),
                    media_type="image/png")


@router.get("/icon-512.png")
def pwa_icon512():
    return Response(content=(_PWA_DIR / "icon-512.png").read_bytes(),
                    media_type="image/png")


@router.get("/api/questions")
def get_questions():
    return {"questions": quiz.questions_payload()}


class SubmitIn(BaseModel):
    name: str = ""
    company: str = ""
    phone: str = ""
    answers: List[bool] = []


@router.post("/api/submit")
def submit(inp: SubmitIn):
    if len(inp.answers) != 10:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="need_10_answers")
    name = inp.name.strip()[:120]
    company = inp.company.strip()[:120]
    phone = inp.phone.strip()[:40]
    result = quiz.score_answers([bool(a) for a in inp.answers])
    db.q(
        "INSERT INTO quiz_leads (name, company, phone, score, answers_json, gaps_json,"
        " created_at) VALUES (?,?,?,?,?,?,?)",
        (name, company, phone, result["score"], quiz.dump(inp.answers),
         quiz.dump(result["gaps"]), db.now()))
    # notify owner (demo provider logs it; Meta provider sends it for real)
    try:
        body = (f"🧪 New PharmaReg Self-Check lead\n"
                f"Name: {name or '-'} | Company: {company or '-'}\n"
                f"Phone: {phone or '-'}\n"
                f"Score: {result['score']}/100 ({result['band_label']})")
        whatsapp.send_text(OWNER_PHONE, body)
    except Exception:
        log.exception("owner notify failed")
    wa_text = (f"Hi! I scored {result['score']}/100 on the DRAP Audit Readiness Check "
               f"({company or 'my facility'}). I'd like a full compliance audit.")
    result["whatsapp_cta"] = OWNER_WA + "?text=" + urllib.parse.quote(wa_text)
    result["ok"] = True
    return JSONResponse(result)


@router.get("/api/leads")
def recent_leads():
    """Simple lead list (no auth — keep URL unlinked; for owner use)."""
    rows = db.qall("SELECT id, name, company, phone, score, created_at FROM quiz_leads"
                   " ORDER BY id DESC LIMIT 100")
    return {"leads": [dict(r) for r in rows], "count": len(rows)}
