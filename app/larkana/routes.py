"""Larkana Property routes — Larkana-city-only buy/sell board.

Public: browse/search (free, no login), listing detail, post-a-property
form (goes to the admin approval queue — nothing goes live unapproved).
Admin: key-gated (X-Admin-Key == LARKANA_ADMIN_KEY env var).
No seeded listings — launch state is honestly empty.
"""

import os
import re
import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from . import db
from . import pages

router = APIRouter(prefix="/larkana-property")
BASE = "/larkana-property"


def _lang(request: Request):
    lang = (request.query_params.get("lang") or "ur").lower()
    return lang if lang in ("ur", "en") else "ur"


def _admin_ok(request: Request) -> bool:
    key = os.environ.get("LARKANA_ADMIN_KEY", "")
    if not key:
        return False
    return request.headers.get("X-Admin-Key") == key


def _to_int(raw, default=None):
    try:
        return int(str(raw).replace(",", "").strip())
    except Exception:
        return default


def _to_float(raw, default=None):
    try:
        return float(str(raw).replace(",", "").strip())
    except Exception:
        return default


@router.get("", response_class=HTMLResponse)
def index(request: Request, q: str = "", ptype: str = "", purpose: str = "",
          locality: str = "", min_price: str = "", max_price: str = ""):
    lang = _lang(request)
    filters = {"q": q.strip(), "ptype": ptype, "purpose": purpose,
               "locality": locality,
               "min_price": min_price, "max_price": max_price}
    if ptype and ptype not in db.PTYPES:
        filters["ptype"] = ""
    if purpose and purpose not in db.PURPOSES:
        filters["purpose"] = ""
    if locality and locality not in db.LOCALITIES:
        filters["locality"] = ""
    filters["min_price"] = _to_int(min_price)
    filters["max_price"] = _to_int(max_price)
    listings = db.search_listings(filters, status="approved")
    return pages.render_browse(listings, filters, lang, BASE)


@router.get("/post", response_class=HTMLResponse)
def post_form(request: Request):
    return pages.render_post_form(_lang(request), base_path=BASE)


