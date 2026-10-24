"""Dars single-page UI — plain, minimal, teal accents only."""

DARS_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dars — free AI study companion</title>
<style>
:root{--teal:#0d9488;--ink:#1f2937;--mut:#6b7280;--bg:#f8fafc;--card:#fff}
*{box-sizing:border-box}body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
color:var(--ink);background:var(--bg);margin:0;padding:0 12px 60px}
.wrap{max-width:900px;margin:0 auto}
h1{font-size:1.5rem;margin:18px 0 2px}h1 .t{color:var(--teal)}
.sub{color:var(--mut);font-size:.92rem;margin:0 0 14px}
.card{background:var(--card);border:1px solid #e5e7eb;border-radius:10px;
padding:14px;margin:12px 0}
textarea{width:100%;min-height:170px;border:1px solid #d1d5db;border-radius:8px;
padding:10px;font-size:.95rem;font-family:inherit}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
button{background:var(--teal);color:#fff;border:0;border-radius:8px;padding:9px 16px;
font-size:.95rem;cursor:pointer}button.ghost{background:#eef2f7;color:var(--ink)}
button:disabled{opacity:.5;cursor:default}
select{padding:8px;border:1px solid #d1d5db;border-radius:8px}
.tabs{display:flex;gap:6px;margin:14px 0 0;flex-wrap:wrap}
.tab{padding:8px 14px;border:1px solid #d1d5db;border-radius:8px;background:#fff;
cursor:pointer;font-size:.92rem}.tab.on{background:var(--teal);color:#fff;border-color:var(--teal)}
.note-h{font-weight:700;margin:12px 0 4px;color:var(--teal)}
ul{margin:6px 0;padding-left:20px}li{margin:3px 0}
.fcard{border:1px solid #d1d5db;border-radius:10px;padding:22px;text-align:center;
min-height:110px;display:flex;align-items:center;justify-content:center;
font-size:1.05rem;cursor:pointer;margin:10px 0;background:#fff}
.qopt{display:block;width:100%;text-align:left;margin:6px 0;background:#fff;
border:1px solid #d1d5db;color:var(--ink);padding:10px;border-radius:8px;cursor:pointer}
.qopt.right{border-color:var(--teal);background:#ecfdf5}
.qopt.wrong{border-color:#ef4444;background:#fef2f2}
.badge{display:inline-block;background:#ecfdf5;color:#047857;border-radius:6px;
padding:2px 8px;font-size:.8rem;margin:2px 4px 2px 0}
.small{font-size:.85rem;color:var(--mut)}
input[type=file]{font-size:.9rem}
.revbtns{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
.revbtns button{padding:6px 12px;font-size:.85rem}
.warn{background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:10px;font-size:.9rem}
details{margin-top:8px}summary{cursor:pointer;color:var(--teal)}
</style></head>
<body><div class="wrap">
<h1><span class="t">Dars</span> درس</h1>
<p class="sub">Paste a lecture, chapter, or notes → study notes, flashcards, quiz,
aur spaced repetition — <b>free, unlimited, no account</b>. Data browser me hi rehta hai.</p>

<div class="card">
<textarea id="src" placeholder="Lecture transcript, chapter text ya notes yahan paste karo (English / Urdu / Roman-Urdu)..."></textarea>
<div class="row">
<input type="file" id="file" accept=".txt,.md,.text">
<select id="lang"><option value="en">English</option><option value="ur">اردو</option>
<option value="ru">Roman-Urdu</option></select>
<button id="go">Study pack banao</button>
<button class="ghost" id="ai" disabled>✨ AI se behtar pack</button>
<span class="small" id="stat"></span>
</div>
<div class="small" id="aistat" style="margin-top:6px"></div>
</div>

<div class="tabs">
<button class="tab on" data-t="notes">📝 Notes</button>
<button class="tab" data-t="cards">🃏 Flashcards <span id="cnt"></span></button>
<button class="tab" data-t="quiz">❓ Quiz</button>
<button class="tab" data-t="review">🔁 Review <span id="due"></span></button>
</div>

<div class="card" id="pane-notes"><div id="notes"></div>
<div class="row"><button class="ghost" id="dlmd">⬇ Notes (.md)</button>
<button class="ghost" onclick="window.print()">🖨 Print</button></div></div>

<div class="card" id="pane-cards" hidden>
<div id="cardbox"></div>
<div class="row"><button class="ghost" id="prev">← Prev</button>
<button class="ghost" id="flip">Flip</button><button class="ghost" id="next">Next →</button>
<button class="ghost" id="dlcsv">⬇ Flashcards (.csv — Anki)</button></div>
<div class="small">Grade khud do (Again/Hard/Good/Easy) — SM-2 schedule Review tab me.</div>
</div>

<div class="card" id="pane-quiz" hidden><div id="quiz"></div>
<div class="row"><button class="ghost" id="newq">↻ Naye sawal</button></div></div>

<div class="card" id="pane-review" hidden><div id="rev"></div></div>

<div class="small" style="margin-top:20px">
<b>Honest note:</b> rule-based notes/flashcards/quiz source text se <i>verbatim</i>
nikalte hain — kuch invent nahi karte. AI pack (jab available) source se ground
hota hai. Spaced repetition SM-2 algorithm par hai. Tumhara text server par save nahi hota.
</div>
</div>
<script>
const $=id=>document.getElementById(id);
let pack=null, ci=0, qi=0, flipped=false, grades={};
const store={
 get(k,d){try{const v=localStorage.getItem("dars_"+k);return v?JSON.parse(v):d}catch(e){return d}},
 set(k,v){try{localStorage.setItem("dars_"+k,JSON.stringify(v))}catch(e){}}
};
function todayOrd(){return Math.floor(Date.now()/864e5)}
// ---- tabs ----
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on"));
 t.classList.add("on");
 ["notes","cards","quiz","review"].forEach(k=>$("pane-"+k).hidden=(k!==t.dataset.t));
 if(t.dataset.t==="review")renderReview();
});
// ---- build ----
$("file").onchange=e=>{const f=e.target.files[0];if(!f)return;
 const r=new FileReader();r.onload=()=>{$("src").value=r.result};r.readAsText(f)};
async function build(){
 const text=$("src").value.trim();
 if(text.length<50){$("stat").textContent="Thora lamba text paste karo (50+ chars).";return}
 $("stat").textContent="Ban raha hai...";
 const r=await fetch("/dars/api/build",{method:"POST",
  headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
 pack=await r.json();ci=0;qi=0;flipped=false;
 grades=store.get("sm2",{});
 pack.cards.forEach(c=>{if(!grades[c.front])grades[c.front]={reps:0,interval:0,ease:2.5,due:todayOrd()}});
 store.set("sm2",grades);
 $("stat").textContent=`${pack.notes.sentence_count} sentences → ${pack.cards.length} cards, ${pack.quiz.length} sawal.`;
 $("cnt").textContent=`(${pack.cards.length})`;
 renderNotes();renderCard();renderQuiz();updateDue();
}
$("go").onclick=build;
async function aiPack(){
 const text=$("src").value.trim(),lang=$("lang").value;
 if(text.length<50)return;$("stat").textContent="AI soch raha hai...";
 const r=await fetch("/dars/api/ai-pack",{method:"POST",
  headers:{"Content-Type":"application/json"},body:JSON.stringify({text,lang})});
 const j=await r.json();
 if(j.error){$("stat").textContent="AI: "+j.error;return}
 // AI pack ko rule-based pack ki shape me map karo
 pack={notes:{headings:j.notes.map(n=>n.heading),definitions:[],key_terms:[],
   summary:j.notes.flatMap(n=>n.points).slice(0,5),sentence_count:text.split(/[.!?۔]/).length,
   _ai:j.notes},
  cards:j.flashcards.map(f=>({front:f.front,back:f.back,kind:"ai"})),
  quiz:j.quiz.map(q=>({type:"mcq",question:q.question,options:q.options,answer:q.answer}))};
 ci=0;qi=0;renderNotes();renderCard();renderQuiz();updateDue();
 $("stat").textContent="✨ AI pack tayyar.";
}
$("ai").onclick=aiPack;
fetch("/dars/api/ai-status").then(r=>r.json()).then(j=>{
 $("aistat").textContent=j.ai_available?
  "✨ AI available — behtar pack ke liye 'AI se behtar pack' dabao.":
  "Rule-based mode (AI key nahi hai) — phir bhi full notes/cards/quiz milenge.";
 $("ai").disabled=!j.ai_available;
});
// ---- notes ----
function renderNotes(){
 const n=pack.notes;let h="";
 if(n._ai){n._ai.forEach(s=>{h+=`<div class="note-h">${esc(s.heading)}</div><ul>`+
   s.points.map(p=>`<li>${esc(p)}</li>`).join("")+"</ul>"})}
 else{
  if(n.headings.length)h+=n.headings.map(x=>`<span class="badge">§ ${esc(x)}</span>`).join("");
  h+="<div class='note-h'>Khulasa (extractive summary)</div><ul>"+
    n.summary.map(s=>`<li>${esc(s)}</li>`).join("")+"</ul>";
  if(n.definitions.length){h+="<div class='note-h'>Definitions</div><ul>"+
    n.definitions.map(d=>`<li><b>${esc(d.term)}</b> — ${esc(d.sentence)}</li>`).join("")+"</ul>"}
  if(n.key_terms.length){h+="<div class='note-h'>Key terms</div><div>"+
    n.key_terms.map(k=>`<span class="badge">${esc(k.term)}</span>`).join("")+"</div>"}
 }
 $("notes").innerHTML=h||"<span class='small'>Pehle text do.</span>";
}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
// ---- flashcards ----
function renderCard(){
 const b=$("cardbox");
 if(!pack.cards.length){b.innerHTML="<span class='small'>Koi card nahi bana.</span>";return}
 const c=pack.cards[ci];
 b.innerHTML=`<div class="small">Card ${ci+1} / ${pack.cards.length} · ${esc(c.kind)}</div>
  <div class="fcard" onclick="flip()">${esc(flipped?c.back:c.front)}</div>
  <div class="revbtns">
   <button class="ghost" onclick="grade(0)">Again</button>
   <button class="ghost" onclick="grade(3)">Hard</button>
   <button class="ghost" onclick="grade(4)">Good</button>
   <button class="ghost" onclick="grade(5)">Easy</button>
  </div><div class="small" id="sched"></div>`;
 showSched();
}
function flip(){flipped=!flipped;renderCard()}
$("flip").onclick=flip;
$("prev").onclick=()=>{ci=(ci-1+pack.cards.length)%pack.cards.length;flipped=false;renderCard()};
$("next").onclick=()=>{ci=(ci+1)%pack.cards.length;flipped=false;renderCard()};
function sm2(s,q){if(q>=3){s.interval=s.reps===0?1:s.reps===1?6:Math.round(s.interval*s.ease);s.reps++}
 else{s.reps=0;s.interval=1}
 s.ease=Math.max(1.3,s.ease+(0.1-(5-q)*(0.08+(5-q)*0.02)));return s}
function grade(q){if(!pack.cards.length)return;const c=pack.cards[ci];
 const s=sm2(grades[c.front]||{reps:0,interval:0,ease:2.5,due:0},q);
 s.due=todayOrd()+s.interval;grades[c.front]=s;store.set("sm2",grades);
 showSched();updateDue()}
function showSched(){const s=grades[pack.cards[ci].front];if(!s)return;
 $("sched").textContent=`Agla review: ${s.interval} din baad (ease ${s.ease.toFixed(2)})`}
function updateDue(){if(!pack)return;const t=todayOrd();
 const d=pack.cards.filter(c=>(grades[c.front]||{due:0}).due<=t).length;
 $("due").textContent=d?`(${d} due)`:""}
// ---- quiz ----
function renderQuiz(){
 const box=$("quiz");
 if(!pack.quiz.length){box.innerHTML="<span class='small'>Quiz ke liye definitions chahiye — text me 'X is ...' wale jumle hon.</span>";return}
 const q=pack.quiz[qi];
 let h=`<div class="small">Sawal ${qi+1} / ${pack.quiz.length}</div><p><b>${esc(q.question)}</b></p>`;
 q.options.forEach((o,i)=>{h+=`<button class="qopt" data-i="${i}">${esc(o)}</button>`});
 box.innerHTML=h;
 box.querySelectorAll(".qopt").forEach(b=>b.onclick=()=>{
  box.querySelectorAll(".qopt").forEach(x=>x.disabled=true);
  const i=+b.dataset.i;
  if(i===q.answer){b.classList.add("right")}
  else{b.classList.add("wrong");box.querySelector(`[data-i="${q.answer}"]`).classList.add("right")}
 });
}
$("newq").onclick=()=>{qi=(qi+1)%pack.quiz.length;renderQuiz()};
// ---- review ----
function renderReview(){
 if(!pack){$("rev").innerHTML="<span class='small'>Pehle study pack banao.</span>";return}
 const t=todayOrd();
 const due=pack.cards.filter(c=>(grades[c.front]||{due:0}).due<=t);
 $("rev").innerHTML=due.length?
  `<p><b>${due.length}</b> cards aaj due hain:</p><ul>`+
  due.map(c=>`<li><b>${esc(c.front)}</b> <span class="small">— ${esc(c.back.slice(0,80))}…</span></li>`).join("")+"</ul>"+
  `<div class="small">Flashcards tab me grade do — schedule khud update hoga.</div>`:
  `<p>🎉 Aaj ke liye sab clear! Agla review kal.</p>`;
}
// ---- downloads ----
$("dlmd").onclick=async()=>{const text=$("src").value;
 const r=await fetch("/dars/api/download-md",{method:"POST",
  headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
 const blob=await r.blob();dl(URL.createObjectURL(blob),"dars-notes.md")};
$("dlcsv").onclick=async()=>{const text=$("src").value;
 const r=await fetch("/dars/api/download-csv",{method:"POST",
  headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
 const blob=await r.blob();dl(URL.createObjectURL(blob),"dars-flashcards.csv")};
function dl(url,name){const a=document.createElement("a");a.href=url;a.download=name;a.click()}
</script></body></html>
"""
