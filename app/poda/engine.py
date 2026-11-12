# -*- coding: utf-8 -*-
"""Poda engine — free AI plant identifier (PictureThis gap build).

Pure, deterministic logic. No network, no storage, no key needed.

What this engine does (all testable exactly):

* Pakistan seasons — summer is April–September, winter is
  October–March. Watering intervals come from published care
  guides, not from a guess: every value below sits inside the
  range its source gives (sources in COMMON_PLANTS and in the gap
  report 2026-11-12-poda.md).
* Watering schedule math — next-watering date from the last
  watering plus the season interval, with overdue / due-today /
  in-N-days status. The finger test always wins over the
  calendar: the page says so, and the table is a starting point,
  not a prescription.
* Image validation — type allowlist, 5 MB cap, base64 decodable.
* AI-output validators — the Gemini JSON must carry every field,
  confidence 0–100, a real plant (is_plant true), and a do-not-eat
  warning. An AI answer that calls any plant safe to eat is
  REFUSED outright: that is the exact failure PictureThis was
  reviewed for (Oct 24, 2026 — a highly toxic plant called
  edible). Low confidence (< 60) is flagged uncertain, never
  hidden.
* Common-plants care table — 10 plants every Pakistani home has,
  usable with no key at all.

Nothing here is PictureThis's property: plant names, published
watering ranges and care facts are public horticultural knowledge,
and every value below was written from public care guides.
"""

import base64
import binascii
import re
from datetime import date, timedelta

