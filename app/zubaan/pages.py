"""Zubaan page — single-page tutor UI.

All learning state (XP, level, streak, done scenarios) lives in
the browser's localStorage. The server only serves the content
bank and the optional AI chat. Dictation audio uses the device's
own speech synthesis — no audio files ship with the app.
"""

ZUBAAN_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zubaan — Free AI Language Tutor</title>
<style>
body{font-family:system-ui,sans-serif;margin:0;background:#f4f7f4;color:#1c2b1c}
header{background:#14532d;color:#fff;padding:14px 16px}
header h1{margin:0;font-size:22px} header p{margin:4px 0 0;opacity:.9;font-size:14px}
.wrap{max-width:760px;margin:0 auto;padding:14px}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;background:#fff;border:1px solid #cfe0cf;border-radius:12px;padding:10px 12px}
.pill{background:#e6f2e6;border-radius:999px;padding:4px 10px;font-size:13px}
.tabs{display:flex;gap:6px;margin:14px 0;flex-wrap:wrap}
.tabs button{border:1px solid #14532d;background:#fff;color:#14532d;border-radius:999px;padding:8px 14px;cursor:pointer;font-size:15px}
.tabs button.on{background:#14532d;color:#fff}
.card{background:#fff;border:1px solid #cfe0cf;border-radius:12px;padding:14px;margin-bottom:12px}
button.big{background:#14532d;color:#fff;border:0;border-radius:10px;padding:10px 16px;font-size:15px;cursor:pointer}
button.alt{background:#fff;color:#14532d;border:1px solid #14532d;border-radius:10px;padding:8px 12px;cursor:pointer}
select,input[type=text],textarea{width:100%;padding:10px;border:1px solid #b9ccb9;border-radius:10px;font-size:15px;box-sizing:border-box}
.opt{display:block;width:100%;text-align:left;margin:6px 0;background:#f7faf7;border:1px solid #cfe0cf;border-radius:10px;padding:10px;cursor:pointer;font-size:15px}
.opt.right{border-color:#14532d;background:#e6f2e6}
.opt.wrong{border-color:#b91c1c;background:#fdecea}
.rule{background:#fffbe6;border:1px solid #e7d27a;border-radius:10px;padding:10px;margin-top:8px}
.muted{color:#5a6b5a;font-size:13px}
.flash{font-size:26px;text-align:center;padding:18px 6px;cursor:pointer}
.flash .ur{font-size:30px}
.msg{white-space:pre-wrap}
.lang{float:right}
a{color:#14532d}
</style></head><body>
<header><h1>🗣️ Zubaan — Free AI Language Tutor</h1>
<p id="tag">Learn English from Urdu — unlimited, free forever. No card, no energy, no subscription.</p></header>
<div class="wrap">
<div class="bar">
<span class="pill">⭐ XP: <b id="xp">0</b></span>
<span class="pill">🎓 Level: <b id="lvl">A1</b></span>
<span class="pill">🔥 Streak: <b id="streak">0</b> din</span>
<span style="flex:1"></span>
<label class="muted">Zubaan:
<select id="uilang" style="width:auto;padding:6px">
<option value="en">English</option><option value="roman">Roman-Urdu</option><option value="ur">اردو</option>
</select></label>
</div>
<div class="tabs">
<button class="on" data-tab="learn">📖 Seekho</button>
<button data-tab="quiz">✏️ Quiz</button>
<button data-tab="chat">💬 Guftagu</button>
<button data-tab="listen">👂 Sunno</button>
</div>

<div id="tab-learn" class="tabpane">
<div class="card"><p id="learnIntro">Tap a card to flip it. Words repeat on a 1 / 3 / 7 / 14 / 30-day rhythm — come back tomorrow and the words you got right come back later.</p>
<label>Deck <select id="deck"></select></label>
<div class="card flash" id="flash"></div>
<div style="display:flex;gap:8px"><button class="alt" id="prevW">◀ Pehle</button><button class="big" id="nextW">Agla →</button><button class="alt" id="knowW">✓ Yaad hai (+5 XP)</button></div>
<p class="muted" id="deckCount"></p></div>
</div>

<div id="tab-quiz" class="tabpane" style="display:none">
<div class="card"><label>Topic <select id="topic"></select></label>
<div id="qbox" style="margin-top:12px"></div>
<button class="big" id="nextQ" style="display:none">Agla sawaal →</button>
<p class="muted">Har jawab ke baad rule samjhaya jata hai — sahi ho ya ghalat. Quiz kabhi khatam nahi hota: topics dobara khel sakte ho.</p></div>
</div>

<div id="tab-chat" class="tabpane" style="display:none">
<div class="card"><label>Scenario <select id="scen"></select></label>
<p class="muted" id="scenSet"></p><div id="chatbox"></div>
<textarea id="chatIn" rows="2" placeholder="Apna jumla English mein likhein..."></textarea>
<div style="display:flex;gap:8px;margin-top:8px"><button class="big" id="sendStep">Bhejo ✓</button><button class="alt" id="hintBtn">💡 Hint</button><button class="alt" id="aiBtn">🤖 AI se guftagu</button></div>
<p class="muted" id="aiState"></p></div>
</div>

<div id="tab-listen" class="tabpane" style="display:none">
<div class="card"><p id="listenIntro">Sunno aur likho: sentence suno, phir wohi likho. 80% lafz sahi hon to pass. Awaaz aapke device ki hai — is liye quality device par depend karti hai.</p>
<label>Deck <select id="ldeck"></select></label>
<div style="display:flex;gap:8px;margin:10px 0"><button class="big" id="speakBtn">🔊 Sunno</button><button class="alt" id="newSen">Naya jumla</button></div>
<input type="text" id="dictIn" placeholder="Jo suna, woh likhein...">
<button class="big" id="checkDict" style="margin-top:8px">Check karo ✓</button>
<div id="dictOut" style="margin-top:10px"></div></div>
</div>

<div class="card"><h3 style="margin:0 0 6px">Honest limits — imandari se</h3>
<p class="muted" style="margin:0">Ye starter course hai (51 lafz, 36 quiz sawaal, 4 scenarios) — 135M users wala course nahi. Ye aapko B1/B2 tak le jata hai, native fluency ka dawa nahi karta. Pronunciation scoring dictation se hoti hai (likh kar), acoustic analysis se nahi — browser mein muft acoustic scorer nahi hai. AI guftagu ke liye key chahiye; bina key ke scripted scenarios poore kaam karte hain.</p></div>
</div>
<script>
let BANK=null, xp=+(localStorage.getItem('zub_xp')||0), streak=+(localStorage.getItem('zub_streak')||0);
let lastDay=localStorage.getItem('zub_day')||'';
const today=new Date().toISOString().slice(0,10);
if(lastDay && lastDay!==today){
  const d=(new Date(today)-new Date(lastDay))/86400000;
  streak = (d===1)? streak+1 : 1; localStorage.setItem('zub_streak',streak);
} else if(!lastDay){ streak=1; localStorage.setItem('zub_streak',streak); }
localStorage.setItem('zub_day',today);
function levelFor(x){return x>=1200?'B2':x>=600?'B1':x>=200?'A2':'A1';}
function saveXP(g){const before=levelFor(xp); xp+=g; localStorage.setItem('zub_xp',xp);
  document.getElementById('xp').textContent=xp;
  document.getElementById('lvl').textContent=levelFor(xp);
  document.getElementById('streak').textContent=streak;
  if(levelFor(xp)!==before) alert('Mubarak! Level '+levelFor(xp)+' ho gaya! 🎉');}
document.getElementById('xp').textContent=xp;
document.getElementById('lvl').textContent=levelFor(xp);
document.getElementById('streak').textContent=streak;

document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on')); b.classList.add('on');
  document.querySelectorAll('.tabpane').forEach(p=>p.style.display='none');
  document.getElementById('tab-'+b.dataset.tab).style.display='block';});

fetch('/zubaan/api/bank').then(r=>r.json()).then(b=>{BANK=b; initLearn(); initQuiz(); initChat(); initListen();});
fetch('/zubaan/api/ai-status').then(r=>r.json()).then(s=>{
  document.getElementById('aiState').textContent = s.ai_available ? '🤖 AI ON hai — AI se guftagu ka button kaam karega.' : '🤖 AI OFF hai (key set nahi). Scripted scenarios poore kaam karte hain.';});

// ---- Seekho ----
let deckIdx=0, wordIdx=0, flipped=false;
function initLearn(){
  const sel=document.getElementById('deck'); BANK.vocab.forEach((d,i)=>{let o=document.createElement('option');o.value=i;o.textContent=d.title_en+' — '+d.title_roman;sel.appendChild(o);});
  sel.onchange=()=>{deckIdx=+sel.value;wordIdx=0;flipped=false;showWord();};
  document.getElementById('flash').onclick=()=>{flipped=!flipped;showWord();};
  document.getElementById('prevW').onclick=()=>{wordIdx=(wordIdx-1+BANK.vocab[deckIdx].words.length)%BANK.vocab[deckIdx].words.length;flipped=false;showWord();};
  document.getElementById('nextW').onclick=()=>{wordIdx=(wordIdx+1)%BANK.vocab[deckIdx].words.length;flipped=false;showWord();};
  document.getElementById('knowW').onclick=()=>{saveXP(5);document.getElementById('nextW').click();};
  showWord();}
function showWord(){const w=BANK.vocab[deckIdx].words[wordIdx];
  document.getElementById('flash').innerHTML = flipped
    ? '<div><b>'+w.en+'</b></div><div class="muted">'+w.example+'</div>'
    : '<div>'+(w.ur?'<span class="ur">'+w.ur+'</span><br>':'')+w.roman+'</div><div class="muted">Tap karo — English dekho</div>';
  document.getElementById('deckCount').textContent='Lafz '+(wordIdx+1)+' / '+BANK.vocab[deckIdx].words.length;}

// ---- Quiz ----
let qTopic=0, qIdx=0, qOrder=[];
function initQuiz(){
  const sel=document.getElementById('topic'); BANK.grammar.forEach((t,i)=>{let o=document.createElement('option');o.value=i;o.textContent=t.title_en;sel.appendChild(o);});
  sel.onchange=()=>{qTopic=+sel.value;startQuiz();}; startQuiz();
  document.getElementById('nextQ').onclick=()=>{qIdx++;showQ();};}
function startQuiz(){qOrder=BANK.grammar[qTopic].items.map((_,i)=>i).sort(()=>Math.random()-0.5);qIdx=0;showQ();}
function showQ(){const it=BANK.grammar[qTopic].items[qOrder[qIdx]];
  document.getElementById('nextQ').style.display='none';
  let h='<p><b>Sawaal '+(qIdx+1)+' / '+qOrder.length+'</b><br>'+it.q+'</p>';
  it.options.forEach((o,i)=>{h+='<button class="opt" data-i="'+i+'">'+o+'</button>';});
  h+='<div id="qrule"></div>'; document.getElementById('qbox').innerHTML=h;
  document.querySelectorAll('#qbox .opt').forEach(b=>b.onclick=()=>{
    const right=b.dataset.i==it.answer;
    document.querySelectorAll('#qbox .opt').forEach(x=>{x.disabled=true; if(x.dataset.i==it.answer)x.classList.add('right');});
    if(!right) b.classList.add('wrong'); else saveXP(10);
    document.getElementById('qrule').innerHTML='<div class="rule"><b>'+(right?'✅ Sahi!':'❌ Ghalat — sahi jawab: '+it.options[it.answer])+'</b><br>'+it.rule+'</div>';
    document.getElementById('nextQ').style.display='inline-block';
    if(qIdx>=qOrder.length-1) document.getElementById('nextQ').textContent='Dobara khelo ↻'; else document.getElementById('nextQ').textContent='Agla sawaal →';
    if(qIdx>=qOrder.length-1) document.getElementById('nextQ').onclick=()=>startQuiz(); else document.getElementById('nextQ').onclick=()=>{qIdx++;showQ();};
  });}

// ---- Guftagu ----
let scenIdx=0, stepIdx=0, aiMode=false, hist=[];
function initChat(){
  const sel=document.getElementById('scen'); BANK.scenarios.forEach((s,i)=>{let o=document.createElement('option');o.value=i;o.textContent=s.title_en+' — '+s.title_roman;sel.appendChild(o);});
  sel.onchange=()=>{scenIdx=+sel.value;startScen();}; startScen();
  document.getElementById('sendStep').onclick=sendStep;
  document.getElementById('hintBtn').onclick=()=>{if(aiMode)return; const st=BANK.scenarios[scenIdx].steps[stepIdx]; addMsg('hint','💡 Hint: '+st.hint);};
  document.getElementById('aiBtn').onclick=()=>{aiMode=!aiMode; hist=[];
    addMsg('ai', aiMode?'🤖 AI mode ON — ab aap khul kar baat kar sakte hain. AI aapka jumla correct karke scene jaari rakhega.':'🤖 AI mode OFF — wapas scripted scenario par.');};}
function startScen(){stepIdx=0;aiMode=false;hist=[];document.getElementById('chatbox').innerHTML='';
  const s=BANK.scenarios[scenIdx]; document.getElementById('scenSet').textContent=s.setting;
  addMsg('ai','🎬 '+s.title_en+' — '+s.steps[0].prompt);}
function addMsg(who,txt){const d=document.createElement('div');d.className='card msg';d.style.marginBottom='8px';
  d.innerHTML='<b>'+(who==='you'?'🧑 Aap':who==='hint'?'💡 Hint':'🤖 Partner')+':</b> '+txt.replace(/</g,'&lt;');
  document.getElementById('chatbox').appendChild(d); d.scrollIntoView(false);}
function sendStep(){const txt=document.getElementById('chatIn').value.trim(); if(!txt)return;
  addMsg('you',txt); document.getElementById('chatIn').value='';
  if(aiMode){ hist.push({who:'you',text:txt});
    const s=BANK.scenarios[scenIdx];
    const fd=new FormData(); fd.append('scenario',s.title_en); fd.append('setting',s.setting);
    fd.append('history',JSON.stringify(hist)); fd.append('text',txt);
    fetch('/zubaan/api/roleplay',{method:'POST',body:fd}).then(r=>r.json()).then(j=>{
      if(j.ok){addMsg('ai',j.reply); hist.push({who:'ai',text:j.reply});}
      else addMsg('ai','⚠️ '+j.error);});
    return;}
  const st=BANK.scenarios[scenIdx].steps[stepIdx];
  const fd=new FormData(); fd.append('payload',JSON.stringify({keywords:st.keywords,text:txt}));
  fetch('/zubaan/api/score-step',{method:'POST',body:fd}).then(r=>r.json()).then(j=>{
    if(j.passed){saveXP(15); addMsg('ai','✅ Zabardast! ('+j.matched+'/'+j.total+' lafz mile) — Model: “'+st.model+'”');}
    else addMsg('ai','👍 Koshish achhi hai ('+j.matched+'/'+j.total+' lafz mile). Model: “'+st.model+'” — dobara try karein ya agle step par jayein.');
    stepIdx++;
    const s=BANK.scenarios[scenIdx];
    if(stepIdx<s.steps.length) addMsg('ai','➡️ '+s.steps[stepIdx].prompt);
    else {addMsg('ai','🎉 Scenario mukammal! Dobara khelne ke liye scenario dobara select karein.'); stepIdx=0; addMsg('ai','➡️ '+s.steps[0].prompt);}
  });}

// ---- Sunno ----
let senDeck=0, curSen='';
function initListen(){
  const sel=document.getElementById('ldeck'); BANK.vocab.forEach((d,i)=>{let o=document.createElement('option');o.value=i;o.textContent=d.title_en;sel.appendChild(o);});
  const lsel=document.getElementById('ldeck'); lsel.onchange=()=>{senDeck=+lsel.value;newSen();}; newSen();
  document.getElementById('speakBtn').onclick=()=>{if(!curSen)return;
    const u=new SpeechSynthesisUtterance(curSen); u.lang='en-US'; u.rate=0.85; speechSynthesis.speak(u);};
  document.getElementById('newSen').onclick=newSen;
  document.getElementById('checkDict').onclick=()=>{
    const typed=document.getElementById('dictIn').value;
    const fd=new FormData(); fd.append('payload',JSON.stringify({target:curSen,typed:typed}));
    fetch('/zubaan/api/dictation',{method:'POST',body:fd}).then(r=>r.json()).then(j=>{
      if(j.passed) saveXP(10);
      document.getElementById('dictOut').innerHTML='<div class="rule"><b>'+(j.passed?'✅ Pass! ':'❌ Dobara suno — ')+'Score: '+Math.round(j.score*100)+'%</b><br>Sahi jumla: “'+curSen+'”</div>';});};}
function newSen(){const w=BANK.vocab[senDeck].words[Math.floor(Math.random()*BANK.vocab[senDeck].words.length)];
  curSen=w.example; document.getElementById('dictIn').value=''; document.getElementById('dictOut').innerHTML='';}
</script></body></html>
"""