@router.post("/post")
async def post_submit(
    request: Request,
    title: str = Form(""), purpose: str = Form("sale"),
    ptype: str = Form("house"), locality: str = Form(""),
    locality_other: str = Form(""), address: str = Form(""),
    price: str = Form(""), size_value: str = Form(""),
    size_unit: str = Form("sqyd"), bedrooms: str = Form("0"),
    description: str = Form(""), seller_name: str = Form(""),
    phone: str = Form(""),
    photos: list[UploadFile] = File(default=[]),
):
    lang = _lang(request)
    err = ""

    def fail(msg):
        return HTMLResponse(pages.render_post_form(lang, error=msg,
                                                   base_path=BASE),
                            status_code=400)

    title = title.strip()
    if not title or len(title) > 120:
        return fail("عنوان ضروری ہے (زیادہ سے زیادہ 120 حروف)۔"
                    if lang == "ur" else "A title is required (max 120 chars).")
    if purpose not in db.PURPOSES:
        purpose = "sale"
    if ptype not in db.PTYPES:
        ptype = "house"
    if locality == "__other__":
        locality = locality_other.strip()
    locality = locality.strip()
    if not locality or len(locality) > 60:
        return fail("علاقہ ضروری ہے۔" if lang == "ur"
                    else "A locality is required.")
    price_i = _to_int(price)
    if price_i is None or price_i < 10_000 or price_i > 10_000_000_000:
        return fail("قیمت درست لکھیں (کم سے کم 10,000 روپے)۔"
                    if lang == "ur"
                    else "Enter a valid price (at least PKR 10,000).")
    size_f = _to_float(size_value, 0.0)
    if size_f is None or size_f <= 0 or size_f > 1_000_000:
        return fail("رقبہ درست لکھیں۔" if lang == "ur"
                    else "Enter a valid size.")
    if size_unit not in db.SIZE_UNITS:
        size_unit = "sqyd"
    beds = _to_int(bedrooms, 0) or 0
    beds = max(0, min(30, beds))
    if not seller_name.strip():
        return fail("آپ کا نام ضروری ہے۔" if lang == "ur"
                    else "Your name is required.")
    if not db.valid_phone(phone):
        return fail("فون نمبر درست لکھیں (مثلاً 0300-1234567)۔"
                    if lang == "ur"
                    else "Enter a valid phone number (e.g. 0300-1234567).")
    description = description.strip()[:1000]

    # Photos: max 3, images only, 2MB each.
    saved = []
    uploads = [p for p in (photos or []) if p and p.filename]
    if len(uploads) > db.MAX_PHOTOS:
        return fail("زیادہ سے زیادہ 3 تصاویر۔" if lang == "ur"
                    else "Maximum 3 photos.")
    for up in uploads:
        ext = os.path.splitext(up.filename or "")[1].lower()
        if ext not in db.ALLOWED_PHOTO_EXTS:
            return fail("صرف JPG / PNG / WebP تصاویر۔" if lang == "ur"
                        else "Only JPG / PNG / WebP photos.")
        data = await up.read()
        if len(data) > db.MAX_PHOTO_BYTES:
            return fail("ہر تصویر 2MB سے کم ہو۔" if lang == "ur"
                        else "Each photo must be under 2MB.")
        name = f"{uuid.uuid4().hex[:12]}{ext}"
        with open(os.path.join(db.UPLOAD_DIR, name), "wb") as fh:
            fh.write(data)
        saved.append(name)

    db.create_listing({
        "purpose": purpose, "ptype": ptype, "title": title,
        "locality": locality, "address": address.strip()[:160],
        "price": price_i, "size_value": size_f, "size_unit": size_unit,
        "bedrooms": beds, "description": description,
        "seller_name": seller_name.strip()[:60], "phone": phone.strip(),
    }, saved)
    return RedirectResponse(f"{BASE}/submitted?lang={lang}", status_code=303)


@router.get("/submitted", response_class=HTMLResponse)
def submitted(request: Request):
    return pages.render_submitted(_lang(request), BASE)


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return pages.render_admin(_lang(request), BASE)


@router.get("/photos/{name}")
def serve_photo(name: str):
    if not re.fullmatch(r"[0-9a-f]{12}\.(jpg|jpeg|png|webp)", name):
        return JSONResponse({"ok": False, "error": "not found"},
                            status_code=404)
    path = os.path.join(db.UPLOAD_DIR, name)
    if not os.path.isfile(path):
        return JSONResponse({"ok": False, "error": "not found"},
                            status_code=404)
    return FileResponse(path)


@router.get("/api/status")
def api_status():
    return {"ok": True, "city": "Larkana", **db.counts()}


@router.get("/api/admin/list")
def admin_list(request: Request, status: str = "pending"):
    if not _admin_ok(request):
        return JSONResponse({"ok": False, "error": "unauthorized"},
                            status_code=401)
    if status not in ("pending", "approved", "rejected"):
        status = "pending"
    return {"ok": True, "listings": db.list_by_status(status)}


@router.post("/api/admin/{lid}/{action}")
def admin_action(request: Request, lid: str, action: str):
    if not _admin_ok(request):
        return JSONResponse({"ok": False, "error": "unauthorized"},
                            status_code=401)
    if action == "delete":
        return {"ok": db.delete_listing(lid)}
    if action not in ("approve", "reject"):
        return JSONResponse({"ok": False, "error": "bad action"},
                            status_code=400)
    ok = db.set_status(lid, "approved" if action == "approve" else "rejected")
    return {"ok": ok}


@router.get("/{lid}", response_class=HTMLResponse)
def detail(request: Request, lid: str):
    lang = _lang(request)
    d = db.get_listing(lid)
    if not d or d.get("status") != "approved":
        return HTMLResponse("<h1>404 — listing not found</h1>",
                            status_code=404)
    return pages.render_detail(d, lang, BASE)
