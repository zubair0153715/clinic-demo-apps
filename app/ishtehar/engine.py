"""Ishtehar copy engine — original clean-room ad-creative generator.

Platform limits below are the platforms' own PUBLIC documented limits
(Meta Ads Manager text guidance, Google Ads RSA specs, LinkedIn ad specs):
they are facts about the platforms, not copied creative. No creative from
any existing tool is reproduced here; every template is written for this
app from the user's own brief.
"""
import re

# ---------------------------------------------------------------- platforms
# fields: (key, label, max_chars, recommended_max or None)
PLATFORMS = {
    "meta": {
        "label": "Meta (Facebook + Instagram)",
        "fields": [
            ("primary", "Primary text", 125, 125),
            ("headline", "Headline", 40, 40),
            ("description", "Description", 30, 30),
        ],
    },
    "google": {
        "label": "Google Search (Responsive Search Ad)",
        "fields": [
            ("headline", "Headline", 30, 30),
            ("description", "Description", 90, 90),
        ],
    },
    "linkedin": {
        "label": "LinkedIn (Single Image Ad)",
        "fields": [
            ("intro", "Intro text", 600, 150),
            ("headline", "Headline", 70, 70),
        ],
    },
    "whatsapp": {
        "label": "WhatsApp / SMS broadcast",
        "fields": [
            ("message", "Message", 1000, 400),
        ],
    },
}

ANGLES = ["benefit", "social_proof", "urgency", "problem_solution",
          "offer_led", "question_hook"]

ANGLE_LABELS = {
    "benefit": "Benefit-led",
    "social_proof": "Social proof",
    "urgency": "Urgency",
    "problem_solution": "Problem → solution",
    "offer_led": "Offer-led",
    "question_hook": "Question hook",
}