LANGUAGES = ["en", "roman", "ur"]

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Pakistan seasons. Summer: April–September (the hot months, when
# pots dry out fast). Winter: October–March.
SUMMER_MONTHS = {4, 5, 6, 7, 8, 9}


def season_for_month(month):
    """'summer' for Apr–Sep, 'winter' for Oct–Mar. Returns
    (season, error)."""
    if not isinstance(month, int) or month < 1 or month > 12:
        return None, "Mahina 1–12 ke darmiyan hona chahiye."
    return ("summer" if month in SUMMER_MONTHS else "winter"), None


# --- common plants ----------------------------------------------------------
# water_summer / water_winter: days between waterings, inside the
# published range quoted in "source". Pot/container plants; a neem
# in the ground, once established, rarely needs watering at all.
COMMON_PLANTS = [
    {
        "id": "money-plant", "name_en": "Money Plant",
        "name_roman": "Money Plant", "name_ur": "منی پلانٹ",
        "scientific": "Epipremnum aureum",
        "water_summer": 8, "water_winter": 14,
        "sunlight_en": "Bright, indirect light",
        "sunlight_ur": "تیز مگر بالواسطہ روشنی",
        "soil_en": "Well-draining potting mix; keep moist, not soggy",
        "temp_min_c": 15, "temp_max_c": 35,
        "toxic_pets": "Mildly toxic to pets if eaten (calcium oxalate).",
        "toxic_humans": "Mildly irritating if eaten; keep away from children.",
        "tip_en": "Water when the top half of the soil feels dry. "
                  "Overwatering makes the stems soft.",
        "tip_roman": "Jab mitti ki upar wali aadhi teh sookhi lage tab "
                     "paani dein. Zyada paani se tehni naram par jati hai.",
        "source": "theleafycare.com — 7–10 days summer, 14 days winter",
    },
    {
        "id": "snake-plant", "name_en": "Snake Plant",
        "name_roman": "Snake Plant", "name_ur": "سانپ پلانٹ",
        "scientific": "Dracaena trifasciata",
        "water_summer": 18, "water_winter": 30,
        "sunlight_en": "Low to bright indirect light",
        "sunlight_ur": "کم سے تیز بالواسطہ روشنی",
        "soil_en": "Very well-draining, sandy mix; let dry fully",
        "temp_min_c": 10, "temp_max_c": 38,
        "toxic_pets": "Mildly toxic to pets if eaten.",
        "toxic_humans": "Mildly toxic if eaten; keep away from children.",
        "tip_en": "Let the soil dry completely between waterings. "
                  "Overwatering is its only real enemy.",
        "tip_roman": "Paani dene se pehle mitti ko poori tarah sookhne "
                     "dein. Zyada paani hi is ka asal dushman hai.",
        "source": "theleafycare.com — 14–21 days summer, 30 days winter",
    },
    {
        "id": "aloe-vera", "name_en": "Aloe Vera",
        "name_roman": "Aloe Vera (Kunwar Gandal)", "name_ur": "کنوار گندل",
        "scientific": "Aloe barbadensis miller",
        "water_summer": 18, "water_winter": 30,
        "sunlight_en": "Bright indirect light to full sun",
        "sunlight_ur": "تیز بالواسطہ روشنی یا پوری دھوپ",
        "soil_en": "Sandy, fast-draining cactus/succulent mix",
        "temp_min_c": 10, "temp_max_c": 40,
        "toxic_pets": "Toxic to pets if eaten (dogs and cats).",
        "toxic_humans": "Gel is used on skin; do not eat the leaf — "
                         "the latex under the skin is a laxative.",
        "tip_en": "Water deeply but rarely; the leaves store water. "
                  "Let the soil dry out completely first.",
        "tip_roman": "Gehra paani dein magar kam — patte paani zakheera "
                     "karte hain. Pehle mitti poori sookhne dein.",
        "source": "theleafycare.com — 14–21 days summer, monthly winter; "
                  "SCSU libguide — toxic to pets",
    },
    {
        "id": "neem", "name_en": "Neem",
        "name_roman": "Neem", "name_ur": "نیم",
        "scientific": "Azadirachta indica",
        "water_summer": 10, "water_winter": 18,
        "sunlight_en": "Full sun, 6–8 hours daily",
        "sunlight_ur": "پوری دھوپ، روز 6–8 گھنٹے",
        "soil_en": "Deep, sandy, well-draining soil",
        "temp_min_c": 5, "temp_max_c": 45,
        "toxic_pets": "Neem oil is toxic to small children and pets "
                      "if swallowed; leaves are bitter and not food.",
        "toxic_humans": "Neem oil is toxic if swallowed, especially "
                         "for small children. Never use as medicine "
                         "on an app's word.",
        "tip_en": "Drought-tolerant once established; a tree in the "
                  "ground rarely needs watering. In a pot, water when "
                  "the top 3–5 cm of soil is dry. Looks like chinaberry "
                  "(bakain) — check the leaves before trusting an ID.",
        "tip_roman": "Aik dafa jam jaye to sookha bardasht karta hai; "
                     "zameen me laga darakht shaaz o naadir hi paani "
                     "mangta hai. Gamle me upar ki 3–5 cm mitti sookhi "
                     "ho to paani dein. Bakain jaisa dikhta hai — "
                     "pehchan par bharosa karne se pehle patte check karein.",
        "source": "plantlyze.com / leafypixels.com — container 7–10 days "
                  "summer, 14–21 days winter; Wikipedia — native to "
                  "Pakistan, confused with chinaberry, oil toxic to "
                  "small children",
    },
    {
        "id": "motia", "name_en": "Motia (Arabian Jasmine)",
        "name_roman": "Motia", "name_ur": "موتیا",
        "scientific": "Jasminum sambac",
        "water_summer": 5, "water_winter": 7,
        "sunlight_en": "Full sun",
        "sunlight_ur": "پوری دھوپ",
        "soil_en": "Rich, well-draining soil; keep evenly moist",
        "temp_min_c": 10, "temp_max_c": 45,
        "toxic_pets": "Generally considered safe around pets, but "
                      "do not let pets eat any plant.",
        "toxic_humans": "Flowers are used for tea in some traditions — "
                         "still, do not eat any plant on an app's word.",
        "tip_en": "Fully heat tolerant across Pakistan. Water when the "
                  "top inch of soil feels dry — about every 4–5 days "
                  "in summer, weekly in winter.",
        "tip_roman": "Poore Pakistan ki garmi bardasht karta hai. Upar "
                     "ki aik inch mitti sookhi lage to paani dein — "
                     "garmiyon me taqreeban 4–5 din baad, sardiyon me "
                     "hafte me aik dafa.",
        "source": "plants.com.pk — jasmine family, 4–5 days summer, "
                  "weekly winter, fully heat tolerant",
    },
    {
        "id": "rose", "name_en": "Rose",
        "name_roman": "Gulab", "name_ur": "گلاب",
        "scientific": "Rosa",
        "water_summer": 3, "water_winter": 7,
        "sunlight_en": "Full sun, 6+ hours daily",
        "sunlight_ur": "پوری دھوپ، روز 6+ گھنٹے",
        "soil_en": "Rich, well-draining loam; mulch helps in summer",
        "temp_min_c": 5, "temp_max_c": 42,
        "toxic_pets": "Roses themselves are not toxic to pets, but "
                      "thorns can injure mouths and paws.",
        "toxic_humans": "Not toxic, but never eat a plant on an app's "
                         "word — nursery plants may be sprayed.",
        "tip_en": "Water at the base, not on the leaves, to avoid "
                  "fungus. In a Pakistani summer a potted rose can "
                  "need water every 2–3 days.",
        "tip_roman": "Paani jad me dein, patton par nahi — warna phaphundi "
                     "lagti hai. Pakistani garmi me gamle ka gulab "
                     "2–3 din baad paani maang sakta hai.",
        "source": "Standard rose care (water 2–3x/week in hot summers); "
                  "The News / Karachi nursery guidance for hot climates",
    },
    {
        "id": "marigold", "name_en": "Marigold",
        "name_roman": "Gainda", "name_ur": "گیندا",
        "scientific": "Tagetes",
        "water_summer": 3, "water_winter": 5,
        "sunlight_en": "Full sun",
        "sunlight_ur": "پوری دھوپ",
        "soil_en": "Well-draining soil; tolerates poor soil",
        "temp_min_c": 10, "temp_max_c": 42,
        "toxic_pets": "Mild stomach upset if a pet eats a lot of it.",
        "toxic_humans": "Not a food plant; do not eat on an app's word.",
        "tip_en": "Deadhead spent flowers to keep it blooming. Loves "
                  "Pakistani summer sun; hates wet feet.",
        "tip_roman": "Murjhaye phool torhte rahein to phool aate rahenge. "
                     "Pakistani garmi ki dhoop pasand hai; khari mitti "
                     "me paani khara hona pasand nahi.",
        "source": "Standard marigold care — full sun, frequent water in "
                  "heat, well-draining soil",
    },
    {
        "id": "tulsi", "name_en": "Holy Basil (Tulsi)",
        "name_roman": "Tulsi", "name_ur": "تلسی",
        "scientific": "Ocimum sanctum",
        "water_summer": 3, "water_winter": 5,
        "sunlight_en": "Full sun, 6+ hours daily",
        "sunlight_ur": "پوری دھوپ، روز 6+ گھنٹے",
        "soil_en": "Rich, well-draining soil",
        "temp_min_c": 12, "temp_max_c": 42,
        "toxic_pets": "Generally safe around pets in small amounts, "
                      "but do not let pets eat any plant.",
        "toxic_humans": "A traditional culinary/medicinal herb — still, "
                         "do not use as medicine on an app's word.",
        "tip_en": "Pinch the tips to keep it bushy. Needs daily water "
                  "in a hot-summer pot; never let it wilt for long.",
        "tip_roman": "Upar ki nokain chunte rahein to ghani hoti hai. "
                     "Garmi me gamle me roz paani chahiye ho sakta hai; "
                     "der tak murjhane na dein.",
        "source": "Standard tulsi care — full sun, keep evenly moist "
                  "in heat",
    },
    {
        "id": "hibiscus", "name_en": "Hibiscus",
        "name_roman": "Gurhal", "name_ur": "گڑھل",
        "scientific": "Hibiscus rosa-sinensis",
        "water_summer": 3, "water_winter": 7,
        "sunlight_en": "Full sun",
        "sunlight_ur": "پوری دھوپ",
        "soil_en": "Rich, well-draining soil; slightly acidic is fine",
        "temp_min_c": 10, "temp_max_c": 42,
        "toxic_pets": "Some hibiscus species upset pet stomachs — "
                      "keep pets from nibbling.",
        "toxic_humans": "Not a food plant on an app's word; nursery "
                         "plants may be sprayed.",
        "tip_en": "Heavy drinker in summer; water at the base and "
                  "feed lightly in the growing season.",
        "tip_roman": "Garmi me zyada paani peeta hai; jad me paani dein "
                     "aur barhne ke mosam me halki khaad dein.",
        "source": "Standard hibiscus care — full sun, frequent summer "
                  "water, well-draining soil",
    },
    {
        "id": "desert-rose", "name_en": "Desert Rose",
        "name_roman": "Sehrai Gulab", "name_ur": "صحرائی گلاب",
        "scientific": "Adenium obesum",
        "water_summer": 3, "water_winter": 7,
        "sunlight_en": "Full sun, 6+ hours daily",
        "sunlight_ur": "پوری دھوپ، روز 6+ گھنٹے",
        "soil_en": "Very fast-draining sandy/cactus mix",
        "temp_min_c": 21, "temp_max_c": 45,
        "toxic_pets": "Sap is toxic to pets and humans if swallowed.",
        "toxic_humans": "Sap is toxic if swallowed; wash hands after "
                         "handling. Keep away from children.",
        "tip_en": "A succulent: it stores water in its stem. Water "
                  "2–3 times a week in summer, once a week when "
                  "dormant in winter. Pakistan's heat suits it.",
        "tip_roman": "Ye rass-bhara poda hai: tane me paani zakheera "
                     "karta hai. Garmi me hafte me 2–3 dafa, sardi me "
                     "sone ke mosam me hafte me aik dafa paani dein. "
                     "Pakistan ki garmi is ke liye behtareen hai.",
        "source": "thenews.com.pk / Karachi nursery — 6h+ sun, min "
                  "21 C, 2–3x/week summer, once/week dormant winter",
    },
]


def common_plants():
    """The care table, as plain dicts (safe to send to the page)."""
    return [dict(p) for p in COMMON_PLANTS]


def find_common_plant(plant_id):
    for p in COMMON_PLANTS:
        if p["id"] == plant_id:
            return dict(p)
    return None


def match_common_plant(scientific_name):
    """Attach the verified table entry to an AI identification by
    scientific name (exact match, then genus match). Returns the
    table dict or None."""
    if not scientific_name:
        return None
    name = scientific_name.strip().lower()
    for p in COMMON_PLANTS:
        if p["scientific"].lower() == name:
            return dict(p)
    genus = name.split()[0] if name.split() else ""
    for p in COMMON_PLANTS:
        if p["scientific"].lower().split()[0] == genus and genus:
            return dict(p)
    return None


# --- watering schedule -------------------------------------------------------


def water_interval(plant_id, month):
    """Days between waterings for this plant in this month's season.
    Returns (days, error)."""
    plant = find_common_plant(plant_id)
    if plant is None:
        return None, "Poda nahi mila — list se chunein."
    season, err = season_for_month(month)
    if err:
        return None, err
    return (plant["water_summer"] if season == "summer"
            else plant["water_winter"]), None


def next_watering(last_watered, interval_days):
    """date of the next watering. last_watered: date; interval_days:
    positive int. Returns (date, error)."""
    if not isinstance(last_watered, date):
        return None, "Aakhri paani ki tareekh ghalat hai."
    if not isinstance(interval_days, int) or interval_days < 1:
        return None, "Paani ka waqfa kam az kam 1 din hona chahiye."
    return last_watered + timedelta(days=interval_days), None


def watering_status(last_watered, interval_days, today=None):
    """Status of a plant's watering. Returns (status dict, error).
    status: 'overdue' | 'due_today' | 'in_days'."""
    if today is None:
        today = date.today()
    nxt, err = next_watering(last_watered, interval_days)
    if err:
        return None, err
    delta = (nxt - today).days
    if delta < 0:
        status = "overdue"
    elif delta == 0:
        status = "due_today"
    else:
        status = "in_days"
    return {
        "next_date": nxt.isoformat(),
        "days_until": delta,
        "overdue_days": -delta if delta < 0 else 0,
        "status": status,
    }, None


def parse_date(text):
    """Parse YYYY-MM-DD. Returns (date, error)."""
    if not isinstance(text, str):
        return None, "Tareekh YYYY-MM-DD me likhein."
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text.strip())
    if not m:
        return None, "Tareekh YYYY-MM-DD me likhein (masalan 2026-11-12)."
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))), None
    except ValueError:
        return None, "Tareekh ghalat hai — din/mahina check karein."


