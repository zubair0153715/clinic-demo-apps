"""HTML pages for the No-Show Guard SaaS (inline, no build step)."""

LANDING_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/saas/manifest.json"><meta name="theme-color" content="#1a56db"><link rel="apple-touch-icon" href="/saas/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>No-Show Guard — Automatic WhatsApp Appointment Reminders for Clinics</title>
<meta name="description" content="Cut no-shows with automatic WhatsApp appointment reminders. 24h + 2h before every visit, patients confirm or cancel with one tap. $29-$49/month.">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{background:#0b3d2e;color:#fff;padding:56px 0}
header h1{margin:0 0 12px;font-size:2rem;line-height:1.25}
header p{margin:0 0 24px;opacity:.92;max-width:640px}
.btn{display:inline-block;background:#25d366;color:#062b1f;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin:6px 10px 6px 0}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
section{padding:36px 0;border-bottom:1px solid #eee}
h2{color:#0b3d2e;margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px}
.card b{color:#0b3d2e}
.price{font-size:1.8rem;font-weight:800;color:#0b3d2e}
footer{padding:28px 0;color:#666;font-size:.9rem}
.chat{background:#f4faf7;border-radius:12px;padding:20px;max-width:420px}
.bubble{background:#fff;border-radius:10px;padding:10px 14px;margin:8px 0;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.bubble.me{background:#d9fdd3;margin-left:40px}
.bubble small{color:#888}
</style></head><body>
<header><div class="wrap">
<h1>Empty slots are lost revenue.<br>We fill them automatically.</h1>
<p>No-Show Guard sends every patient a WhatsApp reminder 24 hours and 2 hours before their appointment. They tap <b>1</b> to confirm or <b>2</b> to cancel — your schedule updates itself.</p>
<a class="btn" href="/saas/app">Start free trial</a>
<a class="btn ghost" href="#how">How it works</a>
</div></header>
<div class="wrap">
<section id="how"><h2>How it works</h2><div class="grid">
<div class="card"><b>1. Add appointments</b><br>Add them in your dashboard in seconds — or paste a day's list. Works with any clinic.</div>
<div class="card"><b>2. Patients get WhatsApp reminders</b><br>Automatic messages 24h and 2h before, in English or Arabic, with your clinic's name.</div>
<div class="card"><b>3. They confirm or cancel</b><br>One tap. Your dashboard shows confirmed / cancelled instantly — refill cancelled slots.</div>
</div></section>
<section><h2>What the patient sees</h2>
<div class="chat">
<div class="bubble"><small>No-Show Guard • Clinic</small><br>Hello Ahmed! This is SmileCare Dental reminding you of your appointment tomorrow (Cleaning) at Sat 10:00 AM. Reply 1 to CONFIRM, 2 to CANCEL.</div>
<div class="bubble me">1</div>
<div class="bubble"><small>No-Show Guard • Clinic</small><br>✅ Confirmed! See you tomorrow at 10:00 AM.</div>
</div></section>
<section><h2>Simple pricing</h2><div class="grid">
<div class="card"><span class="price">$29</span><b>/month — Starter</b><br>Up to 200 reminders/month, 1 clinic, English + Arabic.</div>
<div class="card"><span class="price">$49</span><b>/month — Growth</b><br>Unlimited reminders, 3 staff logins, priority support.</div>
</div><p>14-day free trial. No card required. Cancel anytime.</p>
<p><a class="btn" href="/saas/app">Start free trial</a></p></section>
</div>
<footer><div class="wrap">No-Show Guard — by Zubair Ahmed. Questions? <a href="https://wa.me/923116925020">WhatsApp us</a>.</div></footer>
<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/saas/sw.js").catch(()=>{});}</script></body></html>"""


DASHBOARD_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/saas/manifest.json"><meta name="theme-color" content="#1a56db"><link rel="apple-touch-icon" href="/saas/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>No-Show Guard — Clinic Dashboard</title>
<style>
:root{--green:#0b3d2e;--wa:#25d366}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;background:#f6f8f7}
header{background:var(--green);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
header b{font-size:1.1rem}
.wrap{max-width:1000px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
h2{margin:0 0 12px;color:var(--green);font-size:1.15rem}
input,select,textarea{width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:8px;font-size:1rem;box-sizing:border-box}
button{background:var(--green);color:#fff;border:0;padding:10px 18px;border-radius:8px;font-size:1rem;cursor:pointer;margin:6px 6px 6px 0}
button.wa{background:var(--wa);color:#062b1f;font-weight:700}
button.danger{background:#c0392b}
button.small{padding:6px 10px;font-size:.85rem}
table{width:100%;border-collapse:collapse;font-size:.95rem}
td,th{text-align:left;padding:10px 8px;border-bottom:1px solid #eee}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:600}
.scheduled{background:#e3f2fd;color:#1565c0}.reminder_sent{background:#fff3e0;color:#e65100}
.confirmed{background:#e8f5e9;color:#2e7d32}.cancelled{background:#fce4ec;color:#c62828}
.completed{background:#f3e5f5;color:#6a1b9a}.no_show{background:#efebe9;color:#4e342e}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tabs button{background:#e0e0e0;color:#333}
.tabs button.on{background:var(--green);color:#fff}
.hidden{display:none}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.stat{background:#f4faf7;border-radius:10px;padding:14px;text-align:center}
.stat b{font-size:1.5rem;color:var(--green);display:block}
.note{background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:12px;margin-bottom:16px;font-size:.9rem}
#auth{max-width:420px;margin:60px auto}
.row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1;min-width:140px}
.msg{font-size:.85rem;color:#555;border-bottom:1px solid #f0f0f0;padding:6px 0}
</style></head><body>
<header><b>🔔 No-Show Guard</b><span id="hdr-user"></span></header>
<div class="wrap">

<div id="auth"><div class="card">
<h2 id="auth-title">Clinic login</h2>
<input id="a-name" placeholder="Clinic name (signup only)">
<input id="a-email" placeholder="Email" type="email">
<input id="a-pass" placeholder="Password (min 8 chars)" type="password">
<button onclick="doAuth('login')">Log in</button>
<button class="wa" onclick="doAuth('signup')">Create free account</button>
<p id="auth-err" style="color:#c0392b"></p>
<p style="font-size:.85rem;color:#666">14-day free trial • no card required</p>
</div></div>

<div id="app" class="hidden">
<div id="demo-note" class="note hidden"></div>
<div class="tabs">
<button class="on" onclick="tab('dash')">📅 Appointments</button>
<button onclick="tab('add')">➕ Add appointment</button>
<button onclick="tab('stats')">📊 Stats &amp; log</button>
<button onclick="tab('settings')">⚙️ Settings</button>
<button onclick="logout()" style="margin-left:auto">Logout</button>
</div>

<div id="t-dash" class="card"><h2>Upcoming appointments</h2><div id="appt-list"></div></div>

<div id="t-add" class="card hidden"><h2>Add appointment</h2>
<div class="row">
<input id="f-name" placeholder="Patient name *">
<input id="f-phone" placeholder="Patient WhatsApp (e.g. +971501234567) *">
</div><div class="row">
<input id="f-when" type="datetime-local">
<input id="f-treatment" placeholder="Treatment (e.g. Cleaning)">
</div><div class="row">
<select id="f-lang"><option value="en">English reminder</option><option value="ar">Arabic reminder / تذكير عربي</option></select>
</div>
<button class="wa" onclick="addAppt()">Add appointment</button>
<p id="add-err" style="color:#c0392b"></p></div>

<div id="t-stats" class="card hidden"><h2>Stats</h2><div class="stat-grid" id="stat-grid"></div>
<h2 style="margin-top:18px">Recent reminder log</h2><div id="msg-log"></div></div>

<div id="t-settings" class="card hidden"><h2>Clinic settings</h2>
<input id="s-name" placeholder="Clinic name">
<input id="s-wa" placeholder="Clinic WhatsApp number (for patient replies)">
<div class="row"><select id="s-lang"><option value="en">English</option><option value="ar">Arabic / العربية</option></select>
<input id="s-tz" placeholder="Timezone (e.g. Asia/Dubai)"></div>
<input id="s-hours" placeholder='Reminder hours, e.g. [24, 2]'>
<textarea id="s-t24" rows="3" placeholder="Custom 24h template (blank = default). Use {patient} {clinic} {treatment} {time}"></textarea>
<textarea id="s-t2" rows="3" placeholder="Custom 2h template (blank = default)."></textarea>
<button onclick="saveSettings()">Save settings</button>
<p id="set-ok" style="color:#2e7d32"></p></div>
</div>
</div>

<script>
const $=id=>document.getElementById(id);
let ME=null;
async function api(p,m,b){const r=await fetch(p,{method:m||'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});const j=await r.json();if(!r.ok)throw new Error(j.detail||'error');return j}
async function boot(){try{const d=await api('/saas/api/me');ME=d.clinic;showApp();}catch(e){$('auth').classList.remove('hidden')}}
function showApp(){$('auth').classList.add('hidden');$('app').classList.remove('hidden');$('hdr-user').textContent=ME.name;
 api('/saas/api/me').then(d=>{if(d.whatsapp.provider==='demo'){$('demo-note').classList.remove('hidden');$('demo-note').innerHTML='⚠️ <b>Demo mode:</b> reminders are simulated (logged, not sent on WhatsApp). Connect the WhatsApp Business API to go live.'}});
 loadAppts();}
async function doAuth(mode){$('auth-err').textContent='';try{const d=await api('/saas/api/'+mode,{},{name:$('a-name').value,email:$('a-email').value,password:$('a-pass').value});ME=d.clinic;showApp()}catch(e){$('auth-err').textContent=e.message==='email_taken'?'This email is already registered — log in instead.':e.message==='password_short'?'Password must be at least 8 characters.':e.message==='invalid_credentials'?'Wrong email or password.':e.message}}
async function logout(){await api('/saas/api/logout','POST');location.reload()}
function tab(t){['dash','add','stats','settings'].forEach(x=>$('t-'+x).classList.add('hidden'));$('t-'+t).classList.remove('hidden');
 document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));event.target.classList.add('on');
 if(t==='stats')loadStats();if(t==='settings')loadSettings()}
const BADGES={scheduled:'Scheduled',reminder_sent:'Reminder sent',confirmed:'Confirmed ✅',cancelled:'Cancelled ❌',completed:'Completed',no_show:'No-show'};
async function loadAppts(){const d=await api('/saas/api/appointments');const now=new Date();
 let h='<table><tr><th>Patient</th><th>When</th><th>Treatment</th><th>Status</th><th></th></tr>';
 const upcoming=d.appointments.filter(a=>new Date(a.appointment_at)>=now||['scheduled','reminder_sent'].includes(a.status));
 if(!upcoming.length)h+='<tr><td colspan=5 style="color:#888">No upcoming appointments. Add your first one 👆</td></tr>';
 for(const a of upcoming){const when=new Date(a.appointment_at).toLocaleString();
  h+='<tr><td><b>'+esc(a.patient_name)+'</b><br><small>'+esc(a.patient_phone)+'</small></td><td>'+when+'</td><td>'+esc(a.treatment||'—')+'</td><td><span class="badge '+a.status+'">'+(BADGES[a.status]||a.status)+'</span></td><td>';
  if(['scheduled','reminder_sent'].includes(a.status)){h+='<button class="small" onclick="simReply('+a.id+',\'1\')">Simulate: patient confirms</button><button class="small" onclick="simReply('+a.id+',\'2\')">Simulate: cancels</button>';}
  h+='<button class="small danger" onclick="delAppt('+a.id+')">Delete</button></td></tr>'}
 $('appt-list').innerHTML=h+'</table>'}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function addAppt(){$('add-err').textContent='';try{const iso=new Date($('f-when').value).toISOString();
 await api('/saas/api/appointments','POST',{patient_name:$('f-name').value,patient_phone:$('f-phone').value,appointment_at:iso,treatment:$('f-treatment').value,language:$('f-lang').value});
 $('f-name').value=$('f-phone').value=$('f-treatment').value='';tab('dash');loadAppts()}catch(e){$('add-err').textContent=e.message}}
async function delAppt(id){if(confirm('Delete this appointment?')){await api('/saas/api/appointments/'+id,'DELETE');loadAppts()}}
async function simReply(id,text){const r=await api('/saas/api/simulate-reply','POST',{appointment_id:id,text});
 alert(r.intent==='unknown'?'Reply not understood (try 1 or 2).':('Patient '+(r.status||r.intent)+(r.matched?' — appointment updated ✅':'')));loadAppts()}
async function loadStats(){const d=await api('/saas/api/stats');
 $('stat-grid').innerHTML='<div class="stat"><b>'+d.upcoming+'</b>upcoming</div><div class="stat"><b>'+d.reminders_sent+'</b>reminders sent</div><div class="stat"><b>'+(d.by_status.confirmed||0)+'</b>confirmed</div><div class="stat"><b>'+(d.by_status.cancelled||0)+'</b>cancelled</div>';
 let h='';for(const m of d.recent_messages){h+='<div class="msg"><b>'+(m.direction==='out'?'📤 Reminder':'📥 Reply')+'</b> '+(m.patient_name||'')+' <small>'+new Date(m.created_at*1000).toLocaleString()+'</small><br>'+esc(m.body).slice(0,160)+(m.status==='simulated'?' <i>(simulated)</i>':'')+'</div>'}
 $('msg-log').innerHTML=h||'<p style="color:#888">No reminders sent yet.</p>'}
async function loadSettings(){const d=await api('/saas/api/me');const c=d.clinic;
 $('s-name').value=c.name||'';$('s-wa').value=c.whatsapp_number||'';$('s-lang').value=c.language||'en';
 $('s-tz').value=c.timezone||'Asia/Dubai';$('s-hours').value=c.reminder_hours||'[24, 2]';
 $('s-t24').value=c.template_24h||'';$('s-t2').value=c.template_2h||''}
async function saveSettings(){$('set-ok').textContent='';try{await api('/saas/api/settings','POST',{name:$('s-name').value,whatsapp_number:$('s-wa').value,language:$('s-lang').value,timezone:$('s-tz').value,reminder_hours:$('s-hours').value,template_24h:$('s-t24').value,template_2h:$('s-t2').value});$('set-ok').textContent='Saved ✅'}catch(e){$('set-ok').textContent='Error: '+e.message}}
boot();
</script><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/saas/sw.js").catch(()=>{});}</script></body></html>"""
