"""Bayan single-page app HTML (no external dependencies)."""
BAYAN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bayan — free AI slide decks</title>
<style>
:root{--bg:#0F1B2D;--card:#1B2A44;--accent:#F2A900;--text:#fff;--muted:#9FB2CC}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.5}
.wrap{max-width:960px;margin:0 auto;padding:20px}
header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px}
h1{margin:0;font-size:28px}.tag{color:var(--accent);font-size:14px}
.honest{background:#12233a;border:1px solid #2a3f5f;border-radius:10px;padding:10px 14px;
margin:14px 0;font-size:13px;color:var(--muted)}
.honest b{color:var(--text)}
.card{background:var(--card);border-radius:12px;padding:16px;margin:12px 0}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
input[type=text],input[type=number],textarea,select{width:100%;background:#0d1828;color:var(--text);
border:1px solid #2a3f5f;border-radius:8px;padding:10px;font-size:15px}
textarea{min-height:90px;resize:vertical}
.row{display:flex;gap:10px;flex-wrap:wrap}.row>*{flex:1;min-width:140px}
button{background:var(--accent);color:#111;border:0;border-radius:8px;padding:11px 18px;
font-size:15px;font-weight:700;cursor:pointer;margin:8px 6px 0 0}
button.ghost{background:transparent;color:var(--text);border:1px solid #2a3f5f}
button.small{padding:6px 10px;font-size:13px;margin:4px 4px 0 0}
button:disabled{opacity:.5;cursor:wait}
.badge{display:inline-block;background:#0d1828;border:1px solid #2a3f5f;border-radius:20px;
padding:3px 12px;font-size:12px;color:var(--muted);margin-right:6px}
.slidecard{background:#0d1828;border:1px solid #2a3f5f;border-radius:10px;padding:12px;margin:10px 0}
.slidecard h3{margin:0 0 6px;font-size:15px}
.warn{background:#3a2a08;border:1px solid #7a5c10;color:#ffd97a;border-radius:8px;
padding:8px 12px;font-size:13px;margin:8px 0}
.err{background:#3a1414;border:1px solid #7a2020;color:#ff9a9a;border-radius:8px;
padding:8px 12px;font-size:13px;margin:8px 0}
#viewer{background:#000;border-radius:12px;padding:12px;margin:12px 0}
#slideStage{position:relative;width:100%;aspect-ratio:16/9;border-radius:8px;overflow:hidden}
.pslide{position:absolute;inset:0;padding:5%;display:none;flex-direction:column;justify-content:center}
.pslide.active{display:flex}
.pslide h2{margin:0 0 12px;font-size:clamp(18px,4vw,40px)}
.pslide ul{margin:0;padding-left:24px;font-size:clamp(13px,2.2vw,22px)}
.pslide li{margin:8px 0}
.pslide .stat-v{font-size:clamp(28px,7vw,72px);font-weight:800}
.pslide .stat-l{font-size:clamp(12px,2vw,20px);opacity:.75}
.pslide .quote{font-style:italic;font-size:clamp(16px,3.4vw,34px);text-align:center}
.pslide .by{text-align:center;opacity:.7;margin-top:12px}
.pslide .cover-t{text-align:center;font-size:clamp(22px,5vw,52px);font-weight:800}
.pslide .cover-s{text-align:center;opacity:.75;margin-top:10px;font-size:clamp(13px,2.4vw,24px)}
.nav{display:flex;justify-content:space-between;align-items:center;margin-top:8px}
footer{color:var(--muted);font-size:12px;margin:26px 0;text-align:center}
.hidden{display:none}
</style>
</head>
<body>
<div class="wrap">
<header>
<div><h1>Bayan <span class="tag">بیان</span></h1>
<div style="color:var(--muted);font-size:14px">AI slide decks — free forever, no credits, no branding on exports.</div></div>
<div><span class="badge" id="aiBadge">AI: checking…</span></div>
</header>

<div class="honest">
<b>Honest limits:</b> AI outlines are <b>drafts</b> — verify facts before presenting.
AI generation runs on the owner's free Gemini quota (the badge above shows live status).
Your drafts stay in <b>your browser</b> — the server stores nothing and trains on nothing.
Exports carry <b>zero branding</b>.
</div>

<div class="card" id="step1">
<h2 style="margin-top:0">1 · Describe your deck</h2>
<label>Topic</label>
<input type="text" id="topic" placeholder="e.g. MDCAT preparation strategy, or apni dukaan ka pitch">
<label>Your notes (optional — paste rough points; the AI structures them)</label>
<textarea id="notes" placeholder="One point per line. Lines ending with ':' become section headers."></textarea>
<div class="row">
<div><label>Slides (3–20)</label><input type="number" id="count" value="8" min="3" max="20"></div>
<div><label>Tone</label><select id="tone">
<option value="punchy">Punchy (pitch)</option><option value="formal">Formal</option>
<option value="academic">Academic</option><option value="friendly">Friendly</option></select></div>
<div><label>Theme</label><select id="theme">
<option value="midnight">Midnight</option><option value="paper">Paper</option>
<option value="forest">Forest</option></select></div>
</div>
<div><button id="btnAI">Generate outline (AI)</button>
<button class="ghost" id="btnRule">Draft from my notes (no AI)</button></div>
<div id="warn1"></div>
</div>

<div class="card hidden" id="step2">
<h2 style="margin-top:0">2 · Edit the outline</h2>
<div id="warn2"></div>
<div id="editor"></div>
<div><button class="ghost small" id="btnAdd">+ Add slide</button>
<button id="btnPreview">Preview deck →</button></div>
</div>

<div class="card hidden" id="step3">
<h2 style="margin-top:0">3 · Preview &amp; export</h2>
<div id="viewer"><div id="slideStage"></div>
<div class="nav"><div>
<button class="ghost small" id="btnPrev">← Prev</button>
<button class="ghost small" id="btnNext">Next →</button>
<span class="badge" id="pgNum"></span></div>
<div><button class="ghost small" id="btnPresent">⛶ Present</button>
<button class="small" id="btnPptx">Download .pptx</button>
<button class="ghost small" id="btnPrint">Print / PDF</button></div>
</div></div>
<div><button class="ghost" id="btnBack">← Back to outline</button></div>
</div>

<footer>Bayan — an original build. Not affiliated with Gamma or any presentation tool.<br>
AI output is a draft; you own your content.</footer>
</div>

<script>
const S = {deck:null, theme:'midnight', tone:'punchy', idx:0, ai:false};
const $ = id => document.getElementById(id);
const THEMES = {
 midnight:{bg:'#0F1B2D',accent:'#F2A900',text:'#FFFFFF',muted:'#9FB2CC',card:'#1B2A44'},
 paper:{bg:'#FFFFFF',accent:'#1D4ED8',text:'#111827',muted:'#6B7280',card:'#F3F4F6'},
 forest:{bg:'#0C2318',accent:'#7BC47F',text:'#FFFFFF',muted:'#A8C3B0',card:'#14301F'}};

async function api(path, body){
  const r = await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body||{})});
  return r.json();
}
function showWarn(el, msgs){
  $(el).innerHTML = (msgs||[]).map(m=>'<div class="warn">'+esc(m)+'</div>').join('');
}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

