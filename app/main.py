"""AI Receptionist for Gulf Clinics — offer page + live demo (GEO-wired)."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
import os
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response

from app.saas.routes import router as saas_router
from app.saas import reminders as nsg_reminders
from app.reviews.routes import router as reviews_router
from app.reviews import engine as reviews_engine
from app.leads.routes import router as leads_router
from app.selfcheck.routes import router as selfcheck_router
from app.study.routes import router as study_router
from app.mediscribe.routes import router as mediscribe_router
from app.discovery.routes import router as discovery_router
from app.expiry.routes import router as expiry_router
from app.pgx.routes import router as pgx_router
from app.drugsafety.routes import router as drugsafety_router
from app.iq.routes import router as iq_router
from app.style.routes import router as style_router
from app.strait_signal.routes import router as strait_signal_router
from app.apkaudit.routes import router as apkaudit_router
from app.pharma_ai.routes import router as pharma_ai_router
from app.receptionist.routes import router as receptionist_router
from app.content.routes import router as content_router
from app.hotelpms.routes import router as hotelpms_router
from app.sehatplate.routes import router as sehatplate_router
from app.flowstore.routes import router as flowstore_router
from app.bayan.routes import router as bayan_router
from app.jalsa.routes import router as jalsa_router
from app.hisab.routes import router as hisab_router
from app.tukra.routes import router as tukra_router
from app.dars.routes import router as dars_router
from app.ishtehar.routes import router as ishtehar_router
from app.quwwat.routes import router as quwwat_router
from app.ibarat.routes import router as ibarat_router
from app.ujala.routes import router as ujala_router
from app.lablink.routes import router as lablink_router
from app.stats.routes import router as stats_router
from app.strait_signal import collector as strait_signal_collector

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    t1 = asyncio.create_task(nsg_reminders.loop_forever(60))
    t2 = asyncio.create_task(reviews_engine.loop_forever(60))
    t3 = asyncio.create_task(strait_signal_collector.run_forever())
    t4 = asyncio.create_task(strait_signal_collector.detect_forever())
    yield
    t1.cancel()
    t2.cancel()
    t3.cancel()
    t4.cancel()

app = FastAPI(lifespan=lifespan)
app.include_router(saas_router)
app.include_router(reviews_router)
app.include_router(leads_router)
app.include_router(selfcheck_router)
app.include_router(study_router)
app.include_router(mediscribe_router)
app.include_router(discovery_router)
app.include_router(expiry_router)
app.include_router(pgx_router)
app.include_router(drugsafety_router)
app.include_router(iq_router)
app.include_router(style_router)
app.include_router(strait_signal_router)
app.include_router(apkaudit_router)
app.include_router(pharma_ai_router)
app.include_router(receptionist_router)
app.include_router(content_router)
app.include_router(hotelpms_router)
app.include_router(sehatplate_router)
app.include_router(flowstore_router)
app.include_router(bayan_router)
app.include_router(jalsa_router)
app.include_router(hisab_router)
app.include_router(tukra_router)
app.include_router(dars_router)
app.include_router(ishtehar_router)
app.include_router(quwwat_router)
app.include_router(ibarat_router)
app.include_router(ujala_router)
app.include_router(lablink_router)
app.include_router(stats_router)

WHATSAPP = "https://wa.me/923116925020?text=Hi!%20I%27m%20interested%20in%20the%2024%2F7%20AI%20receptionist%20for%20our%20clinic."
DEMO_URL = "https://clinic-demo.fastapicloud.dev/demo"

FAQS = [
    ("What exactly is the AI receptionist?",
     "A 24/7 virtual receptionist for your clinic that chats with patients on WhatsApp in English and Arabic. It answers common questions (prices, timings, treatments, location, insurance), books appointments directly into your schedule, follows up missed calls within seconds, and sends appointment reminders."),
    ("Does it replace my front-desk staff?",
     "No — it handles the repetitive first contact: after-hours questions, missed calls, booking requests, reminders. Your staff focus on patients in the clinic instead of the phone. Anything the AI can't answer confidently is handed to your team."),
    ("Does it work in Arabic?",
     "Yes. Every deployment is bilingual — English and Arabic — with Gulf-dialect-aware phrasing for patient messages."),
    ("How long does setup take?",
     "Typical setup is 5–7 days: we load your treatments, prices, timings, location and booking rules, connect WhatsApp, and test the full patient journey with you before going live."),
    ("What happens to patient data?",
     "Conversations are used only to serve your clinic. We don't sell data or train shared models on it. On request we can configure data-retention windows and deletion."),
    ("What does it cost?",
     "One-time setup of $900, then $500/month all-inclusive: hosting, WhatsApp, updates, and support. No per-message or per-booking fees."),
]

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>24/7 AI Receptionist for Gulf Clinics — WhatsApp Booking, Missed-Call Capture | Zubair Ahmed</title>
<meta name="description" content="Never miss a patient inquiry again. A 24/7 AI receptionist for dental, dermatology, physio and eye clinics in UAE & Saudi Arabia — WhatsApp booking, missed-call follow-up and reminders in English & Arabic.">
<meta property="og:title" content="24/7 AI Receptionist for Gulf Clinics">
<meta property="og:description" content="WhatsApp appointment booking, missed-call capture and reminders for UAE & Saudi clinics — English & Arabic. Try the live demo.">
<meta property="og:type" content="website">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{background:#0b3d2e;color:#fff;padding:56px 0}
header h1{margin:0 0 12px;font-size:2rem;line-height:1.25}
header p{margin:0 0 24px;opacity:.92;max-width:640px}
.btn{display:inline-block;background:#25d366;color:#062b1f;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin-right:10px}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
section{padding:40px 0;border-bottom:1px solid #eee}
h2{color:#0b3d2e;margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px}
.card b{color:#0b3d2e}
.price{font-size:1.6rem;font-weight:800;color:#0b3d2e}
details{margin:10px 0;border:1px solid #e5e5e5;border-radius:10px;padding:12px 16px}
summary{font-weight:600;cursor:pointer}
footer{padding:28px 0;color:#666;font-size:.9rem}
.demo{border:2px dashed #0b3d2e;border-radius:12px;padding:24px;text-align:center;background:#f4faf7}
</style>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ProfessionalService",
 "name":"24/7 AI Receptionist for Gulf Clinics",
 "description":"AI receptionist for dental, dermatology, physiotherapy and eye clinics in UAE and Saudi Arabia: WhatsApp appointment booking, missed-call capture, reminders, English & Arabic.",
 "areaServed":["United Arab Emirates","Saudi Arabia"],
 "priceRange":"$900 setup + $500/mo",
 "url":"__BASE__"}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
__FAQJSON__]}
</script>
</head><body>
<header><div class="wrap">
<h1>Your clinic's receptionist, awake 24/7.</h1>
<p>Patients message at 9pm. They call while your front desk is busy. Our AI receptionist answers instantly on WhatsApp — in English and Arabic — books the appointment, and never lets an inquiry go cold.</p>
<a class="btn" href="__WA__">Chat on WhatsApp</a>
<a class="btn ghost" href="__DEMO__">Try the live demo</a>
</div></header>
<div class="wrap">
<section><h2>What it does for your clinic</h2><div class="grid">
<div class="card"><b>💬 Instant WhatsApp replies</b><br>Prices, timings, treatments, location, insurance — answered in seconds, 24/7, in English &amp; Arabic.</div>
<div class="card"><b>📅 Automatic booking</b><br>Patients pick a treatment, day and time; the appointment is confirmed without your staff lifting a finger.</div>
<div class="card"><b>📞 Missed-call capture</b><br>Every missed call gets an instant WhatsApp follow-up — the inquiry that used to die becomes a booking.</div>
<div class="card"><b>🔔 No-show reminders</b><br>Automatic reminders that cut empty slots in your schedule.</div>
</div></section>
<section><h2>See it working</h2>
<div class="demo"><p><b>Interactive demo — "Sara", receptionist for a Dubai dental clinic.</b><br>Ask about prices, book an appointment, see the confirmation flow.</p>
<p><a class="btn" href="__DEMO__">Open the live demo</a></p></div>
</section>
<section><h2>Simple pricing</h2>
<div class="grid">
<div class="card"><span class="price">$900</span><br><b>one-time setup</b><br>Your treatments, prices, timings &amp; booking rules loaded; WhatsApp connected; full journey tested with you.</div>
<div class="card"><span class="price">$500/mo</span><br><b>all-inclusive</b><br>Hosting, WhatsApp, updates and support. No per-message or per-booking fees.</div>
</div></section>
<section><h2>Frequently asked questions</h2>
__FAQHTML__
</section>
<section><h2>Talk to us</h2>
<p>Message us on WhatsApp for a free 10-minute walkthrough — we'll show you exactly how it would work for your specialty.</p>
<p><a class="btn" href="__WA__">Chat on WhatsApp</a></p>
</section>
</div>
<footer><div class="wrap">
Built by Zubair Ahmed — AI automation for healthcare clinics in UAE &amp; Saudi Arabia.<br>
Also: <a href="https://pharmareg-ai.fastapicloud.dev">PharmaReg AI</a> — AI regulatory-compliance audits for pharma manufacturers.
</div></footer>
</body></html>"""

