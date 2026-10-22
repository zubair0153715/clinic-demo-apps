"""Hisab — free AI math tutor: photo/type a problem, learn the steps.

Original clean-room build. Not affiliated with Photomath/Google or
Gauth/ByteDance. Answers are computed by SymPy (exact CAS); the server
stores nothing and trains on nothing.
"""
import logging

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from . import gemini
from . import solver
from .pages import HISAB_HTML

log = logging.getLogger("hisab.routes")
router = APIRouter(prefix="/hisab")

MAX_PHOTO = 8 * 1024 * 1024  # 8 MB


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def page():
    return HTMLResponse(HISAB_HTML)


@router.get("/api/ai-status")
def api_ai_status():
    return JSONResponse({"ai_available": gemini.key_available()})


@router.post("/api/read-photo")
async def api_read_photo(photo: UploadFile = File(...)):
    if not gemini.key_available():
        return JSONResponse(
            {"error": "Photo parhne ke liye AI key set nahi hai — "
                      "masla type kar ke hal karo (wo hamesha free hai)."},
            status_code=200)
    data = await photo.read()
    if not data:
        return JSONResponse({"error": "Photo khaali hai."}, status_code=400)
    if len(data) > MAX_PHOTO:
        return JSONResponse({"error": "Photo 8MB se chhoti honi chahiye."},
                            status_code=400)
    if not (photo.content_type or "").startswith("image/"):
        return JSONResponse({"error": "Sirf image file upload karo."},
                            status_code=400)
    d, err = gemini.read_photo(data)
    if err:
        return JSONResponse({"error": err}, status_code=200)
    return JSONResponse(d)


class SolveIn(BaseModel):
    text: str = ""
    mode: str = "auto"
    lang: str = "en"
    use_ai: bool = True


@router.post("/api/solve")
def api_solve(body: SolveIn):
    text = (body.text or "").strip()
    if not text:
        return JSONResponse({"error": "Masla likho ya photo upload karo."},
                            status_code=400)
    mode = body.mode if body.mode in (
        "auto", "solve", "simplify", "factor", "expand",
        "differentiate", "integrate") else "auto"
    lang = body.lang if body.lang in ("en", "ur") else "en"
    try:
        sol = solver.solve_problem(text, mode=mode)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=200)
    except Exception:
        log.exception("solver crashed")
        return JSONResponse(
            {"error": "Hal karne mein masla hua — masla dobara likho."},
            status_code=200)
    out = {"solution": sol, "ai": False, "warnings": []}
    if body.use_ai and gemini.key_available():
        expl, err = gemini.explain(sol, lang)
        if err:
            out["warnings"].append(f"AI wazahat nahi ho saki ({err})")
        else:
            out["explanation"] = expl
            out["ai"] = True
    elif body.use_ai:
        out["warnings"].append(
            "AI wazahat ke liye key set nahi — computed hal poora hai.")
    return JSONResponse(out)


class ChatIn(BaseModel):
    solution: dict = {}
    question: str = ""
    lang: str = "en"
    history: str = ""


@router.post("/api/chat")
def api_chat(body: ChatIn):
    lang = body.lang if body.lang in ("en", "ur") else "en"
    if not body.solution:
        return JSONResponse({"error": "Pehle koi masla hal karo."},
                            status_code=200)
    if not gemini.key_available():
        return JSONResponse(
            {"error": "AI chat ke liye GEMINI_API_KEY set nahi hai."},
            status_code=200)
    answer, err = gemini.chat(body.solution, body.question, lang,
                              body.history or "")
    if err:
        return JSONResponse({"error": err}, status_code=200)
    return JSONResponse({"answer": answer})