fetch('/bayan/api/ai-status').then(r=>r.json()).then(j=>{
  $('aiBadge').textContent = 'AI: ' + (j.ai_available ? 'online ✓' : 'offline — rule-based mode');
}).catch(()=>{$('aiBadge').textContent='AI: unknown';});

async function genOutline(useAI){
  const btn = useAI ? $('btnAI') : $('btnRule');
  btn.disabled = true;
  try{
    const j = await api('/bayan/api/outline',{topic:$('topic').value,notes:$('notes').value,
      slide_count:parseInt($('count').value||'8'),tone:$('tone').value,use_ai:useAI});
    if(j.error){ showWarn('warn1',[j.error]); return; }
    S.deck=j.deck; S.ai=!!j.ai; S.theme=$('theme').value; S.tone=$('tone').value;
    showWarn('warn1',[]); showWarn('warn2',j.warnings);
    $('step2').classList.remove('hidden'); $('step3').classList.add('hidden');
    renderEditor(); saveDraft();
    $('step2').scrollIntoView({behavior:'smooth'});
  }finally{ btn.disabled=false; }
}
$('btnAI').onclick=()=>genOutline(true);
$('btnRule').onclick=()=>genOutline(false);

function layoutOptions(sel){
  return ['cover','section','bullets','stats','quote','closing']
    .map(l=>'<option value="'+l+'"'+(l===sel?' selected':'')+'>'+l+'</option>').join('');
}
function renderEditor(){
  const ed=$('editor'); ed.innerHTML='';
  S.deck.slides.forEach((s,i)=>{
    const d=document.createElement('div'); d.className='slidecard';
    let extra='';
    if(s.layout==='stats'){
      const txt=(s.stats||[]).map(x=>x.value+' :: '+x.label).join('\n');
      extra='<label>Stats (one per line: value :: label)</label><textarea data-k="stats" rows="2">'+esc(txt)+'</textarea>';
    } else if(s.layout==='quote'){
      extra='<label>Attribution</label><input type="text" data-k="quote_by" value="'+esc(s.quote_by||'')+'">';
    }
    d.innerHTML='<h3>Slide '+(i+1)+' <span class="badge">'+esc(s.layout)+'</span></h3>'
      +'<div class="row"><div><label>Layout</label><select data-k="layout">'+layoutOptions(s.layout)+'</select></div></div>'
      +'<label>Title</label><input type="text" data-k="title" value="'+esc(s.title||'')+'">'
      +'<label>Bullets (one per line)</label><textarea data-k="bullets" rows="3">'+esc((s.bullets||[]).join('\n'))+'</textarea>'
      +'<label>Speaker notes</label><input type="text" data-k="notes" value="'+esc(s.notes||'')+'">'
      +extra
      +'<div><button class="ghost small" data-a="regen">✨ Regenerate</button>'
      +'<button class="ghost small" data-a="up">↑</button>'
      +'<button class="ghost small" data-a="down">↓</button>'
      +'<button class="ghost small" data-a="del">Delete</button></div>';
    d.querySelectorAll('[data-k]').forEach(inp=>{
      inp.onchange=()=>{ readCard(d,i); saveDraft(); };
    });
    d.querySelectorAll('[data-a]').forEach(b=>{
      b.onclick=()=>slideAction(i,b.dataset.a);
    });
    ed.appendChild(d);
  });
}
function readCard(cardEl,i){
  const s=S.deck.slides[i];
  cardEl.querySelectorAll('[data-k]').forEach(inp=>{
    const k=inp.dataset.k;
    if(k==='bullets') s.bullets=inp.value.split('\n').map(x=>x.trim()).filter(Boolean);
    else if(k==='stats') s.stats=inp.value.split('\n').map(x=>x.trim()).filter(Boolean)
      .map(x=>{const p=x.split('::');return {value:(p[0]||'').trim(),label:(p[1]||'').trim()};});
    else s[k]=inp.value;
  });
}
function syncEditor(){
  [...$('editor').children].forEach((c,i)=>readCard(c,i));
}
async function slideAction(i,a){
  syncEditor();
  const slides=S.deck.slides;
  if(a==='del'){ if(slides.length>1){slides.splice(i,1);} }
  else if(a==='up'&&i>0){ [slides[i-1],slides[i]]=[slides[i],slides[i-1]]; }
  else if(a==='down'&&i<slides.length-1){ [slides[i+1],slides[i]]=[slides[i],slides[i+1]]; }
  else if(a==='regen'){
    const ins=prompt('Is slide ko kya badalna hai? (e.g. "make it punchier", "add a stat from my notes")');
    if(!ins) return;
    const j=await api('/bayan/api/regenerate-slide',{deck_title:S.deck.title,
      slide:slides[i],instruction:ins,tone:S.tone});
    if(j.error){ alert(j.error); return; }
    slides[i]=j.slide;
  }
  renderEditor(); saveDraft();
}
$('btnAdd').onclick=()=>{ syncEditor();
  S.deck.slides.push({layout:'bullets',title:'New slide',bullets:['Point one'],notes:'',quote_by:'',stats:[]});
  renderEditor(); saveDraft(); };

