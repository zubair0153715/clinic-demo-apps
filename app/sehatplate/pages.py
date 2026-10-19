"""SehatPlate single-page UI (mobile-first, works fine on a phone browser)."""

SEHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SehatPlate — honest AI calorie tracker with desi foods</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--txt:#e2e8f0;--dim:#94a3b8;
--grn:#22c55e;--amb:#f59e0b;--red:#ef4444;--blu:#38bdf8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;padding:12px;max-width:640px;margin:0 auto}
h1{font-size:1.5rem;margin:.4em 0}.tag{color:var(--dim);font-size:.9rem;margin-top:-.6em}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:14px;margin:12px 0}
.card h2{margin:.1em 0 .6em;font-size:1.05rem}
label{font-size:.82rem;color:var(--dim);display:block;margin:8px 0 3px}
input,select,button{font-size:1rem;padding:10px;border-radius:10px;border:1px solid var(--line);
background:#0b1220;color:var(--txt);width:100%}
.row{display:flex;gap:8px}.row>*{flex:1}
button{background:var(--grn);border:none;color:#06210f;font-weight:700;cursor:pointer;margin-top:10px}
button.ghost{background:transparent;border:1px solid var(--line);color:var(--txt);font-weight:400}
button.blue{background:var(--blu);color:#06202b}
.bar{height:10px;background:#0b1220;border-radius:6px;overflow:hidden;margin:4px 0 10px}
.bar>i{display:block;height:100%;background:var(--grn);border-radius:6px}
.bar.over>i{background:var(--red)}
.kv{display:flex;justify-content:space-between;font-size:.9rem;padding:3px 0}
.kv b{font-variant-numeric:tabular-nums}
.food{display:flex;justify-content:space-between;align-items:center;padding:8px 0;
border-bottom:1px solid var(--line);font-size:.92rem}
.food small{color:var(--dim)}
.badge{font-size:.68rem;padding:2px 8px;border-radius:20px;margin-left:6px;vertical-align:middle}
.badge.usda{background:#134e4a;color:#5eead4}.badge.recipe{background:#451a03;color:#fdba74}
.badge.ai{background:#1e3a8a;color:#93c5fd}
.entry{display:flex;justify-content:space-between;align-items:center;padding:7px 0;
border-bottom:1px solid var(--line);font-size:.9rem}
.entry small{color:var(--dim)}
.del{background:var(--red);color:#fff;border:none;border-radius:8px;padding:6px 10px;
width:auto;margin:0;font-size:.8rem}
.meal{font-size:.75rem;color:var(--dim);text-transform:uppercase;letter-spacing:.08em;
margin:10px 0 2px}
.note{font-size:.8rem;color:var(--dim)}.warn{font-size:.82rem;color:var(--amb)}
footer{font-size:.75rem;color:var(--dim);margin:18px 0;line-height:1.5}
.tabs{display:flex;gap:6px;margin:6px 0}.tabs button{margin:0;padding:8px}
.tabs button.on{background:var(--blu);color:#06202b}
input[type=number]{width:80px}
.qadd{display:inline-block;width:auto;margin:2px;padding:6px 10px;font-size:.8rem}
</style>
</head>
<body>
<h1>🍛 SehatPlate</h1>
<p class="tag">Honest AI calorie tracker — desi food database, no paywall traps, estimates labeled as estimates.</p>

<div class="card">
<h2>👤 Your targets</h2>
<div class="row">
<div><label>Age</label><input id="age" type="number" value="22" min="10" max="100"></div>
<div><label>Sex</label><select id="sex"><option value="male">Male</option><option value="female">Female</option></select></div>
</div>
<div class="row">
<div><label>Height (cm)</label><input id="height" type="number" value="170" min="120" max="230"></div>
<div><label>Weight (kg)</label><input id="weight" type="number" value="70" min="30" max="250"></div>
</div>
<label>Activity</label>
<select id="activity">
<option value="sedentary">Sedentary (desk job)</option>
<option value="light">Light (1–3 days/week)</option>
<option value="moderate" selected>Moderate (3–5 days/week)</option>
<option value="active">Active (6–7 days/week)</option>
<option value="athlete">Athlete (2x/day)</option>
</select>
<label>Goal</label>
<select id="goal">
<option value="lose">Lose weight (~0.5 kg/week)</option>
<option value="maintain" selected>Maintain weight</option>
<option value="gain">Gain weight (lean)</option>
</select>
<button onclick="saveProfile()">Save &amp; compute targets</button>
<div id="targets" style="margin-top:10px"></div>
<p class="note">Math: Mifflin-St Jeor BMR × activity factor; −500 kcal for loss, +300 for gain; protein 1.6 g/kg.</p>
</div>

<div class="card">
<h2>🔍 Add food <span style="font-size:.75rem;color:var(--dim)">(per 100 g database)</span></h2>
<div class="tabs">
<button class="on" onclick="setMeal('breakfast',this)">Breakfast</button>
<button onclick="setMeal('lunch',this)">Lunch</button>
<button onclick="setMeal('dinner',this)">Dinner</button>
<button onclick="setMeal('snack',this)">Snack</button>
</div>
<input id="q" placeholder="Search: biryani, roti, daal, chai…" oninput="searchFoods()">
<div id="results"></div>
</div>

<div class="card">
<h2>🤖 AI meal estimate <span class="badge ai">AI estimate</span></h2>
<p class="note">Type what you ate in English or Roman Urdu — e.g. <i>"2 chicken biryani plates and 1 cup chai"</i>.
Gemini estimates portions + nutrition. Always labeled as an estimate, never a measurement.</p>
<input id="aitext" placeholder="Aaj kya khaya?">
<button class="blue" onclick="aiEstimate()">Estimate with AI</button>
<div id="aires"></div>
</div>

<div class="card">
<h2>📓 Today's diary</h2>
<div id="diary"></div>
<button class="ghost" onclick="clearDiary()">Clear today</button>
</div>

<div class="card">
<h2>🎯 Today vs targets</h2>
<div id="progress"></div>
<label>Water (glasses, 250 ml)</label>
<div class="row"><button class="ghost qadd" onclick="water(1)">+1 🥛</button>
<button class="ghost qadd" onclick="water(-1)">−1</button>
<span id="waterct" style="align-self:center"></span></div>
</div>

<footer>
<b>Honest limits, read me:</b><br>
• <span class="badge recipe">recipe</span> values are documented recipe estimates, not lab measurements —
weigh portions for precision.<br>
• <span class="badge ai">AI estimate</span> items are Gemini guesses; edit grams before adding.<br>
• A photo can't weigh food (NIH NIDDK 2026: photo apps miss ~1/3 of calories) — that's why
we log text-first with explicit grams.<br>
• Your diary &amp; profile stay <b>on this device</b> (browser storage) — nothing is uploaded,
and deploys can't wipe it.<br>
• Study aid, not medical advice. For diabetes, kidney disease, or eating disorders,
talk to a real clinician/dietitian.<br>
• Free forever core. No quiz paywall, no trial traps — the Cal AI playbook we refuse to copy.
</footer>

<script>
const $=id=>document.getElementById(id);
let meal="breakfast";
function setMeal(m,btn){meal=m;document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');}
function today(){return new Date().toISOString().slice(0,10);}
function getP(){try{return JSON.parse(localStorage.getItem('sp_profile'))||{}}catch(e){return{}}}
function getD(){try{return JSON.parse(localStorage.getItem('sp_diary_'+today()))||[]}catch(e){return[]}}
function setD(d){localStorage.setItem('sp_diary_'+today(),JSON.stringify(d));}
function saveProfile(){
 const p={age:+$('age').value||22,sex:$('sex').value,height:+$('height').value||170,
 weight:+$('weight').value||70,activity:$('activity').value,goal:$('goal').value};
 localStorage.setItem('sp_profile',JSON.stringify(p));renderTargets();renderProgress();
}
function calcT(p){
 const bmr=10*p.weight+6.25*p.height-5*p.age+(p.sex==='male'?5:-161);
 const f={sedentary:1.2,light:1.375,moderate:1.55,active:1.725,athlete:1.9}[p.activity]||1.55;
 const adj={lose:-500,maintain:0,gain:300}[p.goal]||0;
 const kcal=Math.max(1200,Math.round(bmr*f+adj));
 const protein=Math.round(1.6*p.weight),fat=Math.round(0.25*kcal/9);
 const carbs=Math.round((kcal-protein*4-fat*9)/4);
 return{kcal,protein,fat,carbs};
}
function renderTargets(){
 const p=getP();if(!p.weight){$('targets').innerHTML='<p class="note">Profile save karo.</p>';return;}
 const t=calcT(p);
 $('targets').innerHTML='<div class="kv"><span>Daily calories</span><b>'+t.kcal+' kcal</b></div>'+
 '<div class="kv"><span>Protein</span><b>'+t.protein+' g</b></div>'+
 '<div class="kv"><span>Carbs</span><b>'+t.carbs+' g</b></div>'+
 '<div class="kv"><span>Fat</span><b>'+t.fat+' g</b></div>';
}
async function searchFoods(){
 const q=$('q').value.trim();if(q.length<2){$('results').innerHTML='';return;}
 const r=await fetch('/sehatplate/api/foods?q='+encodeURIComponent(q));
 const foods=await r.json();
 $('results').innerHTML=foods.map(f=>
 '<div class="food"><div><b>'+f.name+'</b> <span class="badge '+f.src+'">'+(f.src==='usda'?'USDA':'recipe')+'</span><br>'+
 '<small>'+f.kcal+' kcal · P '+f.protein+'g · C '+f.carbs+'g · F '+f.fat+'g /100g'+(f.note?' · '+f.note:'')+'</small></div>'+
 '<div><input type="number" id="g'+f.id+'" value="100" min="1" style="width:64px"><br>'+
 '<button class="qadd" onclick="addFood('+f.id+')">+ add</button></div></div>').join('')
 ||'<p class="note">Nahi mila — AI estimate try karo.</p>';
 window._foods={};foods.forEach(f=>window._foods[f.id]=f);
}
async function addFood(id,pre){
 const f=(window._foods||{})[id];if(!f)return;
 const g=pre&&pre.grams?pre.grams:(+$('g'+id).value||100);
 const s=g/100,d=getD();
 d.push({meal,name:f.name,grams:Math.round(g*10)/10,kcal:Math.round(f.kcal*s*10)/10,
 protein:Math.round(f.protein*s*10)/10,carbs:Math.round(f.carbs*s*10)/10,
 fat:Math.round(f.fat*s*10)/10,src:f.src,ai:!!(pre&&pre.ai)});
 setD(d);renderDiary();renderProgress();
}
async function aiEstimate(){
 const t=$('aitext').value.trim();if(!t)return;
 $('aires').innerHTML='<p class="note">AI soch raha hai…</p>';
 const r=await fetch('/sehatplate/api/estimate',{method:'POST',
 headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
 const j=await r.json();
 if(j.error){$('aires').innerHTML='<p class="warn">'+j.error+'</p>';return;}
 window._ai=j;
 $('aires').innerHTML='<p><span class="badge ai">AI estimate</span> <small class="note">confidence: '
 +j.confidence+(j.note?' — '+j.note:'')+'</small></p>'+
 j.items.map((it,i)=>'<div class="food"><div><b>'+it.name+'</b><br><small>'+it.grams+' g · '
 +it.kcal+' kcal · P '+it.protein+'g C '+it.carbs+'g F '+it.fat+'g</small></div>'+
 '<button class="qadd" onclick="addAI('+i+')">+ add</button></div>').join('')+
 '<button class="blue" onclick="addAllAI()">Add all to diary</button>';
}
function addAI(i){const it=window._ai.items[i];const d=getD();
 d.push({meal,name:it.name+' 🤖',grams:it.grams,kcal:it.kcal,protein:it.protein,carbs:it.carbs,fat:it.fat,src:'ai',ai:true});
 setD(d);renderDiary();renderProgress();}
function addAllAI(){(window._ai.items||[]).forEach((_,i)=>addAI(i));}
function delEntry(i){const d=getD();d.splice(i,1);setD(d);renderDiary();renderProgress();}
function clearDiary(){if(confirm('Aaj ka diary saaf kar dun?')){setD([]);renderDiary();renderProgress();}}
function renderDiary(){
 const d=getD();if(!d.length){$('diary').innerHTML='<p class="note">Abhi khaali — upar se add karo.</p>';return;}
 const meals={breakfast:'Breakfast',lunch:'Lunch',dinner:'Dinner',snack:'Snack'};
 let h='';
 for(const m of ['breakfast','lunch','dinner','snack']){
  const items=d.map((e,i)=>({e,i})).filter(x=>x.e.meal===m);
  if(!items.length)continue;
  h+='<div class="meal">'+meals[m]+'</div>';
  items.forEach(x=>{h+='<div class="entry"><div><b>'+x.e.name+'</b><br><small>'+x.e.grams+' g · '
  +x.e.kcal+' kcal'+(x.e.ai?' · <span class="badge ai">AI</span>':'')+'</small></div>'+
  '<button class="del" onclick="delEntry('+x.i+')">✕</button></div>';});
 }
 $('diary').innerHTML=h;
}
function renderProgress(){
 const p=getP(),d=getD();
 if(!p.weight){$('progress').innerHTML='<p class="note">Pehle profile save karo.</p>';return;}
 const t=calcT(p);
 const sum=k=>d.reduce((a,e)=>a+(+e[k]||0),0);
 const rows=[['Calories',sum('kcal'),t.kcal,'kcal'],['Protein',sum('protein'),t.protein,'g'],
 ['Carbs',sum('carbs'),t.carbs,'g'],['Fat',sum('fat'),t.fat,'g']];
 $('progress').innerHTML=rows.map(r=>{
  const pct=Math.min(100,Math.round(r[1]/r[2]*100)),over=r[1]>r[2];
  return '<div class="kv"><span>'+r[0]+'</span><b>'+Math.round(r[1])+' / '+r[2]+' '+r[3]+'</b></div>'+
  '<div class="bar'+(over?' over':'')+'"><i style="width:'+pct+'%"></i></div>';}).join('');
}
function water(n){const k='sp_water_'+today();let v=+(localStorage.getItem(k)||0)+n;if(v<0)v=0;
 localStorage.setItem(k,v);$('waterct').textContent=v+' glasses';}
(function init(){
 const p=getP();if(p.age){$('age').value=p.age;$('sex').value=p.sex;$('height').value=p.height;
 $('weight').value=p.weight;$('activity').value=p.activity;$('goal').value=p.goal;}
 $('waterct').textContent=(localStorage.getItem('sp_water_'+today())||0)+' glasses';
 renderTargets();renderDiary();renderProgress();
})();
</script>
</body>
</html>
"""