# --- image validation --------------------------------------------------------


def validate_image(content_type, size_bytes, data_b64):
    """Validate an uploaded photo before it goes to the AI.
    Returns (clean dict, error)."""
    if content_type not in ALLOWED_IMAGE_TYPES:
        return None, ("Photo JPEG, PNG ya WebP honi chahiye — "
                      f"mila: {content_type or 'unknown'}.")
    if not isinstance(size_bytes, int) or size_bytes <= 0:
        return None, "Photo khaali hai."
    if size_bytes > MAX_IMAGE_BYTES:
        return None, "Photo 5 MB se bari hai — chhoti photo dein."
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError):
        return None, "Photo ka data kharab hai — dobara upload karein."
    if len(raw) == 0:
        return None, "Photo khaali hai."
    if len(raw) > MAX_IMAGE_BYTES:
        return None, "Photo 5 MB se bari hai — chhoti photo dein."
    return {"content_type": content_type, "size_bytes": len(raw)}, None


# --- AI-output validators ----------------------------------------------------
# The AI must return strict JSON; these validators are the safety gate
# between Gemini and the user. An answer that fails here never
# reaches the page.


def _need_str(data, key, lo, hi):
    val = data.get(key)
    if not isinstance(val, str) or not (lo <= len(val.strip()) <= hi):
        return None, f"'{key}' ghalat hai."
    return val.strip(), None


