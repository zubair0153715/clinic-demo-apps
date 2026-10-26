QUWWAT_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quwwat — Free Strength-Training Planner</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
form{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;background:#f4f7f4;padding:14px;border-radius:10px}
label{font-size:14px;display:block} input,select{width:100%;padding:7px;margin-top:4px;box-sizing:border-box}
fieldset{border:1px solid #ccc;border-radius:8px;grid-column:1/-1} legend{font-weight:600}
button{background:#0b6e4f;color:#fff;border:0;padding:10px 16px;border-radius:8px;cursor:pointer;font-size:15px}
button.sec{background:#e8e8e8;color:#222}
.card{border:1px solid #ddd;border-radius:10px;padding:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px} th,td{border:1px solid #ddd;padding:5px 7px;text-align:left}
.trained{background:#c8e6c9}.recovering{background:#fff9c4}.ready{background:#e3f2fd}
.tag{display:inline-block;background:#eef;padding:2px 8px;border-radius:12px;font-size:12px;margin:2px}
.warn{background:#fff3e0;border:1px solid #ffb74d;border-radius:8px;padding:10px;margin:10px 0}
.tabs button{margin-right:6px}.tabs button.on{background:#0b6e4f}
.small{font-size:13px;color:#555}
@media print{form,.tabs button,.noprint{display:none!important}}
</style></head><body>
<h1>Quwwat <span style="font-size:20px">قُوَّت</span></h1>
<p class="sub">Free strength-training planner — no account, no card, no trial clock.
Original build, not affiliated with Fitbod or any other fitness app.</p>
<div class="warn"><b>Honest scope:</b> general fitness information, not medical advice.
Loads are prescribed only from a 1RM <i>you</i> enter (Epley formula, shown below).
For any other lift: pick a weight you can lift with 2 reps left in the tank.
Stop on sharp pain and see a clinician. No nutrition, no cardio, no form videos — listed as not-included, not upsold.</div>
<form id="f">
<label>Goal
<select name="goal"><option value="general">General strength</option><option value="strength">Strength (heavy)</option><option value="muscle">Muscle (hypertrophy)</option></select></label>
<label>Level
<select name="level"><option value="beginner">Beginner</option><option value="intermediate" selected>Intermediate</option><option value="advanced">Advanced</option></select></label>
<label>Days per week
<select name="days"><option value="2">2</option><option value="3" selected>3</option><option value="4">4</option><option value="5">5</option></select></label>
<label>Equipment
<select name="equipment"><option value="full_gym">Full gym</option><option value="dumbbells">Dumbbells + bodyweight</option><option value="bodyweight">Bodyweight only</option></select></label>
<label>Language for AI notes
<select name="lang"><option value="en">English</option><option value="ru">Roman-Urdu</option><option value="ur">Urdu script</option></select></label>
<fieldset><legend>Injuries / joints to protect — every exercise using that joint is removed (the filter Fitbod lacks)</legend>
<label><input type="checkbox" name="inj" value="shoulder"> Shoulder</label>
<label><input type="checkbox" name="inj" value="elbow"> Elbow</label>
<label><input type="checkbox" name="inj" value="wrist"> Wrist</label>
<label><input type="checkbox" name="inj" value="knee"> Knee</label>
<label><input type="checkbox" name="inj" value="lower_back"> Lower back</label>
</fieldset>
<fieldset><legend>Your best recent set (optional — only these lifts get a prescribed weight)</legend>
<label>Squat: weight (kg) <input name="squat_w" type="number" min="0" step="0.5"></label>
<label>Squat: reps <input name="squat_r" type="number" min="1" max="20" value="5"></label>
<label>Bench: weight (kg) <input name="bench_w" type="number" min="0" step="0.5"></label>
<label>Bench: reps <input name="bench_r" type="number" min="1" max="20" value="5"></label>
<label>Deadlift: weight (kg) <input name="deadlift_w" type="number" min="0" step="0.5"></label>
<label>Deadlift: reps <input name="deadlift_r" type="number" min="1" max="20" value="5"></label>
<label>Overhead press: weight (kg) <input name="press_w" type="number" min="0" step="0.5"></label>
<label>Overhead press: reps <input name="press_r" type="number" min="1" max="20" value="5"></label>
</fieldset>
<div><button type="submit">Build my 4-week plan</button>
<button type="button" class="sec" id="saveBtn">Save plan on this device</button></div>
</form>
<p class="small" id="aiStatus"></p>
<div id="out"></div>
<script>
const $=s=>document.querySelector(s);
let lastPlan=null,lastWeek=0;
fetch('/quwwat/api/ai-status').then(r=>r.json()).then(j=>{
  $('#aiStatus').textContent=j.ai_available?'AI coaching notes: available (Gemini).':'AI coaching notes: unavailable here (no key) — the full plan still works without it.';
});
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function renderWeek(w){
  let h=`<p>${esc(lastPlan.block_note)}</p>`;
  h+=`<p><b>Week ${w.week}${w.deload?' — DELOAD':''}:</b> ${w.sets} sets × ${w.reps} reps at ${(w.intensity*100).toFixed(0)}% of 1RM where a 1RM is known.</p>`;
  w.sessions.forEach(s=>{
    h+=`<div class="card"><b>Day ${s.day} — ${esc(s.type)}</b> <span class="small">(${s.total_reps} total reps${s.tonnage_kg?`, ${s.tonnage_kg} kg prescribed tonnage`:''})</span><table><tr><th>Exercise</th><th>Sets × Reps</th><th>Load</th></tr>`;
    s.exercises.forEach(e=>{h+=`<tr><td>${esc(e.name)} <span class="small">${e.muscles.join(', ')}</span></td><td>${e.sets} × ${e.reps}</td><td>${esc(e.load_note)}</td></tr>`});
    h+=`</table>${s.missing.length?`<p class="small">No available exercise for: ${s.missing.join(', ')} (equipment / injury / level filters removed them — train those muscles another way or loosen a filter).</p>`:''}</div>`;
  });
  return h;
}
function render(){
  const p=lastPlan,w=p.weeks[lastWeek];
  let h=`<h2>Your 4-week ${esc(p.goal)} plan</h2>`;
  h+=`<p class="small">Usable exercises after your filters: ${p.pool_size}. Progression rule: if you complete all sets and reps, move to next week's percentages; if you miss reps, repeat the week.</p>`;
  if(Object.keys(p.one_rep_maxes).length){
    h+=`<div class="card"><b>Your estimated 1RMs (Epley: weight × (1 + reps/30))</b><br>`;
    for(const[k,v] of Object.entries(p.one_rep_maxes)) h+=`<span class="tag">${esc(k)}: ${v} kg</span>`;
    h+=`</div>`;
  }
  h+=`<div class="tabs noprint">${p.weeks.map((x,i)=>`<button class="${i===lastWeek?'on':''}" onclick="lastWeek=${i};render()">${x.deload?'Deload':'Week '+x.week}</button>`).join('')}</div>`;
  h+=renderWeek(w);
  const rec=p.recovery, days=p.weeks[0].sessions.length;
  h+=`<div class="card"><b>Muscle recovery map — week 1</b> (trained / recovering &lt;48h / ready ≥48h, computed from this plan)<table><tr><th>Muscle</th>${Array.from({length:days},(_,i)=>`<th>Day ${i+1}</th>`).join('')}</tr>`;
  for(const m of Object.keys(rec)) h+=`<tr><td>${esc(m)}</td>${rec[m].map(s=>`<td class="${s}">${s}</td>`).join('')}</tr>`;
  h+=`</table></div>`;
  h+=`<div class="noprint"><button onclick="window.print()">Print plan</button> <button class="sec" onclick="dlCSV()">Download CSV</button> <button class="sec" id="aiBtn">AI coaching notes</button></div><div id="aiOut"></div>`;
  $('#out').innerHTML=h;
  const b=$('#aiBtn'); if(b) b.onclick=aiNotes;
}
async function aiNotes(){
  const lang=$('#f').lang.value;
  const w=lastPlan.weeks[lastWeek];
  const summary=`Goal ${lastPlan.goal}, week ${w.week}, injuries filtered: ${lastPlan.injuries.join(', ')||'none'}. Sessions: `+w.sessions.map(s=>s.type+': '+s.exercises.map(e=>e.name).join(', ')).join(' | ');
  $('#aiOut').textContent='AI notes loading…';
  const r=await fetch('/quwwat/api/ai-explain',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({summary,lang})});
  const j=await r.json();
  $('#aiOut').textContent=j.notes||('AI notes unavailable: '+(j.error||'unknown'));
}
function dlCSV(){
  const rows=[['week','day','session','exercise','sets','reps','load']];
  lastPlan.weeks.forEach(w=>w.sessions.forEach(s=>s.exercises.forEach(e=>rows.push([w.week,s.day,s.type,e.name,e.sets,e.reps,e.load_note]))));
  const csv=rows.map(r=>r.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(',')).join('\n');
  const a=document.createElement('a'); a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'})); a.download='quwwat-plan.csv'; a.click();
}
$('#f').addEventListener('submit',async ev=>{
  ev.preventDefault();
  const fd=new FormData(ev.target);
  const lifts={};
  for(const k of ['squat','bench','deadlift','press']){
    const w=parseFloat(fd.get(k+'_w')); const r=parseInt(fd.get(k+'_r')||'5',10);
    if(w>0) lifts[k]={weight:w,reps:r};
  }
  const body={goal:fd.get('goal'),level:fd.get('level'),days:parseInt(fd.get('days'),10),equipment:fd.get('equipment'),injuries:fd.getAll('inj'),lifts};
  const res=await fetch('/quwwat/api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  lastPlan=await res.json(); lastWeek=0; render();
});
$('#saveBtn').addEventListener('click',()=>{
  if(!lastPlan){alert('Build a plan first.');return}
  localStorage.setItem('quwwat-plan',JSON.stringify(lastPlan)); alert('Plan saved on this device.');
});
try{const saved=localStorage.getItem('quwwat-plan'); if(saved){lastPlan=JSON.parse(saved); lastWeek=0; render();}}catch(e){}
</script></body></html>
"""
