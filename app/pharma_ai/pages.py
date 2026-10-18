"""PharmaAI chat page (single-file HTML)."""

CHAT_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PharmaAI — Your Pharma Study Assistant</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--acc:#38bdf8;--txt:#e2e8f0;--mut:#94a3b8;--ok:#4ade80;--warn:#fbbf24}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--txt)}
.wrap{max-width:860px;margin:0 auto;padding:20px}
.hero{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-radius:16px;padding:28px;margin-bottom:16px}
.hero h1{margin:0 0 6px;font-size:26px}.hero p{margin:4px 0;color:#e0f2fe}
.banner{background:#422006;border:1px solid var(--warn);color:#fde68a;border-radius:12px;padding:12px 16px;margin-bottom:16px;font-size:14px}
.card{background:var(--card);border-radius:12px;padding:18px;margin-bottom:16px}
textarea{width:100%;min-height:76px;background:#0f172a;color:var(--txt);border:1px solid #334155;border-radius:8px;padding:10px;font-size:15px}
button{background:var(--acc);border:0;color:#082f49;font-weight:700;border-radius:8px;padding:10px 22px;font-size:15px;cursor:pointer;margin-top:10px}
button:disabled{opacity:.5;cursor:wait}
.q{border-left:3px solid var(--acc);padding:6px 12px;margin:14px 0 6px;color:#bae6fd;font-weight:600}
.a{line-height:1.65;white-space:pre-wrap}
.a em{color:var(--mut)}
.cites{margin:10px 0;display:flex;flex-wrap:wrap;gap:8px}
.cite{background:#0f172a;border:1px solid #334155;border-radius:20px;padding:4px 12px;font-size:12px;color:var(--mut)}
details{margin-top:10px}summary{cursor:pointer;color:var(--acc);font-size:14px}
.pass{background:#0f172a;border-radius:8px;padding:10px;margin:8px 0;font-size:13.5px;line-height:1.6;color:#cbd5e1}
.pass b{color:var(--warn)}
.notice{background:#422006;border-radius:8px;padding:10px;font-size:13.5px;color:#fde68a;margin-bottom:8px}
.meta{color:var(--mut);font-size:12.5px;margin-top:14px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input[type=file]{color:var(--mut);font-size:13px}
h3{margin:0 0 10px;font-size:16px}
ul.docs{margin:6px 0;padding-left:20px;font-size:14px;color:#cbd5e1}
</style></head><body><div class="wrap">
<div class="hero"><h1>💊 PharmaAI</h1>
<p>Your own pharma knowledge assistant — answers grounded in <b>your books</b>, with citations.</p>
<p style="font-size:13px">RAG v1: book text retrieval (BM25) + AI generation. No fine-tuning, no GPU — honest by design.</p></div>
<div class="banner">⚠️ <b>Study &amp; research aid only — NOT medical advice.</b> Always verify with your textbooks and a qualified pharmacist/doctor before any clinical use.</div>
<div class="card"><h3>Ask a question</h3>
<textarea id="q" placeholder="e.g. Why do aminoglycosides cause nephrotoxicity?"></textarea><br>
<button id="ask" onclick="ask()">Ask PharmaAI</button>
<div id="out"></div></div>
<div class="card"><h3>📚 Knowledge base</h3><div id="docs">loading…</div></div>
<div class="card"><h3>➕ Add a document</h3>
<div class="row"><input type="file" id="pdf" accept=".pdf"><button onclick="upload()">Upload &amp; index PDF</button></div>
<div id="upmsg" class="meta"></div>
<p class="meta">Books, FDA labels, DRAP guidelines — anything pharma. Text is extracted, chunked and indexed automatically.</p></div>
<script>
async function loadDocs(){
  const r=await fetch('/pharma-ai/api/docs');const j=await r.json();
  document.getElementById('docs').innerHTML='<ul class="docs">'+j.docs.map(d=>
    `<li><b>${d.title}</b> — ${d.chunks} chunks, ${d.pages} pages <span style="color:#64748b">(${d.source})</span></li>`).join('')+'</ul>';
}
async function ask(){
  const q=document.getElementById('q').value.trim();if(!q)return;
  const btn=document.getElementById('ask');btn.disabled=true;btn.textContent='Thinking…';
  const out=document.getElementById('out');out.innerHTML='<p class="meta">Searching your books…</p>';
  try{
    const r=await fetch('/pharma-ai/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    const j=await r.json();
    let h=`<div class="q">${j.question}</div>`;
    if(j.notice)h+=`<div class="notice">${j.notice}</div>`;
    if(j.answer)h+=`<div class="a">${j.answer.replace(/</g,'&lt;')}</div>`;
    if(j.citations&&j.citations.length)h+=`<div class="cites">${j.citations.map(c=>`<span class="cite">📖 ${c}</span>`).join('')}</div>`;
    h+=`<details><summary>Source passages (${j.passages.length})</summary>`+j.passages.map(p=>
      `<div class="pass"><b>${p.doc_title} — ${p.section} (p.${p.page_start})</b><br>${p.text.slice(0,900).replace(/</g,'&lt;')}…</div>`).join('')+`</details>`;
    h+=`<p class="meta">${j.generated?'Generated with citations from your books.':'Retrieved passages only (AI generation unavailable).'} Study aid only — not medical advice.</p>`;
    out.innerHTML=h;
  }catch(e){out.innerHTML='<p class="notice">Request failed: '+e+'</p>';}
  btn.disabled=false;btn.textContent='Ask PharmaAI';
}
async function upload(){
  const f=document.getElementById('pdf').files[0];if(!f)return;
  const m=document.getElementById('upmsg');m.textContent='Uploading & indexing…';
  const fd=new FormData();fd.append('file',f);
  const r=await fetch('/pharma-ai/api/upload',{method:'POST',body:fd});
  const j=await r.json();
  m.textContent=j.ok?`✅ ${j.title}: ${j.chunks} chunks indexed.`:`❌ ${j.error}`;
  loadDocs();
}
loadDocs();
</script></div></body></html>"""
