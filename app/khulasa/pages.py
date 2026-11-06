"""Khulasa page — single-file HTML/JS.

Tabs: Library (6 public-domain classics with 3 depths each) and
Apna Khulasa (paste your own text -> AI summary + quiz). XP,
streak, checklists and flashcard progress live in localStorage.
Read-aloud uses the device's own speech synthesis.
"""

KHULASA_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Khulasa — Free AI Book-Summary Studio</title>
<style>
:root{--ink:#1c1917;--muted:#78716c;--paper:#fafaf9;--card:#fff;--line:#e7e5e4;
--brand:#9a3412;--brand2:#c2410c;--good:#15803d;--soft:#fff7ed}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
background:var(--paper);color:var(--ink);line-height:1.6}
header{background:#1c1917;color:#fafaf9;padding:26px 16px 20px}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}
h1{margin:0;font-size:30px;line-height:1.2}
h1 span{color:#fdba74}
.sub{color:#d6d3d1;margin:6px 0 0;font-size:15px}
.badges{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px}
.pill{background:#292524;border:1px solid #44403c;color:#fdba74;border-radius:999px;
padding:4px 12px;font-size:13px}
.pill b{color:#fff}
.tabs{display:flex;gap:8px;margin:18px 0 0}
.tab{border:1px solid var(--line);background:var(--card);border-radius:10px 10px 0 0;
padding:10px 18px;font-size:15px;cursor:pointer;border-bottom:none;color:var(--muted)}
.tab.on{background:var(--soft);color:var(--brand);font-weight:700;border-color:#fdba74}
main{padding:20px 0 40px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:18px;margin-bottom:14px}
.card h2{margin:0 0 4px;font-size:20px}
.meta{color:var(--muted);font-size:13px;margin:0 0 8px}
.why{margin:6px 0}
.roman{color:#9a3412;font-style:italic;margin:6px 0}
.depths{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chip{border:1px solid #fdba74;background:var(--soft);color:var(--brand);
border-radius:999px;padding:5px 12px;font-size:13px;cursor:pointer}
.chip.on{background:var(--brand);color:#fff;font-weight:700}
.btn{display:inline-block;background:var(--brand);color:#fff;border:none;border-radius:10px;
padding:10px 18px;font-size:15px;cursor:pointer;margin:4px 6px 4px 0}
.btn.ghost{background:#fff;color:var(--brand);border:1px solid var(--brand)}
.btn:disabled{opacity:.5;cursor:not-allowed}
textarea{width:100%;min-height:180px;border:1px solid var(--line);border-radius:12px;
padding:12px;font:inherit;font-size:15px;resize:vertical}
select,input[type=text]{border:1px solid var(--line);border-radius:10px;padding:9px 12px;
font:inherit;font-size:15px;background:#fff}
label{font-weight:600;font-size:14px;display:block;margin:12px 0 4px}
.hint{color:var(--muted);font-size:13px}
.sum p{margin:0 0 14px}
.idea{border-left:3px solid #fdba74;padding:2px 0 2px 12px;margin:10px 0}
.idea b{display:block}
.act{display:flex;gap:10px;align-items:flex-start;margin:8px 0}
.act input{margin-top:5px;transform:scale(1.2)}
.act.done span{text-decoration:line-through;color:var(--muted)}
.q{border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}
.q p{margin:0 0 10px;font-weight:600}
.opt{display:block;width:100%;text-align:left;background:#fff;border:1px solid var(--line);
border-radius:10px;padding:9px 12px;margin:6px 0;cursor:pointer;font:inherit;font-size:15px}
.opt:hover{border-color:var(--brand)}
.opt.right{border-color:var(--good);background:#f0fdf4}
.opt.wrong{border-color:#b91c1c;background:#fef2f2}
.whyans{font-size:14px;color:var(--muted);margin-top:8px;display:none}
.flash{border:1px solid var(--line);border-radius:12px;padding:18px;margin:10px 0;
min-height:110px;cursor:pointer;background:var(--soft)}
.flash small{color:var(--muted)}
.score{font-weight:700;font-size:17px}
.notice{background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:12px 14px;
font-size:14px;margin:12px 0}
.limits{background:#f5f5f4;border:1px solid var(--line);border-radius:14px;padding:16px 18px;
font-size:14px;color:var(--muted)}
.limits b{color:var(--ink)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.hidden{display:none}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
</style>
</head>
<body>
<header><div class="wrap">
<h1>Khulasa <span>خلاصہ</span></h1>
<p class="sub">Kitabein, 2 minute mein — muft, hamesha. No trial, no card, no auto-renewal, no account.</p>
<div class="badges">
<span class="pill">⭐ XP: <b id="xp">0</b></span>
<span class="pill">🔥 Streak: <b id="streak">0</b> din</span>
<span class="pill">📚 <b id="readCount">0</b>/6 kitabein parhi</span>
<span class="pill" id="aiPill">AI: …</span>
</div>
<div class="tabs">
<button class="tab on" id="tabLib" onclick="showTab('lib')">📚 Library</button>
<button class="tab" id="tabOwn" onclick="showTab('own')">✍️ Apna Khulasa</button>
</div>
</div></header>
<main><div class="wrap">

<!-- LIBRARY LIST -->
<section id="view-lib">
<p class="hint">6 public-domain classics — original summaries written for this app.
Har kitab 3 depths mein: <b>Flash (~1 min)</b>, <b>Standard (~2 min)</b>, <b>Deep (~4 min)</b>.
Reading time honest hai: words ÷ 200 wpm.</p>
<div id="bookGrid" class="grid"></div>
<div class="limits"><b>Honest limits:</b> yeh starter shelf 6 kitabein hain, 1,700 nahi —
asal library woh hai jo aap paste karein (Apna Khulasa). Summaries study aids hain,
kitab ka substitute nahi — har kitab ke neeche Project Gutenberg se muft full text ka link hai.</div>
</section>

<!-- READER -->
<section id="view-reader" class="hidden">
<button class="btn ghost" onclick="backToLib()">← Library</button>
<div class="card">
<h2 id="rTitle"></h2>
<p class="meta" id="rMeta"></p>
<p class="roman" id="rRoman"></p>
<div class="depths" id="rDepths"></div>
<p class="hint" id="rInfo"></p>
<div class="sum" id="rSummary"></div>
<div class="row">
<button class="btn ghost" id="readAloud" onclick="readAloud()">🔊 Suno (read aloud)</button>
<a class="btn ghost" id="rGuten" href="#" target="_blank" rel="noopener">📖 Full text (free, Gutenberg)</a>
</div>
<h3>💡 Key ideas</h3>
<div id="rIdeas"></div>
<h3>✅ Is hafte — action plan</h3>
<div id="rActions"></div>
<h3>🃏 Flashcards</h3>
<p class="hint">Card par tap karein — jawab dekhein. "Jaanta hoon" dabayein to card agle review tak chhup jata hai.</p>
<div id="rCards"></div>
<h3>🧠 Quiz — har jawab ki wazahat ke saath</h3>
<div id="rQuiz"></div>
<p class="score" id="rScore"></p>
</div>
</section>

<!-- APNA KHULASA -->
<section id="view-own" class="hidden">
<div class="card">
<h2>Apna Khulasa — apna text, apni summary</h2>
<p class="hint">Apne notes, kisi chapter ya article ka text paste karein (200–8,000 characters).
AI sirf usi text se summary banata hai — bahar se facts nahi jorta, quotes nahi gharhta.</p>
<label for="paste">Apna text</label>
<textarea id="paste" placeholder="Yahan paste karein — lecture notes, chapter, article…"></textarea>
<p class="hint" id="charCount">0 characters (min 200, max 8,000)</p>
<div class="row">
<div><label for="depth">Depth</label>
<select id="depth">
<option value="flash">Flash — ~100 words (~1 min)</option>
<option value="standard" selected>Standard — ~300 words (~2 min)</option>
<option value="deep">Deep — ~800 words (~4 min)</option>
<option value="study">Study — ~1,500 words, section by section</option>
</select></div>
<div><label for="lang">Language</label>
<select id="lang">
<option value="en" selected>English</option>
<option value="roman">Roman-Urdu</option>
<option value="ur">Urdu (script)</option>
</select></div>
</div>
<p><button class="btn" id="goBtn" onclick="summarize()">✨ Khulasa banao</button></p>
<div id="aiMsg"></div>
<div id="aiResult" class="hidden">
<h3>📝 Summary</h3>
<div class="sum" id="aiSummary"></div>
<div class="row"><button class="btn ghost" onclick="readAloudEl('aiSummary')">🔊 Suno</button></div>
<h3>💡 Key ideas</h3>
<div id="aiIdeas"></div>
<h3>✅ Action plan</h3>
<div id="aiActions"></div>
<h3>🧠 Quiz</h3>
<div id="aiQuiz"></div>
<p class="score" id="aiScore"></p>
</div>
</div>
<div class="limits"><b>AI kaise kaam karta hai:</b> aapka text Gemini ko bheja jata hai,
sirf summary banane ke liye. Kuch save nahi hota — server par kuch store nahi hota.
AI band ho (key na ho ya quota khatam) to Library ki 6 kitabein, quiz aur flashcards
phir bhi poore kaam karte hain.</div>
</section>

</div></main>
<script>
let LIB=null, CUR=null, CURDEPTH='standard', AI=false;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function store(k,v){try{localStorage.setItem('khulasa_'+k,JSON.stringify(v))}catch(e){}}
function read(k,d){try{const v=localStorage.getItem('khulasa_'+k);return v===null?d:JSON.parse(v)}catch(e){return d}}
function xp(){return read('xp',0)}
function addXp(n){store('xp',xp()+n);renderStats()}
function todayStr(){return new Date().toISOString().slice(0,10)}
function touchStreak(){const last=read('streakLast','');const n=read('streak',0);
const t=todayStr();if(last===t)return;const y=new Date(Date.now()-864e5).toISOString().slice(0,10);
store('streak',last===y?n+1:1);store('streakLast',t)}
function renderStats(){$('xp').textContent=xp();$('streak').textContent=read('streak',0);
$('readCount').textContent=(read('read',[])).length}
function showTab(t){$('tabLib').classList.toggle('on',t==='lib');$('tabOwn').classList.toggle('on',t==='own');
$('view-lib').classList.toggle('hidden',t!=='lib');$('view-own').classList.toggle('hidden',t!=='own');
$('view-reader').classList.add('hidden')}
function backToLib(){$('view-reader').classList.add('hidden');$('view-lib').classList.remove('hidden');renderStats()}

async function load(){
  touchStreak();renderStats();
  const r=await fetch('/khulasa/api/library');LIB=await r.json();
  const s=await fetch('/khulasa/api/ai-status');AI=(await s.json()).ai_available;
  $('aiPill').textContent='AI: '+(AI?'ON ✅':'OFF — Library phir bhi kaam karti hai');
  renderGrid();
}
function renderGrid(){
  $('bookGrid').innerHTML=LIB.books.map(b=>{
    const d=b.depths;
    return `<div class="card"><h2>${esc(b.title)}</h2>
    <p class="meta">${esc(b.author)} · ${esc(b.year)} · ${esc(b.category)}</p>
    <p class="why">${esc(b.why)}</p>
    <p class="roman">${esc(b.roman)}</p>
    <p class="hint">Flash ${d.flash.minutes} min · Standard ${d.standard.minutes} min · Deep ${d.deep.minutes} min</p>
    <button class="btn" onclick="openBook('${b.id}')">Parho →</button>
    <button class="btn ghost" onclick="openBook('${b.id}','quiz')">Quiz</button>
    <button class="btn ghost" onclick="openBook('${b.id}','cards')">Flashcards</button></div>`;
  }).join('');
}
function openBook(id,focus){
  CUR=LIB.books.find(b=>b.id===id);if(!CUR)return;CURDEPTH='standard';
  $('view-lib').classList.add('hidden');$('view-own').classList.add('hidden');
  $('view-reader').classList.remove('hidden');
  $('rTitle').textContent=CUR.title;$('rMeta').textContent=`${CUR.author} · ${CUR.year} · ${CUR.category}`;
  $('rRoman').textContent=CUR.roman;$('rGuten').href=CUR.gutenberg;
  renderReader();
  if(focus==='quiz')document.getElementById('rQuiz').scrollIntoView();
  if(focus==='cards')document.getElementById('rCards').scrollIntoView();
}
function renderReader(){
  const b=CUR;
  $('rDepths').innerHTML=['flash','standard','deep'].map(d=>{
    const info=b.depths[d];
    return `<button class="chip ${d===CURDEPTH?'on':''}" onclick="setDepth('${d}')">${LIB.depths[d].label} · ${info.words} words</button>`;
  }).join('');
  const info=b.depths[CURDEPTH];
  $('rInfo').textContent=`${info.words} words · ~${info.minutes} min read (200 wpm) · original summary, public-domain book`;
  $('rSummary').innerHTML=b.summaries[CURDEPTH].split('\n\n').map(p=>`<p>${esc(p)}</p>`).join('');
  $('rIdeas').innerHTML=b.key_ideas.map(i=>`<div class="idea"><b>${esc(i.idea)}</b>${esc(i.detail)}</div>`).join('');
  const done=read('act_'+b.id,[]);
  $('rActions').innerHTML=b.action_plan.map((a,i)=>`<label class="act ${done.includes(i)?'done':''}">
  <input type="checkbox" ${done.includes(i)?'checked':''} onchange="toggleAct(${i})"><span>${esc(a)}</span></label>`).join('');
  const known=read('known_'+b.id,[]);
  $('rCards').innerHTML=b.key_ideas.map((k,i)=>{
    if(known.includes(i))return '';
    return `<div class="flash" onclick="this.querySelector('.back').classList.toggle('hidden')">
    <b>${esc(k.idea)}</b><br><small>tap karein — jawab dekhein</small>
    <div class="back hidden" style="margin-top:8px">${esc(k.detail)}</div>
    <div style="margin-top:10px"><button class="btn ghost" onclick="event.stopPropagation();knowCard(${i})">Jaanta hoon ✓</button></div></div>`;
  }).join('')||'<p class="hint">Sab cards yaad ho gaye! 🎉 Kal dobara review karein.</p>';
  renderQuiz('rQuiz','rScore',b.quiz,b.id);
  const rd=read('read',[]);if(!rd.includes(b.id)){rd.push(b.id);store('read',rd);addXp(5);touchStreak();}
}
function setDepth(d){CURDEPTH=d;renderReader()}
function toggleAct(i){let done=read('act_'+CUR.id,[]);done=done.includes(i)?done.filter(x=>x!==i):[...done,i];
store('act_'+CUR.id,done);renderReader()}
function knowCard(i){let k=read('known_'+CUR.id,[]);if(!k.includes(i)){k.push(i);store('known_'+CUR.id,k);addXp(2)}renderReader()}
function renderQuiz(boxId,scoreId,quiz,tag){
  $(boxId).innerHTML=quiz.map((q,i)=>`<div class="q" data-q="${i}"><p>${i+1}. ${esc(q.q)}</p>
  ${q.options.map((o,j)=>`<button class="opt" onclick="answer(this,${i},${j},${q.answer},'${scoreId}','${tag}')">${esc(o)}</button>`).join('')}
  <p class="whyans" id="why-${tag}-${i}"><b>Wazahat:</b> ${esc(q.why)}</p></div>`).join('');
  $(scoreId).textContent='';$(scoreId).dataset.done='';
}
function answer(btn,qi,choice,correct,scoreId,tag){
  const box=btn.closest('.q');if(box.dataset.done)return;box.dataset.done='1';
  box.querySelectorAll('.opt').forEach((o,j)=>{if(j===correct)o.classList.add('right');
  if(j===choice&&j!==correct)o.classList.add('wrong');o.disabled=true});
  document.getElementById(`why-${tag}-${qi}`).style.display='block';
  const el=$(scoreId);const cur=el.dataset;
  const done=parseInt(cur.done||'0')+1;const good=parseInt(cur.good||'0')+(choice===correct?1:0);
  cur.done=done;cur.good=good;
  el.textContent=`Score: ${good}/${done} sahi`;
  if(done>=3){addXp(good*2)}
}
function readAloud(){readAloudEl('rSummary')}
function readAloudEl(id){
  if(!('speechSynthesis'in window)){alert('Is device par read-aloud nahi hai.');return}
  speechSynthesis.cancel();
  const text=document.getElementById(id).innerText;
  const u=new SpeechSynthesisUtterance(text);u.rate=0.95;speechSynthesis.speak(u);
}
$('paste').addEventListener('input',e=>{
  const n=e.target.value.length;
  $('charCount').textContent=`${n} characters (min 200, max 8,000)${n>8000?' — ZYADA LAMBA HAI':''}`;
});
async function summarize(){
  const text=$('paste').value,depth=$('depth').value,lang=$('lang').value;
  const msg=$('aiMsg');$('aiResult').classList.add('hidden');
  if(text.trim().length<200){msg.innerHTML='<div class="notice">Text thora sa hai — kam az kam 200 characters paste karein.</div>';return}
  if(text.length>8000){msg.innerHTML='<div class="notice">Text bohat lamba hai — zyada se zyada 8,000 characters.</div>';return}
  if(!AI){msg.innerHTML='<div class="notice">AI abhi OFF hai (key nahi lagi). Library ki 6 kitabein phir bhi kaam karti hain — un ke summaries, quiz aur flashcards dekhein.</div>';return}
  $('goBtn').disabled=true;$('goBtn').textContent='Ban raha hai…';
  msg.innerHTML='<p class="hint">AI aapke text se summary bana raha hai…</p>';
  try{
    const fd=new FormData();fd.append('text',text);fd.append('depth',depth);fd.append('language',lang);
    const r=await fetch('/khulasa/api/summarize',{method:'POST',body:fd});
    const data=await r.json();
    if(!data.ok){msg.innerHTML=`<div class="notice">${esc(data.error||'AI se jawab nahi mila.')}</div>`;return}
    const res=data.result;
    msg.innerHTML='';$('aiResult').classList.remove('hidden');
    $('aiSummary').innerHTML=res.summary.split('\n\n').map(p=>`<p>${esc(p)}</p>`).join('');
    $('aiIdeas').innerHTML=res.key_ideas.map(i=>`<div class="idea"><b>•</b> ${esc(i)}</div>`).join('');
    $('aiActions').innerHTML=res.action_plan.map(a=>`<div class="act"><span>☐ ${esc(a)}</span></div>`).join('');
    renderQuiz('aiQuiz','aiScore',res.quiz,'ai');
    addXp(10);touchStreak();
  }catch(e){msg.innerHTML='<div class="notice">Rabta nahi hua — dobara try karein.</div>'}
  finally{$('goBtn').disabled=false;$('goBtn').textContent='✨ Khulasa banao'}
}
load();
</script>
</body>
</html>
"""

# Back-compat alias used by older imports.
KHULASA_HTML_ALIAS = KHULASA_HTML
