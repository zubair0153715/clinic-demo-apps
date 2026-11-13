# -*- coding: utf-8 -*-
"""Daftar page — single-file HTML/JS app.

Notebooks and sources live in the user's browser (localStorage).
The server only chunks, retrieves and calls Gemini for the one
chat / audio script / study kit, then forgets everything.
"""

DAFTAR_HTML = r"""<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daftar دفتر — Free AI Study Notebook</title>
<style>
:root{--ink:#1c2333;--mut:#5a6478;--acc:#0b6e4f;--acc2:#e8f5ee;--line:#dfe5ec;--warn:#8a5a00;--warnbg:#fff4d6}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Nastaliq Urdu",sans-serif;margin:0;color:var(--ink);background:#f7f8fa}
header{background:var(--acc);color:#fff;padding:18px 16px}
header h1{margin:0;font-size:26px}
header p{margin:4px 0 0;opacity:.9}
.wrap{max-width:920px;margin:0 auto;padding:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
h2{margin:0 0 8px;font-size:19px}
h3{margin:14px 0 6px;font-size:16px}
.mut{color:var(--mut);font-size:14px}
.small{font-size:13px;color:var(--mut)}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:9px 14px;font-size:15px;cursor:pointer;margin:2px}
button.sec{background:#fff;color:var(--acc);border:1px solid var(--acc)}
button.ghost{background:#eef1f4;color:var(--ink)}
button:disabled{opacity:.5;cursor:not-allowed}
input,select,textarea{width:100%;padding:9px;border:1px solid var(--line);border-radius:8px;font-size:15px;font-family:inherit}
textarea{min-height:120px}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
.tabs button{background:#fff;color:var(--ink);border:1px solid var(--line)}
.tabs button.on{background:var(--acc);color:#fff;border-color:var(--acc)}
.tab{display:none}.tab.on{display:block}
.badge{display:inline-block;background:var(--acc2);color:var(--acc);border-radius:20px;padding:2px 10px;font-size:13px;margin:2px}
.warn{background:var(--warnbg);border:1px solid #e8c96a;color:var(--warn);border-radius:8px;padding:10px;font-size:14px}
.src{border:1px solid var(--line);border-radius:8px;padding:8px;margin:6px 0}
.src b{display:block}
.chunk{border-left:3px solid var(--acc);background:#f2f7f4;padding:8px;margin:6px 0;font-size:14px}
.cite{font-size:13px;color:var(--mut);border:1px dashed var(--line);border-radius:6px;padding:6px;margin:4px 0}
.cite b{color:var(--acc)}
.turn{padding:8px;border-radius:8px;margin:6px 0}
.turn.A{background:#eef4ff}.turn.B{background:#fdf1e7}
.turn.playing{outline:2px solid var(--acc)}
.flash{border:1px solid var(--line);border-radius:10px;padding:12px;margin:8px 0;cursor:pointer}
.flash .a{display:none;color:var(--acc)}
.flash.open .a{display:block}
.opt{display:block;width:100%;text-align:left;background:#fff;color:var(--ink);border:1px solid var(--line);margin:4px 0}
.opt.right{background:#d9f2e3;border-color:var(--acc)}
.opt.wrong{background:#fde3e3}
pre{white-space:pre-wrap;font-family:inherit}
[dir="rtl"] input,[dir="rtl"] textarea{text-align:right}
</style>
</head>
<body>
<header>
<div class="wrap">
<h1>📒 Daftar دفتر</h1>
<p>Free AI study notebook — apni kitabein, notes aur past papers dein; chat, audio revision aur study kit payein. No account, no card, no daily caps.</p>
</div>
</header>
<div class="wrap">

<div class="card">
<label>Language / زبان</label>
<select id="lang" onchange="setLang()">
<option value="roman">Roman-Urdu (default)</option>
<option value="ur">اردو</option>
<option value="en">English</option>
</select>
<p class="small" id="aiStatus">AI status check ho raha hai…</p>
<p class="small">Daftar NotebookLM / Gemini Notebook se mutasir hai — magar uska code, naam ya design istemal nahi karta. Ye aik naya, free aur original tool hai.</p>
</div>

<div class="card">
<h2>1 · Notebook aur Sources</h2>
<div>
<input id="nbTitle" placeholder="Notebook ka naam — masalan: Pharmacology Ch 2">
<button onclick="newNotebook()">Naya Notebook</button>
<button class="sec" onclick="loadDemo()">Demo Notebook (Photosynthesis)</button>
</div>
<div id="nbList" style="margin-top:8px"></div>
<h3>Source shaamil karein</h3>
<input id="srcTitle" placeholder="Source ka naam — masalan: Ch 2 notes">
<textarea id="srcText" placeholder="Yahan text paste karein (kam se kam 20 lafz)…"></textarea>
<button onclick="addSourceText()">Text se Source banayein</button>
<button class="sec" onclick="document.getElementById('txtFile').click()">.txt / .md upload</button>
<button class="sec" onclick="document.getElementById('pdfFile').click()">PDF upload (text wali)</button>
<input type="file" id="txtFile" accept=".txt,.md" hidden onchange="uploadTextFile(this)">
<input type="file" id="pdfFile" accept=".pdf" hidden onchange="uploadPdf(this)">
<div id="srcList"></div>
<div style="margin-top:8px">
<button class="ghost" onclick="exportNotebook()">Notebook backup (JSON)</button>
<button class="ghost" onclick="document.getElementById('impFile').click()">Backup wapas layein</button>
<input type="file" id="impFile" accept=".json" hidden onchange="importNotebook(this)">
<span class="small" id="libInfo"></span>
</div>
</div>

<div class="tabs">
<button class="on" onclick="showTab('search',this)">🔍 Source Search</button>
<button onclick="showTab('chat',this)">💬 Chat</button>
<button onclick="showTab('audio',this)">🎧 Audio Overview</button>
<button onclick="showTab('kit',this)">📚 Study Kit</button>
</div>

<div class="tab on" id="tab-search">
<div class="card">
<h2>Source Search (bina AI, bina key)</h2>
<p class="mut">Apne sources mein koi lafz ya jumla dhoondhein — ye kaam browser/server par bina AI ke hota hai.</p>
<input id="searchQ" placeholder="Masalan: Calvin cycle" onkeydown="if(event.key==='Enter')doSearch()">
<button onclick="doSearch()">Dhoondhein</button>
<div id="searchOut"></div>
</div>
</div>

<div class="tab" id="tab-chat">
<div class="card">
<h2>Chat — sirf aapke sources se</h2>
<p class="mut">Jawab sirf aapke sources se aata hai. Har daawa ke saath citation hoti hai — quote lafz-ba-lafz source chunk se milta hai, warna jawab reject ho jata hai. Agar jawab sources mein nahi, to Daftar saaf keh deta hai.</p>
<input id="chatQ" placeholder="Sawal likhein — masalan: Calvin cycle kahan hota hai?" onkeydown="if(event.key==='Enter')doChat()">
<button onclick="doChat()">Sawal poochein</button>
<div id="chatOut"></div>
</div>
</div>

<div class="tab" id="tab-audio">
<div class="card">
<h2>Audio Overview — Urdu-first</h2>
<p class="mut">Do hosts (A aur B) aapke sources par guftugu karte hain. NotebookLM ke audio mein na transcript hoti hai, na citation, na voice choice — Daftar mein teeno hain: poora transcript, har section ki citation, aur aapke browser ki awazein (ur-PK jab mojood ho).</p>
<select id="audioStyle">
<option value="brief">Brief — 2-3 min quick revision</option>
<option value="deep" selected>Deep dive — 8-10 min</option>
<option value="revision">Revision — exam-focused recap</option>
</select>
<button onclick="doAudio()">Audio script banayein</button>
<button class="sec" onclick="playAudio()" id="playBtn">▶ Sunayein</button>
<button class="sec" onclick="stopAudio()">⏹ Rokein</button>
<div id="audioOut"></div>
</div>
</div>

<div class="tab" id="tab-kit">
<div class="card">
<h2>Study Kit — aapke sources se</h2>
<p class="mut">Flashcards, quiz aur study guide — sab aapke sources se, citations ke saath. Flashcards CSV mein download karein; quiz aur guide print kar lein.</p>
<button onclick="doKit('flashcards')">Flashcards</button>
<button onclick="doKit('quiz')">Quiz (MCQ)</button>
<button onclick="doKit('guide')">Study Guide</button>
<button class="sec" onclick="downloadCsv()" id="csvBtn" disabled>Flashcards CSV download</button>
<div id="kitOut"></div>
</div>
</div>

<div class="card">
<h2>Honest limits</h2>
<ul class="mut">
<li>AI chat, audio aur study kit ke liye <b>GEMINI_API_KEY</b> chahiye (owner ki free quota). Bina key ke library, chunking, PDF aur source search poore kaam karte hain.</li>
<li>Daftar sirf aapke sources se jawab deta hai — web se kuch nahi laata. Agar jawab sources mein nahi, to wo keh deta hai.</li>
<li>PDF sirf text nikalta hai; scanned/image PDF mein text nahi hota — Daftar saaf bata deta hai.</li>
<li>AI phir bhi ghalat parh sakta hai (aik study mein NotebookLM 13% outputs mein hallucinate karta mila — Hagar et al., 2025). Har citation quote lafz-ba-lafz dikhaya jata hai taake aap aik tap mein verify kar sakein.</li>
<li>Daftar study aid hai, ustaad nahi — exam se pehle asli kitab se verify karein.</li>
</ul>
</div>
</div>

<script>
let notebooks = JSON.parse(localStorage.getItem('daftar_nbs') || '[]');
let current = parseInt(localStorage.getItem('daftar_cur') || '0');
let lastCards = null, lastScript = null, lastChunks = {};
const $ = id => document.getElementById(id);

function save(){ localStorage.setItem('daftar_nbs', JSON.stringify(notebooks)); localStorage.setItem('daftar_cur', String(current)); }
function cur(){ return notebooks[current] || null; }
function lang(){ return $('lang').value; }
function esc(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function setLang(){
  document.documentElement.dir = lang()==='ur' ? 'rtl' : 'ltr';
  document.documentElement.lang = lang()==='ur' ? 'ur' : 'en';
}
async function api(path, body){
  const r = await fetch('/daftar/api/'+path, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body||{})});
  return r.json();
}
async function checkAi(){
  try{ const r = await fetch('/daftar/api/ai-status'); const j = await r.json();
    $('aiStatus').textContent = j.ai_available ? '✅ AI tayyar hai (Gemini key mojood).' : '⚠️ AI key nahi hai — chat, audio aur study kit ke liye GEMINI_API_KEY chahiye; source search aur library bina key ke kaam karte hain.';
  }catch(e){ $('aiStatus').textContent = 'AI status check nahi ho saka.'; }
}
function renderNb(){
  const nb = cur();
  $('nbList').innerHTML = notebooks.map((n,i)=>`<button class="${i===current?'':'ghost'}" onclick="switchNb(${i})">${esc(n.title)} (${n.sources.length})</button>`).join('') || '<span class="mut">Koi notebook nahi — pehle notebook banayein ya demo load karein.</span>';
  $('srcList').innerHTML = nb ? nb.sources.map((s,i)=>`<div class="src"><b>${esc(s.title)}</b><span class="small">${s.text.split(/\s+/).length} lafz</span> <button class="ghost" onclick="delSource(${i})">Hatayein</button></div>`).join('') : '';
  $('libInfo').textContent = nb ? `${nb.sources.length} sources · kul ${nb.sources.reduce((a,s)=>a+s.text.split(/\s+/).length,0)} lafz` : '';
}
function switchNb(i){ current=i; save(); renderNb(); }
function newNotebook(){
  const t = $('nbTitle').value.trim(); if(!t){ alert('Notebook ka naam dein.'); return; }
  notebooks.push({title:t, sources:[]}); current = notebooks.length-1; $('nbTitle').value=''; save(); renderNb();
}
function delSource(i){ const nb=cur(); if(!nb) return; nb.sources.splice(i,1); save(); renderNb(); }
async function loadDemo(){
  const r = await fetch('/daftar/api/demo'); const j = await r.json();
  if(!j.ok){ alert('Demo load nahi ho saka.'); return; }
  notebooks.push({title:'Demo — Photosynthesis', sources:[{title:j.source.title, text:j.source.text}]});
  current = notebooks.length-1; save(); renderNb();
}
function addSourceText(){
  const nb=cur(); if(!nb){ alert('Pehle notebook banayein.'); return; }
  const t=$('srcTitle').value.trim(), x=$('srcText').value.trim();
  if(!t || !x){ alert('Source ka naam aur text dono dein.'); return; }
  if(x.split(/\s+/).length < 20){ alert('Source kam se kam 20 lafz ka ho.'); return; }
  nb.sources.push({title:t, text:x}); $('srcTitle').value=''; $('srcText').value=''; save(); renderNb();
}
function uploadTextFile(inp){
  const nb=cur(); if(!nb){ alert('Pehle notebook banayein.'); return; }
  const f=inp.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=()=>{ nb.sources.push({title:f.name.replace(/\.(txt|md)$/i,''), text:String(rd.result)}); save(); renderNb(); };
  rd.readAsText(f); inp.value='';
}
async function uploadPdf(inp){
  const nb=cur(); if(!nb){ alert('Pehle notebook banayein.'); return; }
  const f=inp.files[0]; if(!f) return;
  const fd=new FormData(); fd.append('pdf', f);
  const r=await fetch('/daftar/api/extract-pdf',{method:'POST', body:fd}); const j=await r.json();
  if(!j.ok){ alert(j.error); inp.value=''; return; }
  nb.sources.push({title:f.name.replace(/\.pdf$/i,''), text:j.text}); save(); renderNb();
  alert(`PDF se ${j.pages} safhe, ${j.words} lafz nikle.`);
  inp.value='';
}
function sourcesPayload(){ const nb=cur(); return nb ? nb.sources : []; }
function needSources(){ if(!cur() || !cur().sources.length){ alert('Pehle notebook mein kam se kam ek source dein (ya demo load karein).'); return false; } return true; }
function showTab(name, btn){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  $('tab-'+name).classList.add('on'); btn.classList.add('on');
}
function chunkHtml(ch){
  return `<div class="chunk"><b>${esc(ch.id)}</b> · source ${esc(ch.source_id)}<br>${esc(ch.text)}</div>`;
}
async function doSearch(){
  if(!needSources()) return;
  const q=$('searchQ').value.trim(); if(!q) return;
  $('searchOut').innerHTML='<p class="mut">Dhoondh rahe hain…</p>';
  const j=await api('search',{sources:sourcesPayload(), query:q});
  if(!j.ok){ $('searchOut').innerHTML=`<p class="warn">${esc(j.error)}</p>`; return; }
  if(!j.results.length){ $('searchOut').innerHTML='<p class="mut">Kuch nahi mila — dosra lafz try karein.</p>'; return; }
  lastChunks={}; j.results.forEach(c=>lastChunks[c.id]=c);
  $('searchOut').innerHTML=`<p class="mut">${j.results.length} chunks mile:</p>`+j.results.map(chunkHtml).join('');
}
async function doChat(){
  if(!needSources()) return;
  const q=$('chatQ').value.trim(); if(!q) return;
  $('chatOut').innerHTML='<p class="mut">Sources parh rahe hain…</p>';
  const j=await api('chat',{sources:sourcesPayload(), question:q, language:lang()});
  if(!j.ok){ $('chatOut').innerHTML=`<p class="warn">${esc(j.error)}</p>`; return; }
  const r=j.result;
  let html=`<div class="card" style="border-color:#0b6e4f"><p>${esc(r.answer)}</p><p class="small">AI-written · sirf aapke sources se</p>`;
  (r.citations||[]).forEach(c=>{
    const ch=(j.used_chunks||[]).find(x=>x.id===c.chunk_id);
    html+=`<div class="cite"><b>${esc(c.chunk_id)}</b> — “${esc(c.quote)}”${ch?`<br><span>${esc(ch.text.slice(0,300))}…</span>`:''}</div>`;
  });
  html+='</div>';
  $('chatOut').innerHTML=html;
}
async function doAudio(){
  if(!needSources()) return;
  $('audioOut').innerHTML='<p class="mut">Audio script likhi ja rahi hai…</p>';
  const j=await api('audio',{sources:sourcesPayload(), language:lang(), style:$('audioStyle').value});
  if(!j.ok){ $('audioOut').innerHTML=`<p class="warn">${esc(j.error)}</p>`; return; }
  lastScript=j.result;
  let html=`<p class="mut">Style: ${esc(j.result.style)} · ${j.result.total_words} lafz · ~${j.result.est_minutes} min · ${j.chunks_used} chunks se · AI-written</p>`;
  j.result.turns.forEach((t,i)=>{
    html+=`<div class="turn ${t.speaker}" id="turn-${i}"><b>Host ${t.speaker}:</b> ${esc(t.text)}<br><span class="small">Sources: ${t.chunk_ids.map(esc).join(', ')}</span></div>`;
  });
  $('audioOut').innerHTML=html;
}
function pickVoice(){
  const vs=speechSynthesis.getVoices();
  return vs.find(v=>/ur(-|_)PK/i.test(v.lang)) || vs.find(v=>/^ur/i.test(v.lang)) || vs.find(v=>/^en-GB/i.test(v.lang)) || vs[0];
}
function playAudio(){
  if(!lastScript){ alert('Pehle audio script banayein.'); return; }
  stopAudio();
  const turns=lastScript.turns; let i=0;
  const sayNext=()=>{
    if(i>=turns.length) return;
    document.querySelectorAll('.turn').forEach(t=>t.classList.remove('playing'));
    const el=$('turn-'+i); if(el) el.classList.add('playing');
    const u=new SpeechSynthesisUtterance(turns[i].text);
    const v=pickVoice(); if(v) u.voice=v;
    u.lang = lang()==='ur' ? 'ur-PK' : (lang()==='roman' ? 'ur-PK' : 'en-US');
    u.rate=0.95; u.onend=()=>{ i++; sayNext(); };
    speechSynthesis.speak(u);
  };
  sayNext();
}
function stopAudio(){ speechSynthesis.cancel(); document.querySelectorAll('.turn').forEach(t=>t.classList.remove('playing')); }
async function doKit(kind){
  if(!needSources()) return;
  $('kitOut').innerHTML='<p class="mut">Study kit ban raha hai…</p>';
  const j=await api('study-kit',{sources:sourcesPayload(), language:lang(), kind});
  if(!j.ok){ $('kitOut').innerHTML=`<p class="warn">${esc(j.error)}</p>`; return; }
  const r=j.result; let html='';
  if(kind==='flashcards'){
    lastCards=r.cards; $('csvBtn').disabled=false;
    html='<h3>Flashcards — card par tap karein, jawab khulega</h3>'+r.cards.map((c,i)=>`<div class="flash" onclick="this.classList.toggle('open')"><b>Q${i+1}:</b> ${esc(c.question)}<div class="a"><b>Jawab:</b> ${esc(c.answer)}<br><span class="small">Source: ${esc(c.chunk_id)}</span></div></div>`).join('');
  } else if(kind==='quiz'){
    html='<h3>Quiz — option chunein</h3>'+r.questions.map((q,i)=>`<div class="card"><b>Q${i+1}:</b> ${esc(q.question)}${q.options.map((o,oi)=>`<button class="opt" onclick="answerQuiz(this,${oi},${q.correct},'exp-${i}')">${esc(o)}</button>`).join('')}<div id="exp-${i}" style="display:none" class="small"><b>Wazahat:</b> ${esc(q.explanation)}<br>Source: ${esc(q.chunk_id)}</div></div>`).join('');
  } else {
    html='<h3>Study Guide</h3><h3>Key points</h3><ul>'+r.key_points.map(p=>`<li>${esc(p)}</li>`).join('')+'</ul><h3>Key terms</h3>'+r.terms.map(t=>`<div class="src"><b>${esc(t.term)}</b>${esc(t.definition)}<br><span class="small">Source: ${esc(t.chunk_id)}</span></div>`).join('');
    if(r.timeline && r.timeline.length) html+='<h3>Timeline</h3><ul>'+r.timeline.map(t=>`<li><b>${esc(t.when)}:</b> ${esc(t.event)}</li>`).join('')+'</ul>';
  }
  $('kitOut').innerHTML=html+'<p class="small">AI-written · sirf aapke sources se</p>';
}
function answerQuiz(btn, chosen, correct, expId){
  const card=btn.parentElement;
  card.querySelectorAll('.opt').forEach(b=>b.disabled=true);
  btn.classList.add(chosen===correct?'right':'wrong');
  if(chosen!==correct) card.querySelectorAll('.opt')[correct].classList.add('right');
  document.getElementById(expId).style.display='block';
}
async function downloadCsv(){
  if(!lastCards) return;
  const r=await fetch('/daftar/api/export-csv',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({cards:lastCards})});
  const blob=await r.blob(); const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='daftar-flashcards.csv'; a.click();
}
async function exportNotebook(){
  const nb=cur(); if(!nb){ alert('Pehle notebook banayein.'); return; }
  const r=await fetch('/daftar/api/export-notebook',{method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:nb.title, sources:nb.sources})});
  if(!r.ok){ const j=await r.json().catch(()=>({})); alert(j.error||'Export nahi ho saka.'); return; }
  const blob=await r.blob(); const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='daftar-notebook.json'; a.click();
}
function importNotebook(inp){
  const f=inp.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=async()=>{
    const j=await api('import-notebook',{json:String(rd.result)});
    if(!j.ok){ alert(j.error); return; }
    notebooks.push(j.notebook); current=notebooks.length-1; save(); renderNb();
  };
  rd.readAsText(f); inp.value='';
}
setLang(); checkAi(); renderNb();
if('speechSynthesis' in window) speechSynthesis.getVoices();
</script>
</body>
</html>
"""

# Keep the HTML out of the module docstring path: the string above is the page.
