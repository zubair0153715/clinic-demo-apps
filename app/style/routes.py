"""StyleSense / Style Advisor v2 — rule-based personal style advisor. Route: /style
Stateless: uploads are processed in memory, nothing is stored.
"""
import io
import os

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response

from PIL import Image

from app.style import engine as E
from app.style import gemini_gen as G

router = APIRouter()
HTML_PATH = os.path.join(os.path.dirname(__file__), "app.html")
MAX_BYTES = 5 * 1024 * 1024


def _read_photo(raw):
    """Validate + open an uploaded photo. Returns (PIL image, error_dict_or_None)."""
    if len(raw) > MAX_BYTES:
        return None, {"error": "Photo 5MB se bari hai — chhoti photo upload karo.", "status": 413}
    if len(raw) == 0:
        return None, {"error": "Khaali file mili.", "status": 400}
    try:
        img = Image.open(io.BytesIO(raw))
        img.verify()
        img = Image.open(io.BytesIO(raw))  # reopen after verify
        if img.format not in ("JPEG", "PNG"):
            return None, {"error": "Sirf JPG ya PNG photo qabool hai.", "status": 400}
    except Exception:
        return None, {"error": "Ye tasveer nahi lagti — JPG/PNG upload karo.", "status": 400}
    return img, None


def _num(value, name, lo, hi, ur_name):
    """Parse + range-check an optional numeric form field. Returns (val, error_or_None)."""
    if not value or not str(value).strip():
        return None, None
    try:
        v = float(str(value).strip())
    except ValueError:
        return None, f"{ur_name} number me likho."
    if not (lo <= v <= hi):
        return None, f"{ur_name} had se bahar hai ({lo}-{hi})."
    return v, None


@router.get("/style", response_class=HTMLResponse)
def style_home():
    with open(HTML_PATH, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.post("/style/api/analyze")
async def analyze(photo: UploadFile = File(...),
                  face_shape: str = Form(...),
                  style: str = Form(default="smart_casual"),
                  height: str = Form(default=""),
                  weight: str = Form(default=""),
                  age: str = Form(default=""),
                  gender: str = Form(default="male"),
                  occasion: str = Form(default="daily"),
                  grooming: str = Form(default="beard")):
    # --- validate enums
    face_shape = (face_shape or "").strip().lower()
    style = (style or "").strip().lower()
    gender = (gender or "male").strip().lower()
    occasion = (occasion or "daily").strip().lower()
    grooming = (grooming or "beard").strip().lower()
    if face_shape not in E.HAIRSTYLES:
        return JSONResponse({"error": "face_shape must be one of: oval, round, square, heart, oblong"},
                            status_code=400)
    if style not in E.STYLES:
        return JSONResponse({"error": "style must be one of: classic, formal, street, smart_casual"},
                            status_code=400)
    if gender not in ("male", "female"):
        return JSONResponse({"error": "gender must be male ya female"}, status_code=400)
    if occasion not in E.OCCASIONS:
        return JSONResponse({"error": "occasion must be one of: daily, office, event, wedding"},
                            status_code=400)
    if grooming not in ("clean", "moustache", "beard"):
        return JSONResponse({"error": "grooming must be one of: clean, moustache, beard"},
                            status_code=400)

    # --- validate numbers
    height_cm, err = _num(height, "height", 120, 230, "Qad")
    if err:
        return JSONResponse({"error": err}, status_code=400)
    weight_kg, err = _num(weight, "weight", 30, 200, "Wazan")
    if err:
        return JSONResponse({"error": err}, status_code=400)
    age_yrs, err = _num(age, "age", 13, 100, "Umar")
    if err:
        return JSONResponse({"error": err}, status_code=400)

    # --- validate photo
    raw = await photo.read()
    _, perr = _read_photo(raw)
    if perr:
        return JSONResponse({"error": perr["error"]}, status_code=perr["status"])

    # --- analyze (stateless, in-memory only)
    skin = E.analyze_skin(raw)
    season = E.detect_season(skin["tone"], skin["undertone"])
    pal = E.SEASONS[season]
    outfits = E.build_outfits(season, style, pal["best"])
    occ_outfits = E.build_occasion_outfits(season, occasion, pal["best"])
    hair = E.get_hairstyles(face_shape)

    body = None
    bmi_band = None
    if height_cm and weight_kg:
        bmi, bmi_band, band_ur = E.body_type(height_cm, weight_kg)
        body = {"bmi": bmi, "band": bmi_band, "band_ur": band_ur,
                "height_cm": height_cm, "weight_kg": weight_kg}

    female = (gender == "female")
    moustaches = [] if female else E.get_moustaches(face_shape, grooming)
    beards = [] if female else E.get_beards(face_shape, grooming)
    best = E.best_pick(face_shape, grooming, occasion, season, pal["best"], bmi_band)
    if female:
        best = dict(best)
        best["moustache"] = None
        best["beard"] = None
        best["headline"] = f"{best['hairstyle']['name']} — {best['outfit']['title']}"
        best["female_note"] = "Mooch/dadhi section male grooming ke liye hai — tumhare liye hairstyle + outfit pick hai."

    return JSONResponse({
        "skin": skin,
        "season": {"id": season, "name": pal["name"], "ur": pal["ur"], "desc": pal["desc"]},
        "palette": {
            "best": [{"name": n, "hex": hx} for n, hx in pal["best"]],
            "avoid": [{"name": n, "hex": hx} for n, hx in pal["avoid"]],
        },
        "style": {"id": style, "name": E.STYLE_UR[style]},
        "occasion": {"id": occasion, "name": E.OCCASION_UR[occasion]},
        "gender": gender,
        "age": age_yrs,
        "grooming": grooming,
        "outfits": outfits,
        "occasion_outfits": occ_outfits,
        "hairstyles": {"face_shape": face_shape, "face_ur": hair["ur"],
                       "tips": hair["tips"], "styles": hair["styles"]},
        "moustaches": moustaches,
        "beards": beards,
        "body": body,
        "fit_tips": E.fit_tips(height_cm, weight_kg),
        "best_pick": best,
        "visualization_available": G.key_available(),
        "honest_note": E.HONEST_NOTE,
    })


@router.post("/style/api/visualize")
async def visualize(photo: UploadFile = File(...),
                    moustache: str = Form(default=""),
                    beard: str = Form(default=""),
                    hairstyle: str = Form(default="")):
    """AI visualization: apply the chosen grooming styles to the user's photo.
    Needs GEMINI_API_KEY (owner's free key). Returns the edited image,
    or JSON {available:false, reason} when the key is missing or the call fails."""
    raw = await photo.read()
    _, perr = _read_photo(raw)
    if perr:
        return JSONResponse({"error": perr["error"]}, status_code=perr["status"])

    if not G.key_available():
        return JSONResponse({
            "available": False,
            "reason": ("GEMINI_API_KEY set nahi hai — \"apni photo par dekho\" wala step "
                       "owner ki free Gemini API key add hone ke baad active hoga. "
                       "Neeche di gayi rule-based guidance tab bhi poori tarah kaam karti hai."),
        })

    prompt = G.build_prompt(moustache.strip(), beard.strip(), hairstyle.strip())
    img_bytes, reason = G.visualize(raw, prompt)
    if img_bytes is None:
        return JSONResponse({"available": False, "reason": reason}, status_code=502)
    return Response(content=img_bytes, media_type="image/jpeg")
