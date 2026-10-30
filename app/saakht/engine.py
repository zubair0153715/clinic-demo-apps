"""Saakht engine — original free business-website builder.

Generates a standalone single-page business website (inline CSS, no
external assets) from facts the owner supplies. Nothing is invented:
services, prices and claims come only from the user's own fields.
SEO is scored by published rules, not promised. No account, no card,
no subscription, no lock-in — the owner downloads the .html file and
keeps it.
"""

import html
import json
import re

MAX_SERVICES = 12

CAPS = {
    "name": 100, "city": 80, "phone": 30, "tagline": 200,
    "about": 1000, "services": 2000, "hours": 500, "address": 200,
}

BUSINESS_TYPES = {
    "clinic": {
        "label": "Clinic",
        "tagline": "Quality healthcare, close to home.",
        "about": "{name} is a trusted clinic serving {city} with "
                 "patient-first care and clear, honest advice.",
        "services": ["General Consultation", "Lab Test Referral",
                     "Vaccination", "Health Checkup", "Follow-up Care"],
    },
    "dental": {
        "label": "Dental Clinic",
        "tagline": "Gentle, affordable dental care for the whole family.",
        "about": "{name} provides modern dental care in {city}, "
                 "with honest pricing and no unnecessary procedures.",
        "services": ["Root Canal Treatment", "Dental Implants",
                     "Teeth Whitening", "Braces", "Dental Checkup"],
    },
    "pharmacy": {
        "label": "Pharmacy",
        "tagline": "Genuine medicines, honest prices, every day.",
        "about": "{name} is a community pharmacy in {city} stocking "
                 "genuine medicines with pharmacist guidance.",
        "services": ["Prescription Medicines", "OTC Medicines",
                     "Health Supplements", "Home Delivery",
                     "Blood Pressure Check"],
    },
    "restaurant": {
        "label": "Restaurant",
        "tagline": "Fresh food, honest flavours, served with care.",
        "about": "{name} serves fresh, hygienic meals in {city} for "
                 "families, friends and takeaway.",
        "services": ["Dine-in", "Takeaway", "Home Delivery",
                     "Family Deals", "Catering"],
    },
    "salon": {
        "label": "Salon",
        "tagline": "Look your best, without the fuss.",
        "about": "{name} is a friendly salon in {city} offering "
                 "professional grooming at fair prices.",
        "services": ["Haircut", "Beard Grooming", "Facial",
                     "Hair Colour", "Bridal Package"],
    },
    "retail": {
        "label": "Store",
        "tagline": "Everyday essentials, fair prices, friendly service.",
        "about": "{name} is a local store in {city} stocking everyday "
                 "essentials and household goods.",
        "services": ["Groceries", "Household Items", "Stationery",
                     "Mobile Recharge", "Home Delivery"],
    },
    "realestate": {
        "label": "Real Estate Agency",
        "tagline": "Honest property advice, no hidden dealing.",
        "about": "{name} helps buyers, sellers and tenants across "
                 "{city} with verified property listings.",
        "services": ["Houses for Sale", "Plots for Sale",
                     "Rental Homes", "Property Valuation",
                     "Documentation Help"],
    },
    "academy": {
        "label": "Academy",
        "tagline": "Learn properly, with teachers who care.",
        "about": "{name} is a coaching academy in {city} preparing "
                 "students with small classes and regular tests.",
        "services": ["Matric Coaching", "FSc Coaching",
                     "Entry Test Preparation", "English Language",
                     "Computer Courses"],
    },
    "repair": {
        "label": "Repair Service",
        "tagline": "Fixed right the first time, at a fair price.",
        "about": "{name} provides reliable repair services in {city} "
                 "with genuine parts and a clear quote first.",
        "services": ["Mobile Repair", "Laptop Repair",
                     "Home Appliance Repair", "AC Service",
                     "Doorstep Visit"],
    },
    "gym": {
        "label": "Gym",
        "tagline": "Stronger every week, at your own pace.",
        "about": "{name} is a friendly gym in {city} with proper "
                 "equipment, trainers and flexible timings.",
        "services": ["Monthly Membership", "Personal Training",
                     "Weight Loss Program", "Muscle Building",
                     "Diet Guidance"],
    },
    "bakery": {
        "label": "Bakery",
        "tagline": "Baked fresh every morning.",
        "about": "{name} is a neighbourhood bakery in {city} baking "
                 "fresh bread, cakes and snacks daily.",
        "services": ["Fresh Bread", "Cakes", "Pastries",
                     "Birthday Cakes", "Snacks"],
    },
    "consultancy": {
        "label": "Consultancy",
        "tagline": "Clear advice, practical next steps.",
        "about": "{name} offers professional consultancy in {city} "
                 "with transparent fees and honest advice.",
        "services": ["Business Advice", "Documentation Help",
                     "Application Support", "One-on-one Consultation",
                     "Follow-up Support"],
    },
    "other": {
        "label": "Business",
        "tagline": "Quality service, honest dealing.",
        "about": "{name} is a local business serving {city} with "
                 "honest service and fair prices.",
        "services": ["Service 1", "Service 2", "Service 3"],
    },
}