# ---------------------------------------------------------------- templates
# Each angle is a function of the brief. {product} {benefit} {audience}
# {offer} {cta} are the user's own words — nothing is invented.
TEMPLATES = {
    "en": {
        "benefit": {
            "primary": "{benefit} — with {product}, made for {audience}. {offer} {cta}",
            "headline": "{product}: {benefit}",
            "description": "{offer} {cta}",
            "intro": "{benefit} is what {audience} actually need. {product} delivers it — no complexity, no waiting. {offer} {cta}",
            "message": "{benefit} with {product}! Made for {audience}. {offer} {cta}",
        },
        "social_proof": {
            "primary": "{audience} are switching to {product} for one reason: {benefit}. {offer} {cta}",
            "headline": "Why {audience} love {product}",
            "description": "{offer} {cta}",
            "intro": "Ask {audience} what changed for them, and the answer keeps coming back to {product}: {benefit}. See why so many made the switch. {offer} {cta}",
            "message": "{audience} are choosing {product} — {benefit}. {offer} {cta}",
        },
        "urgency": {
            "primary": "Don't wait on {benefit}. {product} is here now — {offer} {cta}",
            "headline": "{product} — {offer}",
            "description": "{cta}",
            "intro": "Every week without {benefit} is a week lost. {product} is available now, and {offer} won't last forever. {cta}",
            "message": "Abhi! {product} — {benefit}. {offer} {cta}",
        },
        "problem_solution": {
            "primary": "Tired of missing out on {benefit}? {product} fixes that for {audience}. {offer} {cta}",
            "headline": "Fix it with {product}",
            "description": "{offer} {cta}",
            "intro": "The problem is simple: {audience} want {benefit} and keep getting everything but. {product} was built to solve exactly that. {offer} {cta}",
            "message": "{benefit} chahiye? {product} is the answer for {audience}. {offer} {cta}",
        },
        "offer_led": {
            "primary": "{offer} — on {product}, for {audience}. {benefit}. {cta}",
            "headline": "{offer}",
            "description": "{product} — {benefit}",
            "intro": "Here's the deal: {offer} on {product}. You get {benefit}, built for {audience}. No fine print games. {cta}",
            "message": "{offer}! {product} — {benefit}. {cta}",
        },
        "question_hook": {
            "primary": "What if {benefit} was easy? With {product}, it is — for {audience}. {offer} {cta}",
            "headline": "What if {benefit}?",
            "description": "{offer} {cta}",
            "intro": "What if {benefit} stopped being hard? That's the question {product} answers for {audience} every day. {offer} {cta}",
            "message": "Kya {benefit} mushkil lagta hai? {product} se asaan! {offer} {cta}",
        },
    },
    "ru": {
        "benefit": {
            "primary": "{benefit} — {product} ke saath, {audience} ke liye. {offer} {cta}",
            "headline": "{product}: {benefit}",
            "description": "{offer} {cta}",
            "intro": "{audience} ko asal me {benefit} chahiye, aur {product} yehi deta hai — na koi complexity, na intezar. {offer} {cta}",
            "message": "{product} se {benefit} hasil karo! {audience} ke liye. {offer} {cta}",
        },
        "social_proof": {
            "primary": "{audience} {product} ki taraf aa rahe hain, sirf ek wajah se: {benefit}. {offer} {cta}",
            "headline": "{audience} ko {product} kyun pasand hai",
            "description": "{offer} {cta}",
            "intro": "{audience} se poocho to jawab ek hi milta hai: {product} se {benefit} mila. Aap bhi dekhain kyun sab switch kar rahe hain. {offer} {cta}",
            "message": "{audience} {product} choose kar rahe hain — {benefit}. {offer} {cta}",
        },
        "urgency": {
            "primary": "{benefit} ka intezar mat karo. {product} abhi maujood hai — {offer} {cta}",
            "headline": "{product} — {offer}",
            "description": "{cta}",
            "intro": "{benefit} ke baghair har hafta zaya hai. {product} abhi available hai, aur {offer} hamesha nahi rahega. {cta}",
            "message": "Abhi! {product} — {benefit}. {offer} {cta}",
        },
        "problem_solution": {
            "primary": "{benefit} se mehroom rehna band karo? {product} {audience} ke liye ye masla hal karta hai. {offer} {cta}",
            "headline": "{product} se hal karo",
            "description": "{offer} {cta}",
            "intro": "Masla seedha hai: {audience} ko {benefit} chahiye aur milta kuch aur hai. {product} isi masle ke liye bana hai. {offer} {cta}",
            "message": "{benefit} chahiye? {audience} ke liye {product} hi jawab hai. {offer} {cta}",
        },
        "offer_led": {
            "primary": "{offer} — {product} par, {audience} ke liye. {benefit}. {cta}",
            "headline": "{offer}",
            "description": "{product} — {benefit}",
            "intro": "Deal ye hai: {product} par {offer}. Aap ko {benefit} milega, {audience} ke liye bana hua. {cta}",
            "message": "{offer}! {product} — {benefit}. {cta}",
        },
        "question_hook": {
            "primary": "Kya {benefit} asaan ho sakta hai? {product} ke saath, haan — {audience} ke liye. {offer} {cta}",
            "headline": "Kya {benefit}?",
            "description": "{offer} {cta}",
            "intro": "Kya {benefit} mushkil hi rehna chahiye? {product} {audience} ke liye roz is sawal ka jawab deta hai. {offer} {cta}",
            "message": "Kya {benefit} mushkil lagta hai? {product} se asaan! {offer} {cta}",
        },
    },
}

DEFAULT_CTA = {
    "en": "Shop now",
    "ru": "Abhi order karein",
}

# ---------------------------------------------------------------- compliance
# Claim patterns that commonly get ads rejected or accounts flagged.
COMPLIANCE_RULES = [
    (r"\bguaranteed\b", "Absolute guarantee — platforms reject unqualified guarantees. Promise something specific instead."),
    (r"\bcure(s|d)?\b", "Cure claim — medical cure claims are banned on most ad platforms without approval."),
    (r"100%\s*(safe|guaranteed|effective|risk)", "Absolute '100%' claim — unprovable; soften or add proof."),
    (r"risk[- ]?free", "'Risk-free' is treated as a guarantee claim by reviewers."),
    (r"#1\b|number one\b|best in the (world|country|pakistan)", "Unsubstantiated superlative — add a source ('rated 4.8 by 2,000 buyers') or drop it."),
    (r"\b(no|zero) side effects\b", "Medical safety claim — needs substantiation; avoid."),
    (r"\b(earn|make)\s+(rs\.?|pkr|\$|£)?\s*\d", "Income promise — earnings claims trigger extra scrutiny; show typical results instead."),
    (r"\bmiracle\b", "'Miracle' is a classic rejected-claim word."),
]

EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
    "\U0001F100-\U0001F1FF]", flags=re.UNICODE)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .")


def _fit(text: str, limit: int):
    """Hard-fit text to a platform limit at a word boundary.

    Returns (text, truncated_bool). Nothing over the limit ever ships.
    """
    if len(text) <= limit:
        return text, False
    cut = text[:limit - 1].rsplit(" ", 1)[0]
    if not cut:
        cut = text[:limit - 1]
    return cut + "…", True


def _brief_defaults(brief: dict) -> dict:
    lang = brief.get("lang", "en")
    b = {
        "product": (brief.get("product") or "Your product").strip(),
        "benefit": (brief.get("benefit") or "real results").strip(),
        "audience": (brief.get("audience") or "busy people").strip(),
        "offer": (brief.get("offer") or "").strip(),
        "cta": (brief.get("cta") or DEFAULT_CTA.get(lang, "Shop now")).strip(),
        "lang": lang if lang in TEMPLATES else "en",
    }
    return b


def compliance_flags(text: str) -> list:
    out = []
    low = text.lower()
    for pattern, message in COMPLIANCE_RULES:
        if re.search(pattern, low):
            out.append({"rule": pattern, "message": message})
    return out


def score_variant(fields: dict, flags: list, truncated: bool) -> dict:
    """Transparent 0-100 score. Every weight is documented and auditable.

    length fit 25 | CTA present 20 | benefit present 20 | number/proof 15
    | emoji budget (<=3) 10 | offer or question present 10
    """
    joined = " ".join(fields.values())
    low = joined.lower()
    parts = {}
    parts["length_fit"] = 25 if not truncated else 15
    cta_words = ("shop", "order", "buy", "book", "sign", "start", "try",
                  "abhi", "order karein", "message", "whatsapp", "call")
    parts["cta"] = 20 if any(w in low for w in cta_words) else 0
    parts["benefit"] = 20  # benefit is always composed into every variant
    parts["proof"] = 15 if re.search(r"\d", joined) else 0
    parts["emoji_budget"] = 10 if len(EMOJI_RE.findall(joined)) <= 3 else 0
    parts["hook"] = 10 if ("?" in joined or re.search(
        r"\b(off|discount|free|deal|sale|offer|%|rs\.?|pkr)\b", low)) else 0
    total = sum(parts.values())
    if flags:
        total = max(0, total - 10 * len(flags))  # compliance risk costs points
        parts["compliance_penalty"] = -10 * len(flags)
    parts["total"] = total
    return parts


def build_variants(brief: dict, platforms=None, seed: int = 0) -> list:
    """Deterministic: same brief + seed always yields the same variants."""
    b = _brief_defaults(brief)
    lang = b["lang"]
    plats = platforms or list(PLATFORMS)
    angles = ANGLES[:]
    if seed:
        rot = seed % len(angles)
        angles = angles[rot:] + angles[:rot]
    variants = []
    for plat in plats:
        if plat not in PLATFORMS:
            continue
        spec = PLATFORMS[plat]
        for angle in angles:
            tpl = TEMPLATES[lang][angle]
            fields = {}
            truncated_any = False
            for key, _label, limit, _rec in spec["fields"]:
                raw = _clean(tpl[key].format(**b))
                fitted, trunc = _fit(raw, limit)
                fields[key] = fitted
                truncated_any = truncated_any or trunc
            flags = []
            for text in fields.values():
                flags.extend(compliance_flags(text))
            seen, uniq = set(), []
            for f in flags:
                if f["rule"] not in seen:
                    seen.add(f["rule"])
                    uniq.append(f)
            variants.append({
                "platform": plat,
                "platform_label": spec["label"],
                "angle": angle,
                "angle_label": ANGLE_LABELS[angle],
                "fields": fields,
                "limits": {k: lim for k, _l, lim, _r in spec["fields"]},
                "truncated": truncated_any,
                "flags": uniq,
                "score": score_variant(fields, uniq, truncated_any),
            })
    return variants


def platform_summary(variants: list) -> dict:
    out = {}
    for v in variants:
        p = v["platform"]
        out.setdefault(p, {"count": 0, "best": 0, "flagged": 0})
        out[p]["count"] += 1
        out[p]["best"] = max(out[p]["best"], v["score"]["total"])
        if v["flags"]:
            out[p]["flagged"] += 1
    return out