function renderSlide(s, theme){
  const t=THEMES[theme]||THEMES.midnight;
  const d=document.createElement('div'); d.className='pslide';
  d.style.background=t.bg; d.style.color=t.text;
  let h='';
  if(s.layout==='cover'){
    h='<div class="cover-t">'+esc(s.title)+'</div>';
    const sub=(s.bullets&&s.bullets[0])||S.deck.subtitle;
    if(sub) h+='<div class="cover-s">'+esc(sub)+'</div>';
    h='<div style="height:8px;background:'+t.accent+';margin-bottom:24px"></div>'+h;
  }else if(s.layout==='section'){
    h='<div style="height:8px;width:80px;background:'+t.accent+';margin-bottom:16px"></div>'
      +'<h2 style="font-size:clamp(24px,5vw,54px)">'+esc(s.title)+'</h2>';
    d.style.background=t.card;
  }else if(s.layout==='stats'){
    h='<h2>'+esc(s.title)+'</h2><div class="row">'
      +(s.stats||[]).map(x=>'<div style="text-align:center"><div class="stat-v" style="color:'+t.accent+'">'
        +esc(x.value)+'</div><div class="stat-l">'+esc(x.label)+'</div></div>').join('')+'</div>';
  }else if(s.layout==='quote'){
    const q=(s.bullets&&s.bullets[0])||s.title;
    h='<div class="quote">“'+esc(q)+'”</div>';
    if(s.quote_by) h+='<div class="by">— '+esc(s.quote_by)+'</div>';
    d.style.background=t.card;
  }else if(s.layout==='closing'){
    h='<div class="cover-t">Thank you</div><div class="cover-s" style="color:'+t.accent+'">'
      +esc(s.title)+'</div>';
  }else{
    h='<h2>'+esc(s.title)+'</h2>';
    if(s.layout==='bullets'&&s.bullets&&s.bullets.length)
      h+='<ul>'+s.bullets.map(b=>'<li>'+esc(b)+'</li>').join('')+'</ul>';
    if(s.notes) h+='<div style="opacity:.55;font-size:12px;margin-top:10px;font-style:italic">Notes: '+esc(s.notes)+'</div>';
  }
  d.innerHTML=h; return d;
}
function showSlide(i){
  const n=S.deck.slides.length;
  S.idx=((i%n)+n)%n;
  const stage=$('slideStage'); stage.innerHTML='';
  const el=renderSlide(S.deck.slides[S.idx],S.theme); el.classList.add('active');
  stage.appendChild(el);
  $('pgNum').textContent=(S.idx+1)+' / '+n;
}
$('btnPreview').onclick=()=>{ syncEditor();
  $('step3').classList.remove('hidden'); showSlide(0);
  $('step3').scrollIntoView({behavior:'smooth'}); };