GUIDE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How Gulf clinics lose patients to missed calls — and how to fix it</title>
<meta name="description" content="After-hours WhatsApp inquiries and missed calls are silent patient leaks for Gulf clinics. Here's how a 24/7 AI receptionist captures them.">
<meta property="og:title" content="How Gulf clinics lose patients to missed calls">
<meta property="og:type" content="article">
<style>body{font-family:system-ui,sans-serif;margin:0;color:#1a1a1a;line-height:1.7}.wrap{max-width:760px;margin:0 auto;padding:40px 20px}h1{color:#0b3d2e}</style>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Article",
 "headline":"How Gulf clinics lose patients to missed calls — and how to fix it",
 "description":"After-hours WhatsApp inquiries and missed calls are silent patient leaks for Gulf clinics.",
 "author":{"@type":"Person","name":"Zubair Ahmed"}}
</script>
</head><body><div class="wrap">
<h1>How Gulf clinics lose patients to missed calls — and how to fix it</h1>
<p>Walk into any busy clinic in Dubai, Sharjah, Abu Dhabi, Riyadh or Jeddah at 7pm and you'll see the same scene: the front desk is closed or winding down, the phone keeps ringing, and WhatsApp inquiries sit unread until morning.</p>
<h2>1. The after-hours inquiry gap</h2>
<p>Patients research treatments — Invisalign prices, laser hair-removal costs, LASIK eligibility, physio session rates — in the evening, after work. If nobody answers within minutes, most simply message the next clinic on Google Maps.</p>
<h2>2. The missed-call black hole</h2>
<p>During working hours your receptionist is checking in a patient, and two calls go to voicemail. Few callers try twice. Each missed call was a patient who had already chosen <em>you</em> — and left.</p>
<h2>3. The no-show drain</h2>
<p>Empty slots are lost revenue you never see on a report. A simple reminder message the day before recovers a meaningful share of them.</p>
<h2>The fix: a receptionist that never sleeps</h2>
<p>A 24/7 AI receptionist answers every WhatsApp message instantly (English &amp; Arabic), books appointments automatically, follows up every missed call within seconds, and sends reminders. It doesn't replace your staff — it catches everything that currently falls through the cracks.</p>
<p><a href="__BASE__">See how it works for your clinic →</a></p>
</div></body></html>"""

LLMS = """# AI Receptionist for Gulf Clinics

