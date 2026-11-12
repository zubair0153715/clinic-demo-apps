# -*- coding: utf-8 -*-
"""Poda page — single self-contained HTML page.

The server only identifies/diagnoses the user's photo (Gemini
vision, optional key) and serves the verified care table and
watering math. Photos are never stored. My Plants lives in
localStorage; nothing is stored server-side. No account, no card,
no trial, no credits, no ads.
"""

PODA_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poda — پودا | Free AI plant identifier</title>
<style>
:root{--ink:#1e293b;--bg:#f0fdf4;--card:#ffffff;--line:#bbf7d0;--acc:#15803d;--acc2:#0f766e;--soft:#dcfce7;--warn:#fef3c7;--warnline:#f59e0b;--danger:#fef2f2;--dangerline:#dc2626}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:linear-gradient(135deg,#14532d,#15803d);color:#fff;padding:26px 16px 20px;text-align:center}
header h1{margin:0;font-size:30px}
header p{margin:6px 0 0;opacity:.92}
main{max-width:780px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}
h2{margin:0 0 8px;font-size:19px}
h3{margin:14px 0 6px;font-size:16px}
.muted{color:#64748b;font-size:13px}
button{border:0;border-radius:10px;padding:10px 16px;font-size:15px;background:var(--acc);color:#fff;cursor:pointer}
button.ghost{background:#fff;border:1px solid var(--acc);color:var(--acc)}
button:disabled{opacity:.5;cursor:default}
input,select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:9px;font-size:15px;background:#fff}
label{display:block;font-size:13px;color:#64748b;margin:10px 0 4px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;background:var(--soft);border:1px solid #86efac;border-radius:999px;padding:3px 10px;font-size:13px;margin:2px}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:var(--soft)}
.ai{border-left:4px solid var(--acc2);background:#f0fdfa;padding:10px 12px;border-radius:8px;margin:10px 0;white-space:pre-wrap}
.err{color:#b91c1c;font-size:14px}
.ok{color:#0f766e;font-size:14px}
.warnbox{background:var(--warn);border:1px solid var(--warnline);border-radius:10px;padding:10px 12px;margin:10px 0;font-size:14px}
.dangerbox{background:var(--danger);border:1px solid var(--dangerline);border-radius:10px;padding:10px 12px;margin:10px 0;font-size:14px}
.confbar{height:10px;background:#e2e8f0;border-radius:999px;overflow:hidden;margin:6px 0}
.confbar>div{height:100%;background:var(--acc)}
.confbar.low>div{background:#dc2626}
#preview{max-width:100%;max-height:320px;border-radius:10px;display:none;margin-top:10px}
.myplant{border:1px solid var(--line);border-radius:10px;padding:10px;margin:8px 0}
.myplant b{display:block}
footer{max-width:780px;margin:0 auto;padding:0 16px 30px;color:#64748b;font-size:13px}
</style>
</head>
<body>
<header>
<h1>Poda — پودا</h1>
<p>Free AI plant identifier · Photo dein, poda pehchanein — unlimited, no account, no card, no trial. Urdu-first.</p>
</header>
<main>

<div class="card">
<h2>🌿 Poda pehchanein</h2>
<p class="muted">Podday ki saaf photo dein — poora poda ya patte nazar aayein to behtar hai. Poda aap ki photo sirf is aik pehchan ke liye AI ko bhejta hai, phir delete — kahin save nahi hoti.</p>
<label for="lang">Language / زبان</label>
<select id="lang">
<option value="en">English</option>
<option value="roman" selected>Roman-Urdu</option>
<option value="ur">اردو</option>
</select>
<label>Mode</label>
<div class="row">
<button id="modeId" onclick="setMode('identify')">🔍 Pehchan (Identify)</button>
<button id="modeDg" class="ghost" onclick="setMode('diagnose')">🩺 Bimari check (Diagnose)</button>
</div>
<label for="photo">Photo — camera ya gallery</label>
<input type="file" id="photo" accept="image/jpeg,image/png,image/webp" capture="environment" onchange="showPreview()">
<img id="preview" alt="Photo preview">
<div class="row" style="margin-top:12px">
<button id="goBtn" onclick="runAI()">Pehchanein</button>
<span id="aiState" class="muted"></span>
</div>
<div id="msg" class="err"></div>
<div id="result"></div>
</div>

<div class="card">
<h2>🪴 My Plants — mere poday</h2>
<p class="muted">Pehchan ke baad "My Plants me save karein" dabayein. Paani ka hisaab aap ke browser me save hota hai — server par kuch nahi.</p>
<div id="myplants"></div>
</div>

<div class="card">
<h2>📖 Aam poday — baghair AI, baghair key</h2>
<p class="muted">Ye 10 poday har Pakistani ghar me hote hain. Paani ka waqfa mashhoor care guides se liya gaya hai (har qeemat ke saath source likha hai). Ungli wala test hamesha calendar se behtar hai: upar ki mitti sookhi lage to paani dein.</p>
<div id="common"></div>
</div>

<div class="card">
<h2>⚠️ Ehem — safety pehle</h2>
<div class="dangerbox"><b>Poda kabhi nahi kehta ke koi poda khaana, peena ya dawa ke tor par istemal karna mehfooz hai.</b> Neem aur bakain (chinaberry) aik jaise dikhte hain — mahireen bhi ghalti karte hain. Khaane ya dawa se pehle hamesha kisi maqami botanist ya doctor se tasdeeq karwayein. Neem ka tel chhote bachon ke liye zehreela ho sakta hai.</div>
<p class="muted">Pehchan AI ka behtareen andaza hai, lab test nahi. Confidence 60% se kam ho to page saaf keh deta hai ke "yaqeen nahi" — nursery se tasdeeq karwayein. Photo se har bimari ki tasdeeq nahi ho sakti.</p>
</div>

</main>
<footer>
<h3>Honest limits</h3>
<ul>
<li>Identification aur diagnosis Gemini vision se hote hain — <b>koi accuracy claim nahi</b>. AI ghalti kar sakta hai; neem vs bakain jaisi mushkil jodi par confidence kam dikhaya jata hai.</li>
<li>AI ke liye <code>GEMINI_API_KEY</code> chahiye (owner's free quota). Baghair key ke bhi aam podon ki table, paani ka hisaab aur My Plants poore kaam karte hain.</li>
<li>Photo Google ke Gemini servers ko is aik pehchan ke liye bheji jati hai; Poda khud kuch store nahi karta.</li>
<li>Poda botanist nahi, doctor nahi. Khaane, peene ya dawa ke liye kabhi sirf app par bharosa na karein.</li>
</ul>
<p>Poda is an original clean-room build. Not affiliated with PictureThis or Glority Global Group Ltd.</p>
</footer>
<script>
let mode = 'identify';
let lastResult = null;

function setMode(m){
  mode = m;
  document.getElementById('modeId').className = m==='identify' ? '' : 'ghost';
  document.getElementById('modeDg').className = m==='diagnose' ? '' : 'ghost';
  document.getElementById('goBtn').textContent = m==='identify' ? 'Pehchanein' : 'Bimari check karein';
  document.getElementById('result').innerHTML = '';
  document.getElementById('msg').textContent = '';
}

function showPreview(){
  const f = document.getElementById('photo').files[0];
  const img = document.getElementById('preview');
  if(!f){ img.style.display='none'; return; }
  img.src = URL.createObjectURL(f);
  img.style.display='block';
}

async function aiStatus(){
  try{
    const r = await fetch('/poda/api/ai-status');
    const j = await r.json();
    document.getElementById('aiState').textContent = j.ai_available
      ? 'AI tayyar hai (Gemini).' : 'AI key nahi lagi — pehchan ke liye key chahiye; table aur hisaab phir bhi kaam karte hain.';
  }catch(e){ document.getElementById('aiState').textContent=''; }
}

function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function runAI(){
  const f = document.getElementById('photo').files[0];
  const msg = document.getElementById('msg');
  const res = document.getElementById('result');
  msg.textContent=''; res.innerHTML=''; lastResult=null;
  if(!f){ msg.textContent='Pehle poday ki photo dein.'; return; }
  if(f.size > 5*1024*1024){ msg.textContent='Photo 5 MB se bari hai — chhoti photo dein.'; return; }
  const btn = document.getElementById('goBtn');
  btn.disabled = true; btn.textContent = 'AI dekh raha hai…';
  try{
    const fd = new FormData();
    fd.append('photo', f);
    fd.append('language', document.getElementById('lang').value);
    const r = await fetch('/poda/api/' + mode, {method:'POST', body:fd});
    const j = await r.json();
    if(!j.ok){ msg.textContent = j.error || 'Kuch ghalat hua.'; return; }
    if(mode==='identify') showIdentify(j.result); else showDiagnose(j.result);
  }catch(e){ msg.textContent='AI se rabta nahi hua. Dobara try karein.'; }
  finally{ btn.disabled=false; btn.textContent = mode==='identify' ? 'Pehchanein' : 'Bimari check karein'; }
}

function confHtml(c){
  const low = c < 60;
  return '<div>Confidence: <b>' + c + '%</b>' + (low ? ' — <b>yaqeen kam hai</b>, nursery se tasdeeq karwayein' : '') + '</div>'
    + '<div class="confbar' + (low ? ' low' : '') + '"><div style="width:' + c + '%"></div></div>';
}

function showIdentify(r){
  lastResult = r;
  const v = r.verified_table;
  let h = '<div class="ai"><h3>' + esc(r.common_name_en) + ' — ' + esc(r.name_ur) + ' (' + esc(r.name_roman) + ')</h3>'
    + '<div class="muted"><i>' + esc(r.scientific_name) + '</i> · AI-written pehchan</div>'
    + confHtml(r.confidence)
    + (r.uncertain ? '<div class="warnbox">⚠️ AI ko yaqeen nahi — ye andaza ghalat ho sakta hai. Khaas tor par neem/bakain jaisi milti-julti species me. Nursery ya botanist se tasdeeq karwayein.</div>' : '')
    + '<p>' + esc(r.description) + '</p>'
    + '<h3>Dekh-bhaal</h3><table>'
    + '<tr><th>Paani</th><td>' + esc(r.care.water) + '</td></tr>'
    + '<tr><th>Dhoop</th><td>' + esc(r.care.sunlight) + '</td></tr>'
    + '<tr><th>Mitti</th><td>' + esc(r.care.soil) + '</td></tr>'
    + '<tr><th>Temperature</th><td>' + esc(r.care.temperature) + '</td></tr></table>'
    + (r.season_note_pk ? '<p><b>Pakistan mosam:</b> ' + esc(r.season_note_pk) + '</p>' : '')
    + '<h3>Safety</h3>'
    + '<p>👶 Insaan: ' + esc(r.toxicity_humans) + '<br>🐾 Pets: ' + esc(r.toxicity_pets) + '</p>'
    + '<div class="dangerbox">' + esc(r.edible_warning) + '</div>';
  if(v){
    h += '<div class="warnbox" style="background:#f0fdf4;border-color:#86efac">✅ Ye poda hamari verified table me hai — paani ka waqfa published care guide se: garmi me har <b>'
      + v.water_summer + ' din</b>, sardi me har <b>' + v.water_winter + ' din</b>. (' + esc(v.source) + ')</div>';
  }
  h += '<div class="row"><button onclick="savePlant()">My Plants me save karein</button></div></div>';
  document.getElementById('result').innerHTML = h;
}

function showDiagnose(r){
  let h = '<div class="ai"><h3>🩺 ' + esc(r.problem_en) + ' — ' + esc(r.problem_ur) + '</h3>'
    + '<div class="muted">Severity: <b>' + esc(r.severity) + '</b> · AI-written diagnosis</div>'
    + confHtml(r.confidence)
    + (r.uncertain ? '<div class="warnbox">⚠️ AI ko yaqeen nahi — photo se har bimari ki tasdeeq nahi ho sakti. Patton ke neeche, jad aur mitti khud check karein.</div>' : '')
    + '<h3>Mumkinah wajohat</h3><ul>' + r.likely_causes.map(c=>'<li>'+esc(c)+'</li>').join('') + '</ul>'
    + '<h3>Ilaaj — kya karein</h3><ol>' + r.treatment_steps.map(c=>'<li>'+esc(c)+'</li>').join('') + '</ol>'
    + '<p><b>Kab madad lein:</b> ' + esc(r.when_to_seek_help) + '</p></div>';
  document.getElementById('result').innerHTML = h;
}

function loadPlants(){
  try{ return JSON.parse(localStorage.getItem('poda_myplants') || '[]'); }
  catch(e){ return []; }
}
function storePlants(list){ localStorage.setItem('poda_myplants', JSON.stringify(list)); }

function savePlant(){
  if(!lastResult) return;
  const list = loadPlants();
  const today = new Date().toISOString().slice(0,10);
  list.push({name_en:lastResult.common_name_en, name_ur:lastResult.name_ur,
    name_roman:lastResult.name_roman, scientific:lastResult.scientific_name,
    table_id: lastResult.verified_table ? lastResult.verified_table.id : null,
    water_summer: lastResult.verified_table ? lastResult.verified_table.water_summer : null,
    water_winter: lastResult.verified_table ? lastResult.verified_table.water_winter : null,
    last_watered: today, added: today});
  storePlants(list);
  renderMyPlants();
}

async function waterFor(p){
  const month = new Date().getMonth()+1;
  if(!p.table_id) return null;
  const fd = new FormData();
  fd.append('plant_id', p.table_id);
  fd.append('last_watered', p.last_watered);
  fd.append('month', String(month));
  try{
    const r = await fetch('/poda/api/water-schedule', {method:'POST', body:fd});
    const j = await r.json();
    return j.ok ? j : null;
  }catch(e){ return null; }
}

async function renderMyPlants(){
  const list = loadPlants();
  const box = document.getElementById('myplants');
  if(!list.length){ box.innerHTML = '<p class="muted">Abhi koi poda save nahi. Pehchan ke baad yahan save karein.</p>'; return; }
  let h = '';
  for(let i=0;i<list.length;i++){
    const p = list[i];
    const w = await waterFor(p);
    let status = '';
    if(w){
      status = w.status==='overdue' ? '<span class="err"><b>Paani overdue hai — ' + w.overdue_days + ' din pehle dena tha.</b></span>'
        : w.status==='due_today' ? '<span class="ok"><b>Aaj paani ka din hai.</b></span>'
        : '<span class="ok">Agla paani: ' + esc(w.next_date) + ' (' + w.days_until + ' din baad)</span>';
      status += ' <span class="muted">· har ' + w.interval_days + ' din (' + (w.season==='summer' ? 'garmi' : 'sardi') + ')</span>';
    } else {
      status = '<span class="muted">Paani ka waqfa is poday ke liye table me nahi — AI care se andaza lagayein.</span>';
    }
    h += '<div class="myplant"><b>' + esc(p.name_en) + ' — ' + esc(p.name_ur) + ' (' + esc(p.name_roman) + ')</b>'
      + '<div class="muted"><i>' + esc(p.scientific) + '</i> · aakhri paani: ' + esc(p.last_watered) + '</div>'
      + '<div>' + status + '</div>'
      + '<div class="row" style="margin-top:8px"><button onclick="watered(' + i + ')">💧 Aaj paani diya</button>'
      + '<button class="ghost" onclick="delPlant(' + i + ')">Hatayein</button></div></div>';
  }
  box.innerHTML = h;
}

function watered(i){
  const list = loadPlants();
  list[i].last_watered = new Date().toISOString().slice(0,10);
  storePlants(list); renderMyPlants();
}
function delPlant(i){
  const list = loadPlants();
  list.splice(i,1);
  storePlants(list); renderMyPlants();
}

async function loadCommon(){
  try{
    const r = await fetch('/poda/api/common-plants');
    const j = await r.json();
    let h = '<table><tr><th>Poda</th><th>Paani (garmi / sardi)</th><th>Dhoop</th><th>Tip</th></tr>';
    for(const p of j.plants){
      h += '<tr><td><b>' + esc(p.name_en) + '</b><br>' + esc(p.name_ur) + ' (' + esc(p.name_roman) + ')<br><i>' + esc(p.scientific) + '</i></td>'
        + '<td>har ' + p.water_summer + ' din / har ' + p.water_winter + ' din</td>'
        + '<td>' + esc(p.sunlight_en) + '</td>'
        + '<td>' + esc(p.tip_en) + '<br><span class="muted">' + esc(p.source) + '</span></td></tr>';
    }
    document.getElementById('common').innerHTML = h + '</table>';
  }catch(e){ document.getElementById('common').innerHTML = '<p class="err">Table load nahi hui.</p>'; }
}

aiStatus();
loadCommon();
renderMyPlants();
</script>
</body>
</html>
"""