THEMES = {
    "teal": {"primary": "#0b6e4f", "accent": "#e8f5f0", "dark": "#123f31"},
    "navy": {"primary": "#1d4ed8", "accent": "#eaf0fe", "dark": "#16294d"},
    "maroon": {"primary": "#9f1239", "accent": "#fdeef2", "dark": "#4a0f22"},
    "forest": {"primary": "#3f6212", "accent": "#f2f7e8", "dark": "#24330f"},
    "plum": {"primary": "#6d28d9", "accent": "#f3eefd", "dark": "#341a5e"},
    "charcoal": {"primary": "#b45309", "accent": "#fdf3e3", "dark": "#292524"},
}

HEADINGS = {
    "en": {"services": "Our Services", "about": "About Us",
           "why": "Why Choose Us", "hours": "Opening Hours",
           "contact": "Contact Us", "whatsapp": "Chat on WhatsApp",
           "call": "Call Now"},
    "roman": {"services": "Hamari Services", "about": "Hamare Bare Mein",
              "why": "Hamein Kyun Chunein", "hours": "Khulne Ke Auqaat",
              "contact": "Rabta Karein", "whatsapp": "WhatsApp Par Baat Karein",
              "call": "Call Karein"},
    "ur": {"services": "ہماری خدمات", "about": "ہمارے بارے میں",
          "why": "ہمیں کیوں چنیں", "hours": "کھلنے کے اوقات",
          "contact": "رابطہ کریں", "whatsapp": "واٹس ایپ پر بات کریں",
          "call": "کال کریں"},
}


def check_caps(data):
    """Return an error string if any field breaks a cap, else None."""
    for field, limit in CAPS.items():
        value = (data.get(field) or "")
        if len(value) > limit:
            return f"{field} is too long (max {limit} characters)."
    if not (data.get("name") or "").strip():
        return "Business name is required."
    return None


def parse_services(text):
    """One service per line. 'Name — description' or 'Name: desc'.

    A bare name becomes a service with no description. Returns a list
    of (name, description) tuples.
    """
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "—" in line:
            name, desc = line.split("—", 1)
        elif ":" in line:
            name, desc = line.split(":", 1)
        else:
            name, desc = line, ""
        name, desc = name.strip(), desc.strip()
        if name:
            out.append((name, desc))
    return out


def whatsapp_digits(phone):
    """Digits for a wa.me link. Pakistani 0-prefixed mobiles -> 92..."""
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("0"):
        digits = "92" + digits[1:]
    return digits


def seo_score(title, description, h1_count, service_count, has_contact):
    """Auditable SEO score: every point carries its rule."""
    breakdown = {
        "Title 30-60 characters": 20 if 30 <= len(title) <= 60 else 0,
        "Meta description 120-160 characters": 20 if 120 <= len(description) <= 160 else 0,
        "Exactly one H1 heading": 20 if h1_count == 1 else 0,
        "At least 3 services listed": min(service_count, 3) * 5,
        "Phone or WhatsApp contact present": 15 if has_contact else 0,
        "JSON-LD business schema included": 10,
    }
    return sum(breakdown.values()), breakdown


