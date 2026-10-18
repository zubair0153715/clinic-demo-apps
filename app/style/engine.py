"""StyleSense engine — rule-based color science + style recommendations.
Zero-cost expert system: PIL heuristics + curated data tables. No AI API.
"""
from PIL import Image
import io

# ---------------------------------------------------------------- skin tone
TONE_UR = {"light": "Light (gori rangat)", "medium": "Medium (gehri gori / sanwli)",
           "tan": "Tan (sanwla)", "deep": "Deep (gehra sanwla)"}
UNDERTONE_UR = {"warm": "Warm (sunheri/zard jhalak)", "cool": "Cool (gulabi/neeli jhalak)",
                "neutral": "Neutral (mutawazin)"}

def _is_skin_pixel(r, g, b):
    """Classic RGB skin heuristic."""
    return (r > 95 and g > 40 and b > 20 and r > g and r > b
            and (r - g) > 12 and (max(r, g, b) - min(r, g, b)) > 12)

def analyze_skin(image_bytes):
    """Estimate skin tone + undertone from a photo.
    Samples the central region (face-ish for a portrait photo).
    Returns (tone, undertone, note). Honest: it's an estimate."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((420, 420), Image.LANCZOS)
    w, h = img.size
    # center crop: middle 46% wide, middle 56% tall
    x0, x1 = int(w * 0.27), int(w * 0.73)
    y0, y1 = int(h * 0.22), int(h * 0.78)
    region = img.crop((x0, y0, x1, y1))
    px = list(region.getdata())
    skin = [p for p in px if _is_skin_pixel(*p)]
    note = ""
    if len(skin) < max(50, len(px) * 0.02):
        # fallback: average the whole center region (photo may be full-body / no clear face)
        skin = px
        note = ("Chehra wazeh nazar nahi aaya — poori tasveer ke darmiyani hisse "
                "se andaza lagaya gaya hai. Behtar natije ke liye saaf, seedhi "
                "face photo natural light me upload karo.")
    n = len(skin)
    r = sum(p[0] for p in skin) / n
    g = sum(p[1] for p in skin) / n
    b = sum(p[2] for p in skin) / n
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum >= 185:
        tone = "light"
    elif lum >= 140:
        tone = "medium"
    elif lum >= 100:
        tone = "tan"
    else:
        tone = "deep"
    # undertone: golden/yellow bias (G notably above B) = warm;
    # pink/blue bias (B close to or above G) = cool
    if g - b >= 25:
        undertone = "warm"
    elif b >= g - 8:
        undertone = "cool"
    else:
        undertone = "neutral"
    return {"tone": tone, "tone_ur": TONE_UR[tone],
            "undertone": undertone, "undertone_ur": UNDERTONE_UR[undertone],
            "note": note, "sample_rgb": [round(r), round(g), round(b)]}

# ------------------------------------------------------- seasonal palettes
# Each season: 8 best colors + 4 avoid colors, as (name, hex).
SEASONS = {
    "spring": {
        "name": "Spring", "ur": "Bahar (Spring) — warm, roshan rang",
        "desc": "Warm undertone + light rangat. Tum par roshan, garam, zinda-dil rang jachte hain.",
        "best": [("Coral", "#FF6B6B"), ("Warm Orange", "#FFA552"),
                 ("Golden Yellow", "#FFD166"), ("Fresh Green", "#8AC926"),
                 ("Turquoise", "#4ECDC4"), ("Warm Ivory", "#F4F1DE"),
                 ("Camel", "#C19A6B"), ("Terracotta", "#E07A5F")],
        "avoid": [("Jet Black", "#1A1A1A"), ("Cool Grey", "#8D99AE"),
                  ("Icy Lavender", "#B8B8FF"), ("Deep Cool Purple", "#3A0CA3")],
    },
    "summer": {
        "name": "Summer", "ur": "Garmiyan (Summer) — cool, naram rang",
        "desc": "Cool undertone + light rangat. Tum par naram, halke, thande rang jachte hain.",
        "best": [("Powder Blue", "#A8DADC"), ("Lavender", "#B8B8FF"),
                 ("Soft Pink", "#FFB3C6"), ("Sage Green", "#B2C9AB"),
                 ("Slate Blue", "#6C8EBF"), ("Soft White", "#F8F9FA"),
                 ("Dusty Blue", "#89ABE3"), ("Soft Teal", "#7FBFBF")],
        "avoid": [("Bright Orange", "#FF6B00"), ("Bright Gold", "#FFD700"),
                  ("Saddle Brown", "#8B4513"), ("Harsh Black", "#000000")],
    },
    "autumn": {
        "name": "Autumn", "ur": "Khizan (Autumn) — warm, gehre rang",
        "desc": "Warm undertone + medium/deep rangat. Tum par mitti-jese, gehre, ameer rang jachte hain.",
        "best": [("Rust", "#B7410E"), ("Mustard", "#D4A017"),
                 ("Olive", "#6B8E23"), ("Forest Green", "#2D6A4F"),
                 ("Cognac", "#9C6644"), ("Cream", "#FFF8E7"),
                 ("Bronze", "#7F4F24"), ("Espresso", "#582F0E")],
        "avoid": [("Bubblegum Pink", "#FFB3C6"), ("Icy Lavender", "#B8B8FF"),
                  ("Cool Grey", "#E0E0E0"), ("Cool Slate", "#4A4E69")],
    },
    "winter": {
        "name": "Winter", "ur": "Sarma (Winter) — cool, tez rang",
        "desc": "Cool undertone + medium/deep rangat. Tum par tez, saaf, contrasting rang jachte hain.",
        "best": [("True Red", "#D90429"), ("Black", "#141414"),
                 ("Pure White", "#FFFFFF"), ("Cobalt Blue", "#0047AB"),
                 ("Emerald", "#046A38"), ("Royal Purple", "#7209B7"),
                 ("Silver", "#C0C0C0"), ("Hot Pink", "#FF007F")],
        "avoid": [("Mustard", "#D4A017"), ("Rust", "#B7410E"),
                  ("Cream Yellow", "#F5E6A8"), ("Camel", "#C19A6B")],
    },
}

def detect_season(tone, undertone):
    """Map tone + undertone -> season (standard 4-season heuristic)."""
    if undertone == "warm":
        return "spring" if tone in ("light", "medium") else "autumn"
    if undertone == "cool":
        return "summer" if tone in ("light", "medium") else "winter"
    # neutral: decide by tone
    if tone == "light":
        return "summer"
    if tone == "deep":
        return "winter"
    return "autumn"

# ------------------------------------------------------------------ outfits
def _luminance(hexcode):
    h = hexcode.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.299 * r + 0.587 * g + 0.114 * b

def _saturation(hexcode):
    h = hexcode.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    mx, mn = max(r, g, b), min(r, g, b)
    return (mx - mn) / mx if mx else 0

def _roles(palette_best):
    """Split palette into dark / light / mid / accent roles."""
    items = [{"name": n, "hex": hx, "lum": _luminance(hx), "sat": _saturation(hx)}
             for n, hx in palette_best]
    by_lum = sorted(items, key=lambda x: x["lum"])
    dark = by_lum[:2]
    light = by_lum[-2:]
    mid = by_lum[2:-2] or by_lum[1:-1]
    accent = sorted(items, key=lambda x: x["sat"], reverse=True)[0]
    return {"dark": dark, "light": light, "mid": mid, "accent": accent}

STYLES = ["classic", "formal", "street", "smart_casual"]
STYLE_UR = {"classic": "Classic", "formal": "Formal",
            "street": "Street", "smart_casual": "Smart Casual"}

def build_outfits(season, style, palette_best):
    """3 complete outfit formulas per style, using palette roles."""
    R = _roles(palette_best)
    D, L, M, A = R["dark"][0], R["light"][0], R["mid"][0], R["accent"]
    D2, L2 = R["dark"][1], R["light"][1]
    O = []  # (title, [(piece, color_dict)], note)

    if style == "classic":
        O = [
            ("The Boardroom", [("Blazer", D), ("Shirt", L), ("Trousers", D2), ("Shoes", {"name": "Dark Brown Leather", "hex": "#4A2C17"})],
             "Dark + light ka contrast — hamesha kaam karta hai."),
            ("Weekend Classic", [("Polo Shirt", A), ("Chinos", M), ("Loafers", {"name": "Tan Suede", "hex": "#A67B5B"})],
             "Accent upar, neutral neeche — tawajju chehre par."),
            ("Evening Classic", [("Sweater", M), ("Shirt (collar bahar)", L), ("Dark Jeans", D), ("Boots", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Layering se depth — shaam ki dawat ke liye."),
        ]
    elif style == "formal":
        O = [
            ("Full Suit", [("Suit", D), ("Dress Shirt", L), ("Tie", A), ("Oxford Shoes", {"name": "Black", "hex": "#141414"})],
             "Suit dark, shirt light, tie accent — golden rule."),
            ("Blazer Combo", [("Blazer", D2), ("Shirt", L2), ("Tie", M), ("Trousers", D), ("Shoes", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Mix-and-match formal — office ke liye behtareen."),
            ("Waistcoat Look", [("Waistcoat", M), ("Shirt", L), ("Trousers", D), ("Tie", A), ("Shoes", {"name": "Black", "hex": "#141414"})],
             "Shaadi / event — waistcoat se wazan."),
        ]
    elif style == "street":
        O = [
            ("Urban Layer", [("Jacket", D), ("T-Shirt", L), ("Jeans", D2), ("Sneakers", {"name": "White", "hex": "#F5F5F5"})],
             "Dark layers + white sneakers — street ka classic."),
            ("Color Pop", [("Hoodie", A), ("T-Shirt", L), ("Cargo", M), ("Sneakers", {"name": "Off-White", "hex": "#EDEAE0"})],
             "Ek tez rang, baqi neutral — zyada rang mat pehno."),
            ("Monochrome Street", [("Overshirt", M), ("Tee", D), ("Jeans", D2), ("Sneakers", {"name": "Black", "hex": "#141414"})],
             "Ek hi family ke rang — lamba aur slim look."),
        ]
    else:  # smart_casual
        O = [
            ("Office Casual", [("Shirt", L), ("Chinos", M), ("Belt", {"name": "Brown Leather", "hex": "#5C3A21"}), ("Loafers", {"name": "Tan", "hex": "#A67B5B"})],
             "Tucked shirt + chinos — smart casual ki bunyad."),
            ("Knit Polo", [("Knit Polo", A), ("Trousers", D), ("White Sneakers", {"name": "White", "hex": "#F5F5F5"})],
             "Polo + sneakers — dinner ya hangout."),
            ("Light Layers", [("Unstructured Blazer", M), ("T-Shirt", L), ("Chinos", D2), ("Loafers", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Blazer bina tie ke — smart bhi, relaxed bhi."),
        ]
    out = []
    for title, items, note in O:
        out.append({"title": title, "note": note,
                    "items": [{"piece": p, "color": c["name"], "hex": c["hex"]} for p, c in items]})
    return out

# --------------------------------------------------------------- hairstyles
HAIRSTYLES = {
    "oval": {
        "ur": "Oval (beiza) — mutawazin chehra",
        "tips": "Tumhara chehra balanced hai — taqreeban har style jachega. Bas chehre ko zyada lamba na dikhao.",
        "styles": [
            {"name": "Classic Side Part", "desc": "Side se maang, sides halke short. Har mauqe ke liye safe aur sharp.",
             "why": "Oval par symmetry aur neatness sab se achi lagti hai."},
            {"name": "Textured Crop", "desc": "Upar halki length, texture ke saath, sides fade. Modern aur low-maintenance.",
             "why": "Texture chehre ko zinda rakhta hai bina shape bigare."},
            {"name": "Slick Back", "desc": "Baalo ko peeche ki taraf set karo. Formal events ke liye behtareen.",
             "why": "Oval forehead ko kholna chehre ki khoobsurti dikhata hai."},
        ]},
    "round": {
        "ur": "Round (gol) — naram jaw line",
        "tips": "Maquesad: upar height banao, sides se width kam karo. Gol chehre par chapta (flat) style na rakho.",
        "styles": [
            {"name": "Quiff / Volume on Top", "desc": "Upar lamba volume, sides short fade. Chehra lamba lagega.",
             "why": "Height golai ko kat-ti hai — chehra defined lagta hai."},
            {"name": "Side Part + Fade", "desc": "Gehra side part, sides skin fade. Sharp angles bante hain.",
             "why": "Side part chehre me vertical line banata hai."},
            {"name": "Pompadour", "desc": "Aage se upar uthaya hua classic volume. Daring aur stylish.",
             "why": "Maximum height = maximum slimming effect."},
        ]},
    "square": {
        "ur": "Square (murabba) — mazboot jaw",
        "tips": "Tumhara jaw strong hai — use naram (soften) karo, chhupao mat. Zyada tez edges se bacho.",
        "styles": [
            {"name": "Textured Fringe", "desc": "Maathe par halki fringe, texture ke saath. Edges naram lagte hain.",
             "why": "Fringe forehead ki chaudai ko balance karta hai."},
            {"name": "Side-Swept Medium", "desc": "Medium length, side ki taraf sweep. Natural aur effortless.",
             "why": "Asymmetry square jaw ko naram karti hai."},
            {"name": "Messy Layers", "desc": "Layers ke saath thora messy look. Sides zyada short na karo.",
             "why": "Soft layers tez jawline ke khilaf contrast dete hain."},
        ]},
    "heart": {
        "ur": "Heart (dil) — chaudha maatha, patli thori",
        "tips": "Maatha chauda, thori patli — neeche wazan barhao, upar halka rakho.",
        "styles": [
            {"name": "Medium Length Sides", "desc": "Sides me thori length rakho taake thori bhari lage.",
             "why": "Side volume patli thori ko balance karta hai."},
            {"name": "Side Part (soft)", "desc": "Naram side part, zyada height nahi. Maatha halka cover ho.",
             "why": "Chauda maatha thora cover hone se proportion behtar hota hai."},
            {"name": "Textured Fringe", "desc": "Halki fringe maatha chhota dikhati hai.",
             "why": "Top-heavy chehre ka ilaaj fringe hai."},
        ]},
    "oblong": {
        "ur": "Oblong (lamba) — lamba chehra",
        "tips": "Chehra lamba hai — width banao, height se bacho. Bohat unche styles na rakho.",
        "styles": [
            {"name": "Fringe + Short Sides", "desc": "Maathe par fringe, sides short lekin skin fade nahi.",
             "why": "Fringe chehre ki lambai kam dikhata hai."},
            {"name": "Side Part", "desc": "Classic side part, medium volume. Width ka ehsaas deta hai.",
             "why": "Side sweep chehre ko chauda dikhata hai."},
            {"name": "Buzz with Texture", "desc": "Short buzz lekin upar texture. Lambai par zor nahi.",
             "why": "Short + wide = balanced proportion."},
        ]},
}

def get_hairstyles(face_shape):
    return HAIRSTYLES[face_shape]

# ---------------------------------------------------------------- fit tips
def fit_tips(height_cm, weight_kg=None):
    tips = []
    if height_cm is not None:
        if height_cm < 165:
            tips.append("Qad ke liye: vertical lines aur ek-rang (monochrome) outfits — lambe lagoge. Bohat dheelay kapre na pehno.")
            tips.append("Trousers thore cropped / no-break rakho — joota nazar aana chahiye.")
        elif height_cm <= 182:
            tips.append("Proportions balanced hain — taqreeban har fit chalega. Bas kapre well-fitted hon, na tight na baggy.")
        else:
            tips.append("Lambe qad ke liye: upar-neeche contrasting rang pehno taake silhouette tute. Head-to-toe ek rang se bacho.")
            tips.append("Horizontal patterns / layering tum par achi lagegi.")
    if height_cm and weight_kg:
        bmi, band, band_ur = body_type(height_cm, weight_kg)
        if band == "slim":
            tips.append("Slim build: layering, horizontal patterns aur structured shoulders tum par achay lagte hain. Bohat tight kapre patlaypan ko zyada dikhate hain.")
        elif band == "average":
            tips.append("Balanced build — fit ka khayal rakho, kapre body se chipke hon magar khinche hue na lagen.")
        else:
            tips.append("Bhari build: vertical lines, gehre rang aur ek-rang outfits slimming effect dete hain. Na bohat tight, na bohat dheelay — structured fit chuno.")
            tips.append("V-neck / khule collar gardan lambi dikhate hain. Bare prints se bacho, chhote subtle patterns behtar.")
    return tips

# ---------------------------------------------------------- body type (BMI)
BMI_BANDS = {
    "slim": "Slim (patla)",
    "average": "Average (mutawazin)",
    "heavy": "Heavy (bhaari)",
}

def body_type(height_cm, weight_kg):
    """BMI -> band. Returns (bmi, band, band_ur)."""
    m = height_cm / 100.0
    bmi = weight_kg / (m * m)
    if bmi < 18.5:
        band = "slim"
    elif bmi < 25:
        band = "average"
    else:
        band = "heavy"
    return round(bmi, 1), band, BMI_BANDS[band]

# --------------------------------------------------------------- moustaches
# The 6 styles from the "Moochein Styles Batao" session.
MOUSTACHES = {
    "chevron": {
        "name": "Chevron Moustache", "ur": "Chevron — bhari classic mooch",
        "desc": "Honton ki lakeer ke saath bhari, ghani mooch. Mature, confident look.",
        "good_for": ["oval", "square", "oblong"],
        "tip": "Har 3-4 din trim karo, warna honton par latakne lagti hai."},
    "pencil": {
        "name": "Pencil Moustache", "ur": "Pencil — patli neat line",
        "desc": "Hont ke upar patli, saaf line. Vintage, artistic look.",
        "good_for": ["oval", "heart"],
        "tip": "Roz razor se edges saaf rakho — ye style safai mangta hai."},
    "natural": {
        "name": "Natural Moustache", "ur": "Natural — halki medium mooch",
        "desc": "Qudrati tor par barhi, halki trim. Sab se safe aur versatile.",
        "good_for": ["oval", "round", "square", "heart", "oblong"],
        "tip": "Har chehre par chalti hai — pehli mooch ke liye behtareen shuruaat."},
    "handlebar": {
        "name": "Handlebar Moustache", "ur": "Handlebar — mure hue siray",
        "desc": "Siray upar ki taraf mure hue. Daring, statement look.",
        "good_for": ["oval", "oblong", "square"],
        "tip": "Wax chahiye aur roz styling — waqt dena parega."},
    "moustache_short_beard": {
        "name": "Moustache + Short Beard", "ur": "Mooch + chhoti dadhi",
        "desc": "Bhari mooch ke saath chhoti boxed dadhi. Rugged, mardana look.",
        "good_for": ["oval", "square", "heart"],
        "tip": "Dadhi short rakho taake mooch hero rahe."},
    "thick_desi": {
        "name": "Thick Desi Moustache", "ur": "Desi — ghani rawaiti mooch",
        "desc": "Moti, ghani, rawaiti desi mooch. Waqar wala look.",
        "good_for": ["square", "oval", "oblong"],
        "tip": "Chehre ko bharta hai — patlay chehre par zyada bhari lag sakti hai."},
}

MOUSTACHE_PRIORITY = {"natural": 0, "chevron": 1, "moustache_short_beard": 2,
                      "thick_desi": 3, "handlebar": 4, "pencil": 5}

def get_moustaches(face_shape, grooming="beard"):
    """Rank the 6 moustache styles for this face shape.
    grooming: clean -> [] (no moustache), moustache/beard -> ranked list."""
    if grooming == "clean":
        return []
    ranked = []
    for key, m in MOUSTACHES.items():
        best = face_shape in m["good_for"][:2]
        ranked.append({"id": key, "name": m["name"], "ur": m["ur"], "desc": m["desc"],
                       "tip": m["tip"], "best_for_you": best})
    ranked.sort(key=lambda x: (not x["best_for_you"], MOUSTACHE_PRIORITY[x["id"]], x["name"]))
    return ranked

# ------------------------------------------------------------------ beards
BEARDS = {
    "clean_shaven": {
        "name": "Clean Shaven", "ur": "Clean shave — saaf chehra",
        "desc": "Bilkul saaf. Young, fresh aur professional look.",
        "good_for": ["oval", "heart", "oblong"],
        "tip": "Jawline saaf nazar aati hai — strong jaw walo ke liye best."},
    "light_stubble": {
        "name": "Light Stubble", "ur": "Halki stubble — 2-3 din ki",
        "desc": "Halki khurdari dadhi. Effortless, modern look.",
        "good_for": ["oval", "round", "square", "heart", "oblong"],
        "tip": "Sab se versatile — har 2-3 din trimmer se maintain karo."},
    "short_boxed": {
        "name": "Short Boxed Beard", "ur": "Short boxed — saaf kinare",
        "desc": "Chhoti, tez kinaron wali dadhi. Sharp professional look.",
        "good_for": ["oval", "oblong", "heart"],
        "tip": "Cheeks ki line unchi rakho — chehra lamba lagega."},
    "full_beard": {
        "name": "Full Beard", "ur": "Full dadhi — ghani",
        "desc": "Bhari, ghani dadhi. Mardana, powerful look.",
        "good_for": ["square", "oval", "heart"],
        "tip": "Gardan ki line saaf rakho, warna be-tarteeb lagti hai."},
    "goatee": {
        "name": "Goatee", "ur": "Goatee — thori par",
        "desc": "Sirf thori aur mooch ke ird-gird. Thori lambi dikhti hai.",
        "good_for": ["round", "square"],
        "tip": "Gol chehre ko lamba dikhata hai."},
    "chin_strap": {
        "name": "Chin Strap", "ur": "Chin strap — jawline par patti",
        "desc": "Jawline ke saath patli patti. Edgy, defined look.",
        "good_for": ["oval", "square"],
        "tip": "Roz kinare saaf karo — ye style precision mangta hai."},
}

BEARD_PRIORITY = {"full_beard": 0, "short_boxed": 1, "light_stubble": 2,
                  "clean_shaven": 3, "goatee": 4, "chin_strap": 5}

def get_beards(face_shape, grooming="beard"):
    """Rank beard styles. clean -> [clean_shaven only]; moustache -> clean_shaven first;
    beard -> full ranking."""
    ranked = []
    for key, b in BEARDS.items():
        best = face_shape in b["good_for"][:2]
        ranked.append({"id": key, "name": b["name"], "ur": b["ur"], "desc": b["desc"],
                       "tip": b["tip"], "best_for_you": best})
    if grooming == "clean":
        ranked = [r for r in ranked if r["id"] == "clean_shaven"]
    elif grooming == "moustache":
        # mooch hero hai — dadhi saaf
        ranked = [r for r in ranked if r["id"] == "clean_shaven"]
        ranked[0]["tip"] = "Mooch ko chamakne do — dadhi saaf rakho."
    ranked.sort(key=lambda x: (not x["best_for_you"], BEARD_PRIORITY[x["id"]], x["name"]))
    return ranked

# ------------------------------------------------------------ occasions
OCCASIONS = ["daily", "office", "event", "wedding"]
OCCASION_UR = {"daily": "Rozmarra (Daily)", "office": "Office",
               "event": "Dawat / Event", "wedding": "Shaadi (Wedding)"}

def build_occasion_outfits(season, occasion, palette_best):
    """3 complete outfit formulas per occasion, using palette roles."""
    R = _roles(palette_best)
    D, L, M, A = R["dark"][0], R["light"][0], R["mid"][0], R["accent"]
    D2, L2 = R["dark"][1], R["light"][1]
    O = []
    if occasion == "daily":
        O = [
            ("Rozmarra Casual", [("T-Shirt", L), ("Jeans", D), ("Sneakers", {"name": "White", "hex": "#F5F5F5"})],
             "Saaf T-shirt + achi jeans — roz ke liye kafi."),
            ("Polo Day", [("Polo Shirt", A), ("Chinos", M), ("Loafers", {"name": "Tan Suede", "hex": "#A67B5B"})],
             "Polo upar, neutral neeche — casual bhi, put-together bhi."),
            ("Layered Daily", [("Overshirt", M), ("Tee", L), ("Jeans", D2), ("Sneakers", {"name": "Off-White", "hex": "#EDEAE0"})],
             "Halki layering — mausam badle to bhi tayyar."),
        ]
    elif occasion == "office":
        O = [
            ("Office Sharp", [("Dress Shirt", L), ("Trousers", D), ("Belt", {"name": "Brown Leather", "hex": "#5C3A21"}), ("Oxford Shoes", {"name": "Black", "hex": "#141414"})],
             "Tucked shirt, polished shoes — office ka standard."),
            ("Blazer Day", [("Blazer", D2), ("Shirt", L2), ("Chinos", M), ("Loafers", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Blazer bina tie — meeting ho ya desk work."),
            ("Smart Knit", [("Knit Polo", A), ("Trousers", D), ("Loafers", {"name": "Tan", "hex": "#A67B5B"})],
             "Casual Friday ya creative office ke liye."),
        ]
    elif occasion == "event":
        O = [
            ("Dinner Sharp", [("Blazer", D), ("Shirt", L), ("Dark Jeans", D2), ("Chelsea Boots", {"name": "Black", "hex": "#141414"})],
             "Blazer + dark jeans — dawat ka safe winner."),
            ("Waistcoat Look", [("Waistcoat", M), ("Shirt", L), ("Trousers", D), ("Shoes", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Waistcoat se wazan — photos me acha lagega."),
            ("Monochrome Night", [("Shirt", D), ("Trousers", D2), ("Blazer", M), ("Shoes", {"name": "Black", "hex": "#141414"})],
             "Ek hi family ke gehre rang — shaam ke liye classy."),
        ]
    else:  # wedding
        O = [
            ("Shaadi Classic", [("Sherwani / Suit", A), ("Kurta (neeche)", L), ("Khussa / Oxford", {"name": "Dark Brown", "hex": "#3E2723"})],
             "Accent rang dulha-side — bheed me alag nazar aao."),
            ("Waistcoat Formal", [("Waistcoat", D), ("Kurta Pajama", L), ("Peshawari Chappal", {"name": "Brown", "hex": "#5C3A21"})],
             "Rawaiti + formal — shaadiyon ka tried-and-tested."),
            ("Full Suit", [("Suit", D), ("Dress Shirt", L), ("Tie / Bow", M), ("Oxford Shoes", {"name": "Black", "hex": "#141414"})],
             "Western shaadi look — suit dark, shirt light."),
        ]
    out = []
    for title, items, note in O:
        out.append({"title": title, "note": note,
                    "items": [{"piece": p, "color": c["name"], "hex": c["hex"]} for p, c in items]})
    return out

# ---------------------------------------------------------------- best pick
FACE_BENEFIT = {
    "oval": "chehre ki natural symmetry ko ubharega",
    "round": "chehre ko lamba aur defined dikhayega",
    "square": "mazboot jawline ko naram aur balanced karega",
    "heart": "chaude maathe aur patli thori ko proportion me layega",
    "oblong": "lambe chehre ko balanced aur bhara hua dikhayega",
}

def best_pick(face_shape, grooming, occasion, season, palette_best, bmi_band=None):
    """One recommended combo: moustache + beard + hairstyle + outfit, with a 1-line why."""
    m_list = get_moustaches(face_shape, grooming)
    b_list = get_beards(face_shape, grooming)
    hairs = HAIRSTYLES[face_shape]["styles"]
    # formal occasions -> prefer sleeker hair
    hair = hairs[0]
    if occasion in ("event", "wedding", "office"):
        for h in hairs:
            if "slick" in h["name"].lower() or "side part" in h["name"].lower():
                hair = h
                break
    outfits = build_occasion_outfits(season, occasion, palette_best)
    outfit = outfits[0]
    m = m_list[0] if m_list else None
    b = b_list[0] if b_list else None
    parts = []
    if m:
        parts.append(m["name"])
    if b and b["id"] != "clean_shaven":
        parts.append(b["name"])
    elif b:
        parts.append("clean shave")
    parts.append(hair["name"])
    benefit = FACE_BENEFIT.get(face_shape, "chehre ko balanced rakhega")
    band_txt = f", {BMI_BANDS[bmi_band]} build" if bmi_band else ""
    why = (f"Tumhara {HAIRSTYLES[face_shape]['ur'].split(' — ')[0]} chehra{band_txt} aur "
           f"{OCCASION_UR[occasion]} mauqa — ye combo {benefit}.")
    headline = " + ".join(parts) + f" — {outfit['title']}"
    return {
        "headline": headline,
        "why": why,
        "moustache": m,
        "beard": b,
        "hairstyle": hair,
        "outfit": outfit,
    }

HONEST_NOTE = ("Imaandaar baat: ye science-based color aur style guidance hai — "
               "rule-based, muft. Skin-tone ka andaza bhi ek estimate hai — "
               "behtareen natije ke liye saaf face photo natural light me use karo. "
               "\"Apni photo par dekho\" (AI visualization) sirf tab kaam karega jab "
               "owner apni free Gemini API key add karega — uske baghair ye step active nahi.")