$('btnPrev').onclick=()=>showSlide(S.idx-1);
$('btnNext').onclick=()=>showSlide(S.idx+1);
$('btnBack').onclick=()=>{ $('step3').classList.add('hidden'); };
document.addEventListener('keydown',e=>{
  if($('step3').classList.contains('hidden'))return;
  if(e.key==='ArrowRight')showSlide(S.idx+1);
  if(e.key==='ArrowLeft')showSlide(S.idx-1);
});
$('btnPresent').onclick=()=>{ const v=$('viewer');
  if(document.fullscreenElement)document.exitFullscreen();
  else if(v.requestFullscreen)v.requestFullscreen(); };
$('btnPrint').onclick=()=>window.print();
$('btnPptx').onclick=async()=>{
  syncEditor();
  const r=await fetch('/bayan/api/download-pptx',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({deck:S.deck,theme:S.theme})});
  if(!r.ok){ alert('PPTX download failed.'); return; }
  const blob=await r.blob();
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  const cd=r.headers.get('Content-Disposition')||'';
  const m=cd.match(/filename="([^"]+)"/);
  a.download=m?m[1]:'bayan-deck.pptx'; a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),4000);
};
function saveDraft(){
  try{localStorage.setItem('bayan_draft',JSON.stringify({deck:S.deck,theme:S.theme,tone:S.tone,
    topic:$('topic').value,notes:$('notes').value}));}catch(e){}
}
(function loadDraft(){
  try{const j=JSON.parse(localStorage.getItem('bayan_draft')||'null'); if(!j||!j.deck)return;
    S.deck=j.deck;S.theme=j.theme||'midnight';S.tone=j.tone||'punchy';
    $('topic').value=j.topic||'';$('notes').value=j.notes||'';$('theme').value=S.theme;$('tone').value=S.tone;
    $('step2').classList.remove('hidden');renderEditor();
  }catch(e){}
})();
</script>
</body>
</html>
"""
