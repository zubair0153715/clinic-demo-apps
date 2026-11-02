"""Awaaz page — free read-aloud reader UI (original design).

The speaking runs entirely in the browser (Web Speech API): no server
cost, no account, no meter, no quota. The server only analyses the
text (sentences, language, stats) and offers one optional AI summary.
"""
AWAAZ_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Awaaz — Free Read-Aloud Reader (Urdu, Roman-Urdu, English)</title>
<style>
body{font-family:system-ui,sans-serif;max-width:820px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
textarea{width:100%;min-height:130px;padding:10px;margin:6px 0;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-size:15px;line-height:1.5}
select,input[type=range]{margin:4px 0}
button{padding:10px 18px;border:0;border-radius:6px;background:#14532d;color:#fff;font-size:16px;cursor:pointer;margin:2px}
button.sec{background:#eee;color:#111} button:disabled{background:#bbb;cursor:not-allowed}
button.big{font-size:18px;padding:12px 26px}
.card{border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
.small{color:#555;font-size:13px} .warn{background:#f0fdf4;border:1px solid #86c79a;border-radius:8px;padding:12px;margin:14px 0}
#reader{font-size:19px;line-height:1.9;white-space:pre-wrap}
#reader .sent{cursor:pointer;border-radius:4px;padding:1px 2px}
#reader .sent:hover{background:#eef6ee}
#reader .sent.cur{background:#dcfce7}
#reader .w{border-radius:3px;padding:0 1px}
#reader .w.on{background:#facc15}
#reader .w.done{color:#555}
#stats b{margin-right:14px}
#prog{height:8px;background:#eee;border-radius:4px;overflow:hidden;margin:8px 0}
#bar{height:100%;width:0;background:#14532d}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.row label{font-size:14px;color:#333}
.lib{cursor:pointer;color:#14532d} .lib:hover{text-decoration:underline}
#summary{white-space:pre-wrap;line-height:1.6}
.err{color:#b91c1c}
</style></head><body>
<h1>Awaaz — آواز</h1>
<p class="sub">Paste any text or upload a file — hear it read aloud, word by word.
Free, unlimited, no account, no card, no word limit. Urdu, Roman-Urdu and English.</p>
<div class="warn"><b>Honest limits, stated plainly:</b> the voice comes from
your own device/browser (Chrome/Android system voices) — quality depends on
what your device has installed, and Urdu voices may not exist on every
phone. Word highlighting works best in Chrome. There is <b>no audio file
download</b> in v1 (browser speech cannot export audio). Scanned-image PDFs
need OCR — not in v1, use a PDF with a text layer. AI summary needs the
server Gemini key; when its quota is out the button says so and the reader
keeps working at 100%.</div>

<div class="card">
<textarea id="src" placeholder="Yahan text paste karein… / Paste text here…"></textarea>
<div class="row">
<button class="sec" onclick="loadSample('en')">Sample: English</button>
<button class="sec" onclick="loadSample('ur')">Sample: اردو</button>
<button class="sec" onclick="loadSample('roman')">Sample: Roman-Urdu</button>
<label>.txt <input type="file" id="txtfile" accept=".txt,.md" onchange="loadTxt(this)"></label>
<label>PDF <input type="file" id="pdffile" accept=".pdf" onchange="loadPdf(this)"></label>
</div>
<div class="row" style="margin-top:8px">
<button class="big" onclick="analyze()">▶ Load &amp; analyse</button>
<span id="loadmsg" class="small"></span>
</div>
</div>

<div id="stats" class="card" style="display:none">
<div id="statsline"></div>
<div id="prog"><div id="bar"></div></div>
<div class="row">
<button class="big" id="playbtn" onclick="togglePlay()">▶ Play</button>
<button onclick="stopAll()">■ Stop</button>
<button class="sec" onclick="jumpSentence(-1)">◀ Sentence</button>
<button class="sec" onclick="jumpSentence(1)">Sentence ▶</button>
</div>
<div class="row" style="margin-top:8px">
<label>Speed <input type="range" id="rate" min="0.5" max="3" step="0.25" value="1" oninput="rateChanged()"> <b id="rateval">1x</b></label>
<label>Pitch <input type="range" id="pitch" min="0.5" max="1.5" step="0.1" value="1" oninput="pitchChanged()"> <b id="pitchval">1</b></label>
<label>Voice <select id="voice" style="max-width:280px"></select></label>
<label>Sleep <select id="sleep" onchange="sleepChanged()"><option value="0">off</option><option value="5">5 min</option><option value="10">10 min</option><option value="15">15 min</option><option value="30">30 min</option></select></label>
<span id="sleepmsg" class="small"></span>
</div>
<div class="row" style="margin-top:8px">
<button class="sec" onclick="saveToLibrary()">💾 Save to library</button>
<button class="sec" id="sumbtn" onclick="summarize()">✦ AI summary</button>
<span id="sumstat" class="small"></span>
</div>
<div id="summary" style="margin-top:10px"></div>
</div>

<div class="card"><div id="reader" dir="auto">No document loaded yet. Paste text above, or try a sample.</div></div>

<div class="card"><b>My library</b> <span class="small">(saved in your browser only)</span>
<div id="library" class="small">Empty — save a document to keep it here.</div></div>

<script>
const SAMPLES = {
en: "Larkana is a historic city in Sindh, Pakistan. Every morning, thousands of pharmacy students walk to their university, carrying books on medicines, doses and diseases. Awaaz reads any text aloud — free, unlimited, and without an account. Paste a chapter, upload a PDF, press play, and listen while you walk. The current word lights up as it is spoken, so you always know exactly where you are.",
ur: "لرکانہ سندھ کا ایک تاریخی شہر ہے۔ یہاں کی یونیورسٹی میں ہزاروں طلبہ پڑھتے ہیں۔ دوا ساز طالب علم روزانہ نئی دوائیں سیکھتے ہیں۔ آواز کوئی بھی متن بلند آواز سے پڑھ کر سناتی ہے — مفت، بغیر اکاؤنٹ، بغیر کسی حد کے۔",
roman: "Awaaz aik muft reader hai. Is mein aap koi bhi text paste kar ke sun sakte hain. Urdu, Roman-Urdu aur English — teeno zubanein chalti hain. Jo lafz bola ja raha ho, woh screen par roshan ho jata hai, taake aap ko hamesha pata ho ke aap kahan hain."};
let doc = null, cur = 0, playing = false, utter = null, boundarySeen = false;
let sleepTimer = null, sleepEnd = null, voices = [];

function $(id){ return document.getElementById(id); }
function esc(s){ return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

function loadSample(k){ $("src").value = SAMPLES[k]; $("loadmsg").textContent = ""; }
function loadTxt(inp){
  const f = inp.files[0]; if(!f) return;
  const r = new FileReader();
  r.onload = () => { $("src").value = r.result; $("loadmsg").textContent = "Loaded " + f.name; };
  r.readAsText(f);
}
function loadPdf(inp){
  const f = inp.files[0]; if(!f) return;
  $("loadmsg").textContent = "PDF parh raha hoon…";
  const s = document.createElement("script");
  s.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js";
  s.onload = async () => {
    try{
      pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
      const buf = await f.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({data: buf}).promise;
      let out = [];
      for(let p = 1; p <= pdf.numPages; p++){
        const page = await pdf.getPage(p);
        const tc = await page.getTextContent();
        out.push(tc.items.map(it => it.str).join(" "));
      }
      $("src").value = out.join("\\n\\n");
      $("loadmsg").textContent = "PDF loaded: " + pdf.numPages + " pages.";
    }catch(e){ $("loadmsg").textContent = "PDF nahi parh saka: " + e.message + " — text paste kar lein."; }
  };
  s.onerror = () => { $("loadmsg").textContent = "PDF library load nahi hui (internet check karein) — text paste kar lein."; };
  document.head.appendChild(s);
}

async function analyze(){
  const text = $("src").value;
  stopAll();
  $("loadmsg").textContent = "Analysing…";
  const fd = new FormData(); fd.append("text", text);
  const r = await fetch("/awaaz/api/analyze", {method:"POST", body: fd});
  const d = await r.json();
  if(!d.ok){ $("loadmsg").innerHTML = '<span class="err">' + esc(d.error) + "</span>"; return; }
  doc = d; cur = 0;
  renderReader();
  const mins = (d.words / (180 * parseFloat($("rate").value))).toFixed(1);
  $("statsline").innerHTML = "<b>" + d.words.toLocaleString() + " words</b><b>" + d.sentence_count +
    " sentences</b><b>~" + mins + " min at current speed</b><b>Language: " +
    ({en:"English", ur:"Urdu", roman:"Roman-Urdu"})[d.language] + "</b>" +
    (d.flesch !== null ? "<b>Flesch " + d.flesch + "</b>" : "") +
    (d.headings.length ? "<b>" + d.headings.length + " headings</b>" : "");
  $("stats").style.display = "block";
  $("loadmsg").textContent = "Ready — press Play.";
  $("playbtn").textContent = "▶ Play";
  pickVoice();
  updateBar();
}

function renderReader(){
  let html = "";
  doc.sentences.forEach((s, i) => {
    html += '<span class="sent" data-i="' + i + '" onclick="startAt(' + i + ')">';
    let last = 0;
    const re = /\\S+/g; let m;
    while((m = re.exec(s.text)) !== null){
      if(m.index > last) html += esc(s.text.slice(last, m.index));
      html += '<span class="w" data-s="' + i + '" data-a="' + m.index + '" data-b="' + (m.index + m[0].length) + '">' + esc(m[0]) + "</span>";
      last = m.index + m[0].length;
    }
    if(last < s.text.length) html += esc(s.text.slice(last));
    html += "</span> ";
  });
  $("reader").innerHTML = html;
}

function pickVoice(){
  if(!doc) return;
  const want = doc.language === "ur" ? "ur" : "en";
  const list = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith(want));
  const sel = $("voice");
  if(list.length && !sel.value){
    const pref = list.find(v => /pakistan|india/i.test(v.lang + " " + v.name)) || list[0];
    sel.value = pref.name;
  }
}
function fillVoices(){
  voices = speechSynthesis.getVoices();
  const sel = $("voice");
  const cur_val = sel.value;
  sel.innerHTML = "";
  const groups = {};
  voices.forEach(v => { const g = (v.lang || "?").slice(0,2); (groups[g] = groups[g] || []).push(v); });
  Object.keys(groups).sort().forEach(g => {
    const og = document.createElement("optgroup"); og.label = g;
    groups[g].forEach(v => { const o = document.createElement("option"); o.value = v.name; o.textContent = v.name + " (" + v.lang + ")"; og.appendChild(o); });
    sel.appendChild(og);
  });
  if(cur_val) sel.value = cur_val;
  pickVoice();
}
if("speechSynthesis" in window){
  fillVoices();
  speechSynthesis.onvoiceschanged = fillVoices;
} else {
  $("reader").textContent = "Is browser mein speech nahi hai — Chrome ya Edge istemal karein.";
}

function rateChanged(){ $("rateval").textContent = $("rate").value + "x"; if(doc) analyze_stats_only(); }
function pitchChanged(){ $("pitchval").textContent = $("pitch").value; }
function analyze_stats_only(){
  const mins = (doc.words / (180 * parseFloat($("rate").value))).toFixed(1);
  $("statsline").innerHTML = "<b>" + doc.words.toLocaleString() + " words</b><b>" + doc.sentence_count +
    " sentences</b><b>~" + mins + " min at current speed</b><b>Language: " +
    ({en:"English", ur:"Urdu", roman:"Roman-Urdu"})[doc.language] + "</b>" +
    (doc.flesch !== null ? "<b>Flesch " + doc.flesch + "</b>" : "") +
    (doc.headings.length ? "<b>" + doc.headings.length + " headings</b>" : "");
}
function sleepChanged(){
  const m = parseInt($("sleep").value, 10);
  clearTimeout(sleepTimer); sleepTimer = null; sleepEnd = null;
  if(m > 0){ sleepEnd = Date.now() + m * 60000; sleepTimer = setTimeout(() => { stopAll(); $("sleepmsg").textContent = "Sleep timer: stopped."; }, m * 60000); $("sleepmsg").textContent = "Stops in " + m + " min."; }
  else $("sleepmsg").textContent = "";
}
function markSentence(i){
  document.querySelectorAll("#reader .sent").forEach(el => el.classList.toggle("cur", parseInt(el.dataset.i, 10) === i));
  document.querySelectorAll("#reader .w.on").forEach(el => el.classList.remove("on"));
}
function markWord(sentIdx, charIdx){
  document.querySelectorAll('#reader .w[data-s="' + sentIdx + '"]').forEach(el => {
    const a = parseInt(el.dataset.a, 10), b = parseInt(el.dataset.b, 10);
    el.classList.toggle("on", charIdx >= a && charIdx < b);
    el.classList.toggle("done", charIdx >= b);
  });
}
function updateBar(){
  if(!doc) return;
  let done = 0;
  for(let i = 0; i < cur; i++) done += doc.sentences[i].text.split(/\\s+/).filter(Boolean).length;
  $("bar").style.width = Math.min(100, 100 * done / Math.max(1, doc.words)) + "%";
}
function speakSentence(i){
  if(!playing || !doc || i >= doc.sentences.length){ playing = false; $("playbtn").textContent = "▶ Play"; return; }
  cur = i; markSentence(i); updateBar();
  const u = new SpeechSynthesisUtterance(doc.sentences[i].text);
  const v = voices.find(x => x.name === $("voice").value);
  if(v) u.voice = v;
  u.rate = parseFloat($("rate").value);
  u.pitch = parseFloat($("pitch").value);
  boundarySeen = false;
  u.onboundary = (e) => { if(e.charIndex !== undefined){ boundarySeen = true; markWord(i, e.charIndex); } };
  u.onend = () => { if(playing) speakSentence(i + 1); };
  u.onerror = (e) => { if(e.error !== "canceled" && e.error !== "interrupted"){ playing = false; $("playbtn").textContent = "▶ Play"; $("loadmsg").innerHTML = '<span class="err">Speech error: ' + esc(e.error || "unknown") + "</span>"; } };
  utter = u;
  speechSynthesis.speak(u);
  // Fallback: if the browser never fires word boundaries, highlight the whole sentence.
  setTimeout(() => { if(playing && utter === u && !boundarySeen){ document.querySelectorAll('#reader .sent[data-i="' + i + '"] .w').forEach(el => el.classList.add("on")); } }, 1500);
}
function togglePlay(){
  if(!doc) return;
  if(playing){ speechSynthesis.pause(); playing = false; $("playbtn").textContent = "▶ Resume"; return; }
  if(speechSynthesis.paused){ speechSynthesis.resume(); playing = true; $("playbtn").textContent = "⏸ Pause"; return; }
  playing = true; $("playbtn").textContent = "⏸ Pause";
  speakSentence(cur);
}
function stopAll(){
  playing = false; speechSynthesis.cancel();
  if($("playbtn")) $("playbtn").textContent = "▶ Play";
  document.querySelectorAll("#reader .w.on").forEach(el => el.classList.remove("on"));
}
function startAt(i){ stopAll(); cur = i; markSentence(i); updateBar(); playing = true; $("playbtn").textContent = "⏸ Pause"; speakSentence(i); }
function jumpSentence(d){
  if(!doc) return;
  const n = Math.max(0, Math.min(doc.sentences.length - 1, cur + d));
  if(playing){ stopAll(); startAt(n); } else { cur = n; markSentence(n); updateBar(); }
}

async function summarize(){
  if(!doc) return;
  $("sumstat").textContent = "Summarising…";
  const fd = new FormData(); fd.append("text", $("src").value); fd.append("language", doc.language);
  const r = await fetch("/awaaz/api/summarize", {method:"POST", body: fd});
  const d = await r.json();
  if(!d.ok){ $("summary").innerHTML = '<span class="err">' + esc(d.error) + "</span>"; $("sumstat").textContent = ""; return; }
  $("summary").textContent = d.summary;
  $("sumstat").textContent = "AI summary — re-check numbers at the source.";
}
fetch("/awaaz/api/ai-status").then(r => r.json()).then(d => {
  if(!d.ai_available){ $("sumbtn").disabled = true; $("sumstat").textContent = "AI summary unavailable right now (server key not set or quota out) — reader still works fully."; }
}).catch(() => {});

function getLib(){ try{ return JSON.parse(localStorage.getItem("awaaz_library") || "[]"); }catch(e){ return []; } }
function saveToLibrary(){
  if(!doc) return;
  const lib = getLib();
  const title = (doc.headings[0] && doc.headings[0].text) || doc.sentences[0].text.slice(0, 60);
  lib.unshift({title: title, text: $("src").value, pos: cur, savedAt: new Date().toISOString().slice(0, 10)});
  localStorage.setItem("awaaz_library", JSON.stringify(lib.slice(0, 20)));
  renderLib();
}
function renderLib(){
  const lib = getLib();
  $("library").innerHTML = lib.length ? lib.map((it, i) =>
    '<div><span class="lib" onclick="loadLib(' + i + ')">' + esc(it.title) + "</span> <span>(" + it.savedAt + ')</span> <span class="lib" onclick="delLib(' + i + ')">✕</span></div>').join("")
    : "Empty — save a document to keep it here.";
}
function loadLib(i){
  const it = getLib()[i]; if(!it) return;
  $("src").value = it.text;
  analyze().then(() => { cur = Math.min(it.pos || 0, doc.sentences.length - 1); markSentence(cur); updateBar(); });
}
function delLib(i){ const lib = getLib(); lib.splice(i, 1); localStorage.setItem("awaaz_library", JSON.stringify(lib)); renderLib(); }
renderLib();
</script></body></html>"""
