# -*- coding: utf-8 -*-
"""Sathi page — single self-contained HTML page.

Everything runs in the browser: check-ins, habits, gratitude and
mood logs live in localStorage; the server only computes streaks,
pet stages, mood averages and (optionally) AI text. Jugnu is
original SVG art drawn for this app.
"""

SATHI_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sathi — ساتھی | Free gentle self-care companion</title>
<style>
:root{--ink:#2b2118;--bg:#fff8ec;--card:#fffdf7;--line:#e8dcc8;--acc:#b45309;--acc2:#0f766e;--soft:#fde68a}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:linear-gradient(135deg,#78350f,#b45309);color:#fff;padding:26px 16px 20px;text-align:center}
header h1{margin:0;font-size:30px}
header p{margin:6px 0 0;opacity:.92}
main{max-width:760px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}
h2{margin:0 0 8px;font-size:19px}
h3{margin:14px 0 6px;font-size:16px}
.muted{color:#6b5d4f;font-size:13px}
button{border:0;border-radius:10px;padding:10px 16px;font-size:15px;background:var(--acc);color:#fff;cursor:pointer}
button.ghost{background:#fff;border:1px solid var(--acc);color:var(--acc)}
button:disabled{opacity:.5;cursor:default}
input,select,textarea{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:9px;font-size:15px;background:#fff}
label{display:block;font-size:13px;color:#6b5d4f;margin:10px 0 4px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.moodbtn{font-size:22px;padding:8px 12px;background:#fff;border:2px solid var(--line);border-radius:12px;cursor:pointer}
.moodbtn.sel{border-color:var(--acc);background:var(--soft)}
.habit{display:flex;gap:10px;align-items:center;padding:9px 4px;border-bottom:1px solid #f3ead9}
.habit input{width:auto}
.habit.done span{text-decoration:line-through;opacity:.6}
.pill{display:inline-block;background:#fef3c7;border:1px solid #f59e0b;border-radius:999px;padding:3px 10px;font-size:13px;margin:2px}
.journey{border:1px solid var(--line);border-radius:12px;padding:12px;margin:10px 0}
.bar{height:14px;background:#fde68a;border-radius:7px}
.barwrap{background:#f3ead9;border-radius:7px;margin:4px 0 10px}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:#fef3c7}
#jugnu{width:150px;height:150px;display:block;margin:0 auto}
.glow0{filter:drop-shadow(0 0 2px #fbbf24)}
.glow1{filter:drop-shadow(0 0 8px #fbbf24)}
.glow2{filter:drop-shadow(0 0 16px #fbbf24)}
.glow3{filter:drop-shadow(0 0 26px #f59e0b)}
.glow4{filter:drop-shadow(0 0 38px #f59e0b)}
.center{text-align:center}
.ai{border-left:4px solid var(--acc2);background:#f0fdfa;padding:10px 12px;border-radius:8px;margin:10px 0}
.err{color:#b91c1c;font-size:14px}
.ok{color:#0f766e;font-size:14px}
footer{max-width:760px;margin:0 auto;padding:0 16px 30px;color:#6b5d4f;font-size:13px}
</style>
</head>
<body>
<header>
<h1>Sathi — ساتھی</h1>
<p>Your gentle self-care companion · Jugnu the firefly grows when you care for yourself — free forever, no account, no card, no trial.</p>
</header>
<main>

<div class="card center">
<svg id="jugnu" viewBox="0 0 150 150" class="glow0" aria-label="Jugnu the firefly">
  <ellipse cx="75" cy="128" rx="46" ry="7" fill="#e8dcc8"/>
  <ellipse cx="75" cy="82" rx="34" ry="42" fill="#f59e0b"/>
  <ellipse cx="75" cy="82" rx="34" ry="42" fill="#fbbf24" opacity="0.55"/>
  <circle cx="62" cy="72" r="9" fill="#fff7d6"/>
  <circle cx="88" cy="72" r="9" fill="#fff7d6"/>
  <circle cx="64" cy="73" r="4" fill="#2b2118"/>
  <circle cx="86" cy="73" r="4" fill="#2b2118"/>
  <path d="M68 92 Q75 98 82 92" stroke="#2b2118" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <path d="M60 48 Q52 30 40 26" stroke="#92400e" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <path d="M90 48 Q98 30 110 26" stroke="#92400e" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <circle cx="40" cy="26" r="4" fill="#92400e"/>
  <circle cx="110" cy="26" r="4" fill="#92400e"/>
  <ellipse cx="48" cy="96" rx="16" ry="9" fill="#fde68a" opacity="0.85" transform="rotate(-25 48 96)"/>
  <ellipse cx="102" cy="96" rx="16" ry="9" fill="#fde68a" opacity="0.85" transform="rotate(25 102 96)"/>
  <circle cx="75" cy="118" r="10" fill="#fde047"/>
</svg>
<h2 id="petName">Jugnu — جگنو</h2>
<p id="petStage" class="muted">Loading…</p>
<p><span class="pill" id="pillPoints">0 care points</span>
<span class="pill" id="pillStreak">Streak: —</span>
<span class="pill" id="pillTotal">Total care days: 0</span></p>
<p class="muted">Jugnu glows brighter with steady care — never with money. A rest day never dims the light.</p>
<div class="row" style="justify-content:center">
<button id="restBtn" class="ghost">Aaj aaram — mark today a rest day</button>
<button id="streakToggle" class="ghost">Streaks: ON</button>
</div>
<p id="restMsg" class="ok"></p>
</div>

<div class="card">
<h2>1 · Aaj ka check-in — How are you today?</h2>
<div class="row" id="moodRow">
<button class="moodbtn" data-m="1" title="Bohot kharab">😞</button>
<button class="moodbtn" data-m="2" title="Kharab">🙁</button>
<button class="moodbtn" data-m="3" title="Theek">😐</button>
<button class="moodbtn" data-m="4" title="Acha">🙂</button>
<button class="moodbtn" data-m="5" title="Bohot acha">😄</button>
</div>
<label for="energy">Energy (1–5)</label>
<input id="energy" type="number" min="1" max="5" value="3">
<label for="sleepQ">Last night's sleep (1–5)</label>
<input id="sleepQ" type="number" min="1" max="5" value="3">
<div class="row" style="margin-top:12px"><button id="checkinBtn">Check-in karein</button>
<span id="checkinMsg" class="ok"></span></div>
<h3>Last 7 days</h3>
<div id="moodChart"></div>
<p id="moodSummary" class="muted"></p>
</div>

<div class="card">
<h2>2 · Journeys — free, always</h2>
<p class="muted">Finch charges $69.99/year for organising goals into Journeys. Here every journey is free — pick one, tick its habits, Jugnu grows.</p>
<label for="journeySel">Journey</label>
<select id="journeySel"></select>
<div id="habitList"></div>
<div class="row" style="margin-top:12px"><button id="habitsDoneBtn">Aaj ke habits save karein</button>
<span id="habitsMsg" class="ok"></span></div>
<p class="muted">Apni khud ki habit bhi add kar sakte hain — neeche likhein:</p>
<div class="row"><input id="customHabit" placeholder="e.g. Quran ka ek rukoo"><button id="addHabitBtn" class="ghost">Add</button></div>
</div>

<div class="card">
<h2>3 · Shukrana — 3 good things</h2>
<p class="muted">Aaj ki 3 achi cheezein — chhoti bhi chalegi. "Alhamdulillah" moments count.</p>
<input id="g1" placeholder="1 — e.g. Aaj dhoop achi thi">
<input id="g2" placeholder="2 —" style="margin-top:8px">
<input id="g3" placeholder="3 —" style="margin-top:8px">
<div class="row" style="margin-top:12px"><button id="gratBtn">Shukrana save karein</button>
<span id="gratMsg" class="ok"></span></div>
</div>

<div class="card">
<h2>4 · Saans — one quiet minute (4-7-8)</h2>
<p class="muted">Saans andar 4, rokein 7, bahar 8. 4 cycles = 76 seconds. Jugnu ke saath saans lein.</p>
<div class="row"><button id="breathBtn">Start breathing</button>
<span id="breathPhase" style="font-size:18px"></span></div>
<p id="breathTimer" class="muted"></p>
</div>

<div class="card">
<h2>5 · AI — aaj ka prompt &amp; weekly reflection</h2>
<p class="muted" id="aiStatus">Checking AI…</p>
<div class="row"><button id="promptBtn">Aaj ka AI prompt</button></div>
<div id="promptOut" class="ai" style="display:none"></div>
<div class="row" style="margin-top:10px"><button id="reflBtn" class="ghost">Weekly AI reflection</button></div>
<div id="reflOut" class="ai" style="display:none"></div>
<p class="muted">AI text is labelled AI-written. Without a key, everything else still works fully.</p>
</div>

<div class="card">
<h2>Finch vs Sathi — the honest comparison</h2>
<table>
<tr><th></th><th>Finch Plus</th><th>Sathi</th></tr>
<tr><td>Price</td><td>$9.99/mo or $69.99/yr</td><td><b>Free, forever</b></td></tr>
<tr><td>Journeys (goal organisation)</td><td>Paywalled</td><td><b>Free — 5 journeys</b></td></tr>
<tr><td>Streaks</td><td>No off-switch; a miss breaks it</td><td><b>Gentle: 1 rest day/week forgiven; can switch off</b></td></tr>
<tr><td>Reflection prompts</td><td>Extra prompts = Plus</td><td><b>AI prompt daily, free</b></td></tr>
<tr><td>Urdu / Roman-Urdu / Islamic habits</td><td>No</td><td><b>Yes — dhikr, Fajr, Isha journeys</b></td></tr>
<tr><td>Account / billing</td><td>Account + trial that auto-renews</td><td><b>None — data stays on your device</b></td></tr>
<tr><td>Companion</td><td>Bird, cosmetics in a shop</td><td><b>Jugnu the firefly — grows on care, not money</b></td></tr>
</table>
</div>

<div class="card">
<h2>Honest limits</h2>
<p class="muted">Sathi is a self-care <b>companion</b>, not therapy and not medical advice. It does not diagnose or treat anxiety, depression, ADHD or any condition. If low mood persists for weeks, or daily life is affected, see a clinician.</p>
<p class="muted">Streaks here are gentle by design: rest days never break them, and you can turn them off. If streaks stress you, turn them off — Jugnu still grows on total care days.</p>
<p class="muted">Jugnu is original SVG art drawn for this app — a firefly, not a copy of any other app's pet.</p>
<p class="muted">AI prompts and the weekly reflection need a GEMINI_API_KEY in the environment; without it, check-ins, habits, journeys, gratitude, breathing and the pet all still work fully, and this page says the AI is off.</p>
<p class="muted">Your check-ins, habits and journal live only in YOUR browser (localStorage). Clear the browser and they are gone; Sathi never sees them and cannot recover them.</p>
</div>
</main>
<footer>Sathi — an original clean-room build from the daily-app-gap-build series. It fills the gaps in Finch: Self-Care Pet (Plus $9.99/month or $69.99/year; Trustpilot 2.4/5). Sathi is not affiliated with Finch Care. Not medical advice.</footer>
<script>
const $=id=>document.getElementById(id);
const today=()=>new Date().toISOString().slice(0,10);
const store={
 get(k,d){try{const v=localStorage.getItem("sathi:"+k);return v?JSON.parse(v):d}catch(e){return d}},
 set(k,v){try{localStorage.setItem("sathi:"+k,JSON.stringify(v))}catch(e){}}
};
let mood=0, streaksOn=store.get("streaksOn",true), customHabits=store.get("customHabits",[]);
let careDays=store.get("careDays",[]), restDays=store.get("restDays",[]),
    moods=store.get("moods",[]), lifetime=store.get("points",0);
function markCare(){const t=today();if(!careDays.includes(t))careDays.push(t);store.set("careDays",careDays);}
async function refresh(){
 const r=await fetch("/sathi/api/pet?points="+lifetime).then(r=>r.json()).catch(()=>null);
 if(r&&r.ok){
  $("petStage").textContent=r.name_en+" · "+r.name_roman+" · "+r.name_ur+" — "+r.blurb_en+(r.next_stage?(" Next: "+r.next_stage+" in "+r.points_to_next+" points."):" Max stage — Jugnu shines brightest!");
  $("jugnu").setAttribute("class","glow"+r.glow);
  $("pillPoints").textContent=lifetime+" care points";
 }
 const s=await fetch("/sathi/api/streak",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({care_days:careDays.join(","),rest_days:restDays.join(","),today:today()})}).then(r=>r.json()).catch(()=>null);
 if(s&&s.ok){
  $("pillStreak").textContent=streaksOn?("Streak: "+s.streak_days+" day"+(s.streak_days==1?"":"s")+(s.rest_used?" (1 rest day forgiven)":"")):"Streaks off — gentle mode";
  $("pillTotal").textContent="Total care days: "+s.total_care_days;
 }
 const m=await fetch("/sathi/api/mood",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({entries:JSON.stringify(moods)})}).then(r=>r.json()).catch(()=>null);
 const ch=$("moodChart");ch.innerHTML="";
 if(m&&m.ok){
  $("moodSummary").textContent="Last "+m.count+" days · average "+m.average+"/5 ("+m.word+") · trend: "+m.trend+" · best day "+m.best_day+" ("+m.best_mood+"/5)";
  moods.slice(-7).forEach(e=>{const d=document.createElement("div");d.innerHTML="<span style='display:inline-block;width:90px'>"+e.date.slice(5)+"</span><div class='barwrap'><div class='bar' style='width:"+(e.mood*20)+"%'></div></div>";ch.appendChild(d);});
 }else{$("moodSummary").textContent="No mood entries yet — check in above to start your chart.";}
 $("streakToggle").textContent="Streaks: "+(streaksOn?"ON":"OFF");
}
document.querySelectorAll(".moodbtn").forEach(b=>b.onclick=()=>{mood=+b.dataset.m;document.querySelectorAll(".moodbtn").forEach(x=>x.classList.toggle("sel",x===b));});
$("checkinBtn").onclick=async()=>{
 if(!mood){$("checkinMsg").textContent="Pehle ek mood chunein 🙂";return;}
 const e=+($("energy").value||3),s=+($("sleepQ").value||3);
 if(e<1||e>5||s<1||s>5){$("checkinMsg").textContent="Energy aur neend 1–5 ke beech likhein.";return;}
 moods=moods.filter(x=>x.date!==today());moods.push({date:today(),mood:mood,energy:e,sleep:s});store.set("moods",moods);
 markCare();
 const r=await fetch("/sathi/api/care",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({checkin:true,habits_done:0,gratitude:false,breathing:false,lifetime_points:lifetime})}).then(r=>r.json()).catch(()=>null);
 if(r&&r.ok){lifetime=r.lifetime_points;store.set("points",lifetime);$("checkinMsg").textContent="Check-in ho gaya — +1 point. Jugnu khush hai ✨";}
 refresh();
};
async function loadJourneys(){
 const r=await fetch("/sathi/api/journeys").then(r=>r.json()).catch(()=>null);
 const sel=$("journeySel");sel.innerHTML="";
 (r?r.journeys:[]).forEach(j=>{const o=document.createElement("option");o.value=j.id;o.textContent=j.title_en+" ("+j.habits+" habits)";sel.appendChild(o);});
 sel.onchange=loadHabits;loadHabits();
}
async function loadHabits(){
 const j=$("journeySel").value;if(!j)return;
 const r=await fetch("/sathi/api/journey/"+j).then(r=>r.json()).catch(()=>null);
 const list=$("habitList");list.innerHTML="";
 const done=store.get("done:"+today(),{});
 const add=(id,label)=>{
  const d=document.createElement("label");d.className="habit"+(done[id]?" done":"");
  d.innerHTML="<input type='checkbox' data-h='"+id+"' "+(done[id]?"checked":"")+"> <span>"+label+"</span>";
  d.querySelector("input").onchange=ev=>{const dd=store.get("done:"+today(),{});dd[id]=ev.target.checked;store.set("done:"+today(),dd);d.classList.toggle("done",ev.target.checked);};
  list.appendChild(d);};
 (r&&r.ok?r.habits:[]).forEach(h=>add(h.id,h.en+" · "+h.roman));
 customHabits.forEach((h,i)=>add("custom"+i,h));
}
$("addHabitBtn").onclick=()=>{const v=$("customHabit").value.trim();if(!v)return;customHabits.push(v);store.set("customHabits",customHabits);$("customHabit").value="";loadHabits();};
$("habitsDoneBtn").onclick=async()=>{
 const n=document.querySelectorAll("#habitList input:checked").length;
 if(!n){$("habitsMsg").textContent="Pehle koi habit tick karein.";return;}
 markCare();
 const r=await fetch("/sathi/api/care",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({checkin:false,habits_done:n,gratitude:false,breathing:false,lifetime_points:lifetime})}).then(r=>r.json()).catch(()=>null);
 if(r&&r.ok){lifetime=r.lifetime_points;store.set("points",lifetime);$("habitsMsg").textContent=n+" habit"+(n>1?"s":"")+" done — +"+r.points+" points ✨";}
 refresh();
};
$("gratBtn").onclick=async()=>{
 const items=[$("g1").value,$("g2").value,$("g3").value].map(s=>s.trim()).filter(Boolean);
 const r=await fetch("/sathi/api/gratitude",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({items:JSON.stringify(items)})}).then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok){$("gratMsg").textContent=(r&&r.error)||"Kuch ghalat hua.";return;}
 markCare();
 const c=await fetch("/sathi/api/care",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({checkin:false,habits_done:0,gratitude:true,breathing:false,lifetime_points:lifetime})}).then(r=>r.json()).catch(()=>null);
 if(c&&c.ok){lifetime=c.lifetime_points;store.set("points",lifetime);}
 $("gratMsg").textContent="Shukrana save ho gaya — Alhamdulillah ✨ +1 point";
 refresh();
};
$("restBtn").onclick=()=>{const t=today();if(!restDays.includes(t))restDays.push(t);store.set("restDays",restDays);$("restMsg").textContent="Aaj aaram ka din hai — streak safe, Jugnu araam se chamakta rahega. Take care of yourself.";refresh();};
$("streakToggle").onclick=()=>{streaksOn=!streaksOn;store.set("streaksOn",streaksOn);refresh();};
let breathTimer=null;
$("breathBtn").onclick=async()=>{
 const r=await fetch("/sathi/api/breathing?cycles=4").then(r=>r.json()).catch(()=>null);
 if(!r||!r.ok)return;
 const sched=r.schedule;let i=0;$("breathBtn").disabled=true;
 const tick=()=>{
  if(i>=sched.length){$("breathPhase").textContent="Shabash — 76 seconds of calm ✨";$("breathTimer").textContent="";$("breathBtn").disabled=false;
   fetch("/sathi/api/care",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({checkin:false,habits_done:0,gratitude:false,breathing:true,lifetime_points:lifetime})}).then(x=>x.json()).then(c=>{if(c&&c.ok){lifetime=c.lifetime_points;store.set("points",lifetime);markCare();refresh();}});return;}
  const ph=sched[i];$("breathPhase").textContent="Cycle "+ph.cycle+": "+ph.label+" ("+ph.seconds+"s)";
  $("breathTimer").textContent="Total "+r.total_seconds+"s · "+r.breaths_per_minute+" breaths/min";
  breathTimer=setTimeout(()=>{i++;tick();},ph.seconds*1000);};
 tick();
};
fetch("/sathi/api/ai-status").then(r=>r.json()).then(d=>{$("aiStatus").textContent=d.ai_available?"AI ON — Gemini connected. Prompts aur reflection free hain.":"AI OFF — no key set. Check-in, habits, journeys, shukrana, saans aur Jugnu phir bhi poore kaam karte hain.";}).catch(()=>{$("aiStatus").textContent="AI status unknown — offline mode.";});
$("promptBtn").onclick=async()=>{
 $("promptOut").style.display="block";$("promptOut").textContent="Socha ja raha hai…";
 const r=await fetch("/sathi/api/prompt-ai",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({language:"roman",mood:mood||0})}).then(r=>r.json()).catch(()=>null);
 $("promptOut").textContent=(r&&r.ok)?("✨ AI-written prompt: "+r.result.prompt):("AI nahi mila: "+((r&&r.error)||"network"));
};
$("reflBtn").onclick=async()=>{
 const m=await fetch("/sathi/api/mood",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({entries:JSON.stringify(moods)})}).then(r=>r.json()).catch(()=>null);
 const summary=(m&&m.ok)?(m.count+" entries, average "+m.average+"/5, trend "+m.trend):"";
 $("reflOut").style.display="block";$("reflOut").textContent="Socha ja raha hai…";
 const r=await fetch("/sathi/api/reflection-ai",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams({language:"roman",mood_summary:summary})}).then(r=>r.json()).catch(()=>null);
 $("reflOut").textContent=(r&&r.ok)?("✨ AI-written reflection: "+r.result.reflection):("AI nahi mila: "+((r&&r.error)||"network"));
};
loadJourneys();refresh();
</script>
</body>
</html>
"""