> 24/7 AI receptionist for private healthcare clinics (dental, dermatology/aesthetic, physiotherapy, ophthalmology, GP) in UAE & Saudi Arabia.

## What it does
- Instant WhatsApp replies to patient questions (prices, timings, treatments, location, insurance) in English & Arabic
- Automatic appointment booking
- Missed-call follow-up within seconds
- Appointment reminders that reduce no-shows

## Pricing
- $900 one-time setup, $500/month all-inclusive

## Proof
- Live interactive demo: __DEMO__
- Guide: __BASE__/guides/missed-calls

## Contact
- WhatsApp: __WA__
- Related: PharmaReg AI (AI regulatory-compliance audits for pharma): https://pharmareg-ai.fastapicloud.dev
"""

ROBOTS = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: __BASE__/sitemap.xml
"""


def _base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base = _base(request)
    faq_html = "".join(
        f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQS
    )
    faq_json = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (json_dumps(q), json_dumps(a)) for q, a in FAQS
    )
    html = (PAGE.replace("__BASE__", base).replace("__WA__", WHATSAPP)
            .replace("__DEMO__", DEMO_URL).replace("__FAQHTML__", faq_html)
            .replace("__FAQJSON__", faq_json))
    return HTMLResponse(html)


@app.get("/guides/missed-calls", response_class=HTMLResponse)
def guide(request: Request):
    return HTMLResponse(GUIDE.replace("__BASE__", _base(request)))


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms(request: Request):
    base = _base(request)
    return PlainTextResponse(
        LLMS.replace("__BASE__", base).replace("__WA__", WHATSAPP)
            .replace("__DEMO__", DEMO_URL))


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request):
    return PlainTextResponse(ROBOTS.replace("__BASE__", _base(request)))


@app.get("/sitemap.xml")
def sitemap(request: Request):
    base = _base(request)
    xml = (f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f'<url><loc>{base}/</loc></url>'
           f'<url><loc>{base}/guides/missed-calls</loc></url>'
           f'<url><loc>{base}/demo</loc></url>'
           f'<url><loc>{base}/llms.txt</loc></url></urlset>')
    return Response(xml, media_type="application/xml")




@app.get("/demo", response_class=HTMLResponse)
def demo():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html"))

@app.get("/health")
def health():
    return {"ok": True}


def json_dumps(s: str) -> str:
    import json as _j
    return _j.dumps(s)
