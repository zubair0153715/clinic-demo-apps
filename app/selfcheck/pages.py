"""Single-page quiz HTML for PharmaReg Self-Check (inline, no build step)."""

QUIZ_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><link rel="manifest" href="/selfcheck/manifest.json"><meta name="theme-color" content="#7c3aed"><link rel="apple-touch-icon" href="/selfcheck/icon-192.png"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DRAP Audit Readiness Check — Free 2-Minute Self-Assessment | PharmaReg AI</title>
<meta name="description" content="Is your pharma facility DRAP-audit ready? Answer 10 yes/no questions and get your readiness score plus the gaps auditors will flag. Free.">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6;background:#f6f8f7}
.wrap{max-width:680px;margin:0 auto;padding:0 20px}
header{background:#1a3c5e;color:#fff;padding:48px 0}
header h1{margin:0 0 10px;font-size:1.8rem;line-height:1.3}
header p{margin:0;opacity:.9;max-width:560px}
.btn{display:inline-block;background:#25d366;color:#062b1f;font-weight:700;padding:14px 30px;border-radius:10px;text-decoration:none;margin:10px 10px 10px 0;border:0;font-size:1.05rem;cursor:pointer}
.btn.blue{background:#1a3c5e;color:#fff}
.card{background:#fff;border-radius:14px;padding:26px;margin:24px 0;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.hidden{display:none}
input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;font-size:1rem;box-sizing:border-box}
.q{font-size:1.15rem;font-weight:600;margin:6px 0 4px}
.area{display:inline-block;background:#e8eef5;color:#1a3c5e;font-size:.78rem;font-weight:700;padding:3px 12px;border-radius:20px;margin-bottom:8px}
.yn{display:flex;gap:12px;margin-top:16px}
.yn button{flex:1;padding:16px;font-size:1.1rem;border-radius:10px;border:2px solid #ddd;background:#fff;cursor:pointer;font-weight:700}
.yn button.yes:hover{border-color:#2e7d32;color:#2e7d32}
.yn button.no:hover{border-color:#c62828;color:#c62828}
.progress{height:8px;background:#e0e0e0;border-radius:4px;margin:14px 0}
.progress i{display:block;height:100%;background:#1a3c5e;border-radius:4px;transition:width .3s}
.score{font-size:3.2rem;font-weight:800;color:#1a3c5e;margin:0}
.band{font-size:1.4rem;font-weight:700;margin:6px 0}
.gap{background:#fef6f6;border-left:4px solid #c62828;border-radius:0 10px 10px 0;padding:12px 16px;margin:10px 0}
.gap b{color:#c62828}
.gap p{margin:6px 0 0;font-size:.92rem;color:#444}
.ok-area{background:#f1f8e9;border-left:4px solid #2e7d32;border-radius:0 10px 10px 0;padding:10px 16px;margin:10px 0;font-size:.92rem}
footer{padding:24px 0;color:#666;font-size:.85rem;text-align:center}
.step{font-size:.85rem;color:#888;margin-bottom:4px}
</style></head><body>
<header><div class="wrap">
<h1>Is your facility DRAP-audit ready?</h1>
<p>10 yes/no questions. 2 minutes. Get your readiness score <b>0–100</b> plus the exact gaps a DRAP auditor would flag — free.</p>
</div></header>
<div class="wrap">

<div id="s-intro" class="card">
<div class="step">Step 1 of 3 — Your details</div>
<h2 style="margin-top:0;color:#1a3c5e">Where should we send your report?</h2>
<input id="f-name" placeholder="Your name *">
<input id="f-company" placeholder="Company / facility name *">
<input id="f-phone" placeholder="Phone / WhatsApp (optional)">
<button class="btn blue" onclick="startQuiz()">Start the check →</button>
<p id="intro-err" style="color:#c0392b"></p>
<p style="font-size:.82rem;color:#888">We only use this to send your report and follow up once. No spam, ever.</p>
</div>

<div id="s-quiz" class="card hidden">
<div class="step" id="q-step">Question 1 of 10</div>
<div class="progress"><i id="q-bar" style="width:10%"></i></div>
<div class="area" id="q-area"></div>
<div class="q" id="q-text"></div>
<div class="yn"><button class="yes" onclick="answer(true)">✅ Yes</button><button class="no" onclick="answer(false)">❌ No</button></div>
</div>

<div id="s-result" class="card hidden">
<div class="step">Your result</div>
<p class="score" id="r-score">–/100</p>
<div class="band" id="r-band"></div>
<p id="r-text" style="color:#444"></p>
<h3 style="color:#1a3c5e">Gaps a DRAP auditor would flag 🚩</h3>
<div id="r-gaps"></div>
<div id="r-ok"></div>
<div style="margin-top:22px;text-align:center">
<p><b>Want these gaps fixed before DRAP walks in?</b></p>
<a class="btn" id="r-cta" href="#" target="_blank">💬 Discuss my report on WhatsApp</a>
<p style="font-size:.85rem;color:#666">Or explore <a href="https://pharmareg-ai.fastapicloud.dev">PharmaReg AI</a> — full AI compliance audits for pharma manufacturers.</p>
</div></div>

</div>
<footer>PharmaReg Self-Check — a free tool by <b>Zubair Ahmed</b> · <a href="https://pharmareg-ai.fastapicloud.dev">PharmaReg AI</a></footer>

<script>
const $=id=>document.getElementById(id);
let QS=[], ANS=[], META={};
async function startQuiz(){
 META={name:$('f-name').value.trim(),company:$('f-company').value.trim(),phone:$('f-phone').value.trim()};
 if(!META.name||!META.company){$('intro-err').textContent='Please enter your name and company.';return}
 const d=await (await fetch('/selfcheck/api/questions')).json();QS=d.questions;ANS=[];
 $('s-intro').classList.add('hidden');$('s-quiz').classList.remove('hidden');showQ(0);
}
let QI=0;
function showQ(i){QI=i;const q=QS[i];
 $('q-step').textContent='Question '+(i+1)+' of '+QS.length;
 $('q-bar').style.width=((i+1)/QS.length*100)+'%';
 $('q-area').textContent=q.area;$('q-text').textContent=q.question;}
async function answer(v){ANS.push(v);
 if(ANS.length<QS.length){showQ(ANS.length);return}
 $('s-quiz').classList.add('hidden');
 const r=await (await fetch('/selfcheck/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({name:META.name,company:META.company,phone:META.phone,answers:ANS})})).json();
 $('r-score').textContent=r.score+'/100';$('r-band').textContent=r.band_label;$('r-text').textContent=r.band_text;
 $('r-gaps').innerHTML=r.gaps.length?r.gaps.map(g=>'<div class="gap"><b>🚩 '+g.area+'</b> — '+g.question+'<p>Fix: '+g.fix+'</p></div>').join(''):'<div class="ok-area">✅ No gaps found — excellent!</div>';
 const okCount=10-r.gaps.length;
 $('r-ok').innerHTML=okCount?'<div class="ok-area">✅ <b>'+okCount+'/10</b> areas already audit-ready.</div>':'';
 $('r-cta').href=r.whatsapp_cta;
 $('s-result').classList.remove('hidden');window.scrollTo({top:0,behavior:'smooth'});
}
</script><script>if("serviceWorker" in navigator){navigator.serviceWorker.register("/selfcheck/sw.js").catch(()=>{});}</script></body></html>"""
