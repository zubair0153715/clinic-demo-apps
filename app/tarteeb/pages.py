"""Tarteeb page — single-page resume tailorer UI (original design)."""

TARTEEB_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tarteeb — Free AI Resume Tailorer</title>
<meta name="description" content="Paste your resume and a job description. Tarteeb scores the match, lists missing keywords, and tailors your resume — free, no account, no card.">
<style>
body{font-family:system-ui,sans-serif;max-width:820px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
input,textarea{width:100%;padding:8px;margin:4px 0 12px;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-size:15px}
textarea{min-height:130px} button{padding:10px 18px;border:0;border-radius:6px;background:#0b6e4f;color:#fff;font-size:16px;cursor:pointer}
button.sec{background:#eee;color:#111} .card{border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
.bar{height:12px;background:#eee;border-radius:6px;overflow:hidden}.bar>i{display:block;height:100%;background:#0b6e4f}
#resume{border:1px solid #999;padding:20px;margin-top:10px}
#resume h1{font-size:24px;margin:0}#resume h2{font-size:16px;border-bottom:1px solid #ccc;padding-bottom:2px}
.small{color:#555;font-size:13px} table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #eee;padding:6px;vertical-align:top;text-align:left}
.miss{color:#9b1c1c}.hit{color:#0b6e4f}
@media print{body>*:not(#printarea){display:none!important}#printarea{display:block!important}}
</style></head><body>
<h1>Tarteeb — AI Resume Tailorer</h1>
<p class="sub">Resume ko job ke hisaab se dhaalain. Free, no account, no card.
Aapka resume server par save nahi hota — sirf is request mein istemal hota hai.</p>
<p class="small"><b>Honest limits, seedha seedha:</b> match score sirf keyword/skill
overlap ka <i>estimate</i> hai — yeh asli ATS score nahi, aur interview ki
guarantee nahi. Tarteeb kabhi experience, skill, degree ya achievement
<b>invent nahi karta</b>: jo JD maangta hai aur resume mein nahi hai, woh
<i>gap</i> ke tor par flag hota hai — jhoot se bharna aapka kaam nahi, aur
hamara bhi nahi. AI rewrite bhi sirf aapke likhe facts ko behtar lafzon mein
dhalta hai.</p>
<form id="f" enctype="multipart/form-data">
<label>Your resume — paste text <textarea name="resume_text" id="resumeText" placeholder="Paste your full resume text here…"></textarea></label>
<label>…or upload CV (.pdf / .docx, max 5 MB) <input type="file" name="resume_file" id="resumeFile" accept=".pdf,.docx"></label>
<label>Job description — paste the full ad <textarea name="job_description" id="jdText" placeholder="Paste the job description here…"></textarea></label>
<button type="submit">Analyze + tailor my resume</button>
<button type="button" class="sec" id="sampleBtn">Try a sample</button>
<button type="button" class="sec" id="aiBtn">AI-tailor my bullets (optional)</button>
<span id="aiState" class="small"></span>
</form>
<div id="out"></div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>(s||'').replace(/</g,'&lt;');
fetch('/tarteeb/api/ai-status').then(r=>r.json()).then(d=>{
  $('#aiState').textContent = d.ai_available ? 'AI available' : 'AI not set up here — rule-based tailoring still works fully.';
});
$('#sampleBtn').onclick=()=>{
  $('#resumeText').value = SAMPLE_RESUME;
  $('#jdText').value = SAMPLE_JD;
};
$('#aiBtn').onclick=async()=>{
  const fd=new FormData($('#f'));
  const r=await fetch('/tarteeb/api/ai-tailor',{method:'POST',body:fd});
  const d=await r.json();
  if(!d.ok){ alert(d.error||'AI failed'); return; }
  let h='<div class="card"><h3>AI-tailored (facts only — check every line)</h3>';
  if(d.ai_summary) h+='<p><b>Summary:</b> '+esc(d.ai_summary)+'</p>';
  h+='<table><tr><th>Original</th><th>AI-tailored</th></tr>'
    +d.ai_bullets.map(b=>'<tr><td>'+esc(b.original)+'</td><td>'+esc(b.tailored)+'</td></tr>').join('')+'</table>'
    +'<p class="small">AI rewords only what you wrote. If any line adds a fact you do not have, delete it.</p></div>';
  $('#out').innerHTML=h+$('#out').innerHTML;
};
$('#f').onsubmit=async(e)=>{
  e.preventDefault();
  const fd=new FormData($('#f'));
  const r=await fetch('/tarteeb/api/analyze',{method:'POST',body:fd});
  const d=await r.json();
  if(!d.ok){ alert(d.error); return; }
  const rows=Object.entries(d.breakdown).map(([k,v])=>'<tr><td>'+k+'</td><td>'+v+'</td></tr>').join('');
  const pairs=d.tailored.bullet_pairs.map(p=>'<tr><td>'+esc(p.original)+'</td><td>'+esc(p.tailored)+'<br><span class="small">'+esc(p.notes.join(' '))+'</span></td></tr>').join('');
  const gaps=d.jd.skills_missing.length?'<p class="miss"><b>Skills gaps — do NOT claim these unless true:</b> '+esc(d.jd.skills_missing.join(', '))+'</p>':'<p class="hit"><b>No required-skill gaps found.</b></p>';
  $('#out').innerHTML=
   '<div class="card"><h2>Match score: '+d.score+'/100</h2>'
   +'<div class="bar"><i style="width:'+d.score+'%"></i></div><p>'+esc(d.explanation)+'</p>'
   +'<table>'+rows+'</table></div>'
   +'<div class="card"><h3>Job-description keywords</h3><p>Coverage: '+(d.jd.coverage*100).toFixed(1)+'% ('+d.jd.matched.length+'/'+d.jd.keywords_total+')</p>'
   +'<p><b class="hit">Matched:</b> '+esc(d.jd.matched.join(', '))+'</p>'
   +'<p><b class="miss">Missing:</b> '+(esc(d.jd.missing.join(', '))||'none')+'</p>'
   +'<p><b class="hit">Required skills you have:</b> '+esc(d.jd.skills_matched.join(', '))+'</p>'
   +gaps
   +'<p class="small">Add missing keywords only where they are genuinely true of you.</p></div>'
   +'<div class="card"><h3>Before vs after — bullets (reordered to the JD, openings repaired)</h3><table><tr><th>Original</th><th>Tailored</th></tr>'+pairs+'</table>'
   +'<p class="small">Tailored summary: '+esc(d.tailored.summary)+'</p></div>'
   +'<div class="card"><h3>Your tailored resume</h3><div id="printarea"><div id="resume">'+d.tailored_html+'</div></div>'
   +'<p><button type="button" onclick="window.print()">Print / save as PDF</button> '
   +'<button type="button" class="sec" id="docxBtn">Download .docx</button> '
   +'<button type="button" class="sec" id="txtBtn">Download .txt</button> '
   +'<button type="button" class="sec" id="copyBtn">Copy summary</button></p></div>';
  window._plain=d.tailored_text;
  const dl=(fmt)=>{ const fd2=new FormData(); fd2.append('tailored_text',window._plain); fd2.append('fmt',fmt);
    fetch('/tarteeb/api/download',{method:'POST',body:fd2}).then(r=>r.blob()).then(b=>{ const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='resume-tailored.'+fmt; a.click(); }); };
  $('#docxBtn').onclick=()=>dl('docx');
  $('#txtBtn').onclick=()=>dl('txt');
  $('#copyBtn').onclick=()=>navigator.clipboard.writeText(d.tailored.summary).then(()=>alert('Summary copied'));
};
const SAMPLE_RESUME = `Ayesha Khan
Lahore, Pakistan | ayesha.sample@example.com | +92 300 0000000

SUMMARY
Computer science graduate with hands-on experience building web apps and automating small business workflows. Looking for a junior automation role.

SKILLS
Python, JavaScript, REST APIs, SQL, Git, HTML, CSS

EXPERIENCE
Worked on a small online store website using Python and JavaScript
Helped automate invoice emails for a family shop with Zapier
Built a student attendance tracker with a SQL database
Was responsible for fixing bugs in a college project

EDUCATION
BS Computer Science, University of the Punjab, Lahore (2024)`;
const SAMPLE_JD = `AI Automation Specialist — remote
We are looking for a junior AI Automation Specialist. You will build
workflows with n8n, Make and Zapier, integrate LLMs into business
processes, and connect REST APIs and webhooks. Requirements: Python or
JavaScript, prompt engineering, JSON and databases, error handling and
data privacy. Experience with FastAPI or LangGraph is a plus.`;
</script></body></html>
"""

