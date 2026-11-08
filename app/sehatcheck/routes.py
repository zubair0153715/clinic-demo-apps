"""SehatCheck routes — free public drug-safety lookup (openFDA, no key).

GET  /sehatcheck               home + search box
GET  /sehatcheck/search?q=...  results page (server-rendered)
GET  /sehatcheck/api/lookup?q=...  same data as JSON (for reuse / embeds)

No login, no signup, no storage. Nothing is invented: on API failure or
no results the page says so plainly.
"""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine
from .pages import error_page, home_page, results_page

router = APIRouter(prefix="/sehatcheck")


@router.get("", response_class=HTMLResponse)
def index():
    return home_page()


@router.get("/search", response_class=HTMLResponse)
def search(q: str = ""):
    q = (q or "").strip()
    if not q:
        return error_page("", "Type a drug name to search.")
    res = engine.lookup(q)
    if not res["ok"]:
        return error_page(q, res.get("error", "No data."))
    return results_page(q, res)


@router.get("/api/lookup")
def api_lookup(q: str = ""):
    q = (q or "").strip()
    if not q:
        return JSONResponse({"ok": False, "error": "Missing ?q= drug name."},
                            status_code=400)
    res = engine.lookup(q)
    if not res["ok"]:
        return JSONResponse({"ok": False, "error": res.get("error", "No data.")},
                            status_code=200)
    return {
        "ok": True,
        "display": res["display"],
        "search_name": res["search_name"],
        "note": res.get("note", ""),
        "total_reports": res["total_reports"],
        "serious_reports": res["serious_reports"],
        "outcomes": res["outcomes"],
        "top_reactions": [{"term": t, "count": c}
                          for t, c in res["top_reactions"]],
        "label": {
            "boxed_warning": res["label"]["boxed_warning"][:2000],
            "warnings": res["label"]["warnings"][:2000],
            "adverse_reactions": res["label"]["adverse_reactions"][:2000],
            "dosage_forms": res["label"]["dosage_forms"],
            "brand_names": res["label"]["brand_names"][:12],
            "generic_name": res["label"]["generic_name"],
            "manufacturer_name": res["label"]["manufacturer_name"],
        },
        "last_updated": res.get("last_updated", ""),
        "source": "openFDA (FDA FAERS + drug labels)",
        "caveat": ("FAERS reports show correlation, not causation. "
                   "NOT medical advice — ask a pharmacist or doctor."),
    }
