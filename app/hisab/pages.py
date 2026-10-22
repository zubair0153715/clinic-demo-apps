"""Hisab single-page UI."""

HISAB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hisab (حساب) — free AI math tutor</title>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js" async></script>
<style>
:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--txt:#e2e8f0;--dim:#94a3b8;
--acc:#38bdf8;--ok:#34d399;--warn:#fbbf24}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--txt);font-family:system-ui,-apple-system,
"Segoe UI",Roboto,"Noto Nastaliq Urdu",sans-serif;margin:0;padding:0 12px 60px}
.wrap{max-width:760px;margin:0 auto}
header{padding:26px 4px 8px}
h1{font-size:28px;margin:0}
h1 .ur{color:var(--acc)}
.sub{color:var(--dim);font-size:14px;margin:6px 0 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:16px;margin:14px 0}
textarea{width:100%;min-height:74px;background:#0b1220;color:var(--txt);
border:1px solid var(--line);border-radius:8px;padding:10px;font-size:16px;
font-family:ui-monospace,monospace}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
button{background:var(--acc);color:#06202e;border:0;border-radius:8px;
padding:10px 18px;font-size:15px;font-weight:700;cursor:pointer}
button.ghost{background:transparent;color:var(--acc);border:1px solid var(--acc)}
button:disabled{opacity:.5;cursor:wait}
select{background:#0b1220;color:var(--txt);border:1px solid var(--line);
border-radius:8px;padding:9px}
.step{border-right:3px solid var(--acc);background:#0b1220;border-radius:8px;
padding:10px 12px;margin:10px 0}
.step h4{margin:0 0 4px;font-size:14px;color:var(--acc)}
.step .math{font-family:ui-monospace,monospace;font-size:16px;white-space:pre-wrap}
.step .note{color:var(--dim);font-size:13px;margin-top:4px}
.answer{background:#052e22;border:1px solid #065f46;border-radius:8px;
padding:12px;margin-top:12px;font-size:18px}
.warn{color:var(--warn);font-size:13px}
.err{color:#f87171;font-size:14px}
.dim{color:var(--dim);font-size:13px}
.chatlog{max-height:260px;overflow-y:auto;margin:10px 0}
.msg{padding:8px 10px;border-radius:8px;margin:6px 0;font-size:14px}
.msg.u{background:#0b1220;text-align:left}
.msg.a{background:#132b1f}
footer{color:var(--dim);font-size:12px;margin-top:26px;line-height:1.7}
.kbd{background:#0b1220;border:1px solid var(--line);border-radius:4px;
padding:1px 6px;font-family:ui-monospace,monospace;font-size:12px}
.urdir{direction:rtl;text-align:right}
input[type=file]{color:var(--dim);font-size:13px}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>Hisab <span class="ur">حساب</span></h1>
<p class="sub">Free AI math tutor — photo ya type karo, <b>steps hamesha free</b>,
jawab computer-algebra se verify shuda. <span class="dim">Not affiliated with
Photomath or Gauth.</span></p>
</header>

<div class="card">
<div class="row" style="margin-top:0">
<label class="dim">Photo:</label>
<input type="file" id="photo" accept="image/*">
<button class="ghost" id="readBtn" onclick="readPhoto()">Photo parho</button>
<span class="dim" id="aiBadge"></span>
</div>
<textarea id="prob" placeholder="Masla yahan likho… misaal: 2x^2+5x-3=0 &#10;d/dx x^3+2x &#10;∫ 3x^2 dx &#10;lim x->0 sin(x)/x"></textarea>
<div class="row">
<select id="mode">
<option value="auto">Auto-detect</option>
<option value="solve">Equation hal karo</option>
<option value="simplify">Simplify</option>
<option value="factor">Factor</option>
<option value="expand">Expand</option>
<option value="differentiate">Differentiate</option>
<option value="integrate">Integrate</option>
</select>
<select id="lang">
<option value="en">Wazahat: English</option>
<option value="ur">Wazahat: اردو</option>
</select>
<button id="solveBtn" onclick="solve()">Hal karo</button>
</div>
<div id="status"></div>
</div>

<div id="result"></div>

<div class="card" id="chatCard" style="display:none">
<h3 style="margin:0 0 4px">Sawal poocho <span class="dim">— hal ke steps se</span></h3>
<div class="chatlog" id="chatlog"></div>
<div class="row">
<input id="q" placeholder="Misaal: discriminant kyun nikala?"
style="flex:1;background:#0b1220;color:var(--txt);border:1px solid var(--line);
border-radius:8px;padding:10px;font-size:14px" onkeydown="if(event.key==='Enter')ask()">
<button class="ghost" onclick="ask()">Bhejo</button>
</div>
</div>

<footer>
<b>Engine:</b> har jawab SymPy (exact computer algebra) se compute hota hai —
steps usi computation se nikle hain, is liye jawab se hat nahi sakte.
<b>AI:</b> photo parhna aur wazahat Gemini (free tier) par chalti hai; quota
khatam ho ya key na ho to <b>typed hal hamesha kaam karta hai</b> — koi paywall nahi.
Hisab koi data store nahi karta. Photomath/Google ya Gauth/ByteDance se koi
ta'alluq nahi.
</footer>
</div>

<script>
let lastSolution=null, lastLang='en', chatHist='';
async function api(path, body){
  const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(body)});
  return r.json();
}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function setStatus(h){document.getElementById('status').innerHTML=h;}

fetch('/hisab/api/ai-status').then(r=>r.json()).then(d=>{
  document.getElementById('aiBadge').textContent =
    d.ai_available ? '● AI ready' : '○ AI off — typed hal phir bhi free';
});

async function readPhoto(){
  const f=document.getElementById('photo').files[0];
  if(!f){setStatus('<p class="err">Pehle photo choose karo.</p>');return;}
  setStatus('<p class="dim">Photo parh rahe hain…</p>');
  const fd=new FormData(); fd.append('photo',f);
  try{
    const r=await fetch('/hisab/api/read-photo',{method:'POST',body:fd});
    const d=await r.json();
    if(d.error){setStatus('<p class="err">'+esc(d.error)+'</p>');return;}
    document.getElementById('prob').value=d.problem||'';
    setStatus('<p class="dim">Photo se nikla: <span class="kbd">'+esc(d.problem)+
      '</span> ('+esc(d.confidence||'')+' confidence) — ab "Hal karo" dabao.</p>');
  }catch(e){setStatus('<p class="err">Photo bhejne mein masla: '+esc(e.message)+'</p>');}
}

async function solve(){
  const text=document.getElementById('prob').value.trim();
  if(!text){setStatus('<p class="err">Masla likho ya photo upload karo.</p>');return;}
  lastLang=document.getElementById('lang').value;
  const btn=document.getElementById('solveBtn'); btn.disabled=true;
  setStatus('<p class="dim">Hal ho raha hai…</p>');
  document.getElementById('result').innerHTML='';
  document.getElementById('chatCard').style.display='none';
  try{
    const d=await api('/hisab/api/solve',{text,
      mode:document.getElementById('mode').value, lang:lastLang, use_ai:true});
    if(d.error){setStatus('<p class="err">'+esc(d.error)+'</p>');return;}
    lastSolution=d.solution; chatHist='';
    render(d); setStatus(warnHtml(d.warnings));
  }catch(e){setStatus('<p class="err">Masla: '+esc(e.message)+'</p>');}
  btn.disabled=false;
}
function warnHtml(w){
  return (w||[]).map(x=>'<p class="warn">⚠ '+esc(x)+'</p>').join('');
}
function render(d){
  const s=d.solution, ur = lastLang==='ur';
  let h='<div class="card"><h3 style="margin:0">Hal <span class="dim">('+esc(s.kind)+
    ' · '+esc(s.engine)+')</span></h3>';
  s.steps.forEach((st,i)=>{
    h+='<div class="step"><h4>Step '+(i+1)+': '+esc(st.title)+'</h4>'+
       '<div class="math">'+esc(st.math)+'</div>'+
       (st.note?'<div class="note">'+esc(st.note)+'</div>':'')+'</div>';
  });
  h+='<div class="answer">Jawab: \\['+esc(s.answer_latex)+'\\]</div>';
  if(d.explanation){
    const e=d.explanation;
    h+='<h3 style="margin:16px 0 4px">Wazahat '+(d.ai?'<span class="dim">(AI)</span>':'')+'</h3>';
    if(e.key_idea) h+='<p><b>Asal nukta:</b> <span class="'+(ur?'urdir':'')+'">'+esc(e.key_idea)+'</span></p>';
    (e.walkthrough||[]).forEach(p=>{
      h+='<p class="'+(ur?'urdir':'')+'">'+esc(p)+'</p>';});
    if(e.common_mistake) h+='<p class="warn">Aam ghalti: '+esc(e.common_mistake)+'</p>';
  }
  h+='</div>';
  const el=document.getElementById('result'); el.innerHTML=h;
  if(window.MathJax) MathJax.typesetPromise([el]).catch(()=>{});
  document.getElementById('chatCard').style.display='block';
  document.getElementById('chatlog').innerHTML='';
}
function addMsg(who,txt,ur){
  const d=document.createElement('div');
  d.className='msg '+who; d.innerHTML=esc(txt);
  if(ur&&who==='a') d.classList.add('urdir');
  const log=document.getElementById('chatlog');
  log.appendChild(d); log.scrollTop=log.scrollHeight;
}
async function ask(){
  const q=document.getElementById('q').value.trim();
  if(!q||!lastSolution) return;
  document.getElementById('q').value='';
  addMsg('u',q);
  addMsg('a','…');
  const log=document.getElementById('chatlog');
  try{
    const d=await api('/hisab/api/chat',{solution:lastSolution,question:q,
      lang:lastLang,history:chatHist});
    log.lastChild.remove();
    if(d.error){addMsg('a','⚠ '+d.error);}
    else{addMsg('a',d.answer,lastLang==='ur');
      chatHist+='\\nSawal: '+q+'\\nJawab: '+d.answer;}
  }catch(e){log.lastChild.remove();addMsg('a','⚠ '+e.message);}
}
</script>
</body>
</html>
"""
