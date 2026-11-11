# -*- coding: utf-8 -*-
"""Bolo page — single self-contained HTML page.

Dictation runs in the browser via the Web Speech API (Chrome /
Edge / Safari); the server only applies voice commands, computes
stats, builds exports and (optionally) runs Gemini polish. Sessions
live in localStorage; nothing is stored server-side. No account,
no card, no minute cap, no ads.
"""

BOLO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bolo — بولو | Free AI dictation studio</title>
<style>
:root{--ink:#1e293b;--bg:#f0fdf4;--card:#ffffff;--line:#bbf7d0;--acc:#15803d;--acc2:#0f766e;--soft:#dcfce7}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55}
header{background:linear-gradient(135deg,#14532d,#15803d);color:#fff;padding:26px 16px 20px;text-align:center}
header h1{margin:0;font-size:30px}
header p{margin:6px 0 0;opacity:.92}
main{max-width:780px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}
h2{margin:0 0 8px;font-size:19px}
h3{margin:14px 0 6px;font-size:16px}
.muted{color:#64748b;font-size:13px}
button{border:0;border-radius:10px;padding:10px 16px;font-size:15px;background:var(--acc);color:#fff;cursor:pointer}
button.ghost{background:#fff;border:1px solid var(--acc);color:var(--acc)}
button:disabled{opacity:.5;cursor:default}
button.mic{font-size:18px;padding:14px 26px;border-radius:999px}
button.mic.live{background:#b91c1c;animation:pulse 1.4s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(185,28,28,.4)}70%{box-shadow:0 0 0 12px rgba(185,28,28,0)}100%{box-shadow:0 0 0 0 rgba(185,28,28,0)}}
textarea{width:100%;min-height:180px;padding:12px;border:1px solid var(--line);border-radius:10px;font-size:16px;line-height:1.6;font-family:inherit;resize:vertical}
input,select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:9px;font-size:15px;background:#fff}
label{display:block;font-size:13px;color:#64748b;margin:10px 0 4px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.pill{display:inline-block;background:var(--soft);border:1px solid #86efac;border-radius:999px;padding:3px 10px;font-size:13px;margin:2px}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{background:var(--soft)}
.ai{border-left:4px solid var(--acc2);background:#f0fdfa;padding:10px 12px;border-radius:8px;margin:10px 0;white-space:pre-wrap}
.err{color:#b91c1c;font-size:14px}
.ok{color:#0f766e;font-size:14px}
.center{text-align:center}
.interim{color:#64748b;font-style:italic}
.sess{border:1px solid var(--line);border-radius:10px;padding:10px;margin:8px 0}
.sess b{display:block}
footer{max-width:780px;margin:0 auto;padding:0 16px 30px;color:#64748b;font-size:13px}
</style>
</head>
<body>
<header>
<h1>Bolo — بولو</h1>
<p>Free AI dictation studio · Boliye, likha jayega — unlimited, no account, no card, no minute cap.</p>
</header>
<main>

<div class="card">
<h2>1 · Language chunein</h2>
<label for="langSel">Dictation language</label>
<select id="langSel">
<option value="en" selected>English (US) — en-US</option>
<option value="ur">Urdu (Pakistan) — ur-PK, اردو script</option>
<option value="roman">Roman-Urdu — boliye Urdu, likha jayega Roman letters me (AI)</option>
</select>
<p class="muted" id="langNote">Recognition in English; voice commands in English.</p>
<p class="muted" id="supportNote">Checking browser support…</p>
</div>

<div class="card center">
<h2>2 · Bolo — mic dabayein, bolna shuru karein</h2>
<button id="micBtn" class="mic">🎙️ Start dictation</button>
<p><span class="pill" id="pillTime">0:00</span>
<span class="pill" id="pillWords">0 words</span>
<span class="pill" id="pillWpm">0 WPM</span></p>
<p class="muted">Bolte waqt punctuation bhi boliye: "full stop", "naya paragraph", "نیا پیراگراف" — neeche cheat-sheet hai.</p>
<p id="liveLine" class="interim"></p>
</div>

<div class="card">
<h2>3 · Aapka text</h2>
<textarea id="textArea" placeholder="Yahan aapki dictation aayegi… ya khud type karein."></textarea>
<div class="row" style="margin-top:10px">
<button id="cmdBtn" class="ghost">Voice commands lagayein</button>
<button id="clearBtn" class="ghost">Saaf karein</button>
</div>
<p id="cmdMsg" class="ok"></p>
</div>

<div class="card">
<h2>4 · AI polish — free</h2>
<p class="muted" id="aiStatus">Checking AI…</p>
<label for="styleSel">Style</label>
<select id="styleSel">
<option value="saaf" selected>Saaf karein — grammar aur punctuation theek</option>
<option value="email">Email banayein</option>
<option value="message">WhatsApp message banayein</option>
<option value="notes">Bullet notes banayein</option>
</select>
<div class="row" style="margin-top:10px">
<button id="polishBtn">AI polish</button>
<button id="romanBtn" class="ghost">Roman-Urdu me likhein</button>
<button id="urduBtn" class="ghost">Urdu tarjuma</button>
</div>
<div id="aiOut" class="ai" style="display:none"></div>
<div class="row" style="margin-top:10px">
<button id="useAiBtn" class="ghost" style="display:none">Ye text use karein</button>
</div>
<p class="muted">AI-written text hamesha "AI-written" label ke saath dikhaya jata hai. AI sirf woh text parhta hai jo aap ne dictate ya type kiya.</p>
</div>

<div class="card">
<h2>5 · Save, copy, download</h2>
<div class="row">
<input id="titleIn" placeholder="Session title (jaise: Meeting notes)" style="flex:1;min-width:200px">
<button id="saveBtn">Save session</button>
</div>
<div class="row" style="margin-top:10px">
<button id="copyBtn" class="ghost">Copy text</button>
<button id="dlTxtBtn" class="ghost">Download .txt</button>
<button id="dlMdBtn" class="ghost">Download .md</button>
</div>
<p id="saveMsg" class="ok"></p>
<h3>Saved sessions (is browser me)</h3>
<div id="sessList"><p class="muted">Abhi koi saved session nahi.</p></div>
</div>

<div class="card">
<h2>Voice commands — cheat-sheet</h2>
<table>
<tr><th>Boliye</th><th>Milta hai</th><th>Language</th></tr>
<tr><td>full stop / period</td><td>.</td><td>English</td></tr>
<tr><td>comma</td><td>,</td><td>English / Roman-Urdu</td></tr>
<tr><td>question mark</td><td>?</td><td>English</td></tr>
<tr><td>exclamation mark</td><td>!</td><td>English</td></tr>
<tr><td>new line</td><td>new line</td><td>English</td></tr>
<tr><td>new paragraph</td><td>new paragraph</td><td>English</td></tr>
<tr><td>naya paragraph</td><td>new paragraph</td><td>Roman-Urdu</td></tr>
<tr><td>nayi line / naya line</td><td>new line</td><td>Roman-Urdu</td></tr>
<tr><td>sawaal ka nishan</td><td>?</td><td>Roman-Urdu</td></tr>
<tr><td>نیا پیراگراف</td><td>new paragraph</td><td>Urdu</td></tr>
<tr><td>سوالیہ نشان</td><td>؟</td><td>Urdu</td></tr>
<tr><td>فل سٹاپ</td><td>۔</td><td>Urdu</td></tr>
<tr><td>کاما</td><td>،</td><td>Urdu</td></tr>
</table>
<p class="muted">Urdu voice commands kisi aur dictation app me nahi milte — dictation.io khud native speakers se Urdu commands likhwane ki appeal karta hai. Yahan pehle se maujood hain.</p>
</div>

<div class="card">
<h2>Honest limits — zaroor parhein</h2>
<ul>
<li><b>No accuracy claim.</b> Bolo koi accuracy number nahi deta. Recognition ki quality browser, mic, lehja (accent) aur shor par depend karti hai — saaf English/Urdu achhi pehchani jati hai, tez code-switching kamzor.</li>
<li><b>Browser support:</b> Chrome 25+, Edge 87+, Safari 14.1+ me chalta hai. <b>Firefox me SpeechRecognition nahi hai</b> (flag ke peeche), is liye Firefox me mic kaam nahi karega.</li>
<li><b>Privacy:</b> Chrome/Edge me audio Google ke speech servers ko bheja jata hai (Google Assistant wali service) — dictation ke liye internet zaroori hai. <b>Bolo ka server aapki awaz kabhi nahi sunta</b> aur kuch store nahi karta; sessions sirf aapke browser (localStorage) me rehte hain.</li>
<li><b>AI polish</b> ke liye owner ki free Gemini quota chahiye; us ke baghair dictation, voice commands, sessions aur export poore kaam karte hain.</li>
<li><b>Ye meeting recorder nahi hai:</b> speaker labels, multi-speaker pehchan aur uploaded-file transcription v1 me nahi hain — ye woh kaam hain jin ke Otter paise leta hai.</li>
<li>Bolo ka Voicy ya Otter.ai se koi ta'alluq nahi. Naam, code ya design un ka nahi — sab original hai.</li>
</ul>
</div>

</main>
<footer>
Bolo — free AI dictation studio. Original clean-room build from the daily-app-gap-build series (Voicy / Otter.ai gaps). No account, no card, no minute cap, no ads.
</footer>

<script>
const $ = id => document.getElementById(id);
const LANG_NOTES = {
  en: "Recognition in English; voice commands in English.",
  ur: "Recognition in Urdu script (ur-PK); voice commands in Urdu script.",
  roman: "Speak Urdu; recognition runs in ur-PK, then AI writes it in Roman-Urdu letters. Voice commands in Roman-Urdu."
};
const LANG_CODES = { en: "en-US", ur: "ur-PK", roman: "ur-PK" };
const SESS_KEY = "bolo_sessions";

let rec = null, listening = false, startTs = 0, elapsed = 0, timerId = null;
let finalText = "";

function lang() { return $("langSel").value; }
function updateCounts() {
  const t = $("textArea").value;
  const words = t.trim() ? t.trim().split(/\s+/).length : 0;
  $("pillWords").textContent = words + " words";
  const mins = elapsed / 60;
  $("pillWpm").textContent = (mins > 0 ? Math.round(words / mins) : 0) + " WPM";
}
function fmtTime(s) {
  const m = Math.floor(s / 60), ss = Math.floor(s % 60);
  return m + ":" + String(ss).padStart(2, "0");
}
function tick() {
  elapsed = (Date.now() - startTs) / 1000;
  $("pillTime").textContent = fmtTime(elapsed);
  updateCounts();
}

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!SR) {
  $("supportNote").textContent = "⚠️ Is browser me SpeechRecognition nahi hai (Firefox). Chrome, Edge ya Safari use karein — text phir bhi type karke polish/export kar sakte hain.";
  $("micBtn").disabled = true;
} else {
  $("supportNote").textContent = "✓ Aapka browser speech recognition support karta hai (Chrome/Edge/Safari).";
}
$("langSel").addEventListener("change", () => { $("langNote").textContent = LANG_NOTES[lang()]; });

$("micBtn").addEventListener("click", () => {
  if (!SR) return;
  if (listening) { rec.stop(); return; }
  rec = new SR();
  rec.lang = LANG_CODES[lang()];
  rec.continuous = true;
  rec.interimResults = true;
  finalText = $("textArea").value;
  rec.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      if (res.isFinal) { finalText += (finalText && !finalText.endsWith(" ") ? " " : "") + res[0].transcript; }
      else { interim += res[0].transcript; }
    }
    $("textArea").value = finalText + (interim ? (finalText ? " " : "") + interim : "");
    $("liveLine").textContent = interim ? "Sun rahe hain: " + interim : "";
    updateCounts();
  };
  rec.onerror = (e) => {
    $("liveLine").textContent = "Mic error: " + (e.error || "unknown") + ". Mic permission check karein.";
  };
  rec.onend = () => {
    if (listening) { try { rec.start(); } catch (err) {} return; }
    $("micBtn").textContent = "🎙️ Start dictation";
    $("micBtn").classList.remove("live");
    clearInterval(timerId);
    $("liveLine").textContent = "";
    applyCommands(true);
  };
  try {
    rec.start();
    listening = true;
    startTs = Date.now();
    timerId = setInterval(tick, 500);
    $("micBtn").textContent = "⏹️ Stop dictation";
    $("micBtn").classList.add("live");
    $("liveLine").textContent = "Sun rahe hain… boliye.";
  } catch (err) {
    $("liveLine").textContent = "Mic start nahi hua: " + err.message;
  }
});

async function postForm(url, data) {
  const fd = new FormData();
  for (const k in data) fd.append(k, data[k]);
  const r = await fetch(url, { method: "POST", body: fd });
  return r.json();
}
async function applyCommands(auto) {
  const t = $("textArea").value.trim();
  if (!t) { if (!auto) $("cmdMsg").textContent = "Pehle kuch bolein ya likhein."; return; }
  const j = await postForm("/bolo/api/commands", { text: t, language: lang() });
  if (j.ok) {
    $("textArea").value = j.text;
    $("cmdMsg").textContent = auto ? "Voice commands lag gaye." : "Voice commands lag gaye — " + j.words + " words.";
    updateCounts();
  } else {
    $("cmdMsg").textContent = "Error: " + j.error;
  }
}
$("cmdBtn").addEventListener("click", () => applyCommands(false));
$("clearBtn").addEventListener("click", () => {
  $("textArea").value = ""; finalText = ""; elapsed = 0;
  $("pillTime").textContent = "0:00"; updateCounts();
  $("cmdMsg").textContent = "";
});
$("textArea").addEventListener("input", updateCounts);

// AI
fetch("/bolo/api/ai-status").then(r => r.json()).then(j => {
  $("aiStatus").textContent = j.ai_available
    ? "✓ AI on hai — polish, Roman-Urdu aur Urdu tarjuma free."
    : "AI off hai (GEMINI_API_KEY set nahi). Dictation aur baaki sab phir bhi kaam karta hai.";
});
let lastAi = "";
function showAi(text, label) {
  lastAi = text;
  const o = $("aiOut");
  o.style.display = "block";
  o.textContent = (label ? label + "\n\n" : "") + text;
  $("useAiBtn").style.display = "inline-block";
}
$("polishBtn").addEventListener("click", async () => {
  const t = $("textArea").value.trim();
  if (t.length < 10) { showAi("Pehle kuch bolein ya likhein (kam se kam 10 characters).", ""); return; }
  showAi("AI likh raha hai…", "");
  const j = await postForm("/bolo/api/polish-ai", { language: lang(), text: t, style: $("styleSel").value });
  if (j.ok) showAi(j.result.text, "AI-written · " + j.result.style + " · " + j.result.words + " words");
  else showAi("Error: " + j.error, "");
});
$("romanBtn").addEventListener("click", async () => {
  const t = $("textArea").value.trim();
  if (t.length < 5) { showAi("Pehle Urdu me kuch bolein ya likhein.", ""); return; }
  showAi("AI Roman-Urdu me likh raha hai…", "");
  const j = await postForm("/bolo/api/roman-ai", { text: t });
  if (j.ok) showAi(j.result.text, "AI-written · Roman-Urdu · " + j.result.words + " words");
  else showAi("Error: " + j.error, "");
});
$("urduBtn").addEventListener("click", async () => {
  const t = $("textArea").value.trim();
  if (t.length < 5) { showAi("Pehle English me kuch bolein ya likhein.", ""); return; }
  showAi("AI Urdu tarjuma kar raha hai…", "");
  const j = await postForm("/bolo/api/translate-ai", { text: t });
  if (j.ok) showAi(j.result.text, "AI-written · Urdu tarjuma · " + j.result.words + " words");
  else showAi("Error: " + j.error, "");
});
$("useAiBtn").addEventListener("click", () => {
  if (!lastAi) return;
  $("textArea").value = lastAi; finalText = lastAi; updateCounts();
  $("saveMsg").textContent = "AI text transcript me daal diya.";
});

// Save / copy / download
function loadSessions() {
  try { return JSON.parse(localStorage.getItem(SESS_KEY) || "[]"); } catch (e) { return []; }
}
function renderSessions() {
  const list = loadSessions();
  if (!list.length) { $("sessList").innerHTML = '<p class="muted">Abhi koi saved session nahi.</p>'; return; }
  $("sessList").innerHTML = "";
  list.slice().reverse().forEach((s, idx) => {
    const div = document.createElement("div");
    div.className = "sess";
    const b = document.createElement("b"); b.textContent = s.title;
    const m = document.createElement("span"); m.className = "muted";
    m.textContent = s.words + " words · " + s.lang + " · " + s.date;
    const p = document.createElement("p"); p.textContent = s.text.slice(0, 200) + (s.text.length > 200 ? "…" : "");
    const row = document.createElement("div"); row.className = "row";
    const load = document.createElement("button"); load.className = "ghost"; load.textContent = "Load";
    load.onclick = () => { $("textArea").value = s.text; finalText = s.text; updateCounts(); };
    const del = document.createElement("button"); del.className = "ghost"; del.textContent = "Delete";
    del.onclick = () => {
      const all = loadSessions();
      all.splice(all.length - 1 - idx, 1);
      localStorage.setItem(SESS_KEY, JSON.stringify(all));
      renderSessions();
    };
    row.appendChild(load); row.appendChild(del);
    div.appendChild(b); div.appendChild(m); div.appendChild(p); div.appendChild(row);
    $("sessList").appendChild(div);
  });
}
$("saveBtn").addEventListener("click", () => {
  const t = $("textArea").value.trim();
  if (!t) { $("saveMsg").textContent = "Pehle kuch bolein ya likhein."; return; }
  const all = loadSessions();
  all.push({ title: $("titleIn").value.trim() || "Bolo dictation", text: t,
    words: t.split(/\s+/).length, lang: lang(), date: new Date().toLocaleString() });
  localStorage.setItem(SESS_KEY, JSON.stringify(all));
  $("saveMsg").textContent = "Session save ho gayi (is browser me).";
  renderSessions();
});
$("copyBtn").addEventListener("click", async () => {
  try { await navigator.clipboard.writeText($("textArea").value); $("saveMsg").textContent = "Copy ho gaya."; }
  catch (e) { $("saveMsg").textContent = "Copy nahi hua — manually select karke copy karein."; }
});
function download(content, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], { type: "text/plain" }));
  a.download = name; a.click();
  URL.revokeObjectURL(a.href);
}
async function exportFmt(fmt) {
  const t = $("textArea").value.trim();
  if (!t) { $("saveMsg").textContent = "Pehle kuch bolein ya likhein."; return; }
  const j = await postForm("/bolo/api/export", { text: t, title: $("titleIn").value.trim(), fmt });
  if (!j.ok) { $("saveMsg").textContent = "Error: " + j.error; return; }
  download(j.content, (j.title || "bolo").replace(/[^a-zA-Z0-9_-]+/g, "-") + "." + fmt);
}
$("dlTxtBtn").addEventListener("click", () => exportFmt("txt"));
$("dlMdBtn").addEventListener("click", () => exportFmt("md"));
renderSessions();
updateCounts();
</script>
</body>
</html>
"""