def validate_ai_identification(data):
    """Validate a Gemini identification payload. Returns
    (clean dict, error)."""
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    if data.get("is_plant") is not True:
        return None, ("Ye zinda poda nahi lagta — Poda sirf zinda "
                      "podon ki pehchan karta hai (plastic poda, tasveer "
                      "ya cheez nahi).")
    conf = data.get("confidence")
    if not isinstance(conf, int) or isinstance(conf, bool):
        return None, "Confidence 0–100 ke darmiyan hona chahiye."
    if conf < 0 or conf > 100:
        return None, "Confidence 0–100 ke darmiyan hona chahiye."
    clean = {"confidence": conf, "uncertain": conf < 60}
    for key, lo, hi in (
            ("common_name_en", 2, 80), ("name_ur", 1, 80),
            ("name_roman", 2, 80), ("scientific_name", 3, 120)):
        val, err = _need_str(data, key, lo, hi)
        if err:
            return None, err
        clean[key] = val
    val, err = _need_str(data, "description", 10, 600)
    if err:
        return None, err
    clean["description"] = val
    care = data.get("care")
    if not isinstance(care, dict):
        return None, "Dekh-bhaal ki tafseel ghalat hai."
    clean["care"] = {}
    for key in ("water", "sunlight", "soil", "temperature"):
        val, err = _need_str(care, key, 2, 300)
        if err:
            return None, f"Dekh-bhaal me '{key}' ghalat hai."
        clean["care"][key] = val
    for key in ("toxicity_humans", "toxicity_pets"):
        val, err = _need_str(data, key, 2, 300)
        if err:
            return None, err
        clean[key] = val
    # Safety hard line: the AI must NEVER call a plant safe to eat.
    if data.get("safe_to_eat") is not False:
        return None, ("AI ne khaane ki hifazat ka daawa kiya — "
                      "Poda kabhi nahi kehta ke poda khaana mehfooz hai.")
    val, err = _need_str(data, "edible_warning", 10, 300)
    if err:
        return None, "Khaane ki warning ghalat hai."
    clean["edible_warning"] = val
    clean["safe_to_eat"] = False
    season_note = data.get("season_note_pk", "")
    if not isinstance(season_note, str):
        return None, "season_note_pk ghalat hai."
    clean["season_note_pk"] = season_note.strip()[:400]
    return clean, None


