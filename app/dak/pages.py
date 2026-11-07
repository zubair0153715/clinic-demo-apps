"""Dak page — single-file HTML for the free AI email triage studio."""

DAK_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dak ڈاک — Free AI Email Triage</title>
<style>
:root{--ink:#1a2233;--mut:#5b6577;--bg:#f4f6f8;--card:#fff;--line:#dfe5ec;
--acc:#0b6e4f;--acc2:#e8f5ee;--warn:#9a6a00;--warnbg:#fff4d6;--bad:#a61c1c;--badbg:#fdecea}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
background:var(--bg);color:var(--ink);line-height:1.55}
header{background:var(--ink);color:#fff;padding:22px 16px}
header .wrap{max-width:920px;margin:0 auto}
h1{margin:0;font-size:30px}
h1 .ur{font-size:24px;opacity:.85}
.sub{opacity:.85;margin:6px 0 0;max-width:640px}
.wrap{max-width:920px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:18px;margin:14px 0}
h2{margin:0 0 8px;font-size:20px}
h3{margin:14px 0 6px;font-size:16px}
.mut{color:var(--mut);font-size:14px}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:13px;
background:var(--acc2);color:var(--acc);border:1px solid #bfe3cf}
.pill.off{background:#f1f1f1;color:var(--mut);border-color:var(--line)}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
textarea,input,select{width:100%;padding:10px;border:1px solid var(--line);
border-radius:8px;font:inherit;background:#fff}
textarea{min-height:120px;resize:vertical}
label{font-weight:600;font-size:14px;display:block;margin:10px 0 4px}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;
padding:11px 18px;font:inherit;font-weight:600;cursor:pointer}
button.ghost{background:#fff;color:var(--ink);border:1px solid var(--line)}
button:disabled{opacity:.5;cursor:default}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 0}
.tabs button{background:#fff;color:var(--ink);border:1px solid var(--line)}
.tabs button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.score{height:12px;background:#e8ecf1;border-radius:999px;overflow:hidden}
.score>i{display:block;height:100%;background:var(--acc)}
.kv{display:grid;grid-template-columns:130px 1fr;gap:4px 12px;font-size:15px}
.kv b{font-weight:600}
.flag{border:1px solid #ecd27a;background:var(--warnbg);border-radius:8px;
padding:10px 12px;margin:8px 0}
.flag.bad{border-color:#f0b4b4;background:var(--badbg)}
.flag b{color:var(--warn)}
.flag.bad b{color:var(--bad)}
.mail{border:1px solid var(--line);border-radius:10px;padding:12px;margin:10px 0;
cursor:pointer;background:#fff}
.mail:hover{border-color:var(--acc)}
.mail .subj{font-weight:700}
.mail .meta{color:var(--mut);font-size:13px}
.badge{display:inline-block;font-size:12px;padding:1px 8px;border-radius:999px;
background:#eef2f7;border:1px solid var(--line);margin-right:6px}
.badge.hot{background:#fdecea;color:var(--bad);border-color:#f0b4b4}
.badge.today{background:var(--warnbg);color:var(--warn);border-color:#ecd27a}
pre{white-space:pre-wrap;word-wrap:break-word;background:#f8fafc;border:1px solid var(--line);
border-radius:8px;padding:12px;font:inherit}
ul{margin:6px 0;padding-left:22px}
.compare{width:100%;border-collapse:collapse;font-size:14px}
.compare td,.compare th{border:1px solid var(--line);padding:8px;text-align:left}
.compare th{background:#eef2f7}
footer{color:var(--mut);font-size:13px;padding:10px 16px 30px}
.hidden{display:none}
.note{background:#eef4ff;border:1px solid #c9dcff;border-radius:8px;padding:10px 12px;
font-size:14px;margin:10px 0}
</style>
</head>
<body>
<header><div class="wrap">
<h1>Dak <span class="ur">ڈاک</span> — Free AI Email Triage</h1>
<p class="sub">Paste any email → triage, thread summary &amp; reply draft with a Safety Check.
Free forever. No account, no card, no trial, no auto-renewal. Nothing is sent by this app — ever.</p>
<div class="row" style="margin-top:10px">
<span id="aiBadge" class="pill off">AI status…</span>
<span class="pill">Rule-based triage: always on</span>
<span class="pill">Demo inbox: 8 sample emails</span>
</div>
</div></header>

<div class="wrap">
<div class="card">
<div class="row">
<label style="margin:0">Language / Zubaan:</label>
<select id="lang" style="max-width:220px">
<option value="en">English</option>
<option value="roman" selected>Roman-Urdu</option>
<option value="ur">Urdu (script)</option>
</select>
<span class="mut">Triage labels, summaries aur drafts isi zubaan mein aayenge.</span>
</div>
<div class="tabs">
<button data-tab="triage" class="on">1 · Triage karo</button>
<button data-tab="inbox">2 · Demo Inbox</button>
<button data-tab="thread">3 · Thread Summary</button>
<button data-tab="draft">4 · Draft + Safety Check</button>
</div>
</div>

<!-- TRIAGE -->
<section id="tab-triage" class="card">
<h2>Triage karo — ek email paste karein</h2>
<p class="mut">Subject aur email ka text paste karein. Rule-based triage foran chalega;
AI triage sirf tab jab server par key set ho.</p>
<label>Subject</label>
<input id="trSubject" placeholder="e.g. Interview invite — Junior Pharmacist (reply by Friday)">
<label>Email text</label>
<textarea id="trBody" placeholder="Email ka poora text yahan paste karein…"></textarea>
<div class="row" style="margin-top:12px">
<button onclick="doTriage()">Triage karo</button>
<button class="ghost" onclick="fillDemo(0)">Demo email bharo</button>
</div>
<div id="trOut" style="margin-top:14px"></div>
</section>

<!-- INBOX -->
<section id="tab-inbox" class="card hidden">
<h2>Demo Inbox — 8 sample emails</h2>
<p class="mut">Ye <b>demo</b> emails hain — asli mail nahi. Kisi par click karein to uska
triage dekhein; snooze karein to woh aapke browser mein save hoga (localStorage).</p>
<div id="inboxList">Loading…</div>
<h3>Snoozed / Follow-up (is browser mein saved)</h3>
<div id="snoozeList" class="mut">Kuch snooze nahi kiya — kisi demo email par “Snooze” dabayein.</div>
</section>

<!-- THREAD -->
<section id="tab-thread" class="card hidden">
<h2>Thread Summary — poori thread, sirf aakhri message nahi</h2>
<p class="mut">Superhuman ka auto-respond sirf aakhri message parhta hai — Dak poori
thread parhta hai: faislay, khulay sawal, aur kaun kya karega.</p>
<label>Poori thread paste karein (reply-chain samet)</label>
<textarea id="thText" style="min-height:180px" placeholder="Pehla message…&#10;&#10;On 5 Nov, … wrote:&#10;Doosra message…"></textarea>
<div class="row" style="margin-top:12px">
<button onclick="doThread()">Thread summarise karo (AI)</button>
<button class="ghost" onclick="fillDemo(7)">Demo thread bharo</button>
</div>
<div id="thOut" style="margin-top:14px"></div>
</section>

<!-- DRAFT -->
<section id="tab-draft" class="card hidden">
<h2>Draft + Safety Check — pehle check, phir bhejain</h2>
<div class="note"><b>Warning:</b> AI drafts ghalat bhi ho sakte hain — aadhi raat ki
meeting maan lena, vaada kar dena, ghalat raqam likh dena. Is liye har draft
<b>Safety Check</b> se guzarta hai, aur Dak kuch bhi <b>send nahi karta</b> — aap
draft copy kar ke khud bhejte hain.</div>
<label>Thread / email paste karein</label>
<textarea id="drThread" style="min-height:140px" placeholder="Jis email ka jawab likhna hai…"></textarea>
<div class="row">
<div style="flex:1"><label>Tone</label>
<select id="drTone"><option value="polite" selected>Polite</option>
<option value="short">Short</option><option value="firm">Firm</option></select></div>
<div style="flex:1"><label>&nbsp;</label>
<button onclick="doDraft()" style="width:100%">Draft likho (AI)</button></div>
</div>
<div id="drOut" style="margin-top:14px"></div>
<h3>Safety Check — bina AI ke bhi</h3>
<p class="mut">Apna khud ka draft yahan paste karein — Safety Check bina AI key ke bhi chalta hai.</p>
<label>Apna draft</label>
<textarea id="scDraft" style="min-height:90px" placeholder="e.g. Sure, let's meet at 2:30 AM tomorrow…"></textarea>
<div class="row" style="margin-top:12px">
<button class="ghost" onclick="doSafety()">Safety Check karo</button>
<button class="ghost" onclick="document.getElementById('scDraft').value='Sure, let\'s meet at 2:30 AM tomorrow. I agree to the terms and will pay Rs 50,000. I have attached the file.'">Trap wala draft bharo</button>
</div>
<div id="scOut" style="margin-top:14px"></div>
</section>

<div class="card">
<h2>Superhuman vs Dak — farq kya hai?</h2>
<table class="compare">
<tr><th></th><th>Superhuman Mail</th><th>Dak</th></tr>
<tr><td>Price</td><td>$30/mo (Starter) · $40/mo (Business) · no free plan, no trial</td><td><b>Free, hamesha</b> — no card, no trial</td></tr>
<tr><td>AI drafts</td><td>Auto Drafts (Business only) — aadhi raat ki meeting bhi maan lete hain</td><td>Draft + <b>Safety Check</b>, aur kuch send nahi hota</td></tr>
<tr><td>Thread</td><td>AI sirf aakhri message parhta hai</td><td><b>Poori thread</b> parhi jati hai</td></tr>
<tr><td>Providers</td><td>Gmail / Outlook only</td><td>Koi bhi — paste karo, triage pao</td></tr>
<tr><td>Offline</td><td>No offline mode</td><td>Rule-based triage + snooze <b>offline</b> chalte hain</td></tr>
<tr><td>Seekhna</td><td>Keyboard shortcuts — ek hafta lagta hai</td><td>Zero learning curve — ek click</td></tr>
<tr><td>Urdu</td><td>Nahi</td><td>English · Roman-Urdu · Urdu script</td></tr>
</table>
<p class="mut">Comparison public pricing pages aur 2026 reviews par mabni hai (Superhuman
Mail Starter $30/mo ya $25/mo annual; Business $40/mo ya $33/mo annual).
Dak Superhuman se affiliated nahi hai — yeh ek original, clean-room rebuild hai.</p>
</div>

<div class="card">
<h2>Honest limits — saaf baat</h2>
<ul>
<li>Dak email <b>client nahi hai</b>: yeh aapke inbox se connect nahi hota, mail nahi
bhejta, Gmail nahi parhta. Sirf woh text triage karta hai jo aap paste karein.
Live Gmail/Outlook connection ke liye OAuth chahiye — woh future step hai.</li>
<li>AI triage, summaries aur drafts ke liye server par GEMINI_API_KEY chahiye;
bina key ke rule-based triage, demo inbox, snooze aur Safety Check poore kaam karte hain.</li>
<li>AI drafts suggestions hain — bhejne se pehle Safety Check parhein aur khud verify karein.</li>
<li>Deadline extraction aam English/Urdu phrases samajhta hai ("by Friday", "tomorrow",
"10 Nov", "EOD"); mushkil tareekh ko "ambiguous" likha jata hai, andaza nahi lagaya jata.</li>
<li>Aapka pasted email server par save <b>nahi</b> hota; snooze sirf aapke browser mein rehta hai.</li>
</ul>
</div>
</div>

<footer><div class="wrap">
Dak — original clean-room build (Superhuman Mail gap, 7 Nov 2026). Free forever.
Koi data collect nahi hota, koi account nahi, koi card nahi.
</div></footer>

<script>
const $=id=>document.getElementById(id);
const lang=()=>$("lang").value;
let DEMO=[];
async function aiStatus(){
  try{const r=await fetch("/dak/api/ai-status");const j=await r.json();
    $("aiBadge").textContent=j.ai_available?"AI: ON (Gemini)":"AI: OFF — rule-based triage on";
    $("aiBadge").className="pill"+(j.ai_available?"":" off");
  }catch(e){$("aiBadge").textContent="AI status nahi mila — rule-based triage on";$("aiBadge").className="pill off";}
}
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{
  document.querySelectorAll(".tabs button").forEach(x=>x.classList.remove("on"));
  b.classList.add("on");
  ["triage","inbox","thread","draft"].forEach(t=>
    $("tab-"+t).classList.toggle("hidden",t!==b.dataset.tab));
  if(b.dataset.tab==="inbox") loadInbox();
});
function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function bandBadge(band){return band==="Abhi karo"?"hot":band==="Aaj"?"today":"";}
function triageCard(t,prefix){
  const dl=t.deadline?("Deadline: <b>"+esc(t.deadline)+"</b>"+(t.deadline_phrase?" ("+esc(t.deadline_phrase)+")":"")+(t.deadline_ambiguous?" — <b>ambiguous, verify karein</b>":"")):"Deadline: koi nahi mili";
  return `<div class="kv">
  <b>Priority</b><span><span class="badge ${bandBadge(t.band)}">${esc(t.band)}</span> ${t.score}/100</span>
  <b>Score</b><span><span class="score"><i style="width:${t.score}%"></i></span></span>
  <b>Category</b><span>${esc(t.category_label)}</span>
  <b>${prefix} deadline</b><span>${dl}</span>
  <b>Thread</b><span>${t.messages} message(s) · ${t.words} words · ~${t.minutes} min parhne mein</span>
  </div>`;
}
async function doTriage(){
  const out=$("trOut");out.innerHTML="Triage ho raha hai…";
  const fd=new FormData();fd.append("subject",$("trSubject").value);
  fd.append("body",$("trBody").value);fd.append("language",lang());
  const r=await fetch("/dak/api/triage",{method:"POST",body:fd});
  const j=await r.json();
  if(!j.ok){out.innerHTML=`<div class="flag bad"><b>Error:</b> ${esc(j.error)}</div>`;return;}
  let h=`<h3>Rule-based triage (hamesha chalta hai)</h3>`+triageCard(j.rule,"Rule-based");
  if(j.ai){h+=`<h3>AI triage</h3><div class="kv"><b>Category</b><span>${esc(j.ai.category)}</span>
  <b>Score</b><span>${j.ai.score}/100</span><b>Summary</b><span>${esc(j.ai.summary)}</span></div>
  <h3>AI actions</h3><ul>${j.ai.actions.map(a=>`<li>${esc(a)}</li>`).join("")}</ul>`;}
  else if(j.ai_error){h+=`<p class="mut">AI: ${esc(j.ai_error)}</p>`;}
  out.innerHTML=h;
}
async function loadInbox(){
  const el=$("inboxList");if(DEMO.length){renderInbox();return;}
  const r=await fetch("/dak/api/demo-inbox");const j=await r.json();
  DEMO=j.emails;renderInbox();renderSnooze();
}
function renderInbox(){
  $("inboxList").innerHTML=DEMO.map((m,i)=>{
    const t=m.triage;
    return `<div class="mail" onclick="showMail(${i})">
    <span class="badge ${bandBadge(t.band)}">${esc(t.band)} · ${t.score}</span>
    <span class="badge">${esc(t.category_label)}</span>
    <span class="badge">DEMO</span>
    <div class="subj">${esc(m.subject)}</div>
    <div class="meta">${esc(m.from)} · ${esc(m.date)}${t.deadline?(" · deadline "+esc(t.deadline)):""}</div>
    <div class="row" style="margin-top:8px">
    <button class="ghost" onclick="event.stopPropagation();snooze('${m.id}',1)">Snooze 1 din</button>
    <button class="ghost" onclick="event.stopPropagation();snooze('${m.id}',3)">Snooze 3 din</button>
    <button class="ghost" onclick="event.stopPropagation();followup('${m.id}')">Follow-up (3 din)</button>
    </div><div id="mail-${i}"></div></div>`;
  }).join("");
}
function showMail(i){
  const m=DEMO[i];
  $("mail-"+i).innerHTML=`<div style="margin-top:10px">${triageCard(m.triage,"Rule-based")}
  <pre>${esc(m.body)}</pre>
  <div class="row"><button class="ghost" onclick="useForDraft(${i})">Is ka draft likho →</button></div></div>`;
}
function getStore(){try{return JSON.parse(localStorage.getItem("dak-snooze")||"{}");}catch(e){return{};}}
function setStore(o){localStorage.setItem("dak-snooze",JSON.stringify(o));}
function snooze(id,days){
  const s=getStore();const d=new Date();d.setDate(d.getDate()+days);
  s[id]={kind:"snoozed",until:d.toISOString().slice(0,10)};setStore(s);renderSnooze();
}
function followup(id){
  const s=getStore();const d=new Date();d.setDate(d.getDate()+3);
  s[id]={kind:"follow-up",until:d.toISOString().slice(0,10)};setStore(s);renderSnooze();
}
function renderSnooze(){
  const s=getStore();const ids=Object.keys(s);
  if(!ids.length){$("snoozeList").textContent="Kuch snooze nahi kiya — kisi demo email par “Snooze” dabayein.";return;}
  $("snoozeList").innerHTML="<ul>"+ids.map(id=>{
    const m=DEMO.find(x=>x.id===id);const v=s[id];
    return `<li><b>${esc(m?m.subject:id)}</b> — ${v.kind} until ${v.until}
    <button class="ghost" onclick="unsnooze('${id}')">Hatao</button></li>`;}).join("")+"</ul>";
}
function unsnooze(id){const s=getStore();delete s[id];setStore(s);renderSnooze();}
function fillDemo(i){
  const m=DEMO[i]||null;
  if(!m){loadInbox().then(()=>fillDemo(i));return;}
  $("trSubject").value=m.subject;$("trBody").value=m.body;doTriage();
}
function useForDraft(i){
  const m=DEMO[i];
  document.querySelector('[data-tab="draft"]').click();
  $("drThread").value="Subject: "+m.subject+"\nFrom: "+m.from+"\n\n"+m.body;
}
async function doThread(){
  const out=$("thOut");out.innerHTML="Thread parhi ja rahi hai… (AI poori thread parhta hai)";
  const fd=new FormData();fd.append("thread",$("thText").value);fd.append("language",lang());
  const r=await fetch("/dak/api/thread",{method:"POST",body:fd});
  const j=await r.json();
  if(!j.ok){out.innerHTML=`<div class="flag bad"><b>Error:</b> ${esc(j.error)}</div>`;return;}
  const x=j.result;
  out.innerHTML=`<p class="mut">AI ne <b>${j.messages_read} message(s)</b> parhe.</p>
  <h3>Summary</h3><p>${esc(x.summary)}</p>
  <h3>Faislay (decisions)</h3><ul>${(x.decisions||[]).map(d=>`<li>${esc(d)}</li>`).join("")||"<li>Koi nahi</li>"}</ul>
  <h3>Khulay sawal</h3><ul>${(x.open_questions||[]).map(d=>`<li>${esc(d)}</li>`).join("")||"<li>Koi nahi</li>"}</ul>
  <h3>Actions</h3><ul>${(x.actions||[]).map(a=>`<li>${esc(a.text)} — <b>${esc(a.owner||"?")}</b></li>`).join("")||"<li>Koi nahi</li>"}</ul>`;
}
async function doDraft(){
  const out=$("drOut");out.innerHTML="Draft likha ja raha hai…";
  const fd=new FormData();fd.append("thread",$("drThread").value);
  fd.append("tone",$("drTone").value);fd.append("language",lang());
  const r=await fetch("/dak/api/draft",{method:"POST",body:fd});
  const j=await r.json();
  if(!j.ok){out.innerHTML=`<div class="flag bad"><b>Error:</b> ${esc(j.error)}</div>`;return;}
  const x=j.result;
  let h=`<h3>Draft (${esc(x.tone)}) — AI-generated, verify karein</h3><pre>${esc(x.draft)}</pre>
  <div class="row"><button onclick="navigator.clipboard.writeText(document.querySelector('#drOut pre').textContent)">Copy karo</button></div>`;
  h+=safetyHtml(x.safety);
  out.innerHTML=h;
}
function safetyHtml(flags){
  if(!flags||!flags.length)return `<div class="flag"><b>Safety Check:</b> koi flag nahi — phir bhi bhejne se pehle khud parh lein.</div>`;
  return `<h3>Safety Check — ${flags.length} flag(s)</h3>`+flags.map(f=>
    `<div class="flag"><b>${esc(f.code)}:</b> ${esc(f.message)}</div>`).join("");
}
async function doSafety(){
  const out=$("scOut");out.innerHTML="Check ho raha hai…";
  const fd=new FormData();fd.append("draft",$("scDraft").value);fd.append("thread",$("drThread").value);
  const r=await fetch("/dak/api/safety-check",{method:"POST",body:fd});
  const j=await r.json();
  if(!j.ok){out.innerHTML=`<div class="flag bad"><b>Error:</b> ${esc(j.error)}</div>`;return;}
  out.innerHTML=safetyHtml(j.flags);
}
aiStatus();loadInbox();
</script>
</body>
</html>
"""

