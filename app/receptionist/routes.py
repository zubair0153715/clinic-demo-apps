"""AI receptionist for clinics — demo + sales tool. Route: /receptionist"""
import csv
import html
import io
import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from app.receptionist import db
from app.receptionist.engine import Engine, CLINIC, SERVICE_KEYS
from app.saas import whatsapp as wa

router = APIRouter()
engine = Engine()

WHATSAPP_CTA = ("https://wa.me/923116925020?text="
                "Hi!%20I%20want%20the%2024%2F7%20AI%20receptionist%20for%20our%20clinic.")


def admin_ok(key: str) -> bool:
    expected = os.environ.get("RECEPTIONIST_ADMIN_KEY", "")
    return bool(expected) and key == expected


CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6;background:#fff}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
header{background:#0b3b36;color:#fff;padding:52px 0}
header h1{margin:0 0 10px;font-size:2rem}
header p{opacity:.92;max-width:640px;margin:0 0 22px}
.btn{display:inline-block;background:#00a884;color:#fff;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin:4px 8px 4px 0;border:0;cursor:pointer;font-size:1rem}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
.btn.dark{background:#0b3b36}
section{padding:36px 0;border-bottom:1px solid #eee}
h2{margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px;background:#fff}
.badge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.8rem;font-weight:700;color:#fff;background:#00a884}
table{border-collapse:collapse;width:100%;margin:12px 0}
td,th{border:1px solid #e5e5e5;padding:8px 10px;text-align:left;font-size:.9rem}
th{background:#f0faf7}
footer{padding:26px 0;color:#666;font-size:.9rem}
.note{background:#fff8e1;border:1px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:14px 0;font-size:.92rem}
code{background:#f4f4f4;padding:2px 6px;border-radius:6px}
"""

NAV = """<div style="background:#0b3b36;color:#fff;padding:10px 0;font-size:.95rem">
<div class="wrap" style="display:flex;justify-content:space-between;align-items:center">
<div><a href="/receptionist" style="color:#fff;text-decoration:none;margin-right:18px"><b>🏥 AI Receptionist</b></a>
<a href="/receptionist/demo" style="color:#fff;text-decoration:none;margin-right:18px">Live demo</a></div>
<div><a href="{cta}" style="color:#fff">Get this for your clinic →</a></div></div></div>""".format(cta=WHATSAPP_CTA)


# ---------------------------------------------------------------- landing --
@router.get("/receptionist", response_class=HTMLResponse)
def landing():
    body = f"""{NAV}<header><div class="wrap">
<h1>Your clinic never misses a patient again</h1>
<p>24/7 AI receptionist on WhatsApp — answers in English &amp; Arabic, books appointments
automatically, follows up missed calls in seconds, sends reminders. Setup $900, then $500/month.</p>
<a class="btn" href="/receptionist/demo">▶ Try the live demo</a>
<a class="btn ghost" href="{WHATSAPP_CTA}">Get a free 10-min demo →</a>
</div></header>
<section><div class="wrap"><h2>What it does</h2><div class="grid">
<div class="card"><b>📅 Books appointments</b><br>Full booking flow: treatment → day → time → name → phone → confirmation.</div>
<div class="card"><b>🌙 Works 24/7</b><br>After-hours questions, missed calls, holiday inquiries — answered in seconds.</div>
<div class="card"><b>🗣️ English + Arabic</b><br>Bilingual out of the box, Gulf-aware phrasing.</div>
<div class="card"><b>🔁 Reschedule &amp; cancel</b><br>Patients change plans without calling your staff.</div>
<div class="card"><b>🧑 Human handoff</b><br>Anything tricky goes to your front-desk team, flagged in the lead inbox.</div>
<div class="card"><b>📋 Lead inbox</b><br>Every booking &amp; inquiry logged with full transcript.</div>
</div></div></section>
<section><div class="wrap"><h2>Pricing</h2>
<p><b>$900</b> one-time setup (we load your treatments, prices, timings, connect WhatsApp)
+ <b>$500/month</b> all-inclusive. No per-message fees.</p>
<a class="btn dark" href="{WHATSAPP_CTA}">Talk to us on WhatsApp →</a>
</div></section>
<section><div class="wrap">
<div class="note"><b>Honest note:</b> the demo on this page <i>simulates</i> WhatsApp —
messages are processed by the same conversation engine, but nothing is sent over the
real WhatsApp network. Going live for a real clinic needs the clinic's Meta WhatsApp
Cloud API credentials (the clinic owner connects them; we never ask for passwords).</div>
</div></section>
<footer><div class="wrap">Built by Zubair's AI Automation Agency · Demo clinic: {html.escape(CLINIC["name"])}, Dubai</div></footer>"""
    return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'>"
                        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                        f"<title>24/7 AI Receptionist for Clinics</title><style>{CSS}</style></head>"
                        f"<body>{body}</body></html>")


# ------------------------------------------------------------------- demo --
DEMO_JS = r"""
const chat=document.getElementById('chat'), quickBox=document.getElementById('quick'),
      inp=document.getElementById('inp');
let sid=null, lang='en';
function tstamp(){const d=new Date();let h=d.getHours(),m=String(d.getMinutes()).padStart(2,'0');const ap=h>=12?'PM':'AM';h=h%12||12;return h+':'+m+' '+ap;}
function addMsg(text,who){const d=document.createElement('div');d.className='msg '+who;
  d.innerHTML=text.replace(/\n/g,'<br>')+'<span class="time">'+tstamp()+'</span>';
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
function typing(cb){const t=document.createElement('div');t.className='typing';
  t.innerHTML='<span></span><span></span><span></span>';chat.appendChild(t);
  chat.scrollTop=chat.scrollHeight;setTimeout(()=>{t.remove();cb();},700+Math.random()*600);}
function setQuick(labels){quickBox.innerHTML='';labels.forEach(l=>{const b=document.createElement('button');
  b.textContent=l;b.onclick=()=>send(l);quickBox.appendChild(b);});}
async function api(text){
  const r=await fetch('/receptionist/api/chat',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({session_id:sid,text:text,lang:lang})});
  return r.json();
}
async function send(text){
  text=(text||inp.value).trim(); if(!text||!sid) return;
  addMsg(text.replace(/</g,'&lt;'),'user'); inp.value='';
  typing(async()=>{const d=await api(text); lang=d.lang||lang;
    addMsg(d.reply.replace(/</g,'&lt;'),'bot'); setQuick(d.quick||[]);});
}
async function start(){
  const r=await fetch('/receptionist/api/session',{method:'POST'});
  const d=await r.json(); sid=d.session_id;
  typing(async()=>{const g=await api('__start__'); addMsg(g.reply,'bot'); setQuick(g.quick||[]);});
}
function setLang(l){lang=l;document.querySelectorAll('.langbtn').forEach(b=>b.classList.toggle('on',b.dataset.l===l));}
inp.addEventListener('keydown',e=>{if(e.key==='Enter')send();});
start();
"""

@router.get("/receptionist/demo", response_class=HTMLResponse)
def demo():
    page = """<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>AI Receptionist — Live Demo</title><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
body{background:#0b141a;display:flex;flex-direction:column;align-items:center;min-height:100vh;color:#e9edef}
.demo-note{max-width:480px;padding:14px 18px 6px;font-size:13px;color:#8696a0;text-align:center}
.demo-note b{color:#00a884}
.langrow{display:flex;gap:8px;margin:6px 0}
.langbtn{background:transparent;border:1px solid #8696a0;color:#8696a0;border-radius:16px;padding:5px 16px;font-size:13px;cursor:pointer}
.langbtn.on{border-color:#00a884;color:#00a884}
.phone{width:100%;max-width:430px;height:min(760px,calc(100vh - 150px));background:#0b141a;display:flex;flex-direction:column;border-radius:12px;overflow:hidden;margin:4px 8px 8px;box-shadow:0 8px 40px rgba(0,0,0,.5)}
.wa-header{background:#1f2c34;padding:10px 14px;display:flex;align-items:center;gap:12px}
.avatar{width:42px;height:42px;border-radius:50%;background:linear-gradient(135deg,#00a884,#008069);display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.wa-header .name{font-size:16px;font-weight:500}
.wa-header .status{font-size:12px;color:#00a884}
.chat{flex:1;overflow-y:auto;padding:16px 12px;display:flex;flex-direction:column;gap:8px}
.msg{max-width:82%;padding:8px 12px;border-radius:10px;font-size:14.5px;line-height:1.45;word-wrap:break-word;white-space:pre-wrap}
.msg.bot{background:#1f2c34;align-self:flex-start;border-top-left-radius:2px}
.msg.user{background:#005c4b;align-self:flex-end;border-top-right-radius:2px}
.msg .time{display:block;font-size:10.5px;color:#8696a0;text-align:right;margin-top:4px}
.typing{background:#1f2c34;align-self:flex-start;border-radius:10px;padding:12px 16px;display:flex;gap:5px}
.typing span{width:7px;height:7px;border-radius:50%;background:#8696a0;animation:blink 1.2s infinite}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}
@keyframes blink{0%,60%,100%{opacity:.3}30%{opacity:1}}
.quick{display:flex;gap:8px;padding:8px 12px;flex-wrap:wrap}
.quick button{background:transparent;border:1px solid #00a884;color:#00a884;border-radius:20px;padding:7px 14px;font-size:13.5px;cursor:pointer}
.inputbar{display:flex;gap:8px;padding:10px 12px;background:#1f2c34;align-items:center}
.inputbar input{flex:1;background:#2a3942;border:none;border-radius:22px;padding:11px 16px;color:#e9edef;font-size:15px;outline:none}
.inputbar button{width:44px;height:44px;border-radius:50%;border:none;background:#00a884;color:#fff;font-size:18px;cursor:pointer;flex-shrink:0}
.cta{max-width:480px;padding:8px 18px 20px;text-align:center;font-size:13px;color:#8696a0}
.cta a{color:#00a884;font-weight:600;text-decoration:none}
</style></head><body>
<div class="demo-note"><b>● LIVE DEMO</b> — This is how the 24/7 AI receptionist answers your clinic's WhatsApp.
<br>Simulated chat — no real WhatsApp messages are sent.</div>
<div class="langrow"><button class="langbtn on" data-l="en" onclick="setLang('en')">English</button>
<button class="langbtn" data-l="ar" onclick="setLang('ar')">العربية</button></div>
<div class="phone">
<div class="wa-header"><div class="avatar">🦷</div>
<div><div class="name">CLINIC_NAME</div><div class="status">online · replies instantly</div></div></div>
<div class="chat" id="chat"></div><div class="quick" id="quick"></div>
<div class="inputbar"><input id="inp" placeholder="Message" autocomplete="off">
<button onclick="send()">➤</button></div></div>
<div class="cta">Like what you see? <a href="WHATSAPP_CTA">Get this for your clinic →</a></div>
<script>DEMO_JS</script></body></html>"""
    page = page.replace("CLINIC_NAME", html.escape(CLINIC["name"]))
    page = page.replace("WHATSAPP_CTA", WHATSAPP_CTA)
    page = page.replace("DEMO_JS", DEMO_JS)
    return HTMLResponse(page)


# --------------------------------------------------------------------- api --
@router.post("/receptionist/api/session")
def api_session():
    sid = db.new_session_id()
    state = engine.new_session("en")
    db.save_session(sid, "en", state)
    return JSONResponse({"session_id": sid})


@router.post("/receptionist/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    sid = (data.get("session_id") or "").strip()
    text = (data.get("text") or "").strip()
    want_lang = (data.get("lang") or "").strip().lower()

    loaded = db.load_session(sid) if sid else None
    if not loaded:
        sid = db.new_session_id()
        state = engine.new_session("en")
    else:
        state = loaded["state"]

    if want_lang in ("en", "ar"):
        state["lang"] = want_lang

    # greeting trigger for a fresh widget open
    if text == "__start__":
        lang = state.get("lang", "en")
        reply = engine._t("greeting", lang)
        db.add_message(sid, "user", "(session started)")
        db.add_message(sid, "bot", reply)
        db.save_session(sid, lang, state)
        return JSONResponse({"reply": reply, "lang": lang, "lead_id": None,
                             "quick": ["Book appointment", "Prices", "Timings"]
                             if lang == "en" else ["احجز موعد", "الأسعار", "أوقات الدوام"]})

    db.add_message(sid, "user", text[:1000])
    reply, quick, event = engine.handle(state, text)
    lang = state.get("lang", "en")
    db.add_message(sid, "bot", reply)
    db.save_session(sid, lang, state)

    lead_id = None
    if event and event.get("type") == "lead":
        slots = event.get("slots", {})
        lead_id = db.add_lead(sid, event.get("intent", ""), slots)
        # staff notification stub — honest: goes through the provider abstraction
        # ("demo" provider logs it as simulated; "meta" would really send it)
        try:
            staff_msg = (f"🏥 New {event['intent']} lead #{lead_id}: "
                         f"{slots.get('name','')} {slots.get('phone','')} "
                         f"{slots.get('service','')} {slots.get('date','')} {slots.get('time','')}")
            wa.send_text(os.environ.get("RECEPTIONIST_STAFF_PHONE", ""),
                         staff_msg)
        except Exception:
            pass

    return JSONResponse({"reply": reply, "lang": lang, "quick": quick,
                         "lead_id": lead_id})


# ------------------------------------------------------------------- inbox --
@router.get("/receptionist/inbox", response_class=HTMLResponse)
def inbox(key: str = ""):
    if not admin_ok(key):
        return HTMLResponse("<h1>403</h1><p>Invalid key.</p>", status_code=403)
    leads = db.list_leads()
    rows = []
    for l in leads:
        svc = SERVICE_KEYS.get(l["service"], ("", l["service"] or "—", "", ""))[1]
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(l["created"]))
        rows.append(
            f"<tr><td>#{l['id']}</td><td>{html.escape(l['intent'])}</td>"
            f"<td>{html.escape(l['name'] or '—')}</td>"
            f"<td dir='ltr'>{html.escape(l['phone'] or '—')}</td>"
            f"<td>{html.escape(svc)}</td>"
            f"<td>{html.escape(l['date'] or '—')} {html.escape(l['time'] or '')}</td>"
            f"<td>{html.escape(l['status'])}</td><td>{created}</td>"
            f"<td><a href='/receptionist/inbox/transcript?key={html.escape(key)}&sid={l['session_id']}'>view</a></td></tr>")
    body = f"""{NAV}<section><div class="wrap"><h2>📋 Lead inbox <span class="badge">{len(leads)} leads</span></h2>
<p><a class="btn dark" href="/receptionist/inbox/export?key={html.escape(key)}">⬇ Export CSV</a>
<a class="btn dark" href="/receptionist/demo">Open demo</a></p>
<table><tr><th>ID</th><th>Intent</th><th>Name</th><th>Phone</th><th>Service</th>
<th>Slot</th><th>Status</th><th>Created</th><th></th></tr>{''.join(rows) or '<tr><td colspan=9>No leads yet — run the demo.</td></tr>'}</table>
</div></section>"""
    return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'>"
                        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
                        f"<title>Lead inbox</title><style>{CSS}</style></head><body>{body}</body></html>")


@router.get("/receptionist/inbox/transcript", response_class=HTMLResponse)
def inbox_transcript(key: str = "", sid: str = ""):
    if not admin_ok(key):
        return HTMLResponse("<h1>403</h1>", status_code=403)
    msgs = db.transcript(sid)
    lines = "".join(
        f"<p><b>{'🧑' if m['role']=='user' else '🤖'}</b> {html.escape(m['text'])}</p>"
        for m in msgs)
    return HTMLResponse(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
                        f"<body><div class='wrap'><h2>Transcript</h2>{lines or '<p>Empty.</p>'}"
                        f"<p><a href='/receptionist/inbox?key={html.escape(key)}'>← back</a></p>"
                        f"</div></body></html>")


@router.get("/receptionist/inbox/export")
def inbox_export(key: str = ""):
    if not admin_ok(key):
        return JSONResponse({"error": "forbidden"}, status_code=403)
    leads = db.list_leads()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "intent", "name", "phone", "service", "date", "time",
                "status", "created_utc", "session_id"])
    for l in leads:
        w.writerow([l["id"], l["intent"], l["name"], l["phone"], l["service"],
                    l["date"], l["time"], l["status"],
                    time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(l["created"])),
                    l["session_id"]])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition":
                                      "attachment; filename=receptionist-leads.csv"})
