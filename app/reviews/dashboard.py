"""HTML pages for Review Booster (inline, no build step)."""

LANDING_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/reviews/manifest.json"><meta name="theme-color" content="#d97706"><link rel="apple-touch-icon" href="/reviews/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review Booster — Turn Happy Patients into 5-Star Google Reviews</title>
<meta name="description" content="Automatically ask every patient for a 1-5 rating after their visit. Happy patients get your Google review link; unhappy ones give private feedback first. $19-$39/month.">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{background:#7c4d00;color:#fff;padding:56px 0}
header h1{margin:0 0 12px;font-size:2rem;line-height:1.25}
header p{margin:0 0 24px;opacity:.92;max-width:640px}
.btn{display:inline-block;background:#ffc107;color:#3d2b00;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin:6px 10px 6px 0}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
section{padding:36px 0;border-bottom:1px solid #eee}
h2{color:#7c4d00;margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px}
.card b{color:#7c4d00}
.price{font-size:1.8rem;font-weight:800;color:#7c4d00}
footer{padding:28px 0;color:#666;font-size:.9rem}
.chat{background:#fff8e1;border-radius:12px;padding:20px;max-width:420px}
.bubble{background:#fff;border-radius:10px;padding:10px 14px;margin:8px 0;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.bubble.me{background:#d9fdd3;margin-left:40px}
.bubble small{color:#888}
.stars{color:#f5a623;font-size:1.3rem}
</style></head><body>
<header><div class="wrap">
<h1>Your happiest patients are silent.<br>Make them loud.</h1>
<p>Review Booster texts every patient after their visit and asks for a 1–5 rating. Ratings of 4–5 get your Google review link automatically. Ratings of 1–3 are deflected into <b>private</b> feedback — so problems reach you, not Google.</p>
<a class="btn" href="/reviews/app">Start free trial</a>
<a class="btn ghost" href="#how">How it works</a>
</div></header>
<div class="wrap">
<section id="how"><h2>How it works</h2><div class="grid">
<div class="card"><b>1. Visit ends</b><br>When an appointment is marked completed (or 2 hours pass), the patient gets a WhatsApp rating request — in English or Arabic.</div>
<div class="card"><b>2. Happy → Google</b><br>Patients rating 4–5 instantly receive your Google review link. One tap, review done.</div>
<div class="card"><b>3. Unhappy → private</b><br>Ratings of 1–3 are asked for private feedback instead. You see an alert on your dashboard and can fix it before it becomes a 1-star review.</div>
</div></section>
<section><h2>What the patient sees</h2>
<div class="chat">
<div class="bubble"><small>Review Booster • Clinic</small><br>How was your visit to SmileCare Dental? ⭐<br>Reply with a rating from 1 to 5</div>
<div class="bubble me">5</div>
<div class="bubble"><small>Review Booster • Clinic</small><br>Thank you! <span class="stars">⭐⭐⭐⭐⭐</span><br>Please share your experience on Google — it helps other patients find us:<br><i>[your Google review link]</i></div>
</div></section>
<section><h2>Simple pricing</h2><div class="grid">
<div class="card"><span class="price">$19</span><b>/month — Basic</b><br>Up to 200 review requests/month, 1 clinic, English + Arabic.</div>
<div class="card"><span class="price">$39</span><b>/month — Pro</b><br>Unlimited requests, multi-location, private-feedback alerts, priority support.</div>
</div><p>14-day free trial. No card required. Works with the same login as No-Show Guard.</p>
<p><a class="btn" href="/reviews/app">Start free trial</a></p></section>
</div>
<footer><div class="wrap">Review Booster — by Zubair Ahmed. Questions? <a href="https://wa.me/923116925020">WhatsApp us</a>.</div></footer>
<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/reviews/sw.js").catch(()=>{});}</script></body></html>"""


APP_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/reviews/manifest.json"><meta name="theme-color" content="#d97706"><link rel="apple-touch-icon" href="/reviews/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Review Booster — Dashboard</title>
<style>
:root{--gold:#7c4d00;--wa:#25d366}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;background:#faf8f3}
header{background:var(--gold);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
header b{font-size:1.1rem}
.wrap{max-width:1000px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
h2{margin:0 0 12px;color:var(--gold);font-size:1.15rem}
input,select,textarea{width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:8px;font-size:1rem;box-sizing:border-box}
button{background:var(--gold);color:#fff;border:0;padding:10px 18px;border-radius:8px;font-size:1rem;cursor:pointer;margin:6px 6px 6px 0}
button.wa{background:var(--wa);color:#062b1f;font-weight:700}
button.small{padding:6px 10px;font-size:.85rem}
button.danger{background:#c0392b}
table{width:100%;border-collapse:collapse;font-size:.95rem}
td,th{text-align:left;padding:10px 8px;border-bottom:1px solid #eee}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tabs button{background:#e0e0e0;color:#333}
.tabs button.on{background:var(--gold);color:#fff}
.hidden{display:none}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px}
.stat{background:#fff8e1;border-radius:10px;padding:14px;text-align:center}
.stat b{font-size:1.5rem;color:var(--gold);display:block}
.note{background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:12px;margin-bottom:16px;font-size:.9rem}
.alert{background:#fce4ec;border:1px solid #f8bbd0;border-radius:10px;padding:12px;margin-bottom:16px;font-size:.9rem}
#auth{max-width:420px;margin:60px auto}
.stars{color:#f5a623}
.fb{border-bottom:1px solid #f0f0f0;padding:10px 0;font-size:.95rem}
.fb small{color:#888}
</style></head><body>
<header><b>⭐ Review Booster</b><span id="hdr-user"></span></header>
<div class="wrap">

<div id="auth"><div class="card">
<h2 id="auth-title">Clinic login</h2>
<input id="a-name" placeholder="Clinic name (signup only)">
<input id="a-email" placeholder="Email" type="email">
<input id="a-pass" placeholder="Password (min 8 chars)" type="password">
<button onclick="doAuth('login')">Log in</button>
<button class="wa" onclick="doAuth('signup')">Create free account</button>
<p id="auth-err" style="color:#c0392b"></p>
<p style="font-size:.85rem;color:#666">Same account as No-Show Guard works here too. 14-day free trial.</p>
</div></div>

<div id="app" class="hidden">
<div id="demo-note" class="note hidden"></div>
<div class="tabs">
<button class="on" onclick="tab('dash')">📊 Overview</button>
<button onclick="tab('fb')">💬 Private feedback</button>
<button onclick="tab('send')">📤 Send requests</button>
<button onclick="tab('settings')">⚙️ Settings</button>
<button onclick="logout()" style="margin-left:auto">Logout</button>
</div>

<div id="t-dash" class="card"><h2>Overview</h2><div class="stat-grid" id="stat-grid"></div>
<h2 style="margin-top:18px">Recent requests</h2><div id="req-list"></div></div>

<div id="t-fb" class="card hidden"><h2>Private feedback (ratings 1–3)</h2>
<div id="low-alert"></div><div id="fb-list"></div></div>

<div id="t-send" class="card hidden"><h2>Send review requests</h2>
<p style="color:#666;font-size:.9rem">Completed appointments (or 2h past) without a request yet. Requests also go out automatically.</p>
<div id="elig-list"></div>
<h2 style="margin-top:16px">Simulate a patient reply (demo)</h2>
<div class="row" style="display:flex;gap:10px;flex-wrap:wrap">
<input id="sim-phone" placeholder="Patient phone" style="flex:1;min-width:160px">
<input id="sim-text" placeholder="Reply text, e.g. 5" style="flex:1;min-width:120px">
<button class="small" onclick="simReply()">Send</button></div>
<p id="sim-out" style="font-size:.9rem"></p></div>

<div id="t-settings" class="card hidden"><h2>Settings</h2>
<label style="font-size:.9rem;color:#555">Google review link (sent to patients who rate 4–5)</label>
<input id="s-link" placeholder="https://g.page/r/... (your Google review link)">
<button onclick="saveSettings()">Save</button>
<p id="set-ok" style="color:#2e7d32"></p>
<p style="font-size:.85rem;color:#666">Find it: Google Business Profile → Ask for reviews → copy the link.</p></div>
</div>
</div>

<script>
const $=id=>document.getElementById(id);
let ME=null;
async function api(p,m,b){const r=await fetch(p,{method:m||'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});const j=await r.json();if(!r.ok)throw new Error(j.detail||'error');return j}
async function boot(){try{const d=await api('/reviews/api/me');ME=d.clinic;showApp();}catch(e){$('auth').classList.remove('hidden')}}
function showApp(){$('auth').classList.add('hidden');$('app').classList.remove('hidden');$('hdr-user').textContent=ME.name;
 api('/reviews/api/me').then(d=>{if(d.whatsapp.provider==='demo'){$('demo-note').classList.remove('hidden');$('demo-note').innerHTML='⚠️ <b>Demo mode:</b> messages are simulated (logged, not sent on WhatsApp). Connect the WhatsApp Business API to go live.'}});
 loadStats();loadFeedback();}
async function doAuth(mode){$('auth-err').textContent='';try{const d=await api('/reviews/api/'+mode,{},{name:$('a-name').value,email:$('a-email').value,password:$('a-pass').value});ME=d.clinic;showApp()}catch(e){$('auth-err').textContent=e.message==='email_taken'?'This email is already registered — log in instead.':e.message==='password_short'?'Password must be at least 8 characters.':e.message==='invalid_credentials'?'Wrong email or password.':e.message}}
async function logout(){await api('/reviews/api/logout','POST');location.reload()}
function tab(t){['dash','fb','send','settings'].forEach(x=>$('t-'+x).classList.add('hidden'));$('t-'+t).classList.remove('hidden');
 document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));event.target.classList.add('on');
 if(t==='dash')loadStats();if(t==='fb')loadFeedback();if(t==='send')loadEligible();if(t==='settings')loadSettings()}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function stars(n){return n?'<span class="stars">'+'★'.repeat(n)+'☆'.repeat(5-n)+'</span>':'—'}
async function loadStats(){const d=await api('/reviews/api/stats');
 $('stat-grid').innerHTML='<div class="stat"><b>'+d.total_requests+'</b>requests sent</div>'
 +'<div class="stat"><b>'+d.response_rate+'%</b>response rate</div>'
 +'<div class="stat"><b>'+(d.avg_rating??'—')+'</b>avg rating</div>'
 +'<div class="stat"><b>'+d.low_alerts+'</b>low ratings (1–3)</div>';
 const r=await api('/reviews/api/requests');
 let h='<table><tr><th>Patient</th><th>Rating</th><th>Status</th><th>Sent</th></tr>';
 for(const q of r.requests.slice(0,20)){h+='<tr><td><b>'+esc(q.patient_name)+'</b><br><small>'+esc(q.patient_phone)+'</small></td><td>'+stars(q.rating)+'</td><td>'+esc(q.status)+'</td><td><small>'+new Date(q.sent_at*1000).toLocaleString()+'</small></td></tr>'}
 $('req-list').innerHTML=h+'</table>'||'<p>No requests yet.</p>'}
async function loadFeedback(){const d=await api('/reviews/api/feedback');
 const low=d.feedback.filter(f=>(f.rating||0)<=3);
 $('low-alert').innerHTML=low.length?'<div class="alert">⚠️ <b>'+low.length+'</b> unhappy patient(s) need attention — reply to them before this becomes a public review.</div>':'';
 $('fb-list').innerHTML=d.feedback.length?d.feedback.map(f=>'<div class="fb">'+stars(f.rating)+' <b>'+esc(f.patient_name||'')+'</b> <small>'+esc(f.patient_phone||'')+' • '+new Date(f.created_at*1000).toLocaleString()+'</small><br>'+esc(f.text||'(rating only)')+'</div>').join(''):'<p style="color:#888">No private feedback yet. Good news! 🎉</p>'}
async function loadEligible(){const d=await api('/reviews/api/eligible');
 $('elig-list').innerHTML=d.appointments.length?'<table><tr><th>Patient</th><th>When</th><th>Status</th><th></th></tr>'+d.appointments.map(a=>'<tr><td><b>'+esc(a.patient_name)+'</b><br><small>'+esc(a.patient_phone)+'</small></td><td><small>'+new Date(a.appointment_at).toLocaleString()+'</small></td><td>'+esc(a.status)+'</td><td><button class="small wa" onclick="sendNow('+a.id+')">Send request</button></td></tr>').join('')+'</table>':'<p style="color:#888">Nothing to send — mark appointments completed in No-Show Guard first.</p>'}
async function sendNow(id){await api('/reviews/api/send-now','POST',{appointment_id:id});alert('Review request sent ✅');loadEligible();loadStats()}
async function simReply(){const r=await api('/reviews/api/simulate-reply','POST',{phone:$('sim-phone').value,text:$('sim-text').value});
 $('sim-out').textContent='Handled ✅ '+(r.rating?('rating: '+r.rating):(r.feedback?'feedback saved':''));loadStats();loadFeedback()}
async function loadSettings(){const d=await api('/reviews/api/me');$('s-link').value=d.clinic.google_review_link||''}
async function saveSettings(){$('set-ok').textContent='';try{await api('/reviews/api/settings','POST',{google_review_link:$('s-link').value});$('set-ok').textContent='Saved ✅'}catch(e){$('set-ok').textContent='Error: '+e.message}}
boot();
</script><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/reviews/sw.js").catch(()=>{});}</script></body></html>"""
