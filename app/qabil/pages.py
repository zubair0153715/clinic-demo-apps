"""Qabil page — single-page resume builder UI (original design)."""

QABIL_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Qabil — Free Resume Builder</title>
<style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
input,textarea{width:100%;padding:8px;margin:4px 0 12px;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-size:15px}
textarea{min-height:90px} button{padding:10px 18px;border:0;border-radius:6px;background:#0b6e4f;color:#fff;font-size:16px;cursor:pointer}
button.sec{background:#eee;color:#111} .card{border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
.bar{height:12px;background:#eee;border-radius:6px;overflow:hidden}.bar>i{display:block;height:100%;background:#0b6e4f}
#resume{border:1px solid #999;padding:20px;margin-top:10px}
#resume h1{font-size:24px;margin:0}#resume h2{font-size:16px;border-bottom:1px solid #ccc;padding-bottom:2px}
.small{color:#555;font-size:13px} table{border-collapse:collapse;width:100%}td{border-bottom:1px solid #eee;padding:6px;vertical-align:top}
@media print{body>*:not(#printarea){display:none!important}#printarea{display:block!important}}
</style></head><body>
<h1>Qabil — Free Resume Builder</h1>
<p class="sub">Unlimited resumes. No account, no card, no download cap, no watermark.
Your resume is never stored — it exists only while you build it.</p>
<p class="small"><b>Honest limits, stated plainly:</b> the score measures <i>document
quality only</i> — it is NOT a prediction that you will get an interview.
Bullet repair never invents numbers or achievements: missing results are
flagged for <i>you</i> to fill in with real ones. Output is single-column
plain text, because that is what ATS software actually reads.</p>
<form id="f">
<label>Full name <input name="name" placeholder="Zubair Ali"></label>
<label>Target role <input name="target_role" placeholder="Bioinformatics Research Assistant"></label>
<label>Email <input name="email" placeholder="you@example.com"></label>
<label>Phone <input name="phone" placeholder="+92 3XX XXXXXXX"></label>
<label>City <input name="city" placeholder="Larkana, Pakistan"></label>
<label>Company (for cover letter, optional) <input name="company" placeholder="e.g. Aga Khan University"></label>
<label>Summary <textarea name="summary" placeholder="2-4 lines: who you are, what you do best, what you are looking for."></textarea></label>
<label>Skills (comma separated) <textarea name="skills" placeholder="Python, RDKit, molecular docking, HPLC, data analysis"></textarea></label>
<label>Experience — one bullet per line <textarea name="experience" placeholder="Built a drug-discovery pipeline screening 500 compounds&#10;Reduced report preparation time by 40% with automation"></textarea></label>
<label>Education — one line each <textarea name="education" placeholder="Pharm-D, SMBBMU Larkana (ongoing)"></textarea></label>
<label>Job description — paste it here for keyword matching <textarea name="job_description" placeholder="Paste the job ad text. Qabil lists which of its keywords your resume already has, and which are missing."></textarea></label>
<button type="submit">Analyze + build resume</button>
<button type="button" class="sec" id="aiBtn">AI-improve my bullets (optional)</button>
<span id="aiState" class="small"></span>
</form>
<div id="out"></div>
<script>
const $=s=>document.querySelector(s);
fetch('/qabil/api/ai-status').then(r=>r.json()).then(d=>{
  $('#aiState').textContent = d.ai_available ? 'AI available' : 'AI not set up here — rule-based tools still work fully.';
});
$('#aiBtn').onclick=async()=>{
  const fd=new FormData($('#f'));
  const r=await fetch('/qabil/api/ai-improve',{method:'POST',body:new URLSearchParams({experience:fd.get('experience')})});
  const d=await r.json();
  if(d.ok){ $('#out').innerHTML='<div class="card"><h3>AI-improved bullets</h3><pre>'+d.improved.replace(/</g,'&lt;')+'</pre><p class="small">Check every line before using it — AI rewords only; it must not invent facts.</p></div>'+$('#out').innerHTML; }
  else alert(d.error||'AI failed');
};
$('#f').onsubmit=async(e)=>{
  e.preventDefault();
  const r=await fetch('/qabil/api/analyze',{method:'POST',body:new FormData($('#f'))});
  const d=await r.json();
  if(!d.ok){ alert(d.error); return; }
  const rows=Object.entries(d.breakdown).map(([k,v])=>'<tr><td>'+k+'</td><td>'+v+'</td></tr>').join('');
  const fixes=d.bullet_fixes.map(f=>'<tr><td>'+f.original.replace(/</g,'&lt;')+'</td><td>'+f.fixed.replace(/</g,'&lt;')+'<br><span class="small">'+f.notes.join(' ')+'</span></td></tr>').join('');
  $('#out').innerHTML=
   '<div class="card"><h2>ATS document score: '+d.score+'/100</h2>'
   +'<div class="bar"><i style="width:'+d.score+'%"></i></div>'
   +'<p class="small">This scores the document, not your hiring chances. Counts: '
   +d.counts.bullets+' bullets, '+d.counts.skills+' skills, '+d.counts.summary_words+' summary words, '
   +d.counts.quantified_bullets+' quantified, '+d.counts.action_bullets+' action-verb openings.</p>'
   +'<table>'+rows+'</table></div>'
   +'<div class="card"><h3>Job-description keywords</h3><p>Coverage: '+(d.jd.coverage*100).toFixed(1)+'% ('+d.jd.matched.length+'/'+d.jd.keywords_total+')</p>'
   +'<p><b>Matched:</b> '+d.jd.matched.join(', ')+'</p><p><b>Missing:</b> '+(d.jd.missing.join(', ')||'none')+'</p>'
   +'<p class="small">Add missing keywords only where they are genuinely true of you.</p></div>'
   +'<div class="card"><h3>Bullet repair (no invented facts)</h3><table><tr><th>Original</th><th>Fixed</th></tr>'+fixes+'</table></div>'
   +'<div class="card"><h3>Your resume</h3><div id="printarea"><div id="resume">'+d.resume_html+'</div></div>'
   +'<p><button type="button" onclick="window.print()">Print / save as PDF</button> '
   +'<button type="button" class="sec" id="txtBtn">Download plain text (.txt)</button> '
   +'<button type="button" class="sec" id="copyBtn">Copy plain text</button></p>'
   +'<h3>Cover letter draft</h3><pre id="cover">'+d.cover_letter.replace(/</g,'&lt;')+'</pre></div>';
  window._plain=d.plain_text;
  $('#txtBtn').onclick=()=>{ const b=new Blob([window._plain],{type:'text/plain'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='resume.txt'; a.click(); };
  $('#copyBtn').onclick=()=>navigator.clipboard.writeText(window._plain).then(()=>alert('Copied'));
};
</script></body></html>
"""
