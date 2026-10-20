"""FlowStore product catalog — the 5 ready n8n automations + custom intake."""
import json
import os

# slug -> workflow JSON filename shipped inside this module
WORKFLOW_FILES = {
    "whatsapp-sales-agent": "whatsapp-sales-agent.json",
    "appointment-booking-reminders": "appointment-booking-reminders.json",
    "abandoned-cart-recovery": "abandoned-cart-recovery.json",
    "lead-capture-instant-whatsapp": "lead-capture-instant-whatsapp.json",
    "review-booster": "review-booster.json",
}

PRODUCTS = [
    {
        "slug": "whatsapp-sales-agent",
        "name": "WhatsApp Sales Agent",
        "tagline": "Your WhatsApp replies in 10 seconds, 24/7",
        "desc": "AI answers customer questions in Arabic or English around the clock, "
                "qualifies every lead and logs the hot ones while you sleep. "
                "Connects to your product catalog and order flow.",
        "for_who": "E-commerce stores, real-estate agencies, clinics",
        "setup": 200,
        "monthly": 99,
        "demo": "https://clinic-demo.fastapicloud.dev/demo",
        "demo_label": "Try the live demo",
    },
    {
        "slug": "appointment-booking-reminders",
        "name": "Appointment Booking + Reminders",
        "tagline": "Every booking confirmed, every no-show chased",
        "desc": "Patients book on WhatsApp straight into your calendar. Automatic "
                "reminders 24h and 2h before, plus no-show follow-up — cut empty "
                "chairs by half.",
        "for_who": "Dental / derma / aesthetic clinics, salons",
        "setup": 200,
        "monthly": 99,
        "demo": "",
        "demo_label": "",
    },
    {
        "slug": "abandoned-cart-recovery",
        "name": "Abandoned Cart Recovery",
        "tagline": "Recover 10–15% of lost sales on autopilot",
        "desc": "Every dropped cart gets a WhatsApp within 1 hour (with a discount "
                "code), then once more at 24h. Works with Shopify and WooCommerce.",
        "for_who": "Online stores (Shopify / WooCommerce)",
        "setup": 200,
        "monthly": 99,
        "demo": "",
        "demo_label": "",
    },
    {
        "slug": "lead-capture-instant-whatsapp",
        "name": "Lead Capture → Instant WhatsApp",
        "tagline": "Every ad lead answered in under a minute",
        "desc": "New leads from Facebook Lead Ads get a WhatsApp in under 60 seconds, "
                "auto-qualified by budget, location and timeline — scored HOT / WARM / "
                "COLD. Hot buyers ping your phone instantly.",
        "for_who": "Real-estate agencies, clinics, course sellers",
        "setup": 200,
        "monthly": 129,
        "demo": "",
        "demo_label": "",
    },
    {
        "slug": "review-booster",
        "name": "Review Booster",
        "tagline": "Your Google rating climbs on its own",
        "desc": "Happy customers automatically receive your Google review link; "
                "unhappy ones get a private feedback form instead — bad reviews "
                "never go public.",
        "for_who": "Clinics, restaurants, hotels",
        "setup": 200,
        "monthly": 49,
        "demo": "",
        "demo_label": "",
    },
]

CUSTOM = {
    "slug": "custom",
    "name": "Custom Automation",
    "tagline": "Tell us your system — we build it for you",
    "desc": "Need something different? Describe your workflow and the tools you use. "
            "We customize one of our automations for your business within 48 hours.",
    "for_who": "Any business with a manual, repetitive process",
    "setup": 200,
    "monthly": 99,
}

SYSTEM_OPTIONS = [
    "WhatsApp Business",
    "Google Calendar",
    "Google Sheets",
    "Facebook Lead Ads",
    "Shopify",
    "WooCommerce",
    "Instagram DMs",
    "Email (Gmail)",
    "Other",
]

STATUS_LABELS = {
    "received": "Order received",
    "building": "Building your automation",
    "ready": "Ready — connect your n8n",
    "connected": "Connected — deploying",
    "live": "Live 🎉",
}

STATUS_ORDER = ["received", "building", "ready", "connected", "live"]


def get_product(slug: str):
    if slug == "custom":
        return CUSTOM
    for p in PRODUCTS:
        if p["slug"] == slug:
            return p
    return None


def workflow_path(slug: str) -> str:
    """Local path of the shipped workflow JSON for a product slug."""
    fname = WORKFLOW_FILES.get(slug)
    if not fname:
        return ""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "workflows", fname)


def workflow_payload(slug: str) -> dict:
    """Sanitized payload for the n8n REST API (create workflow)."""
    path = workflow_path(slug)
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "name": raw.get("name", slug),
        "nodes": raw.get("nodes", []),
        "connections": raw.get("connections", {}),
        "settings": raw.get("settings", {}),
        "pinData": raw.get("pinData", {}),
        "active": False,
    }
