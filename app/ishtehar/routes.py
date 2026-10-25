"""Ishtehar routes — free AI ad-creative studio.

Original clean-room build. Not affiliated with AdCreative.ai or any other
ad-creative tool. Stateless: no server storage, no account, no card, no
credits; brand profiles live in the user's own browser.
"""
import csv
import io

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

from . import engine as copymod
from . import gemini
from .pages import ISHTEHAR_HTML

router = APIRouter(prefix="/ishtehar")


class BuildReq(BaseModel):
    product: str = ""
    benefit: str = ""
    audience: str = ""
    offer: str = ""
    cta: str = ""
    lang: str = "en"
    platforms: list = []
    seed: int = 0


class RewriteReq(BaseModel):
    fields: dict = {}
    platform_label: str = "Meta (Facebook + Instagram)"
    lang: str = "en"


@router.get("", response_class=HTMLResponse)
def index():
    return ISHTEHAR_HTML


@router.get("/api/platforms")
def platforms():
    return {
        name: {"label": spec["label"],
               "fields": [{"key": k, "label": l, "max": m, "recommended": r}
                          for k, l, m, r in spec["fields"]]}
        for name, spec in copymod.PLATFORMS.items()
    }


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/build")
def build(req: BuildReq):
    brief = {"product": req.product, "benefit": req.benefit,
             "audience": req.audience, "offer": req.offer, "cta": req.cta,
             "lang": req.lang}
    plats = [p for p in req.platforms if p in copymod.PLATFORMS] or None
    variants = copymod.build_variants(brief, platforms=plats, seed=req.seed)
    return {"variants": variants,
            "summary": copymod.platform_summary(variants)}


@router.post("/api/ai-rewrite")
def ai_rewrite(req: RewriteReq):
    if not req.fields:
        return JSONResponse({"error": "fields empty"}, status_code=400)
    out, err = gemini.ai_rewrite(req.fields, req.platform_label, req.lang)
    if err:
        return JSONResponse({"error": err}, status_code=502)
    return {"fields": out}


@router.post("/api/download-csv")
def download_csv(req: BuildReq):
    brief = {"product": req.product, "benefit": req.benefit,
             "audience": req.audience, "offer": req.offer, "cta": req.cta,
             "lang": req.lang}
    plats = [p for p in req.platforms if p in copymod.PLATFORMS] or None
    variants = copymod.build_variants(brief, platforms=plats, seed=req.seed)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["platform", "angle", "field", "text", "limit", "score",
                "compliance_flags"])
    for v in variants:
        for key, text in v["fields"].items():
            w.writerow([v["platform_label"], v["angle_label"], key, text,
                        v["limits"][key], v["score"]["total"],
                        "; ".join(f["message"] for f in v["flags"])])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=ishtehar-ads.csv"})
