"""Majlis page — free AI meeting-notes studio UI (original design)."""

MAJLIS_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Majlis — Free AI Meeting Notes</title>
<style>
body{font-family:system-ui,sans-serif;max-width:780px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
input,textarea,select{width:100%;padding:8px;margin:4px 0 12px;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-size:15px}
textarea{min-height:180px} button{padding:10px 18px;border:0;border-radius:6px;background:#14532d;color:#fff;font-size:16px;cursor:pointer}
button.sec{background:#eee;color:#111} .card{border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
.small{color:#555;font-size:13px} table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #eee;padding:6px;vertical-align:top;text-align:left}
pre{white-space:pre-wrap;background:#f6f6f6;padding:10px;border-radius:6px;font-size:14px}
.done{text-decoration:line-through;color:#777}
li{margin:4px 0}
</style></head><body>
<h1>Majlis — Free AI Meeting Notes</h1>
<p class="sub">Paste a transcript (or type notes live) and get structured
minutes: decisions, owned action items, open questions and a
WhatsApp follow-up draft. No account, no card, no subscription —
and your history is never locked.</p>
<p class="small"><b>Honest limits, stated plainly:</b> Majlis does NOT
record audio and does NOT transcribe speech. Paste a transcript from
any recorder or free transcription tool, or type notes during the
meeting — one line per turn, like <i>Ayesha: we agreed to launch on
5 November.</i> Nothing is stored on our server: your notes live in
your own browser. <b>Consent:</b> always tell the people in the
meeting that you are taking notes.</p>
<form id="f">
<label>Meeting title <input name="title" placeholder="Weekly clinic sync"></label>
<label>Date <input name="date" type="date"></label>
<label>Meeting type <select name="mtype">
<option value="team" selected>Team sync</option>
<option value="client">Client call</option>
<option value="sales">Sales call</option>
<option value="one-on-one">One-on-one</option>
<option value="brainstorm">Brainstorm</option>
<option value="other">Other</option></select></label>
<label>Minutes language <select name="language">
<option value="en" selected>English</option>
<option value="roman">Roman-Urdu</option>
<option value="ur">Urdu (script, RTL)</option></select></label>
<label>Transcript / live notes — one turn per line, “Name: what was said”
<textarea name="transcript" id="transcript" placeholder="Ayesha: Let's decide the launch date today. We agreed to launch on 5 November.&#10;Bilal: I will prepare the pricing sheet by Friday.&#10;Sara: I will call the printer tomorrow."></textarea></label>
<button type="submit">Structure my notes</button>
<button type="button" class="sec" id="sampleBtn">Load a sample meeting</button>
<button type="button" class="sec" id="aiBtn">AI-polish the summary (optional)</button>
<span id="aiState" class="small"></span>
</form>
<div id="out"></div>
<div class="card"><h3 style="margin-top:0">My meetings (saved in this browser only)</h3>
<div id="history"></div>
<button type="button" class="sec" id="clearHist">Clear browser history</button></div>
<script>
const $=s=>document.querySelector(s);
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
fetch('/majlis/api/ai-status').then(r=>r.json()).then(d=>{
  $('#aiState').textContent = d.ai_available ? 'AI available' : 'AI not set up here — structuring still works fully.';
});
const SAMPLE = "Ayesha: Let's decide the launch date today. We agreed to launch on 5 November.\nBilal: I will prepare the pricing sheet by Friday.\nSara: I will call the printer tomorrow.\nBilal: Should we include the Urdu flyer? Decided: yes, include it.\nAyesha: What about the stall booking?\nBilal: I need to confirm the stall by Monday.";
$('#sampleBtn').onclick=()=>{ $('#transcript').value=SAMPLE; };
function loadHist(){ try{ return JSON.parse(localStorage.getItem('majlis_hist')||'[]'); }catch(e){ return []; } }
function saveHist(list){ localStorage.setItem('majlis_hist', JSON.stringify(list.slice(0,50))); }
function renderHist(){
  const h=loadHist();
  $('#history').innerHTML = h.length ? h.map((m,i)=>'<div><b>'+esc(m.title)+'</b> <span class="small">'+esc(m.date||'')+' · '+m.actions+' actions · '+m.decisions+' decisions</span> <button type="button" class="sec" data-i="'+i+'">Open</button></div>').join('') : '<p class="small">No meetings saved yet in this browser.</p>';
  document.querySelectorAll('#history button').forEach(b=>b.onclick=()=>{
    const m=loadHist()[+b.dataset.i]; if(!m) return;
    $('#f').title.value=m.title; $('#f').date.value=m.date||'';
    $('#transcript').value=m.transcript; $('#f').dispatchEvent(new Event('submit',{cancelable:true}));
  });
}
$('#clearHist').onclick=()=>{ localStorage.removeItem('majlis_hist'); renderHist(); };
renderHist();
let lastResult=null;
$('#f').addEventListener('submit', async ev=>{
  ev.preventDefault();
  const fd=new FormData($('#f'));
  const r=await fetch('/majlis/api/structure',{method:'POST',body:new URLSearchParams(fd)});
  const d=await r.json();
  if(!d.ok){ $('#out').innerHTML='<div class="card"><b>Error:</b> '+esc(d.error||'Unknown error')+'</div>'; return; }
  lastResult=d;
  const st=d.stats;
  const shareRows=st.share.map(s=>'<tr><td>'+esc(s.speaker)+'</td><td>'+s.words+' words</td><td>'+s.pct+'%</td></tr>').join('');
  const dec=d.decisions.length?d.decisions.map(x=>'<li>'+esc(x.text)+' <span class="small">(line '+x.line+', '+esc(x.speaker)+')</span></li>').join(''):'<li>None recorded.</li>';
  const act=d.actions.length?d.actions.map((x,i)=>'<li><label><input type="checkbox" class="act" data-i="'+i+'"> '+esc(x.text)+' — <b>'+esc(x.owner)+'</b>'+(x.due?' (by '+esc(x.due)+')':'')+' <span class="small">(line '+x.line+')</span></label></li>').join(''):'<li>None found.</li>';
  const q=d.questions.length?d.questions.map(x=>'<li>'+esc(x.text)+' <span class="small">(line '+x.line+')</span></li>').join(''):'<li>None recorded.</li>';
  $('#out').innerHTML='<div class="card"><h3 style="margin-top:0">'+esc(d.title)+' '+(d.date?'('+esc(d.date)+')':'')+'</h3>'
    +'<p><b>'+st.words+' words · '+st.turns+' turns · '+st.speakers+' speakers · about '+st.est_minutes+' min</b> (at 150 words/min)</p>'
    +'<table><tr><th>Speaker</th><th>Words</th><th>Talk share</th></tr>'+shareRows+'</table>'
    +'<h4>Decisions ('+d.decisions.length+')</h4><ul>'+dec+'</ul>'
    +'<h4>Action items ('+d.actions.length+') — tick when done</h4><ul>'+act+'</ul>'
    +'<h4>Open questions ('+d.questions.length+')</h4><ul>'+q+'</ul>'
    +'<h4>Follow-up message (WhatsApp-ready)</h4><pre id="followup">'+esc(d.followup)+'</pre>'
    +'<button type="button" class="sec" id="copyBtn">Copy follow-up</button> '
    +'<button type="button" class="sec" id="dlBtn">Download minutes (.md)</button> '
    +'<button type="button" class="sec" id="saveBtn">Save to browser history</button>'
    +'<div id="polished"></div></div>';
  document.querySelectorAll('.act').forEach(c=>c.onchange=()=>{ c.closest('li').classList.toggle('done', c.checked); });
  $('#copyBtn').onclick=()=>{ navigator.clipboard.writeText(d.followup); $('#copyBtn').textContent='Copied!'; };
  $('#dlBtn').onclick=()=>{
    const blob=new Blob([d.markdown],{type:'text/markdown'});
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download=(d.title||'meeting').replace(/[^A-Za-z0-9]+/g,'-').toLowerCase()+'.md'; a.click();
  };
  $('#saveBtn').onclick=()=>{
    const h=loadHist();
    h.unshift({title:d.title,date:d.date,actions:d.actions.length,decisions:d.decisions.length,transcript:fd.get('transcript')});
    saveHist(h); renderHist(); $('#saveBtn').textContent='Saved in this browser';
  };
});
$('#aiBtn').onclick=async()=>{
  if(!lastResult){ alert('Pehle “Structure my notes” dabayein — phir AI polish.'); return; }
  const r=await fetch('/majlis/api/ai-polish',{method:'POST',body:new URLSearchParams({summary:lastResult.markdown,language:$('#f').language.value})});
  const d=await r.json();
  const box=$('#polished');
  if(!box) return;
  box.innerHTML = d.ok ? '<h4>AI-polished summary</h4><pre>'+esc(d.polished)+'</pre>' : '<p><b>AI error:</b> '+esc(d.error||'Unknown error')+'</p>';
};
</script></body></html>
"""
