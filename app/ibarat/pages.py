IBARAT_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ibarat — Free Writing Studio: Paraphrase, Summarize, Cite</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:980px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{font-size:26px;margin-bottom:2px} .sub{color:#555;margin-top:0}
.card{border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0}
label{display:block;font-weight:600;margin:10px 0 4px}
input[type=text],select,textarea{width:100%;padding:9px;border:1px solid #bbb;border-radius:8px;box-sizing:border-box;font-size:15px}
button{background:#0b6e4f;color:#fff;border:0;border-radius:8px;padding:10px 16px;font-size:15px;cursor:pointer;margin:4px 4px 0 0}
button.ghost{background:#eee;color:#222} button:disabled{opacity:.5}
.muted{color:#666;font-size:14px} .ok{color:#0b6e4f} .bad{color:#a33}
.flag{color:#a33;background:#fff3f3;border:1px solid #e5b4b4;border-radius:8px;padding:6px 8px;margin:6px 0;font-size:14px}
.out{white-space:pre-wrap;border:1px solid #ddd;border-radius:12px;padding:12px;margin:10px 0;font-size:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
</style></head><body>
<h1>✍️ Ibarat</h1>
<p class="sub">Free writing studio — paraphrase in 7 modes, summarize, check style,
and build citations. No account, no card, no word cap, no history stored.</p>
<p class="muted">Honest scope: the built-in paraphraser is <b>rule-based</b> (curated
synonym/phrase tables) — it changes wording, it does not understand meaning, so
read every output before using it. It does <b>not</b> check plagiarism (no corpus
= no honest score), it does <b>not</b> beat AI detectors, and it never invents a
DOI. Paraphrasing someone else's work without citing it is still plagiarism.
Not affiliated with QuillBot or any other writing tool.</p>

<div class="card">
<h2 style="margin-top:0">Your text</h2>
<label>Text *<textarea id="text" rows="7" placeholder="Paste your paragraph, abstract, email or report section here — any length."></textarea></label>
<label>Paraphrase mode
<select id="mode">
<option value="standard">Standard</option><option value="fluency">Fluency (light touch)</option>
<option value="formal">Formal</option><option value="simple">Simple</option>
<option value="creative">Creative</option><option value="shorten">Shorten</option>
<option value="expand">Expand</option></select></label>
<label>Protected terms — never swapped (comma separated; e.g. drug names, author names)
<input type="text" id="protected" placeholder="e.g. metformin, Smith, HbA1c"></label>
<label>Summary length (sentences) <input type="text" id="sumN" value="3" style="width:80px"></label>
<button onclick="paraphrase()">🔁 Paraphrase (rule-based)</button>
<button onclick="aiRewrite()">✨ AI rewrite (Gemini)</button>
<button class="ghost" onclick="summarize()">📝 Summarize</button>
<button class="ghost" onclick="analyze()">🔍 Style + readability</button>
<button class="ghost" onclick="copyOut()">📋 Copy output</button>
<span id="aiBadge" class="muted"></span>
<div id="meta" class="muted"></div>
<div id="out" class="out">Your result will appear here.</div>
</div>

<div class="card">
<h2 style="margin-top:0">Citation builder — never invents a DOI</h2>
<p class="muted">Fill only what you know. DOI/URL appear only if you supply them;
otherwise the citation ends cleanly — a missing DOI is always better than a fake one.</p>
<div class="grid">
<div><label>Style<select id="cStyle"><option value="apa">APA</option><option value="mla">MLA</option><option value="chicago">Chicago (author-date)</option></select></label></div>
<div><label>Author surname<input type="text" id="cSurname" placeholder="e.g. Khan"></label></div>
<div><label>Author initials<input type="text" id="cInitials" placeholder="e.g. A. B."></label></div>
<div><label>Year<input type="text" id="cYear" placeholder="e.g. 2024"></label></div>
</div>
<label>Title<input type="text" id="cTitle" placeholder="e.g. Drug pricing in Pakistan"></label>
<label>Journal / container<input type="text" id="cContainer" placeholder="e.g. Journal of Pharmacy Practice"></label>
<div class="grid">
<div><label>DOI (only if real)<input type="text" id="cDoi" placeholder="e.g. 10.1234/abc"></label></div>
<div><label>URL (only if real)<input type="text" id="cUrl" placeholder="https://…"></label></div>
</div>
<button onclick="cite()">📚 Build citation</button>
<div id="citeOut" class="out">Your citation will appear here.</div>
</div>

<script>
const $=id=>document.getElementById(id);
async function post(p,b){const r=await fetch(p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});return r.json();}
function prot(){return $('protected').value.split(',').map(s=>s.trim()).filter(Boolean);}
async function paraphrase(){
  $('out').textContent='Working…';
  const d=await post('/ibarat/api/paraphrase',{text:$('text').value,mode:$('mode').value,protected:prot()});
  if(d.error){$('out').textContent='Error: '+d.error;return;}
  $('out').textContent=d.rewritten;
  $('meta').innerHTML='Mode: '+d.mode+' · '+d.engine+' · '+d.words+' words, '+d.changed_words+' changed · word-set similarity '+d.similarity+' (1.0 = identical wording). Read it before using — rule-based rewrites can shift nuance.';
}
async function aiRewrite(){
  $('out').textContent='Asking Gemini…';
  const d=await post('/ibarat/api/ai-rewrite',{text:$('text').value,mode:$('mode').value});
  if(d.error){$('out').textContent='AI unavailable: '+d.error+' — the rule-based Paraphrase button still works.';return;}
  $('out').textContent=d.rewritten;
  $('meta').innerHTML='Engine: '+d.engine+' · technical terms and numbers were instructed to stay exact — still verify them.';
}
async function summarize(){
  $('out').textContent='Working…';
  const d=await post('/ibarat/api/summarize',{text:$('text').value,sentences:parseInt($('sumN').value)||3});
  if(d.error){$('out').textContent='Error: '+d.error;return;}
  $('out').textContent=d.summary;
  $('meta').innerHTML='Extractive summary: sentences '+d.picked.map(i=>i+1).join(', ')+' of '+d.total_sentences+' picked by keyword frequency, kept in original order. No wording invented.';
}
async function analyze(){
  $('out').textContent='Working…';
  const d=await post('/ibarat/api/analyze',{text:$('text').value});
  if(d.error){$('out').textContent='Error: '+d.error;return;}
  const r=d.readability;
  let h='Words: '+r.words+' · Sentences: '+r.sentences+' · Flesch Reading Ease: '+r.flesch_reading_ease+' · Grade level: '+r.flesch_kincaid_grade+' (estimate — syllables by vowel-group heuristic).\n';
  h+=d.flags.length?d.flags.map(f=>'⚠ '+f.detail).join('\n'):'No style flags — no doubled words, long sentences, passive candidates or fillers found.';
  $('out').textContent=h;
  $('meta').textContent='';
}
async function cite(){
  const d=await post('/ibarat/api/cite',{style:$('cStyle').value,surname:$('cSurname').value,initials:$('cInitials').value,year:$('cYear').value,title:$('cTitle').value,container:$('cContainer').value,url:$('cUrl').value,doi:$('cDoi').value});
  $('citeOut').textContent=d.error?('Error: '+d.error):(d.citation+(d.note?'\n\n'+d.note:''));
}
function copyOut(){navigator.clipboard.writeText($('out').textContent);}
fetch('/ibarat/api/ai-status').then(r=>r.json()).then(d=>{
  $('aiBadge').textContent=d.ai_available?'AI rewrite: available ✅':'AI rewrite: not configured — rule-based tools work fully.';
});
</script></body></html>
"""
