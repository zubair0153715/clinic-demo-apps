# -*- coding: utf-8 -*-
"""Zehn page — single self-contained HTML page.

Everything runs in the browser: the server only generates rounds,
scores answers, computes Zehn Scores and (optionally) AI text.
Scores and levels live in localStorage; nothing is stored
server-side. No account, no card, no ads.
"""

ZEHN_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zehn — ذہن | Free brain-training studio</title>
<style>
:root{--ink:#1e293b;--bg:#f0f9ff;--card:#ffffff;--line:#dbeafe;--acc:#0369a1;--acc2:#0f766e;--soft:#e0f2fe}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:linear-gradient(135deg,#0c4a6e,#0369a1);color:#fff;padding:26px 16px 20px;text-align:center}
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
.pill{display:inline-block;background:var(--soft);border:1px solid #7dd3fc;border-radius:999px;padding:3px 10px;font-size:13px;margin:2px}
.bar{height:14px;background:#38bdf8;border-radius:7px}
.barwrap{background:#e0f2fe;border-radius:7px;margin:4px 0 10px}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:var(--soft)}
.gamebtn{font-size:15px;padding:12px 14px;text-align:left;background:#fff;border:2px solid var(--line);border-radius:12px;cursor:pointer;color:var(--ink);width:100%}
.gamebtn.sel{border-color:var(--acc);background:var(--soft)}
.big{font-size:44px;font-weight:700;text-align:center;padding:18px 0;letter-spacing:6px}
.stroopword{font-size:52px;font-weight:800;text-align:center;padding:18px 0}
.colorbtn{flex:1;min-width:100px;padding:14px;font-size:16px;font-weight:700;border-radius:12px;border:0;cursor:pointer;color:#fff}
.grid{display:grid;gap:8px;max-width:320px;margin:12px auto}
.cell{aspect-ratio:1;border-radius:10px;border:2px solid #7dd3fc;background:#f0f9ff;cursor:pointer;font-size:20px}
.cell.lit{background:#facc15;border-color:#eab308}
.cell.picked{background:#38bdf8;border-color:#0369a1;color:#fff}
.ai{border-left:4px solid var(--acc2);background:#f0fdfa;padding:10px 12px;border-radius:8px;margin:10px 0}
.err{color:#b91c1c;font-size:14px}
.ok{color:#0f766e;font-size:14px}
.center{text-align:center}
footer{max-width:780px;margin:0 auto;padding:0 16px 30px;color:#64748b;font-size:13px}
</style>
</head>
<body>
<header>
<h1>Zehn — ذہن</h1>
<p>Free brain-training studio · 5 games, all levels, all free — no account, no card, no ads, no "Premium".</p>
</header>
<main>

<div class="card center">
<h2>Aapka Zehn Score</h2>
<p class="muted">0–100 per skill · 70% accuracy + 30% speed (target time ke muqable me). Formula page par likha hai — koi black box nahi.</p>
<div id="skillBars"></div>
<p><span class="pill" id="pillGames">0 games played</span>
<span class="pill" id="pillBest">Best: —</span></p>
<div class="row" style="justify-content:center">
<button id="zenToggle" class="ghost">Zen practice: OFF — scores count</button>
</div>
<p class="muted">Zen practice = bina score ke khelna. Lumosity ye mode 50 games ke baad aur Premium me deta hai — yahan pehle game se free hai.</p>
</div>

<div class="card">
<h2>Aaj ka workout — 5 games</h2>
<p class="muted" id="workoutNote">Har din order badalta hai; sab se kamzor skill pehle aati hai.</p>
<div id="workoutList"></div>
</div>

<div class="card">
<h2>Khel chunein</h2>
<div class="row" id="gameList" style="flex-direction:column;align-items:stretch"></div>
<label for="levelSel">Level (1–5) — acha kheleinge to level khud barhega</label>
<select id="levelSel"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option></select>
</div>

<div class="card" id="playCard" style="display:none">
<h2 id="playTitle">Khel</h2>
<div id="playArea"></div>
<p id="playMsg" class="ok"></p>
</div>

<div class="card">
<h2>AI coach — aaj ka tip &amp; weekly summary</h2>
<p class="muted" id="aiStatus">Checking AI…</p>
<div class="row"><button id="tipBtn">Aaj ka AI tip</button></div>
<div id="tipOut" class="ai" style="display:none"></div>
<div class="row" style="margin-top:10px"><button id="sumBtn" class="ghost">Weekly AI summary</button></div>
<div id="sumOut" class="ai" style="display:none"></div>
<p class="muted">AI text is labelled AI-written. Without a key, all five games, workouts, scores and Zen practice still work fully.</p>
</div>

<div class="card">
<h2>Lumosity vs Zehn — the honest comparison</h2>
<table>
<tr><th></th><th>Lumosity Premium</th><th>Zehn</th></tr>
<tr><td>Price</td><td>~$11.99/mo or $59.99–$89/yr — and the price is hidden until you sign in</td><td><b>Free, forever — nothing to hide</b></td></tr>
<tr><td>Games</td><td>Free: 3 preselected games/day; full 40+ library = Premium</td><td><b>All 5 games, all levels, any time</b></td></tr>
<tr><td>Daily workout</td><td>5 games chosen by their algorithm = Premium</td><td><b>Free — rotates daily, leans into your weakest skill</b></td></tr>
<tr><td>Zen (no-score) practice</td><td>Unlocks after 50 games; unlimited = Premium</td><td><b>Free from game one</b></td></tr>
<tr><td>Coaching</td><td>Insights describe your past score</td><td><b>AI tip tells you what to practise next, free</b></td></tr>
<tr><td>Ads</td><td>3+ Premium ads every time you open the app</td><td><b>None — nothing to sell</b></td></tr>
<tr><td>Urdu / Roman-Urdu</td><td>No — English only</td><td><b>Yes — EN + Roman-Urdu + Urdu script</b></td></tr>
<tr><td>Account / billing</td><td>Account required; auto-renews; trial forfeits if you buy</td><td><b>None — scores stay in your browser</b></td></tr>
<tr><td>Brain claims</td><td>FTC fined Lumos Labs $2M (2016) for unproven claims</td><td><b>Honest: games train the games themselves</b></td></tr>
</table>
</div>

<div class="card">
<h2>Honest limits</h2>
<p class="muted">Brain games train the games themselves. A 2016 review of brain-training research found performance improves on the trained tasks, with thin evidence for transfer to everyday thinking. <b>Zehn does NOT raise IQ, prevent dementia, or treat any condition</b> — and says so, because Lumosity's maker paid $2 million to the FTC for claiming otherwise.</p>
<p class="muted">Yaad, Rang, Tez Hisab, Do Peeche and Raasta are original designs written for this app. Sequence recall, Stroop, arithmetic, 2-back and grid recall are standard cognitive tasks in the public literature, not any company's property. No Lumosity game names, art, code or assets are used. Zehn is not affiliated with Lumos Labs.</p>
<p class="muted">Zehn Score = 70% accuracy + 30% speed (speed factor 1.0 at or under the game's target time, falling to 0 at twice the target). Targets: Yaad 8s, Rang 3s, Hisab 6s, Peeche 2.5s, Raasta 10s per round.</p>
<p class="muted">AI tips and summaries need a GEMINI_API_KEY in the environment; without it, everything else works fully and this page says the AI is off.</p>
<p class="muted">Your scores live only in YOUR browser (localStorage). Clear the browser and they are gone; Zehn never sees them and cannot recover them.</p>
</div>
</main>
<footer>Zehn — an original clean-room build from the daily-app-gap-build series. It fills the gaps in Lumosity: Brain Training (Premium ~$11.99/month or $59.99–$89/year, price hidden until sign-in; Google Play 4.8/5). Zehn is not affiliated with Lumos Labs. Not medical advice.</footer>
<script>
const $=id=>document.getElementById(id);
const store={
 get(k,d){try{const v=localStorage.getItem("zehn:"+k);return v?JSON.parse(v):d}catch(e){return d}},
 set(k,v){try{localStorage.setItem("zehn:"+k,JSON.stringify(v))}catch(e){}}
};
let curGame="yaad", zen=store.get("zen",false), levels=store.get("levels",{}), scores=store.get("scores",{}), played=store.get("played",0);
const SKILL_OF={yaad:"memory",rang:"attention",hisab:"speed",peeche:"flexibility",raasta:"memory"};
const SKILL_NAME={memory:"Memory · Yaad",attention:"Attention · Rang",speed:"Speed · Tez Hisab",flexibility:"Flexibility · Do Peeche"};
function dayOfYear(){const n=new Date();const s=new Date(n.getFullYear(),0,0);return Math.floor((n-s)/86400000);}
function weakestSkill(){
 let worst=null,worstScore=101;
 for(const s of Object.keys(SKILL_NAME)){const v=scores[s];if(v!==undefined&&v<worstScore){worstScore=v;worst=s;}}
 return worst;
}
function renderSkills(){
 const el=$("skillBars");el.innerHTML="";
 for(const s of Object.keys(SKILL_NAME)){
  const v=scores[s];
  el.innerHTML+="<div><span>"+SKILL_NAME[s]+" — <b>"+(v===undefined?"—":v+"/100")+"</b></span><div class='barwrap'><div class='bar' style='width:"+(v===undefined?0:v)+"%'></div></div></div>";
 }
 $("pillGames").textContent=played+" games played";
 let best=null,bv=-1;for(const s of Object.keys(scores)){if(scores[s]>bv){bv=scores[s];best=s;}}
 $("pillBest").textContent=best?("Best: "+SKILL_NAME[best]+" "+bv):"Best: —";
 $("zenToggle").textContent=zen?"Zen practice: ON — scores won't count":"Zen practice: OFF — scores count";
}
async function loadGames(){
 const r=await fetch("/zehn/api/games").then(r=>r.json()).catch(()=>null);
 const list=$("gameList");list.innerHTML="";
 (r?r.games:[]).forEach(g=>{
  const b=document.createElement("button");b.className="gamebtn"+(curGame===g.id?" sel":"");
  b.innerHTML="<b>"+g.name_en+"</b> · "+g.name_ur+"<br><span class='muted'>"+g.blurb_en+" · Target "+g.target_seconds+"s/round · Level "+(levels[g.id]||3)+"</span>";
  b.onclick=()=>{curGame=g.id;document.querySelectorAll(".gamebtn").forEach(x=>x.classList.remove("sel"));b.classList.add("sel");$("levelSel").value=levels[g.id]||3;};
  list.appendChild(b);
 });
 const w=await fetch("/zehn/api/workout?day="+dayOfYear()+(weakestSkill()?("&weakest="+weakestSkill()):"")).then(r=>r.json()).catch(()=>null);
 const wl=$("workoutList");wl.innerHTML="";
 if(w&&w.ok){w.games.forEach((g,i)=>{const d=document.createElement("div");d.innerHTML="<span class='pill'>"+(i+1)+". "+g.name_en+"</span> <span class='muted'>"+g.skill+" · "+g.target_seconds+"s/round</span>";wl.appendChild(d);});}
 else{$("workoutNote").textContent="Workout load nahi hua — khel phir bhi neeche se chunein.";}
}
function level(){return +$("levelSel").value||3;}
async function postForm(url,params){
 return fetch(url,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams(params)}).then(r=>r.json());
}
async function finishGame(game,accuracy,avgSeconds){
 const t0=Date.now();
 const s=await postForm("/zehn/api/score",{accuracy:accuracy,avg_seconds:avgSeconds,game:game}).catch(()=>null);
 if(!s||!s.ok){$("playMsg").textContent="Score compute nahi hua.";return;}
 const a=await postForm("/zehn/api/adapt",{level:level(),accuracy:accuracy,avg_seconds:avgSeconds,target_seconds:({yaad:8,rang:3,hisab:6,peeche:2.5,raasta:10})[game]}).catch(()=>null);
 if(zen){$("playMsg").textContent="Zen practice — score "+s.score+"/100 (saved nahi hua). "+(a&&a.ok?("Level "+(a.change==="up"?"barhega":a.change==="down"?"ghatega":"waise hi rahega")+" — agle game se."):"");return;}
 const sk=SKILL_OF[game];
 scores[sk]=Math.max(scores[sk]||0,s.score);played+=1;store.set("scores",scores);store.set("played",played);
 if(a&&a.ok){levels[game]=a.new_level;store.set("levels",levels);$("levelSel").value=a.new_level;}
 $("playMsg").textContent="Zehn Score: "+s.score+"/100 · Accuracy "+Math.round(accuracy*100)+"% · Avg "+avgSeconds+"s/round"+(a&&a.ok?(" · Level "+a.level+" → "+a.new_level+" ("+a.change+")"):"");
 renderSkills();
}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
async function playYaad(){
 const r=await fetch("/zehn/api/memory?level="+level()).then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok){$("playMsg").textContent=(r&&r.error)||"Round nahi mila.";return;}
 const area=$("playArea");$("playTitle").textContent="Yaad — digits yaad rakhein";
 area.innerHTML="<p class='muted'>Digits ek-ek karke dikhenge, phir wapas likhne hain.</p><div class='big' id='show'>—</div>";
 const t0=Date.now();
 for(const d of r.digits){$("show").textContent=d;await sleep(1000);}
 $("show").textContent="?";
 area.innerHTML+="<label>Sequence likhein (e.g. 31415)</label><input id='ans' inputmode='numeric' placeholder='Digits'><div class='row' style='margin-top:10px'><button id='go'>Check karein</button></div>";
 $("go").onclick=async()=>{
  const secs=((Date.now()-t0)/1000/r.digits.length).toFixed(1);
  const sc=await postForm("/zehn/api/memory/score",{digits:JSON.stringify(r.digits),answer:$("ans").value}).catch(()=>null);
  if(!sc||!sc.ok){$("playMsg").textContent=(sc&&sc.error)||"Score nahi hua.";return;}
  finishGame("yaad",sc.accuracy,+secs);
 };
}
async function playRang(){
 const r=await fetch("/zehn/api/stroop?level="+level()).then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok){$("playMsg").textContent=(r&&r.error)||"Round nahi mila.";return;}
 const area=$("playArea");$("playTitle").textContent="Rang — INK ka rang chunein (lafz nahi!)";
 const answers=[];let i=0;const t0=Date.now();
 const COLHEX={laal:"#dc2626",neela:"#2563eb",sabz:"#16a34a",peela:"#ca8a04"};
 const COLNAME={laal:"Laal · لال",neela:"Neela · نیلا",sabz:"Sabz · سبز",peela:"Peela · پیلا"};
 function showTrial(){
  if(i>=r.trials.length){
   const secs=((Date.now()-t0)/1000/r.trials.length).toFixed(1);
   postForm("/zehn/api/stroop/score",{trials:JSON.stringify(r.trials),answers:JSON.stringify(answers)}).then(sc=>{
    if(!sc||!sc.ok){$("playMsg").textContent=(sc&&sc.error)||"Score nahi hua.";return;}
    $("playMsg").textContent="Stroop: "+sc.correct+"/"+sc.total+" · Congruent "+sc.congruent_correct+"/"+sc.congruent_total+" · Incongruent "+sc.incongruent_correct+"/"+sc.incongruent_total+". ";
    finishGame("rang",sc.accuracy,+secs);
   });return;
  }
  const t=r.trials[i];
  area.innerHTML="<p class='muted'>Trial "+(i+1)+" / "+r.trials.length+" — lafz ko NAHI, rang ko dekhein.</p><div class='stroopword' style='color:"+t.ink_hex+"'>"+t.word_en+"</div><div class='row' id='opts'></div>";
  const opts=$("opts");
  r.options.forEach(c=>{const b=document.createElement("button");b.className="colorbtn";b.style.background=COLHEX[c];b.textContent=COLNAME[c];b.onclick=()=>{answers.push(c);i++;showTrial();};opts.appendChild(b);});
 }
 showTrial();
}
async function playHisab(){
 const area=$("playArea");$("playTitle").textContent="Tez Hisab — 10 sawaal, jaldi!";
 area.innerHTML="<p class='muted'>Har sawaal ka jawab likhein. Tez + sahi = behtar score.</p><div id='q'></div>";
 let i=0,correct=0;const t0=Date.now();
 async function nextQ(){
  if(i>=10){
   const secs=((Date.now()-t0)/1000/10).toFixed(1);
   $("playMsg").textContent="Hisab: "+correct+"/10 sahi. ";
   finishGame("hisab",correct/10,+secs);return;
  }
  const q=await fetch("/zehn/api/math?level="+level()).then(r=>r.json()).catch(()=>null);
  if(!q||!q.ok){$("playMsg").textContent=(q&&q.error)||"Sawaal nahi mila.";return;}
  $("q").innerHTML="<div class='big' style='letter-spacing:2px'>"+q.a+" "+q.op+" "+q.b+" = ?</div><input id='ans' inputmode='numeric' placeholder='Jawab'><div class='row' style='margin-top:10px'><button id='go'>Check</button></div><p class='muted'>Sawaal "+(i+1)+" / 10</p>";
  $("go").onclick=async()=>{
   const g=parseInt($("ans").value,10);
   const c=await postForm("/zehn/api/math/check",{answer:q.answer,given:isNaN(g)?-999999:g}).catch(()=>null);
   if(c&&c.ok&&c.correct)correct++;
   i++;nextQ();
  };
  $("ans").focus();
 }
 nextQ();
}
async function playPeeche(){
 const r=await fetch("/zehn/api/nback?level="+level()).then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok){$("playMsg").textContent=(r&&r.error)||"Round nahi mila.";return;}
 const area=$("playArea");$("playTitle").textContent="Do Peeche — 2-back";
 area.innerHTML="<p class='muted'>Harf ek-ek karke dikhega. Kya ye harf <b>2 peeche wale</b> se milta hai? Pehle 2 harf par koi jawab nahi.</p><div class='big' id='show'>—</div><div class='row' style='justify-content:center'><button id='yesBtn' class='ghost'>Milta hai ✓</button><button id='noBtn' class='ghost'>Nahi milta ✗</button></div>";
 const answers=[];let i=0,shown=-1;const t0=Date.now();
 $("yesBtn").onclick=()=>answer(true);$("noBtn").onclick=()=>answer(false);
 function answer(v){if(shown<2)return;answers[shown]=v;next();}
 async function next(){
  if(i>=r.letters.length){
   const ans=r.letters.map((_,idx)=>idx<2?false:!!answers[idx]);
   const secs=((Date.now()-t0)/1000/r.letters.length).toFixed(1);
   const sc=await postForm("/zehn/api/nback/score",{targets:JSON.stringify(r.targets),answers:JSON.stringify(ans)}).catch(()=>null);
   if(!sc||!sc.ok){$("playMsg").textContent=(sc&&sc.error)||"Score nahi hua.";return;}
   $("playMsg").textContent="2-back: hits "+sc.hits+" · miss "+sc.misses+" · ghalat haan "+sc.false_alarms+". ";
   finishGame("peeche",sc.accuracy,+secs);return;
  }
  shown=i;$("show").textContent=r.letters[i];i++;
  if(shown<2){await sleep(1500);next();}
 }
 next();
}
async function playRaasta(){
 const r=await fetch("/zehn/api/grid?level="+level()).then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok){$("playMsg").textContent=(r&&r.error)||"Round nahi mila.";return;}
 const area=$("playArea");$("playTitle").textContent="Raasta — lit squares yaad rakhein";
 area.innerHTML="<p class='muted'>Peelay squares yaad rakhein — 3 second me gayab ho jayenge, phir unhi par tap karein.</p><div class='grid' id='grid' style='grid-template-columns:repeat("+r.size+",1fr)'></div><div class='row' style='justify-content:center;margin-top:10px'><button id='go' disabled>Check karein</button></div>";
 const g=$("grid");const cells=[];
 for(let c=0;c<r.size*r.size;c++){const b=document.createElement("button");b.className="cell"+(r.lit.includes(c)?" lit":"");b.textContent="";g.appendChild(b);cells.push(b);}
 const t0=Date.now();
 await sleep(3000);
 cells.forEach(b=>b.classList.remove("lit"));
 const picked=new Set();
 cells.forEach((b,c)=>{b.onclick=()=>{if(picked.has(c)){picked.delete(c);b.classList.remove("picked");}else{picked.add(c);b.classList.add("picked");}};});
 $("go").disabled=false;
 $("go").onclick=async()=>{
  const secs=((Date.now()-t0)/1000).toFixed(1);
  const sc=await postForm("/zehn/api/grid/score",{lit:JSON.stringify(r.lit),picked:JSON.stringify([...picked]),size:r.size}).catch(()=>null);
  if(!sc||!sc.ok){$("playMsg").textContent=(sc&&sc.error)||"Score nahi hua.";return;}
  $("playMsg").textContent="Grid: "+sc.true_positives+" sahi · "+sc.false_positives+" ghalat tap · "+sc.false_negatives+" chhoot gaye. ";
  finishGame("raasta",sc.accuracy,+secs);
 };
}
$("zenToggle").onclick=()=>{zen=!zen;store.set("zen",zen);renderSkills();};
$("levelSel").onchange=()=>{levels[curGame]=level();store.set("levels",levels);};
const PLAYERS={yaad:playYaad,rang:playRang,hisab:playHisab,peeche:playPeeche,raasta:playRaasta};
const startBtn=document.createElement("button");
startBtn.textContent="▶ Khel shuru karein";startBtn.style.marginTop="12px";
startBtn.onclick=()=>{$("playCard").style.display="block";$("playMsg").textContent="";PLAYERS[curGame]();};
$("gameList").after(startBtn);
fetch("/zehn/api/ai-status").then(r=>r.json()).then(d=>{$("aiStatus").textContent=d.ai_available?"AI ON — Gemini connected. Tips aur summary free hain.":"AI OFF — no key set. Paanch khel, workout, score aur Zen practice phir bhi poore kaam karte hain.";}).catch(()=>{$("aiStatus").textContent="AI status unknown — offline mode.";});
$("tipBtn").onclick=async()=>{
 $("tipOut").style.display="block";$("tipOut").textContent="Socha ja raha hai…";
 const parts=[];for(const s of Object.keys(scores))parts.push(s+" "+scores[s]);
 const summary=parts.length?("games played "+played+", "+parts.join(", ")):"";
 const r=await postForm("/zehn/api/tip-ai",{language:"roman",score_summary:summary}).catch(()=>null);
 $("tipOut").textContent=(r&&r.ok)?("✨ AI-written tip: "+r.result.tip):("AI nahi mila: "+((r&&r.error)||"network"));
};
$("sumBtn").onclick=async()=>{
 $("sumOut").style.display="block";$("sumOut").textContent="Socha ja raha hai…";
 const parts=[];for(const s of Object.keys(scores))parts.push(s+" "+scores[s]);
 const summary=parts.length?("games played "+played+", "+parts.join(", ")):"";
 const r=await postForm("/zehn/api/summary-ai",{language:"roman",week_summary:summary}).catch(()=>null);
 $("sumOut").textContent=(r&&r.ok)?("✨ AI-written summary: "+r.result.summary):("AI nahi mila: "+((r&&r.error)||"network"));
};
loadGames();renderSkills();
</script>
</body>
</html>
"""