def build_site(data):
    """Build the standalone site. Returns a dict with html + seo."""
    btype = data.get("btype") or "other"
    spec = BUSINESS_TYPES.get(btype, BUSINESS_TYPES["other"])
    lang = data.get("language") or "en"
    if lang not in HEADINGS:
        lang = "en"
    head = HEADINGS[lang]
    theme = THEMES.get(data.get("theme") or "teal", THEMES["teal"])

    name = (data.get("name") or "").strip()
    city = (data.get("city") or "").strip()
    phone = (data.get("phone") or "").strip()
    tagline = (data.get("tagline") or "").strip() or spec["tagline"]
    about = (data.get("about") or "").strip() or spec["about"].format(
        name=name, city=city or "your city")
    services = parse_services(data.get("services") or "")
    if not services:
        services = [(s, "") for s in spec["services"]]
    if len(services) > MAX_SERVICES:
        return {"ok": False,
                "error": f"Max {MAX_SERVICES} services (you listed {len(services)})."}
    hours = [ln.strip() for ln in (data.get("hours") or "").splitlines()
             if ln.strip()]
    address = (data.get("address") or "").strip()

    title = f"{name} — {spec['label']} in {city}" if city else f"{name} — {spec['label']}"
    service_names = ", ".join(s[0] for s in services)
    description = (f"{tagline} {name} in {city} offers {service_names}."
                   if city else f"{tagline} {name} offers {service_names}.")
    if phone:
        description += f" Call or WhatsApp {phone}."
    digits = whatsapp_digits(phone)
    wa_url = f"https://wa.me/{digits}" if digits else ""

    score, breakdown = seo_score(title, description, 1, len(services),
                                 bool(phone))
    esc = html.escape
    schema = {"@context": "https://schema.org", "@type": "LocalBusiness",
              "name": name, "description": description}
    if phone:
        schema["telephone"] = phone
    if city or address:
        schema["address"] = {"@type": "PostalAddress",
                             "addressLocality": city,
                             "streetAddress": address}
    schema_json = json.dumps(schema, ensure_ascii=False)
    # Escape for safe embedding inside <script>: a raw "</script>" in a
    # business name would otherwise break out of the JSON-LD block.
    schema_json = (schema_json.replace("<", "\\u003c")
                   .replace(">", "\\u003e").replace("&", "\\u0026"))

    def service_cards():
        cards = []
        for sname, sdesc in services:
            desc_html = f"<p>{esc(sdesc)}</p>" if sdesc else ""
            cards.append(f"<div class='card'><h3>{esc(sname)}</h3>{desc_html}</div>")
        return "\n".join(cards)

    hours_html = ""
    if hours:
        items = "".join(f"<li>{esc(h)}</li>" for h in hours)
        hours_html = (f"<section><h2>{esc(head['hours'])}</h2>"
                      f"<ul>{items}</ul></section>")
    contact_bits = []
    if wa_url:
        contact_bits.append(
            f"<a class='btn' href='{wa_url}'>{esc(head['whatsapp'])}</a>")
    if phone:
        contact_bits.append(
            f"<a class='btn sec' href='tel:+{digits}'>{esc(head['call'])}: {esc(phone)}</a>")
    contact_html = " ".join(contact_bits)
    address_html = f"<p>{esc(address)}, {esc(city)}</p>" if address or city else ""
    rtl = ' dir="rtl" lang="ur"' if lang == "ur" else ' lang="en"'

    site_html = f"""<!DOCTYPE html>
<html{rtl}><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<script type="application/ld+json">{schema_json}</script>
<style>body{{font-family:system-ui,sans-serif;margin:0;color:#1a1a1a}}
header{{background:{theme['primary']};color:#fff;padding:40px 20px;text-align:center}}
header h1{{margin:0;font-size:32px}}header p{{font-size:18px}}
.btn{{display:inline-block;background:#25D366;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;margin:6px;font-weight:bold}}
.btn.sec{{background:#fff;color:{theme['primary']};border:2px solid {theme['primary']}}}
section{{max-width:760px;margin:0 auto;padding:24px 20px}}
h2{{color:{theme['dark']};border-bottom:3px solid {theme['primary']};padding-bottom:6px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.card{{background:{theme['accent']};border-radius:10px;padding:16px}}
.card h3{{margin:0 0 6px}}footer{{background:{theme['dark']};color:#fff;text-align:center;padding:20px}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}</style></head><body>
<header><h1>{esc(name)}</h1><p>{esc(tagline)}</p>{contact_html}</header>
<section><h2>{esc(head['about'])}</h2><p>{esc(about)}</p></section>
<section><h2>{esc(head['services'])}</h2><div class="grid">{service_cards()}</div></section>
<section><h2>{esc(head['why'])}</h2><ul>
<li>Local business serving {esc(city) if city else 'your area'}.</li>
<li>{len(services)} services under one roof.</li>
<li>Direct WhatsApp and phone contact — no middleman.</li>
</ul></section>
{hours_html}
<section><h2>{esc(head['contact'])}</h2>{address_html}{contact_html}</section>
<footer><p>{esc(name)} — built free with Saakht. No subscription, no lock-in.</p></footer>
</body></html>"""
    return {"ok": True, "html": site_html, "title": title,
            "description": description, "seo_score": score,
            "seo_breakdown": breakdown, "whatsapp_url": wa_url,
            "service_count": len(services)}