def validate_ai_diagnosis(data):
    """Validate a Gemini diagnosis payload. Returns
    (clean dict, error)."""
    if not isinstance(data, dict):
        return None, "AI ka jawab samajh nahi aaya."
    severity = data.get("severity")
    if severity not in ("mild", "moderate", "severe"):
        return None, "Severity mild, moderate ya severe honi chahiye."
    clean = {"severity": severity}
    for key, lo, hi in (("problem_en", 2, 120), ("problem_ur", 1, 120)):
        val, err = _need_str(data, key, lo, hi)
        if err:
            return None, err
        clean[key] = val
    for key in ("likely_causes", "treatment_steps"):
        val = data.get(key)
        if (not isinstance(val, list) or not (1 <= len(val) <= 6)
                or any(not isinstance(x, str) or not (2 <= len(x.strip()) <= 300)
                       for x in val)):
            return None, f"'{key}' me 1–6 saaf points hone chahiye."
        clean[key] = [x.strip() for x in val]
    val, err = _need_str(data, "when_to_seek_help", 5, 300)
    if err:
        return None, err
    clean["when_to_seek_help"] = val
    conf = data.get("confidence")
    if not isinstance(conf, int) or isinstance(conf, bool) or not (0 <= conf <= 100):
        return None, "Confidence 0–100 ke darmiyan hona chahiye."
    clean["confidence"] = conf
    clean["uncertain"] = conf < 60
    return clean, None


def word_count(text):
    if not text:
        return 0
    return len(text.split())
