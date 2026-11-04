"""Waqt page — single-file planner UI.

Mobile-first. Tasks + fixed events + settings live in localStorage;
the plan comes from /waqt/api/schedule. Urdu / Roman-Urdu / English
toggle. No account, no card, nothing stored server-side.
"""

WAQT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Waqt — Free AI Day Planner</title>
<style>
:root{--ink:#1c2733;--mut:#5b6b7a;--bg:#f4f7f9;--card:#fff;--line:#dfe7ec;
--must:#c0392b;--should:#b7791f;--nice:#2e7d32;--acc:#0b6fa4;--acc2:#e8f4fa}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
background:var(--bg);color:var(--ink);line-height:1.45}
header{background:#0e2a3d;color:#fff;padding:18px 16px 14px}
header h1{margin:0;font-size:26px}
header h1 span{color:#7fd0f2}
header p{margin:4px 0 0;opacity:.85;font-size:14px}
.wrap{max-width:860px;margin:0 auto;padding:14px 12px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:14px;margin-bottom:12px}
h2{font-size:17px;margin:0 0 10px}
h3{font-size:15px;margin:14px 0 6px}
label{display:block;font-size:13px;color:var(--mut);margin:8px 0 3px}
input,select,textarea{width:100%;padding:9px 10px;border:1px solid var(--line);
border-radius:8px;font-size:15px;background:#fff;color:var(--ink)}
textarea{min-height:64px;resize:vertical}
.row{display:flex;gap:8px;flex-wrap:wrap}
.row>*{flex:1;min-width:120px}
.btn{display:inline-block;border:0;border-radius:9px;padding:11px 16px;font-size:15px;
cursor:pointer;background:var(--acc);color:#fff;font-weight:600}
.btn.alt{background:#eef3f6;color:var(--ink);border:1px solid var(--line)}
.btn.small{padding:6px 10px;font-size:13px}
.btn.big{width:100%;padding:14px;font-size:17px}
.btn:disabled{opacity:.5;cursor:default}
.lang{float:right}
.lang button{background:transparent;border:1px solid rgba(255,255,255,.5);color:#fff;
border-radius:7px;padding:5px 9px;margin-left:4px;cursor:pointer;font-size:13px}
.lang button.on{background:#fff;color:#0e2a3d}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;font-weight:700}
.p1{background:#fdecea;color:var(--must)}
.p2{background:#fdf3d7;color:var(--should)}
.p3{background:#e6f4ea;color:var(--nice)}
.task{display:flex;gap:8px;align-items:flex-start;border-top:1px solid var(--line);padding:10px 0}
.task:first-of-type{border-top:0}
.task .t{flex:1}
.task .t b{font-size:15px}
.task .t small{display:block;color:var(--mut);font-size:13px}
.task .acts{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
.day{border:1px solid var(--line);border-radius:10px;margin-bottom:10px;overflow:hidden}
.day h3{margin:0;padding:10px 12px;background:var(--acc2);font-size:15px}
.day h3 small{float:right;color:var(--mut);font-weight:400}
.slot{display:flex;gap:10px;padding:9px 12px;border-top:1px solid var(--line);align-items:baseline}
.slot .tm{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap;font-size:14px}
.slot .nm{flex:1}
.slot .nm small{display:block;color:var(--mut)}
.slot.ev{background:#f7f9fa}
.slot.must{border-left:4px solid var(--must)}
.slot.should{border-left:4px solid var(--should)}
.slot.nice{border-left:4px solid var(--nice)}
.unp{border:1px solid #f0c6c0;background:#fdf3f2;border-radius:10px;padding:12px;margin-bottom:10px}
.unp b{color:var(--must)}
.stat{display:flex;gap:8px;flex-wrap:wrap}
.stat div{flex:1;min-width:110px;background:var(--acc2);border-radius:10px;padding:10px;text-align:center}
.stat b{display:block;font-size:20px}
.stat span{font-size:12px;color:var(--mut)}
.gaps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px}
.gaps div{background:#eef7ee;border:1px solid #cfe6d2;border-radius:10px;padding:10px;font-size:14px}
.gaps b{display:block;margin-bottom:2px}
.note{font-size:13px;color:var(--mut)}
.warn{background:#fff4d6;border:1px solid #ecd28a;border-radius:10px;padding:10px;font-size:14px}
footer{font-size:13px;color:var(--mut)}
footer li{margin-bottom:4px}
#toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:#0e2a3d;color:#fff;
padding:10px 16px;border-radius:9px;font-size:14px;display:none;z-index:9;max-width:90%}
@media print{header .lang,.no-print{display:none!important}.wrap{max-width:100%}}
</style>
</head>
<body>
<header>
<div class="lang">
<button data-lang="en">EN</button><button data-lang="roman" class="on">Roman</button><button data-lang="ur">اردو</button>
</div>
<h1>Waqt <span>وقت</span></h1>
<p data-i="tag">Free AI day planner — tasks in, a real plan out. No account, no card, no meter.</p>
</header>
<div class="wrap">

<div class="card gaps">
<div><b data-i="g1t">Free forever</b><span data-i="g1">Motion charges $29–49/month with a card-required trial. Waqt is $0 — unlimited tasks, unlimited plans.</span></div>
<div><b data-i="g2t">No AI meter</b><span data-i="g2">Motion rations AI credits and hides the price per action. Waqt's scheduler is free and deterministic; AI only estimates and splits.</span></div>
<div><b data-i="g3t">Phone-first</b><span data-i="g3">Motion's Android app is 2.7★. Waqt is built for the phone first.</span></div>
<div><b data-i="g4t">Focus protected</b><span data-i="g4">Mark deep-work blocks and the planner never books over them.</span></div>
</div>

<div class="card">
<h2 data-i="quick">Quick add — dump it, go</h2>
<p class="note" data-i="quickhint">One task per line. Example: <code>Revise pharmacology 90m tomorrow high</code> — title, minutes, day, priority. Just a title works too (30m, today).</p>
<textarea id="quick" placeholder="Revise pharmacology 90m tomorrow high&#10;Read chapter 4"></textarea>
<div class="row" style="margin-top:8px">
<button class="btn" id="quickAdd" data-i="addtasks">Add tasks</button>
<button class="btn alt" id="sampleBtn" data-i="sample">Load a Pharm-D sample day</button>
</div>
<div id="quickMsg" class="note" style="margin-top:6px"></div>
</div>

<div class="card">
<h2 data-i="addone">Add one task</h2>
<div class="row">
<div><label data-i="title">Title</label><input id="fTitle" placeholder="e.g. Revise pharmacology"></div>
<div style="flex:0 0 110px"><label data-i="mins">Minutes</label><input id="fMin" type="number" min="5" max="960" step="5" value="60"></div>
</div>
<div class="row">
<div><label data-i="deadline">Deadline</label><input id="fDate" type="date"></div>
<div><label data-i="prio">Priority</label><select id="fPrio"><option value="1">Must — zaroori</option><option value="2" selected>Should</option><option value="3">Nice to have</option></select></div>
<div><label data-i="proj">Project / subject (optional)</label><input id="fProj" placeholder="e.g. Pharmacology"></div>
</div>
<div style="margin-top:10px"><button class="btn" id="addOne" data-i="addtask">Add task</button></div>
</div>

<div class="card">
<h2><span data-i="tasks">Tasks</span> (<span id="taskCount">0</span>)</h2>
<div id="taskList"><p class="note" data-i="notasks">No tasks yet — add one above, or load the sample day.</p></div>
</div>

<div class="card">
<h2 data-i="fixed">Fixed events — classes, meetings (planner works around these)</h2>
<div class="row">
<div><label data-i="title">Title</label><input id="eTitle" placeholder="e.g. Pharmacology lecture"></div>
<div><label data-i="date">Date</label><input id="eDate" type="date"></div>
<div style="flex:0 0 100px"><label>Start</label><input id="eStart" type="time" value="09:00"></div>
<div style="flex:0 0 100px"><label>End</label><input id="eEnd" type="time" value="11:00"></div>
</div>
<div style="margin-top:10px"><button class="btn alt" id="addEvent" data-i="addevent">Add event</button></div>
<div id="eventList" style="margin-top:8px"></div>
</div>

<div class="card">
<h2 data-i="settings">Settings</h2>
<div class="row">
<div><label data-i="ws">Work starts</label><input id="sStart" type="time" value="09:00"></div>
<div><label data-i="we">Work ends</label><input id="sEnd" type="time" value="18:00"></div>
<div><label data-i="brk">Break between blocks (min)</label><input id="sBreak" type="number" min="0" max="60" value="10"></div>
<div><label data-i="chunk">Longest single chunk (min)</label><input id="sChunk" type="number" min="15" max="240" step="15" value="90"></div>
</div>
<div class="row">
<div><label data-i="focus">Focus block — deep work, never booked over</label>
<div class="row"><input id="sFocusStart" type="time" value="16:00"><input id="sFocusEnd" type="time" value="17:30"></div></div>
<div><label data-i="prayer">Prayer breaks</label>
<select id="sPrayer"><option value="1" selected>On — Zuhr / Asr respected</option><option value="0">Off</option></select></div>
</div>
<p class="note" data-i="focusnote">Focus and prayer windows are protected time: the scheduler plans around them, never inside them.</p>
</div>

<button class="btn big" id="planBtn" data-i="plan">✨ Plan my day</button>
<div id="aiNote" class="note" style="margin:8px 0"></div>

<div class="card" id="planCard" style="display:none">
<h2 data-i="planhead">Your plan</h2>
<div class="stat" id="stats"></div>
<div id="unplaced" style="margin-top:12px"></div>
<div id="days" style="margin-top:12px"></div>
<div class="row no-print" style="margin-top:10px">
<button class="btn alt" id="printBtn">🖨️ Print plan</button>
<button class="btn alt" id="exportBtn">⬇ Export JSON</button>
<button class="btn alt" id="importBtn">⬆ Import JSON</button>
<input type="file" id="importFile" accept=".json" style="display:none">
<button class="btn alt" id="clearBtn">🗑 Clear all</button>
</div>
</div>

<div class="card">
<h2 data-i="limits">Honest limits</h2>
<ul class="note" style="margin:0;padding-left:18px">
<li data-i="l1">Plans live in your own browser (localStorage) — no cloud sync, no Google Calendar import in v1. Export JSON to keep a copy.</li>
<li data-i="l2">The scheduler is greedy and deterministic, not a learning model: earliest deadline first, Must before Nice, longest chunks first. It never invents time — if a day is full, it says so.</li>
<li data-i="l3">AI estimate / breakdown needs server Gemini quota. If the key is busy, the page says so and the deterministic splitter still works.</li>
<li data-i="l4">Prayer windows are typical Pakistan times (Zuhr 13:00, Asr 16:30, etc.) — edit them by switching prayer off and adding your own fixed events.</li>
<li data-i="l5">Waqt is an original build, not affiliated with Motion (usemotion.com).</li>
</ul>
</div>

<footer class="card">
<span data-i="foot">Waqt — free AI day planner. Built original, clean-room. Motion's gaps (no free plan, metered AI, 2.7★ mobile, no focus protection) are the spec Waqt is built against.</span>
</footer>
</div>
<div id="toast"></div>
<script>
const $=id=>document.getElementById(id);
const I18N={
en:{tag:"Free AI day planner — tasks in, a real plan out. No account, no card, no meter.",
g1t:"Free forever",g1:"Motion charges $29–49/month with a card-required trial. Waqt is $0 — unlimited tasks, unlimited plans.",
g2t:"No AI meter",g2:"Motion rations AI credits and hides the price per action. Waqt's scheduler is free and deterministic; AI only estimates and splits.",
g3t:"Phone-first",g3:"Motion's Android app is 2.7★. Waqt is built for the phone first.",
g4t:"Focus protected",g4:"Mark deep-work blocks and the planner never books over them.",
quick:"Quick add — dump it, go",quickhint:"One task per line. Example: Revise pharmacology 90m tomorrow high — title, minutes, day, priority. Just a title works too (30m, today).",
addtasks:"Add tasks",sample:"Load a Pharm-D sample day",addone:"Add one task",title:"Title",mins:"Minutes",
deadline:"Deadline",prio:"Priority",proj:"Project / subject (optional)",addtask:"Add task",
tasks:"Tasks",notasks:"No tasks yet — add one above, or load the sample day.",
fixed:"Fixed events — classes, meetings (planner works around these)",date:"Date",addevent:"Add event",
settings:"Settings",ws:"Work starts",we:"Work ends",brk:"Break between blocks (min)",chunk:"Longest single chunk (min)",
focus:"Focus block — deep work, never booked over",prayer:"Prayer breaks",
focusnote:"Focus and prayer windows are protected time: the scheduler plans around them, never inside them.",
plan:"✨ Plan my day",planhead:"Your plan",limits:"Honest limits",
l1:"Plans live in your own browser (localStorage) — no cloud sync, no Google Calendar import in v1. Export JSON to keep a copy.",
l2:"The scheduler is greedy and deterministic, not a learning model: earliest deadline first, Must before Nice, longest chunks first. It never invents time — if a day is full, it says so.",
l3:"AI estimate / breakdown needs server Gemini quota. If the key is busy, the page says so and the deterministic splitter still works.",
l4:"Prayer windows are typical Pakistan times (Zuhr 13:00, Asr 16:30, etc.) — edit them by switching prayer off and adding your own fixed events.",
l5:"Waqt is an original build, not affiliated with Motion (usemotion.com).",
foot:"Waqt — free AI day planner. Built original, clean-room. Motion's gaps (no free plan, metered AI, 2.7★ mobile, no focus protection) are the spec Waqt is built against."},
roman:{tag:"Free AI day planner — kaam likho, tayyar plan pao. No account, no card, no meter.",
g1t:"Hamesha free",g1:"Motion $29–49/month leta hai, card wali trial ke saath. Waqt Rs 0 — unlimited tasks, unlimited plans.",
g2t:"AI ka meter nahi",g2:"Motion AI credits ration karta hai aur har action ki qeemat chhupata hai. Waqt ka scheduler free aur deterministic hai; AI sirf andaza aur torna karta hai.",
g3t:"Phone pehle",g3:"Motion ki Android app 2.7★ hai. Waqt phone ke liye bana hai.",
g4t:"Focus mehfooz",g4:"Deep-work block lagao — planner uske andar kuch nahi rakhega.",
quick:"Quick add — likho, chalo",quickhint:"Har line aik task. Misal: Revise pharmacology 90m tomorrow high — title, minutes, din, priority. Sirf title bhi chalega (30m, aaj).",
addtasks:"Tasks add karo",sample:"Pharm-D sample day load karo",addone:"Aik task add karo",title:"Title",mins:"Minutes",
deadline:"Deadline",prio:"Priority",proj:"Project / subject (optional)",addtask:"Task add karo",
tasks:"Tasks",notasks:"Abhi koi task nahi — upar se add karo, ya sample day load karo.",
fixed:"Fixed events — classes, meetings (planner inke ird-gird plan banayega)",date:"Date",addevent:"Event add karo",
settings:"Settings",ws:"Kaam shuru",we:"Kaam khatam",brk:"Blocks ke beech break (min)",chunk:"Aik chunk ki max lambai (min)",
focus:"Focus block — deep work, ismein kuch nahi",prayer:"Namaz breaks",
focusnote:"Focus aur namaz ka waqt mehfooz hai: scheduler inke andar kuch nahi rakhta.",
plan:"✨ Mera din plan karo",planhead:"Aapka plan",limits:"Honest limits",
l1:"Plan aapke apne browser (localStorage) mein hai — v1 mein no cloud sync, no Google Calendar import. Copy ke liye JSON export karo.",
l2:"Scheduler greedy aur deterministic hai, learning model nahi: pehle jaldi deadline, phir Must, phir lamba chunk. Waqt invent nahi karta — din bhara ho to keh deta hai.",
l3:"AI estimate / breakdown ko server Gemini quota chahiye. Key busy ho to page bata deta hai aur deterministic splitter phir bhi chalta hai.",
l4:"Namaz ke waqt aam Pakistan times hain (Zuhr 13:00, Asr 16:30, waghera) — prayer off karke apne fixed events bhi add kar sakte hain.",
l5:"Waqt aik original build hai, Motion (usemotion.com) se affiliated nahi.",
foot:"Waqt — free AI day planner. Original, clean-room build. Motion ke gaps (no free plan, metered AI, 2.7★ mobile, no focus protection) hi Waqt ki spec hain."},
ur:{tag:"مفت AI ڈے پلانر — کام لکھیں، تیار پلان پائیں۔ کوئی اکاؤنٹ نہیں، کوئی کارڈ نہیں۔",
g1t:"ہمیشہ مفت",g1:"موشن $29–49 ماہانہ لیتا ہے، کارڈ والی ٹرائل کے ساتھ۔ وقت صفر روپے — لامحدود ٹاسک، لامحدود پلان۔",
g2t:"AI کا میٹر نہیں",g2:"موشن AI کریڈٹ محدود کرتا ہے۔ وقت کا شیڈیولر مفت اور ڈیٹرمنسٹک ہے؛ AI صرف اندازہ اور تقسیم کرتا ہے۔",
g3t:"فون پہلے",g3:"موشن کی اینڈرائیڈ ایپ 2.7★ ہے۔ وقت فون کے لیے بنا ہے۔",
g4t:"فوکس محفوظ",g4:"ڈیپ ورک بلاک لگائیں — پلانر اس کے اندر کچھ نہیں رکھے گا۔",
quick:"جلدی شامل کریں",quickhint:"ہر لائن ایک ٹاسک۔ مثال: Revise pharmacology 90m tomorrow high۔ صرف عنوان بھی چلے گا (30 منٹ، آج)۔",
addtasks:"ٹاسک شامل کریں",sample:"فارم-ڈی نمونہ دن لوڈ کریں",addone:"ایک ٹاسک شامل کریں",title:"عنوان",mins:"منٹ",
deadline:"آخری تاریخ",prio:"ترجیح",proj:"پروجیکٹ / مضمون (اختیاری)",addtask:"ٹاسک شامل کریں",
tasks:"ٹاسک",notasks:"ابھی کوئی ٹاسک نہیں — اوپر سے شامل کریں یا نمونہ دن لوڈ کریں۔",
fixed:"طے شدہ ایونٹس — کلاسز، میٹنگز (پلانر ان کے ارد گرد بنے گا)",date:"تاریخ",addevent:"ایونٹ شامل کریں",
settings:"ترتیبات",ws:"کام شروع",we:"کام ختم",brk:"بلاکس کے درمیان وقفہ (منٹ)",chunk:"ایک حصے کی زیادہ سے زیادہ لمبائی (منٹ)",
focus:"فوکس بلاک — گہرا کام، اس میں کچھ نہیں",prayer:"نماز کے وقفے",
focusnote:"فوکس اور نماز کا وقت محفوظ ہے: شیڈیولر ان کے اندر کچھ نہیں رکھتا۔",
plan:"✨ میرا دن پلان کریں",planhead:"آپ کا پلان",limits:"ایماندارانہ حدود",
l1:"پلان آپ کے اپنے براؤزر (localStorage) میں ہے — v1 میں کلاؤڈ سنک یا گوگل کیلنڈر امپورٹ نہیں۔ کاپی کے لیے JSON ایکسپورٹ کریں۔",
l2:"شیڈیولر لالچی اور ڈیٹرمنسٹک ہے، لرننگ ماڈل نہیں: پہلے جلدی ڈیڈلائن، پھر Must، پھر لمبا حصہ۔ وقت ایجاد نہیں کرتا — دن بھرا ہو تو کہہ دیتا ہے۔",
l3:"AI اندازہ / تقسیم کو سرور Gemini کوٹہ چاہیے۔ کی busy ہو تو صفحہ بتا دیتا ہے اور ڈیٹرمنسٹک اسپلٹر پھر بھی چلتا ہے۔",
l4:"نماز کے اوقات عام پاکستان کے اوقات ہیں (ظہر 13:00، عصر 16:30 وغیرہ) — prayer بند کر کے اپنے فکسڈ ایونٹس بھی شامل کر سکتے ہیں۔",
l5:"وقت ایک اصل بلڈ ہے، موشن (usemotion.com) سے وابستہ نہیں۔",
foot:"وقت — مفت AI ڈے پلانر۔ اصل، کلین روم بلڈ۔ موشن کی خامیاں (مفت پلان نہیں، میٹرڈ AI، 2.7★ موبائل، فوکس تحفظ نہیں) ہی وقت کی تفصیل ہیں."}
};
let lang="roman";
function t(k){return (I18N[lang]&&I18N[lang][k])||I18N.en[k]||k;}
function applyLang(){
document.querySelectorAll("[data-i]").forEach(el=>{el.textContent=t(el.dataset.i);});
document.querySelectorAll(".lang button").forEach(b=>b.classList.toggle("on",b.dataset.lang===lang));
renderTasks();renderEvents();if(plan)renderPlan();
}
document.querySelectorAll(".lang button").forEach(b=>b.onclick=()=>{lang=b.dataset.lang;applyLang();});

function todayISO(d){d=d||new Date();const p=n=>String(n).padStart(2,"0");return d.getFullYear()+"-"+p(d.getMonth()+1)+"-"+p(d.getDate());}
function addDays(iso,n){const d=new Date(iso+"T12:00:00");d.setDate(d.getDate()+n);return todayISO(d);}
function fmtT(m){return String(Math.floor(m/60)).padStart(2,"0")+":"+String(m%60).padStart(2,"0");}
function fmtD(min){if(min<60)return min+"m";const h=Math.floor(min/60),m=min%60;return m?h+"h "+String(m).padStart(2,"0")+"m":h+"h";}
function uid(){return "t"+Date.now().toString(36)+Math.floor(Math.random()*1000);}
function toast(msg){const el=$("toast");el.textContent=msg;el.style.display="block";setTimeout(()=>el.style.display="none",3500);}

let tasks=JSON.parse(localStorage.getItem("waqt_tasks")||"[]");
let events=JSON.parse(localStorage.getItem("waqt_events")||"[]");
let plan=null;
function save(){localStorage.setItem("waqt_tasks",JSON.stringify(tasks));localStorage.setItem("waqt_events",JSON.stringify(events));}
function settings(){
const toMin=v=>{const[a,b]=v.split(":").map(Number);return a*60+b;};
const fs=$("sFocusStart").value,fe=$("sFocusEnd").value;
return {work_start:toMin($("sStart").value||"09:00"),work_end:toMin($("sEnd").value||"18:00"),
break_min:parseInt($("sBreak").value||"10",10),max_chunk:parseInt($("sChunk").value||"90",10),
prayer:$("sPrayer").value==="1",
focus:(fs&&fe&&toMin(fe)>toMin(fs))?[{start:toMin(fs),end:toMin(fe)}]:[]};
}
const PRIO={1:["Must","p1"],2:["Should","p2"],3:["Nice","p3"]};
function renderTasks(){
$("taskCount").textContent=tasks.length;
const el=$("taskList");
if(!tasks.length){el.innerHTML='<p class="note">'+t("notasks")+"</p>";return;}
el.innerHTML=tasks.map((tk,i)=>{
const d=new Date(tk.deadline+"T12:00:00");
const day=d.toLocaleDateString(undefined,{weekday:"short",day:"numeric",month:"short"});
return '<div class="task"><div class="t"><b>'+esc(tk.title)+'</b> <span class="pill '+PRIO[tk.priority][1]+'">'+PRIO[tk.priority][0]+'</span>'+
'<small>'+fmtD(tk.minutes)+' · '+day+(tk.project?" · "+esc(tk.project):"")+(tk.splittable?"":" · no-split")+'</small></div>'+
'<div class="acts"><button class="btn alt small" onclick="aiBreak('+i+')">✂️ Torna</button>'+
'<button class="btn alt small" onclick="aiEst('+i+')">⏱ Andaza</button>'+
'<button class="btn alt small" onclick="delTask('+i+')">✕</button></div></div>';}).join("");
}
function renderEvents(){
const el=$("eventList");
if(!events.length){el.innerHTML="";return;}
el.innerHTML=events.map((ev,i)=>'<div class="task"><div class="t"><b>'+esc(ev.title)+'</b><small>'+
ev.date+" · "+fmtT(ev.start)+"–"+fmtT(ev.end)+'</small></div><div class="acts">'+
'<button class="btn alt small" onclick="delEvent('+i+')">✕</button></div></div>').join("");
}
function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function delTask(i){tasks.splice(i,1);save();renderTasks();}
function delEvent(i){events.splice(i,1);save();renderEvents();}
$("fDate").value=todayISO();$("eDate").value=todayISO();

$("addOne").onclick=()=>{
const title=$("fTitle").value.trim();
if(!title){toast("Title likhein.");return;}
tasks.push({id:uid(),title,minutes:Math.max(5,parseInt($("fMin").value||"60",10)),
deadline:$("fDate").value||todayISO(),priority:parseInt($("fPrio").value,10),
project:$("fProj").value.trim(),splittable:true});
$("fTitle").value="";$("fProj").value="";save();renderTasks();toast("Task add ho gaya.");
};
$("quickAdd").onclick=async()=>{
const text=$("quick").value.trim();
if(!text)return;
const fd=new FormData();fd.append("text",text);
const r=await fetch("/waqt/api/parse",{method:"POST",body:fd});
const j=await r.json();
tasks=tasks.concat(j.tasks||[]);
$("quickMsg").textContent=(j.tasks||[]).length+" task(s) added."+(j.errors&&j.errors.length?" Issues: "+j.errors.join(" "):"");
$("quick").value="";save();renderTasks();
};
$("addEvent").onclick=()=>{
const title=$("eTitle").value.trim();
if(!title){toast("Event title likhein.");return;}
const toMin=v=>{const[a,b]=v.split(":").map(Number);return a*60+b;};
const s=toMin($("eStart").value),e=toMin($("eEnd").value);
if(e<=s){toast("End time start se baad hona chahiye.");return;}
events.push({title,date:$("eDate").value||todayISO(),start:s,end:e});
$("eTitle").value="";save();renderEvents();toast("Event add ho gaya.");
};
$("sampleBtn").onclick=()=>{
const t=todayISO(),tm=addDays(t,1),fr=addDays(t,2);
tasks=[
{id:uid(),title:"Pharmacology revision — Autonomic drugs",minutes:90,deadline:t,priority:1,project:"Pharmacology",splittable:true},
{id:uid(),title:"Pharmaceutics assignment — tablets",minutes:120,deadline:tm,priority:1,project:"Pharmaceutics",splittable:true},
{id:uid(),title:"MDCAT Biology notes",minutes:60,deadline:t,priority:2,project:"MDCAT",splittable:true},
{id:uid(),title:"Read research paper — SGLT2 inhibitors",minutes:60,deadline:tm,priority:2,project:"Research",splittable:true},
{id:uid(),title:"Gym",minutes:45,deadline:t,priority:3,project:"Health",splittable:false},
{id:uid(),title:"Urdu novel — 1 chapter",minutes:30,deadline:fr,priority:3,project:"Personal",splittable:true}];
events=[
{title:"Pharmacology lecture",date:t,start:540,end:660},
{title:"Pharmaceutics lab",date:t,start:840,end:960},
{title:"Group study",date:tm,start:660,end:720}];
save();renderTasks();renderEvents();
toast("Sample day load ho gaya — ab 'Plan my day' dabayein.");
};
async function aiBreak(i){
const tk=tasks[i];const fd=new FormData();
fd.append("title",tk.title);fd.append("minutes",String(tk.minutes));fd.append("language",lang);
const r=await fetch("/waqt/api/breakdown",{method:"POST",body:fd});
const j=await r.json();
if(!j.ok){toast(j.error||"Error");return;}
const subs=j.subtasks.map(s=>({id:uid(),title:s.title,minutes:s.minutes,deadline:tk.deadline,priority:tk.priority,project:tk.project,splittable:true}));
tasks.splice(i,1,...subs);save();renderTasks();
toast(j.ai?"AI ne "+subs.length+" steps banaye.":"AI busy tha — deterministic split ("+subs.length+" hisse).");
}
async function aiEst(i){
const tk=tasks[i];const fd=new FormData();
fd.append("title",tk.title);fd.append("language",lang);
const r=await fetch("/waqt/api/estimate",{method:"POST",body:fd});
const j=await r.json();
if(!j.ok){toast(j.error||"AI andaza nahi de saka.");return;}
tasks[i].minutes=j.minutes;save();renderTasks();
toast("Andaza: "+fmtD(j.minutes)+" — "+(j.note||""));
}
$("planBtn").onclick=async()=>{
if(!tasks.length){toast("Pehle koi task add karein.");return;}
$("planBtn").disabled=true;$("planBtn").textContent="Planning…";
const fd=new FormData();
fd.append("payload",JSON.stringify({tasks,events,settings:settings(),start_date:todayISO()}));
try{
const r=await fetch("/waqt/api/schedule",{method:"POST",body:fd});
const j=await r.json();
if(!j.ok){toast(j.error||"Schedule error");return;}
plan=j;renderPlan();
}catch(e){toast("Server se rabta nahi hua: "+e);}
$("planBtn").disabled=false;$("planBtn").textContent=t("plan");
};
function renderPlan(){
$("planCard").style.display="block";
const s=plan.stats;
$("stats").innerHTML=
'<div><b>'+s.scheduled+'/'+s.tasks+'</b><span>tasks scheduled</span></div>'+
'<div><b>'+fmtD(s.planned_min)+'</b><span>planned</span></div>'+
'<div><b>'+fmtD(s.focus_min)+'</b><span>focus protected</span></div>'+
'<div><b>'+s.unplaced+'</b><span>fits nahi</span></div>';
const up=$("unplaced");
if(plan.unplaced.length){
up.innerHTML='<div class="warn"><b>⚠ Fits nahi — overload, red flag nahi:</b> neeche tasks deadline tak poore nahi ho sakte. Motion inhein sirf red exclamation se pin karta hai; Waqt fix deta hai.</div>'+
plan.unplaced.map((u,i)=>{
const tk=tasks.find(x=>x.id===u.task_id);
return '<div class="unp"><b>'+esc(u.title)+'</b> — '+esc(u.reason)+
'<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">'+
'<button class="btn small" onclick="fixDefer('+i+')">📅 Deadline +1 din ('+u.suggestions.defer_to+')</button>'+
'<button class="btn alt small" onclick="fixShorten('+i+')">✂️ Shorten by '+fmtD(u.minutes_left)+'</button></div></div>';}).join("");
}else{up.innerHTML='<div class="warn" style="background:#e9f7ec;border-color:#bfe3c6">✅ Sab kuch fit ho gaya — koi overload nahi.</div>';}
const daysEl=$("days");
const byDate={};
plan.blocks.forEach(b=>{(byDate[b.date]=byDate[b.date]||[]).push(b);});
const evByDate={};
events.forEach(ev=>{(evByDate[ev.date]=evByDate[ev.date]||[]).push(ev);});
const dates=Object.keys(plan.days).sort();
daysEl.innerHTML=dates.map(d=>{
const dObj=new Date(d+"T12:00:00");
const head=dObj.toLocaleDateString(undefined,{weekday:"long",day:"numeric",month:"short"});
const info=plan.days[d];
const items=[];
(byDate[d]||[]).forEach(b=>items.push({s:b.start,e:b.end,cls:PRIO[b.priority][1],nm:b.title,sub:fmtD(b.end-b.start)+(b.chunk_of>1?" · hissa "+b.chunk_of:"")+(b.project?" · "+b.project:"")}));
(evByDate[d]||[]).forEach(ev=>items.push({s:ev.start,e:ev.end,cls:"ev",nm:ev.title,sub:"Fixed event"}));
items.sort((a,b)=>a.s-b.s);
const rows=items.length?items.map(it=>'<div class="slot '+it.cls+'"><span class="tm">'+fmtT(it.s)+'–'+fmtT(it.e)+'</span><span class="nm">'+esc(it.nm)+'<small>'+esc(it.sub)+'</small></span></div>').join(""):'<div class="slot"><span class="nm note">Kuch planned nahi — khaali din.</span></div>';
return '<div class="day"><h3>'+head+' <small>'+fmtD(info.planned)+' planned · '+fmtD(info.free)+' free · '+fmtD(info.focus)+' focus</small></h3>'+rows+'</div>';
}).join("");
$("planCard").scrollIntoView({behavior:"smooth"});
}
function fixDefer(i){
const u=plan.unplaced[i];const tk=tasks.find(x=>x.id===u.task_id);
if(!tk)return;tk.deadline=u.suggestions.defer_to;save();renderTasks();$("planBtn").click();
}
function fixShorten(i){
const u=plan.unplaced[i];const tk=tasks.find(x=>x.id===u.task_id);
if(!tk)return;tk.minutes=Math.max(5,tk.minutes-u.minutes_left);save();renderTasks();$("planBtn").click();
}
$("printBtn").onclick=()=>window.print();
$("exportBtn").onclick=()=>{
const blob=new Blob([JSON.stringify({tasks,events,settings:settings()},null,1)],{type:"application/json"});
const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="waqt-plan.json";a.click();
};
$("importBtn").onclick=()=>$("importFile").click();
$("importFile").onchange=e=>{
const f=e.target.files[0];if(!f)return;
const rd=new FileReader();
rd.onload=()=>{try{const j=JSON.parse(rd.result);
if(j.tasks)tasks=j.tasks;if(j.events)events=j.events;
save();renderTasks();renderEvents();toast("Import ho gaya.");}catch(err){toast("Invalid JSON file.");}};
rd.readAsText(f);
};
$("clearBtn").onclick=()=>{if(!confirm("Sab tasks aur events delete kar dein?"))return;tasks=[];events=[];plan=null;save();renderTasks();renderEvents();$("planCard").style.display="none";};
fetch("/waqt/api/ai-status").then(r=>r.json()).then(j=>{
$("aiNote").textContent=j.ai_available?"AI available: estimate + breakdown on.":"AI offline (no key/quota) — scheduler + deterministic splitter phir bhi 100% kaam karte hain.";
}).catch(()=>{});
applyLang();
</script>
</body>
</html>
"""

