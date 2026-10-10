"""HTML pages for Lead Qualifier (inline, no build step)."""

LANDING_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/leads/manifest.json"><meta name="theme-color" content="#047857"><link rel="apple-touch-icon" href="/leads/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lead Qualifier — WhatsApp Lead Qualification for Gulf Real Estate</title>
<meta name="description" content="Every WhatsApp inquiry gets auto-qualified: buy/rent, budget, location, bedrooms, timeline. HOT leads trigger an instant alert to your phone. $49-$99/month. English & Arabic.">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{background:#123a6d;color:#fff;padding:56px 0}
header h1{margin:0 0 12px;font-size:2rem;line-height:1.25}
header p{margin:0 0 24px;opacity:.92;max-width:640px}
.btn{display:inline-block;background:#25d366;color:#062b1f;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin:6px 10px 6px 0}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
section{padding:36px 0;border-bottom:1px solid #eee}
h2{color:#123a6d;margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px}
.card b{color:#123a6d}
.price{font-size:1.8rem;font-weight:800;color:#123a6d}
footer{padding:28px 0;color:#666;font-size:.9rem}
.chat{background:#eef4fb;border-radius:12px;padding:20px;max-width:420px}
.bubble{background:#fff;border-radius:10px;padding:10px 14px;margin:8px 0;box-shadow:0 1px 2px rgba(0,0,0,.08)}
.bubble.me{background:#d9fdd3;margin-left:40px}
.bubble small{color:#888}
.pipe{display:flex;gap:10px;flex-wrap:wrap}
.pcol{flex:1;min-width:150px;border-radius:10px;padding:12px}
.hot{background:#fce4ec}.warm{background:#fff8e1}.cold{background:#e3f2fd}
.pcol b{display:block;margin-bottom:6px}
</style></head><body>
<header><div class="wrap">
<h1>Every inquiry answered.<br>Only the serious ones reach you.</h1>
<p>Lead Qualifier chats with every WhatsApp inquiry in English &amp; Arabic — buy or rent, budget, location, bedrooms, timeline — then scores them <b>HOT / WARM / COLD</b>. HOT leads trigger an instant alert to your phone with the full summary.</p>
<a class="btn" href="/leads/app">Start free trial</a>
<a class="btn ghost" href="#how">How it works</a>
</div></header>
<div class="wrap">
<section id="how"><h2>How it works</h2><div class="grid">
<div class="card"><b>1. Inquiry arrives</b><br>A buyer messages your WhatsApp — from Property Finder, Bayut, Instagram, anywhere.</div>
<div class="card"><b>2. AI qualifies</b><br>Automatic conversation: buy/rent → budget → location → bedrooms → timeline. In English or Arabic.</div>
<div class="card"><b>3. You get HOT alerts</b><br>Serious buyers trigger an instant WhatsApp alert with their full summary. Browsers stay in the pipeline — your phone stays quiet.</div>
</div></section>
<section><h2>What the buyer sees</h2>
<div class="chat">
<div class="bubble"><small>Lead Qualifier • Agency</small><br>Hello! 👋 Thanks for contacting Marina Homes. Are you looking to <b>BUY</b> or <b>RENT</b>?</div>
<div class="bubble me">Buy</div>
<div class="bubble"><small>Lead Qualifier • Agency</small><br>What's your approximate budget? (e.g. 500K AED)</div>
<div class="bubble me">800K</div>
<div class="bubble"><small>Lead Qualifier • Agency</small><br>Which area or city are you interested in? (e.g. Dubai Marina)</div>
</div>
<p style="color:#666;font-size:.9rem">…and your phone buzzes only when the lead is HOT. 🔥</p></section>
<section><h2>Simple pricing</h2><div class="grid">
<div class="card"><span class="price">$49</span><b>/month — Basic</b><br>Up to 300 qualified conversations/month, 1 agency number, English + Arabic.</div>
<div class="card"><span class="price">$99</span><b>/month — Pro</b><br>Unlimited conversations, HOT-lead instant alerts, pipeline analytics, priority support.</div>
</div><p>14-day free trial. No card required. Built for Dubai, Riyadh &amp; Jeddah agencies.</p>
<p><a class="btn" href="/leads/app">Start free trial</a></p></section>
</div>
<footer><div class="wrap">Lead Qualifier — by Zubair Ahmed. Questions? <a href="https://wa.me/923116925020">WhatsApp us</a>.</div></footer>
<script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/leads/sw.js").catch(()=>{});}</script></body></html>"""


APP_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/leads/manifest.json"><meta name="theme-color" content="#047857"><link rel="apple-touch-icon" href="/leads/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lead Qualifier — Dashboard</title>
<style>
:root{--blue:#123a6d;--wa:#25d366}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;background:#f4f7fb}
header{background:var(--blue);color:#fff;padding:14px 20px;display:flex;justify-content:space-between;align-items:center}
header b{font-size:1.1rem}
.wrap{max-width:1100px;margin:0 auto;padding:20px}
.card{background:#fff;border-radius:12px;padding:18px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
h2{margin:0 0 12px;color:var(--blue);font-size:1.15rem}
input,select{width:100%;padding:10px;margin:6px 0;border:1px solid #ddd;border-radius:8px;font-size:1rem;box-sizing:border-box}
button{background:var(--blue);color:#fff;border:0;padding:10px 18px;border-radius:8px;font-size:1rem;cursor:pointer;margin:6px 6px 6px 0}
button.wa{background:var(--wa);color:#062b1f;font-weight:700}
button.small{padding:6px 10px;font-size:.85rem}
.tabs{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
.tabs button{background:#e0e0e0;color:#333}
.tabs button.on{background:var(--blue);color:#fff}
.hidden{display:none}
.note{background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:12px;margin-bottom:16px;font-size:.9rem}
#auth{max-width:460px;margin:60px auto}
.pipe{display:flex;gap:12px;flex-wrap:wrap}
.pcol{flex:1;min-width:220px;border-radius:10px;padding:12px}
.hot{background:#fce4ec}.warm{background:#fff8e1}.cold{background:#e3f2fd}
.pcol h3{margin:0 0 8px;font-size:1rem}
.lead{background:#fff;border-radius:8px;padding:10px;margin-bottom:8px;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,.06)}
.lead small{color:#666}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.75rem;font-weight:700}
.b-hot{background:#c62828;color:#fff}.b-warm{background:#f9a825;color:#fff}.b-cold{background:#1565c0;color:#fff}
.conv{max-height:380px;overflow-y:auto;border:1px solid #eee;border-radius:10px;padding:12px;margin:10px 0;background:#fafafa}
.bubble{background:#fff;border-radius:10px;padding:8px 12px;margin:6px 0;box-shadow:0 1px 2px rgba(0,0,0,.06);max-width:85%}
.bubble.me{background:#d9fdd3;margin-left:auto}
.bubble small{color:#888}
.kv{font-size:.9rem;color:#444;margin:4px 0}
.kv b{color:var(--blue)}
</style></head><body>
<header><b>🔥 Lead Qualifier</b><span id="hdr-user"></span></header>
<div class="wrap">

<div id="auth"><div class="card">
<h2>Agency login</h2>
<input id="a-name" placeholder="Your name (signup only)">
<input id="a-agency" placeholder="Agency name (signup only)">
<div style="display:flex;gap:10px"><input id="a-email" placeholder="Email" type="email" style="flex:1">
<select id="a-city" style="flex:1"><option>Dubai</option><option>Riyadh</option><option>Jeddah</option><option>Abu Dhabi</option><option>Sharjah</option><option>Doha</option><option>Other</option></select></div>
<input id="a-pass" placeholder="Password (min 8 chars)" type="password">
<button onclick="doAuth('login')">Log in</button>
<button class="wa" onclick="doAuth('signup')">Create free account</button>
<p id="auth-err" style="color:#c0392b"></p>
<p style="font-size:.85rem;color:#666">14-day free trial • no card required</p>
</div></div>

<div id="app" class="hidden">
<div id="demo-note" class="note hidden"></div>
<div class="tabs">
<button class="on" onclick="tab('pipe')">🔥 Pipeline</button>
<button onclick="tab('sim')">💬 Simulate lead</button>
<button onclick="tab('settings')">⚙️ Settings</button>
<button onclick="logout()" style="margin-left:auto">Logout</button>
</div>

<div id="t-pipe"><div class="pipe">
<div class="pcol hot"><h3>🔥 HOT (<span id="c-hot">0</span>)</h3><div id="l-hot"></div></div>
<div class="pcol warm"><h3>🟡 WARM (<span id="c-warm">0</span>)</h3><div id="l-warm"></div></div>
<div class="pcol cold"><h3>🔵 COLD (<span id="c-cold">0</span>)</h3><div id="l-cold"></div></div>
</div>
<div id="lead-detail" class="card hidden" style="margin-top:16px"><h2 id="ld-title">Lead</h2>
<div id="ld-kv"></div><div class="conv" id="ld-conv"></div>
<div style="display:flex;gap:8px"><input id="ld-msg" placeholder="Message this lead…" style="flex:1"><button class="small wa" onclick="sendToLead()">Send</button></div>
</div></div>

<div id="t-sim" class="card hidden"><h2>Simulate an incoming WhatsApp lead (demo)</h2>
<div style="display:flex;gap:10px;flex-wrap:wrap">
<input id="sim-phone" placeholder="Lead phone, e.g. +971501234567" style="flex:1;min-width:180px">
<input id="sim-text" placeholder="Message, e.g. I want to buy a 2 bed in Marina" style="flex:2;min-width:220px">
<button class="wa" onclick="simLead()">Send as lead</button></div>
<p id="sim-out" style="font-size:.9rem"></p>
<p style="font-size:.85rem;color:#666">Tip: walk a full conversation — "buy" → "800K" → "Dubai Marina" → "2" → "this month" — and watch it turn HOT. 🔥</p></div>

<div id="t-settings" class="card hidden"><h2>Agency settings</h2>
<input id="s-agency" placeholder="Agency name">
<input id="s-wa" placeholder="Owner WhatsApp number (HOT-lead alerts go here, e.g. +971501234567)">
<div style="display:flex;gap:10px"><select id="s-city" style="flex:1"><option>Dubai</option><option>Riyadh</option><option>Jeddah</option><option>Abu Dhabi</option><option>Sharjah</option><option>Doha</option><option>Other</option></select>
<select id="s-lang" style="flex:1"><option value="en">English default</option><option value="ar">Arabic default / العربية</option></select></div>
<button onclick="saveSettings()">Save settings</button>
<p id="set-ok" style="color:#2e7d32"></p></div>
</div>
</div>

<script>
const $=id=>document.getElementById(id);
let ME=null, LEADS=[], OPEN_LEAD=null;
async function api(p,m,b){const r=await fetch(p,{method:m||'GET',headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});const j=await r.json();if(!r.ok)throw new Error(j.detail||'error');return j}
async function boot(){try{const d=await api('/leads/api/me');ME=d.agency;showApp();}catch(e){$('auth').classList.remove('hidden')}}
function showApp(){$('auth').classList.add('hidden');$('app').classList.remove('hidden');$('hdr-user').textContent=ME.agency_name||ME.name;
 api('/leads/api/me').then(d=>{if(d.whatsapp.provider==='demo'){$('demo-note').classList.remove('hidden');$('demo-note').innerHTML='⚠️ <b>Demo mode:</b> messages are simulated (logged, not sent on WhatsApp). Connect the WhatsApp Business API to go live.'}});
 loadPipe();}
async function doAuth(mode){$('auth-err').textContent='';try{const d=await api('/leads/api/'+mode,{},{name:$('a-name').value,agency_name:$('a-agency').value,email:$('a-email').value,password:$('a-pass').value,city:$('a-city').value});ME=d.agency;showApp()}catch(e){$('auth-err').textContent=e.message==='email_taken'?'This email is already registered — log in instead.':e.message==='password_short'?'Password must be at least 8 characters.':e.message}}
async function logout(){await api('/leads/api/logout','POST');location.reload()}
function tab(t){['pipe','sim','settings'].forEach(x=>$('t-'+x).classList.add('hidden'));if(t==='pipe')$('t-pipe').classList.remove('hidden');else $('t-'+t).classList.remove('hidden');
 document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));event.target.classList.add('on');
 if(t==='pipe')loadPipe();if(t==='settings')loadSettings()}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function badge(s){return '<span class="badge b-'+s+'">'+s.toUpperCase()+'</span>'}
async function loadPipe(){const d=await api('/leads/api/leads');LEADS=d.leads;
 for(const s of ['hot','warm','cold']){$('c-'+s).textContent=d.counts[s]||0;
  const ls=LEADS.filter(l=>l.score===s);
  $('l-'+s).innerHTML=ls.length?ls.map(l=>'<div class="lead" onclick="openLead('+l.id+')"><b>'+esc(l.phone)+'</b> '+badge(l.score)+'<br><small>'+esc([l.intent,l.budget,l.location].filter(Boolean).join(' • ')||'new')+'</small></div>').join(''):'<small style="color:#888">empty</small>'}}
async function openLead(id){const d=await api('/leads/api/leads/'+id);OPEN_LEAD=d.lead;
 $('lead-detail').classList.remove('hidden');$('ld-title').textContent='Lead '+esc(d.lead.phone)+' '+badge(d.lead.score);
 $('ld-kv').innerHTML=['intent','budget','location','bedrooms','timeline'].map(k=>'<div class="kv"><b>'+k+':</b> '+esc(d.lead[k]||'—')+'</div>').join('');
 $('ld-conv').innerHTML=d.messages.map(m=>'<div class="bubble'+(m.direction==='out'?' me':'')+'"><small>'+(m.direction==='out'?'Agency':'Lead')+'</small><br>'+esc(m.body)+'</div>').join('');
 $('ld-conv').scrollTop=$('ld-conv').scrollHeight;$('lead-detail').scrollIntoView({behavior:'smooth'})}
async function sendToLead(){if(!OPEN_LEAD)return;await api('/leads/api/send','POST',{lead_id:OPEN_LEAD,text:$('ld-msg').value});$('ld-msg').value='';openLead(OPEN_LEAD)}
async function simLead(){const r=await api('/leads/api/simulate','POST',{phone:$('sim-phone').value,text:$('sim-text').value});
 $('sim-out').innerHTML='Bot replied: <i>'+esc(r.reply)+'</i><br>Stage: <b>'+esc(r.stage)+'</b> • Score: '+badge(r.score);loadPipe()}
async function loadSettings(){const d=await api('/leads/api/me');const a=d.agency;
 $('s-agency').value=a.agency_name||'';$('s-wa').value=a.whatsapp_number||'';$('s-city').value=a.city||'Dubai';$('s-lang').value=a.language||'en'}
async function saveSettings(){$('set-ok').textContent='';try{await api('/leads/api/settings','POST',{agency_name:$('s-agency').value,whatsapp_number:$('s-wa').value,city:$('s-city').value,language:$('s-lang').value});$('set-ok').textContent='Saved ✅'}catch(e){$('set-ok').textContent='Error: '+e.message}}
boot();
</script><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/leads/sw.js").catch(()=>{});}</script></body></html>"""
