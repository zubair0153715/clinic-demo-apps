"""Ujala engine — original, clean-room photo enhancement.

No Evoto code, model, asset or trademark is used anywhere. Every
operation is a documented Pillow primitive (ImageEnhance factors,
ImageOps.autocontrast, Gaussian blur blend, per-channel warmth scaling)
applied to the user's own uploaded photo, in memory only.

Honest limits (also stated on the page): there is NO face detection,
NO skin segmentation, NO blemish removal, NO background removal, NO
layers and NO RAW support here. "Smoothing" is a global softening
blend of the whole image toward its blurred version — it softens
everything slightly, not just skin. It says so, on purpose.
"""

from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

MAX_BYTES = 10 * 1024 * 1024
MAX_DIM = 3000

PRESETS = {
    "auto": {
        "label": "Auto — balanced clean-up",
        "brightness": 1.0, "contrast": 1.0, "color": 1.15,
        "sharpness": 1.2, "warmth": 0.0, "smooth": 0.0,
        "autocontrast": True,
    },
    "portrait": {
        "label": "Portrait — warm + gently softened",
        "brightness": 1.05, "contrast": 1.05, "color": 1.1,
        "sharpness": 1.0, "warmth": 0.25, "smooth": 0.25,
        "autocontrast": True,
    },
    "product": {
        "label": "Product — bright, clean, background-lifting",
        "brightness": 1.12, "contrast": 1.05, "color": 1.1,
        "sharpness": 1.15, "warmth": 0.0, "smooth": 0.0,
        "autocontrast": True,
    },
    "vivid": {
        "label": "Vivid — colour-forward",
        "brightness": 1.0, "contrast": 1.1, "color": 1.4,
        "sharpness": 1.15, "warmth": 0.1, "smooth": 0.0,
        "autocontrast": False,
    },
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def load_image(data: bytes) -> Image.Image:
    """Decode an upload, enforcing size/dimension caps. Raises ValueError."""
    if not data:
        raise ValueError("Koi photo upload nahi hui.")
    if len(data) > MAX_BYTES:
        raise ValueError("Photo 10 MB se bari hai — chhoti file try karein.")
    try:
        img = Image.open(BytesIO(data))
        img.load()
    except Exception:
        raise ValueError("Ye file photo nahi lag rahi (JPEG/PNG/WebP chahiye).")
    if img.format not in ("JPEG", "PNG", "WEBP"):
        raise ValueError("Sirf JPEG, PNG ya WebP photos supported hain.")
    img = img.convert("RGB")
    if max(img.size) > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    return img


def image_stats(img: Image.Image) -> dict:
    """Measured (never invented) stats: mean brightness 0-255 and mean
    saturation 0-255, computed from the actual pixels."""
    grey = img.convert("L")
    sat = img.convert("HSV").split()[1]
    return {
        "mean_brightness": round(ImageStat.Stat(grey).mean[0], 1),
        "mean_saturation": round(ImageStat.Stat(sat).mean[0], 1),
        "width": img.size[0],
        "height": img.size[1],
    }


def apply_warmth(img: Image.Image, warmth: float) -> Image.Image:
    """warmth in [-1, 1]: positive warms (R up, B down), negative cools.
    Linear per-channel scaling, clamped to 0-255 by Pillow's point()."""
    warmth = _clamp(warmth, -1.0, 1.0)
    if warmth == 0:
        return img
    r, g, b = img.split()
    r = r.point(lambda v: int(_clamp(v * (1 + warmth * 0.20), 0, 255)))
    b = b.point(lambda v: int(_clamp(v * (1 - warmth * 0.20), 0, 255)))
    return Image.merge("RGB", (r, g, b))


def apply_smooth(img: Image.Image, smooth: float) -> Image.Image:
    """Global softening: blend toward a Gaussian-blurred copy.
    smooth 0 = original, 0.6 = strongest offered. NOT face-aware."""
    smooth = _clamp(smooth, 0.0, 0.6)
    if smooth == 0:
        return img
    blurred = img.filter(ImageFilter.GaussianBlur(radius=2))
    return Image.blend(img, blurred, smooth)


def apply_adjust(img: Image.Image, brightness=1.0, contrast=1.0,
                 color=1.0, sharpness=1.0, warmth=0.0, smooth=0.0,
                 autocontrast=False) -> Image.Image:
    """Apply the documented pipeline in fixed order. All factors are
    Pillow ImageEnhance factors where 1.0 = no change."""
    out = img
    if autocontrast:
        out = ImageOps.autocontrast(out, cutoff=1)
    out = apply_warmth(out, warmth)
    out = apply_smooth(out, smooth)
    out = ImageEnhance.Brightness(out).enhance(_clamp(brightness, 0.2, 3.0))
    out = ImageEnhance.Contrast(out).enhance(_clamp(contrast, 0.2, 3.0))
    out = ImageEnhance.Color(out).enhance(_clamp(color, 0.0, 3.0))
    out = ImageEnhance.Sharpness(out).enhance(_clamp(sharpness, 0.0, 3.0))
    return out


def enhance(data: bytes, preset="auto", overrides=None) -> dict:
    """Full pipeline: decode -> preset params (+ overrides) -> process
    -> JPEG bytes + measured before/after stats. Nothing is stored."""
    img = load_image(data)
    params = dict(PRESETS.get(preset, PRESETS["auto"]))
    params.pop("label", None)
    for key, val in (overrides or {}).items():
        if key in params and val is not None:
            params[key] = val
    before = image_stats(img)
    out = apply_adjust(img, **params)
    after = image_stats(out)
    buf = BytesIO()
    out.save(buf, format="JPEG", quality=90)
    return {
        "jpeg": buf.getvalue(),
        "before": before,
        "after": after,
        "preset": preset if preset in PRESETS else "auto",
        "params": params,
    }
