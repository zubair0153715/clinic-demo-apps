"""Sukoon page — single-file HTML for the free sleep & calm studio.

All interactive state (dhikr totals, sleep diary, wind-down times)
lives in the user's browser (localStorage). Story narration uses the
device's own speech voices; sleep sounds are synthesised live with
the Web Audio API from the filter recipes in engine.SOUND_RECIPES.
"""

SUKOON_HTML = r"""<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sukoon — Free Sleep &amp; Calm Studio | سکون</title>
<style>
body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;max-width:860px;margin:0 auto;padding:16px;line-height:1.6;color:#1e2a32;background:#f4f1ea}
h1{font-size:28px;margin:4px 0}h2{font-size:20px;margin-top:36px;border-bottom:2px solid #b9a06a;padding-bottom:4px}
h3{font-size:16px;margin:12px 0 4px}
.card{background:#fff;border:1px solid #ddd6c4;border-radius:12px;padding:16px;margin:12px 0}
.free{background:#1d5c3f;color:#fff;border-radius:10px;padding:14px;margin:12px 0}
.free b{font-size:17px}
button{background:#1d5c3f;color:#fff;border:0;border-radius:8px;padding:10px 16px;font-size:15px;cursor:pointer;margin:4px 4px 4px 0}
button.alt{background:#fff;color:#1d5c3f;border:1px solid #1d5c3f}
button.stop{background:#8a2f2f}
button:disabled{opacity:.5;cursor:default}
input,select,textarea{font-size:15px;padding:8px;border:1px solid #bbb;border-radius:8px;margin:4px 4px 4px 0;width:100%;max-width:320px}
textarea{max-width:100%;min-height:64px}
label{font-weight:600}
.small{font-size:13px;color:#5a6b76}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid #ddd6c4;padding:8px;text-align:left}
th{background:#efe9d8}
#pacer{width:180px;height:180px;border-radius:50%;background:#cfe3d8;margin:18px auto;display:flex;align-items:center;justify-content:center;text-align:center;font-size:18px;font-weight:700;transition:transform 1s ease-in-out,background 1s ease-in-out}
#pacer.big{transform:scale(1.25);background:#9ec7ae}
#pacer.small{transform:scale(.8);background:#e5d9b8}
#dhikrBtn{width:100%;padding:28px;font-size:22px;border-radius:14px}
#dhikrCount{font-size:44px;font-weight:800;text-align:center;margin:8px 0}
.storytext{white-space:pre-wrap;background:#fdfbf5;border:1px solid #e5ddc4;border-radius:10px;padding:14px;margin-top:10px;font-size:16px}
.badge{display:inline-block;background:#efe9d8;border-radius:6px;padding:2px 8px;font-size:12px;margin-right:4px}
.err{color:#8a2f2f;font-weight:600}.ok{color:#1d5c3f;font-weight:600}
ul{padding-left:20px}
</style>
</head>
<body>
<h1>🌙 Sukoon — سکون</h1>
<p><b>Free sleep &amp; calm studio.</b> Saans, neend ki kahaniyan, neend ki awazein, dhikr aur wind-down planner — sab kuch free, sab kuch unlocked.</p>
<div class="free"><b>Free forever — no account, no card, no trial, no auto-renew.</b><br>
Calm Premium $16.99/month ya $79.99/year leta hai (Feb 2026 se), aur free tier me sirf ek breathing exercise aur ek kahani milti hai. Sukoon me sab kuch khula hai — kyun ke yahan charge karne ko kuch hai hi nahi, to bhool kar charge hone ka sawaal hi nahi.</div>
<p class="small">AI status: <span id="aiStatus">check ho raha hai…</span></p>

<h2>Calm vs Sukoon — seedhi baat</h2>
<table>
<tr><th></th><th>Calm Premium</th><th>Sukoon</th></tr>
<tr><td>Price</td><td>$79.99/year (2026)</td><td><b>Free, hamesha</b></td></tr>
<tr><td>Sleep Stories</td><td>100+ — mostly paywalled</td><td>3 original + AI generator, free</td></tr>
<tr><td>Breathing patterns</td><td>1 free (Relax)</td><td>4 patterns, free</td></tr>
<tr><td>Sleep sounds</td><td>Paywalled library</td><td>4 synthesised sounds, free</td></tr>
<tr><td>Urdu / Roman-Urdu</td><td>Nahi</td><td><b>EN + Roman-Urdu + Urdu</b></td></tr>
<tr><td>Dhikr / Isha-aware wind-down</td><td>Nahi</td><td><b>Haan</b></td></tr>
<tr><td>Trustpilot</td><td>1.3/5 — billing complaints</td><td>No billing, no complaints possible</td></tr>
</table>

<h2>🫁 Saans — Guided Breathing</h2>
<div class="card">
<label>Pattern:</label>
<select id="breathPattern">
<option value="478">4-7-8 — neend ke liye</option>
<option value="box">Box 4-4-4-4 — tension kam</option>
<option value="coherent">Coherent 5-5 — dil sakin</option>
<option value="446">4-4-6 — lambi exhale</option>
</select>
<label>Cycles:</label>
<select id="breathCycles"><option>2</option><option selected>4</option><option>6</option><option>8</option></select>
<button id="breathStart" onclick="startBreathing()">Shuru karein</button>
<button class="stop" id="breathStop" onclick="stopBreathing()" disabled>Rok dein</button>
<p id="breathInfo" class="small"></p>
<div id="pacer">Taiyar hain?<br><span class="small">Shuru dabayein</span></div>
<p id="breathPhase" style="text-align:center;font-weight:700"></p>
</div>

<h2>📖 Neend ki Kahaniyan — Sleep Stories</h2>
<div class="card">
<p class="small">Teeno kahaniyan Sukoon ke liye original likhi gayi hain — kisi kitab, film ya mashhoor narration ki copy nahi. Device ki awaz se sunayein (Web Speech API), ya parh lein.</p>
<div id="storyList">Kahaniyan load ho rahi hain…</div>
<div id="storyView" style="display:none">
<h3 id="storyTitle"></h3>
<p>
<button onclick="setLang('en')">English</button>
<button onclick="setLang('roman')">Roman-Urdu</button>
<button onclick="setLang('ur')">Urdu</button>
<button class="alt" id="readBtn" onclick="readAloud()">🔊 Sunayein</button>
<button class="alt" onclick="stopReading()">⏹ Rokein</button>
</p>
<p class="small" id="storyMeta"></p>
<div class="storytext" id="storyText"></div>
<p class="small">Narration aapke device ki installed awazon se hoti hai — Urdu voice har phone me nahi hoti; agar awaz na mile to text phir bhi poora dikhaya jata hai.</p>
</div>
<h3>✨ AI kahani banayein (original, on demand)</h3>
<label>Theme:</label>
<select id="aiTheme">
<option value="river">Darya</option><option value="train">Train</option><option value="garden">Bagh</option>
<option value="desert">Sehra</option><option value="rain">Baarish</option><option value="mountains">Pahar</option>
<option value="sea">Samandar</option><option value="village">Gaon</option><option value="forest">Jungle</option>
<option value="stars">Sitare</option>
</select>
<label>Language:</label>
<select id="aiLang"><option value="en">English</option><option value="roman">Roman-Urdu</option><option value="ur">Urdu</option></select>
<button onclick="aiStory()">AI kahani likhein</button>
<p id="aiStoryOut" class="small"></p>
<div class="storytext" id="aiStoryText" style="display:none"></div>
</div>

<h2>🎧 Neend ki Awazein — Sleep Sounds</h2>
<div class="card">
<p class="small">Ye awazein koi recording nahi — browser me live synthesise hoti hain (filtered noise, Web Audio API). Recipe page par dikhaya gaya hai, aur koi file download nahi hoti.</p>
<div id="soundBtns"></div>
<label>Sleep timer (auto band):</label>
<select id="soundTimer"><option value="0">No timer</option><option value="15">15 min</option><option value="30" selected>30 min</option><option value="45">45 min</option><option value="60">60 min</option><option value="90">90 min</option></select>
<button class="stop" onclick="stopSound()">Awaz band karein</button>
<p id="soundInfo" class="small"></p>
</div>

<h2>📿 Dhikr — Tasbih Counter</h2>
<div class="card">
<div id="dhikrChips"></div>
<p id="dhikrArabic" style="font-size:26px;text-align:center"></p>
<p class="small" style="text-align:center" id="dhikrMeaning"></p>
<button id="dhikrBtn" onclick="tapDhikr()">🤲 Tap karein</button>
<div id="dhikrCount">0</div>
<p style="text-align:center"><span id="dhikrRounds"></span> &nbsp; <button class="alt" onclick="resetDhikr()">Reset</button></p>
<p class="small" style="text-align:center" id="dhikrTotal"></p>
</div>

<h2>🌆 Wind-Down Planner — Isha se bedtime tak</h2>
<div class="card">
<p class="small">Prayer times kisi API se nahi liye jate — aap apni Isha ka waqt khud likhte hain, aur app use kabhi guess nahi karta. Planner dhikr → saans → kahani → awaz ka schedule banata hai jo bedtime par khatam hota hai.</p>
<label>Isha time:</label><input id="ishaTime" type="text" value="21:00" placeholder="21:00">
<label>Bedtime:</label><input id="bedTime" type="text" value="23:00" placeholder="23:00">
<button onclick="planWindDown()">Mera plan banayein</button>
<p id="windOut"></p>
<div id="windPlan"></div>
<h3>✨ AI wind-down plan (aaj raat ke liye)</h3>
<label>Wake time:</label><input id="aiWake" type="text" value="06:30" placeholder="06:30">
<label>Stress (1–5):</label><input id="aiStress" type="number" min="1" max="5" value="3">
<label>Aaj ki fikar (optional — "park it till tomorrow"):</label>
<textarea id="aiWorry" placeholder="Masalan: kal ki presentation ki fikar…"></textarea>
<button onclick="aiPlan()">AI plan banayein</button>
<p id="aiPlanOut" class="small"></p>
<div class="storytext" id="aiPlanText" style="display:none"></div>
</div>

<h2>😴 Sleep Diary</h2>
<div class="card">
<p class="small">Aapki diary sirf aapke browser me rehti hai (localStorage) — server par kuch save nahi hota.</p>
<label>Bedtime:</label><input id="dBed" type="text" value="23:00">
<label>Wake time:</label><input id="dWake" type="text" value="06:30">
<label>Quality (1–5):</label><input id="dQuality" type="number" min="1" max="5" value="4">
<button onclick="saveDiary()">Aaj ki neend save karein</button>
<p id="diaryOut"></p>
<div id="diaryList"></div>
<p id="diaryAvg" class="ok"></p>
</div>

<h2>Honest limits</h2>
<div class="card">
<ul>
<li>Sukoon neend aur sukoon me <b>madad</b> karta hai — ye kisi bimari, insomnia ya anxiety ka <b>ilaaj nahi</b>. Agar neend hafton se kharab hai ya anxiety rozana zindagi par asar daal rahi hai, to doctor se milein.</li>
<li>Kahani ki awaz aapke device ki installed voices par depend karti hai; Urdu voice har phone/browser me nahi hoti.</li>
<li>Sleep sounds live synthesis hain (filtered noise), asli baarish ya samandar ki recording nahi — honest approximation.</li>
<li>Prayer times fetch nahi hote; Isha ka waqt aap khud dete hain.</li>
<li>AI kahani aur AI plan ke liye server par GEMINI_API_KEY chahiye; baghair uske saans, kahaniyan, awazein, dhikr, planner aur diary poore kaam karte hain.</li>
<li>AI ki har kahani "AI-written" label ke saath aati hai, aur har ek ki length aur ending check ki jati hai.</li>
</ul>
<p class="small">Sukoon is an original clean-room build. Not affiliated with Calm, Headspace or any other app. Prices quoted from public sources, Oct 2026.</p>
</div>

<script>
let breathTimer=null, breathIdx=0, breathSched=null;
let curStory=null, curLang='en', curText='';
let audioCtx=null, audioNodes=null, soundTimerH=null;
let dhikrKey='subhanallah', dhikrCount=0;

async function jget(u){const r=await fetch(u);return r.json();}
async function jpost(u,fd){const r=await fetch(u,{method:'POST',body:fd});return r.json();}

fetch('/sukoon/api/ai-status').then(r=>r.json()).then(d=>{
  document.getElementById('aiStatus').textContent = d.ai_available ? 'AI ON (Gemini) — AI kahani aur AI plan available hain.' : 'AI OFF — saans, kahaniyan, awazein, dhikr, planner aur diary phir bhi poore kaam karte hain.';
});

// ---------- breathing ----------
async function startBreathing(){
  const p=document.getElementById('breathPattern').value;
  const c=parseInt(document.getElementById('breathCycles').value,10);
  const d=await jget(`/sukoon/api/breathing?pattern=${p}&cycles=${c}`);
  if(!d.ok){document.getElementById('breathInfo').textContent=d.error;return;}
  breathSched=d.schedule; breathIdx=0;
  document.getElementById('breathInfo').textContent =
    `${d.name}: ${d.cycle_seconds}s per cycle, ${d.total_seconds}s total (${d.cycles} cycles), ~${d.breaths_per_minute} saans/min.`;
  document.getElementById('breathStart').disabled=true;
  document.getElementById('breathStop').disabled=false;
  runPhase();
}
function runPhase(){
  if(!breathSched||breathIdx>=breathSched.length){stopBreathing(true);return;}
  const s=breathSched[breathIdx];
  const pacer=document.getElementById('pacer');
  pacer.textContent=s.label+' — '+s.seconds+'s';
  pacer.className = s.phase==='inhale' ? 'big' : (s.phase==='exhale' ? 'small' : '');
  document.getElementById('breathPhase').textContent =
    `Cycle ${s.cycle}/${breathSched[breathSched.length-1].cycle} — ${s.label} (${s.seconds} second)`;
  breathTimer=setTimeout(()=>{breathIdx++;runPhase();}, s.seconds*1000);
}
function stopBreathing(done){
  if(breathTimer)clearTimeout(breathTimer);
  breathSched=null;
  document.getElementById('breathStart').disabled=false;
  document.getElementById('breathStop').disabled=true;
  const pacer=document.getElementById('pacer');
  pacer.className=''; pacer.textContent=done?'Mubarak — session poora hua. 🌙':'Ruk gaya.';
  if(done)document.getElementById('breathPhase').textContent='Session mukammal. Aaram se baithein, ek gehri saans lein.';
}

// ---------- stories ----------
async function loadStories(){
  const d=await jget('/sukoon/api/stories');
  const el=document.getElementById('storyList');
  if(!d.valid){el.innerHTML='<span class="err">Story check fail: '+d.errors.join('; ')+'</span>';return;}
  el.innerHTML=d.stories.map(s=>
    `<div class="card"><b>${s.title_en}</b> <span class="badge">${s.theme}</span><br>
     <span class="small">${s.title_roman} · ${s.title_ur}</span><br>
     <span class="small">EN ${s.words_en} alfaz (~${s.minutes_en} min) · Roman ${s.words_roman} (~${s.minutes_roman} min) · Urdu ${s.words_ur} (~${s.minutes_ur} min)</span><br>
     <button onclick="openStory('${s.id}')">Parhein / Sunain</button></div>`).join('');
}
async function openStory(id){
  const d=await jget(`/sukoon/api/story/${id}?lang=${curLang}`);
  if(!d.ok)return;
  curStory=id; curText=d.text;
  document.getElementById('storyView').style.display='block';
  document.getElementById('storyTitle').textContent=d.title;
  document.getElementById('storyText').textContent=d.text;
  document.getElementById('storyMeta').textContent=`${d.words} alfaz · ~${d.minutes} min · original story, AI nahi`;
  document.getElementById('storyView').scrollIntoView();
}
async function setLang(l){
  curLang=l;
  if(curStory)openStory(curStory);
}
function readAloud(){
  stopReading();
  if(!('speechSynthesis' in window)){alert('Is browser me speech nahi hai.');return;}
  const u=new SpeechSynthesisUtterance(curText);
  u.lang = curLang==='ur' ? 'ur-PK' : 'en-US';
  u.rate = 0.85; u.pitch = 0.9;
  speechSynthesis.speak(u);
}
function stopReading(){if('speechSynthesis' in window)speechSynthesis.cancel();}
async function aiStory(){
  const fd=new FormData();
  fd.append('theme',document.getElementById('aiTheme').value);
  fd.append('language',document.getElementById('aiLang').value);
  document.getElementById('aiStoryOut').textContent='AI kahani likh raha hai…';
  const d=await jpost('/sukoon/api/story-ai',fd);
  if(!d.ok){document.getElementById('aiStoryOut').textContent=d.error;return;}
  document.getElementById('aiStoryOut').textContent=`AI-written original story · ${d.result.words} alfaz · ~${d.result.minutes} min · theme: ${d.result.theme}`;
  const t=document.getElementById('aiStoryText');
  t.style.display='block'; t.textContent=d.result.story;
}

// ---------- sounds ----------
async function loadSounds(){
  const d=await jget('/sukoon/api/sounds');
  document.getElementById('soundBtns').innerHTML=Object.entries(d.sounds).map(([k,v])=>
    `<button onclick="playSound('${k}')">${v.label}</button>`).join('')+
    `<p class="small">Recipes: `+Object.entries(d.sounds).map(([k,v])=>`${v.label}: ${v.filter} ${v.freq}Hz, gain ${v.gain}`).join(' · ')+`</p>`;
}
function noiseBuffer(ctx){
  const len=ctx.sampleRate*2, buf=ctx.createBuffer(1,len,ctx.sampleRate), ch=buf.getChannelData(0);
  let last=0;
  for(let i=0;i<len;i++){const w=Math.random()*2-1; last=(last+0.02*w)/1.02; ch[i]=last*3.2;} // brown-ish base
  return buf;
}
function playSound(key){
  stopSound();
  const recipes={rain:{freq:1200,type:'bandpass',gain:.35},brown:{freq:400,type:'lowpass',gain:.5},
    waves:{freq:600,type:'lowpass',gain:.4,lfo:.1},fan:{freq:300,type:'lowpass',gain:.3,lfo:11}};
  const r=recipes[key]; if(!r)return;
  audioCtx=audioCtx||new (window.AudioContext||window.webkitAudioContext)();
  const ctx=audioCtx, src=ctx.createBufferSource();
  src.buffer=noiseBuffer(ctx); src.loop=true;
  const filt=ctx.createBiquadFilter(); filt.type=r.type; filt.frequency.value=r.freq; filt.Q.value=.7;
  const g=ctx.createGain(); g.gain.value=0;
  src.connect(filt); filt.connect(g); g.connect(ctx.destination);
  src.start();
  g.gain.linearRampToValueAtTime(r.gain, ctx.currentTime+2);
  if(r.lfo){
    const osc=ctx.createOscillator(), og=ctx.createGain();
    osc.frequency.value=r.lfo; og.gain.value=r.gain*.25;
    osc.connect(og); og.connect(g.gain); osc.start();
    audioNodes={src,osc,g};
  } else audioNodes={src,g};
  const mins=parseInt(document.getElementById('soundTimer').value,10);
  document.getElementById('soundInfo').textContent='Chal rahi hai: '+key+(mins?` — ${mins} min baad auto band.`:' — no timer.');
  if(mins>0){soundTimerH=setTimeout(()=>{stopSound();document.getElementById('soundInfo').textContent='Timer khatam — awaz band. Shubh raat. 🌙';}, mins*60000);}
}
function stopSound(){
  if(soundTimerH){clearTimeout(soundTimerH);soundTimerH=null;}
  if(audioNodes){try{audioNodes.src.stop();}catch(e){} try{if(audioNodes.osc)audioNodes.osc.stop();}catch(e){} audioNodes=null;}
  if(audioCtx){audioCtx.close().catch(()=>{}); audioCtx=null;}
}

// ---------- dhikr ----------
const DHIKR=[
 ['subhanallah','SubhanAllah','سُبْحَانَ اللَّهِ','Allah paak hai',33],
 ['alhamdulillah','Alhamdulillah','الْحَمْدُ لِلَّهِ','Tamam tareef Allah ke liye',33],
 ['allahu_akbar','Allahu Akbar','اللَّهُ أَكْبَرُ','Allah sab se bara hai',34],
 ['la_ilaha','La ilaha illallah','لَا إِلَهَ إِلَّا اللَّهُ','Allah ke siwa koi mabood nahi',100],
 ['astaghfirullah','Astaghfirullah','أَسْتَغْفِرُ اللَّهَ','Main Allah se maghfirat chahta hoon',100],
 ['durood','Durood Sharif','اللَّهُمَّ صَلِّ عَلَى مُحَمَّدٍ','Aye Allah, Muhammad ﷺ par rehmat bhej',100],
];
function renderDhikr(){
  document.getElementById('dhikrChips').innerHTML=DHIKR.map(d=>
    `<button class="${d[0]===dhikrKey?'':'alt'}" onclick="pickDhikr('${d[0]}')">${d[1]} (${d[4]})</button>`).join('');
  const d=DHIKR.find(x=>x[0]===dhikrKey);
  document.getElementById('dhikrArabic').textContent=d[2];
  document.getElementById('dhikrMeaning').textContent=d[1]+' — '+d[3]+' · target '+d[4];
  document.getElementById('dhikrCount').textContent=dhikrCount;
  const rounds=Math.floor(dhikrCount/d[4]), rem=dhikrCount%d[4];
  document.getElementById('dhikrRounds').textContent =
    rounds>0?`${rounds} round mukammal · ${rem}/${d[4]}`:`${rem}/${d[4]} — ${d[4]-rem} baaki, 1 round ke liye`;
  const totals=JSON.parse(localStorage.getItem('sukoon_dhikr_totals')||'{}');
  const today=new Date().toISOString().slice(0,10);
  document.getElementById('dhikrTotal').textContent='Aaj total: '+(totals[today]||0)+' taps (is device par save)';
}
function pickDhikr(k){dhikrKey=k;dhikrCount=0;renderDhikr();}
async function tapDhikr(){
  dhikrCount++;
  const fd=new FormData(); fd.append('key',dhikrKey); fd.append('count',dhikrCount);
  await jpost('/sukoon/api/dhikr',fd); // server verifies the round math
  const totals=JSON.parse(localStorage.getItem('sukoon_dhikr_totals')||'{}');
  const today=new Date().toISOString().slice(0,10);
  totals[today]=(totals[today]||0)+1;
  localStorage.setItem('sukoon_dhikr_totals',JSON.stringify(totals));
  renderDhikr();
}
function resetDhikr(){dhikrCount=0;renderDhikr();}

// ---------- wind-down ----------
async function planWindDown(){
  const fd=new FormData();
  fd.append('isha',document.getElementById('ishaTime').value);
  fd.append('bedtime',document.getElementById('bedTime').value);
  const d=await jpost('/sukoon/api/wind-down',fd);
  if(!d.ok){document.getElementById('windOut').textContent=d.error;return;}
  const names={dhikr:'📿 Dhikr',breathing:'🫁 Saans',story:'📖 Kahani',sounds:'🎧 Neend ki awazein'};
  document.getElementById('windOut').textContent=`Window: ${d.window_minutes} min (Isha ${d.isha} → bedtime ${d.bedtime}).`;
  document.getElementById('windPlan').innerHTML='<table><tr><th>Block</th><th>Waqt</th><th>Minutes</th></tr>'+
    d.blocks.map(b=>`<tr><td>${names[b.block]||b.block}</td><td>${b.start} – ${b.end}</td><td>${b.minutes}</td></tr>`).join('')+'</table>';
}
async function aiPlan(){
  const fd=new FormData();
  fd.append('bedtime',document.getElementById('bedTime').value);
  fd.append('wake',document.getElementById('aiWake').value);
  fd.append('stress',document.getElementById('aiStress').value);
  fd.append('worry',document.getElementById('aiWorry').value);
  fd.append('language',document.getElementById('aiLang').value);
  document.getElementById('aiPlanOut').textContent='AI plan bana raha hai…';
  const d=await jpost('/sukoon/api/wind-down-ai',fd);
  if(!d.ok){document.getElementById('aiPlanOut').textContent=d.error;return;}
  document.getElementById('aiPlanOut').textContent=`AI-written plan · ${d.result.words} alfaz · bedtime ${d.result.bedtime}, wake ${d.result.wake}, stress ${d.result.stress}/5 — general sleep hygiene, medical advice nahi.`;
  const t=document.getElementById('aiPlanText');
  t.style.display='block'; t.textContent=d.result.plan;
}

// ---------- diary ----------
function diaryEntries(){return JSON.parse(localStorage.getItem('sukoon_diary')||'[]');}
async function saveDiary(){
  const fd=new FormData();
  fd.append('bed',document.getElementById('dBed').value);
  fd.append('wake',document.getElementById('dWake').value);
  const d=await jpost('/sukoon/api/sleep',fd);
  if(!d.ok){document.getElementById('diaryOut').textContent=d.error;return;}
  const entries=diaryEntries();
  entries.push({date:new Date().toISOString().slice(0,10),bed:document.getElementById('dBed').value,
    wake:document.getElementById('dWake').value,minutes:d.minutes,
    quality:parseInt(document.getElementById('dQuality').value,10)});
  localStorage.setItem('sukoon_diary',JSON.stringify(entries.slice(-14)));
  document.getElementById('diaryOut').textContent='Save ho gaya: '+d.label+'.';
  renderDiary();
}
async function renderDiary(){
  const entries=diaryEntries();
  document.getElementById('diaryList').innerHTML=entries.length?
    '<table><tr><th>Date</th><th>Bed → Wake</th><th>Neend</th><th>Quality</th></tr>'+
    entries.slice().reverse().map(e=>`<tr><td>${e.date}</td><td>${e.bed} → ${e.wake}</td><td>${Math.floor(e.minutes/60)}h ${String(e.minutes%60).padStart(2,'0')}m</td><td>${e.quality}/5</td></tr>`).join('')+'</table>'
    :'Abhi koi record nahi — aaj ki neend save karein.';
  if(entries.length){
    const fd=new FormData();
    fd.append('minutes',entries.slice(-7).map(e=>e.minutes).join(','));
    const d=await jpost('/sukoon/api/sleep-average',fd);
    if(d.ok)document.getElementById('diaryAvg').textContent=`Pichle ${d.nights} raat ki average: ${d.average_label}.`;
  }
}

loadStories(); loadSounds(); renderDhikr(); renderDiary();
</script>
</body>
</html>
"""

# Keep the HTML importable under both package layouts.
__all__ = ["SUKOON_HTML"]
