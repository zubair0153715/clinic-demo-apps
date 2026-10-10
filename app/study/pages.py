STUDIO_HTML = """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MedExplain Studio — Urdu Study Videos from Your Medical Books</title>
<meta name="description" content="Upload medical book PDFs, get professional Urdu-narrated explainer videos per chapter.">
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
header{background:#0b3d2e;color:#fff;padding:48px 0}
header h1{margin:0 0 10px;font-size:1.9rem}
header p{margin:0;opacity:.92;max-width:640px}
.btn{display:inline-block;background:#25d366;color:#062b1f;font-weight:700;padding:10px 22px;border-radius:10px;border:0;cursor:pointer;font-size:1rem;margin:6px 8px 6px 0;text-decoration:none}
.btn.dark{background:#0b3d2e;color:#fff}
section{padding:32px 0;border-bottom:1px solid #eee}
h2{color:#0b3d2e;margin-top:0}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px;margin-bottom:14px}
.card b{color:#0b3d2e}
input,select{padding:10px;margin:6px 8px 6px 0;border:1px solid #ddd;border-radius:8px;font-size:1rem;box-sizing:border-box}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.8rem;font-weight:600}
.queued{background:#e3f2fd;color:#1565c0}.working{background:#fff3e0;color:#e65100}
.done{background:#e8f5e9;color:#2e7d32}.failed{background:#fce4ec;color:#c62828}
video{width:100%;max-width:640px;border-radius:12px;background:#000}
.note{background:#fff8e1;border:1px solid #ffe082;border-radius:10px;padding:12px;margin-bottom:16px;font-size:.9rem}
footer{padding:28px 0;color:#666;font-size:.9rem}
ol.steps li{margin-bottom:8px}
.muted{color:#666;font-size:.9rem}
</style></head><body>
<header><div class="wrap">
<h1>🎓 MedExplain Studio</h1>
<p>Upload your medical book PDFs. Pick a chapter + page range. Get a professional <b>Urdu-narrated explainer video</b> — slides, diagrams, voiceover, subtitles.</p>
</div></header>
<div class="wrap">

<section><h2>How it works</h2>
<ol class="steps">
<li><b>Upload</b> a book PDF below.</li>
<li><b>Create a chapter job</b> — chapter name + page range (e.g. 45–62).</li>
<li>The studio renders your video (usually within ~15–30 min): Urdu voiceover, animated slides, labeled diagrams, Urdu subtitles.</li>
<li>Watch / download it from <b>My videos</b>.</li>
</ol>
<div class="note">⚠️ Videos are narrated visual explainers with animated slides &amp; diagrams — not 3D cartoon animation. Urdu voiceover accent may be imperfect; medical terms stay in English where standard.</div>
</section>

<section><h2>1. Upload a book (PDF)</h2>
<div class="card">
<input type="file" id="pdf" accept="application/pdf">
<button class="btn dark" onclick="uploadPDF()">Upload PDF</button>
<p id="up-msg" class="muted"></p>
</div>
<h3>Uploaded books</h3>
<div id="books"><p class="muted">Loading…</p></div>
</section>

<section><h2>2. Create a chapter video job</h2>
<div class="card">
<div class="row">
<select id="j-book"><option value="">— select book —</option></select>
<input id="j-chapter" placeholder="Chapter name (e.g. The Human Heart)" style="min-width:260px">
<input id="j-pages" placeholder="Pages (e.g. 45-62)" style="width:140px">
<button class="btn" onclick="createJob()">Create video job</button>
</div>
<p id="job-msg" class="muted"></p>
</div>
<h3>Jobs</h3>
<div id="jobs"><p class="muted">Loading…</p></div>
</section>

<section><h2>3. My videos</h2>
<div id="videos"><p class="muted">Loading…</p></div>
</section>

</div>
<footer><div class="wrap">MedExplain Studio — built for Zubair Ahmed, Pharm-D.</div></footer>

<script>
const $=id=>document.getElementById(id);
async function api(p,m,b,isForm){const o={method:m||'GET'};if(b){if(isForm){o.body=b}else{o.headers={'Content-Type':'application/json'};o.body=JSON.stringify(b)}}const r=await fetch(p,o);const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.detail||'error');return j}
async function uploadPDF(){const f=$('pdf').files[0];if(!f){$('up-msg').textContent='Choose a PDF first.';return}$('up-msg').textContent='Uploading…';const fd=new FormData();fd.append('file',f);try{const d=await api('/study/api/upload','POST',fd,true);$('up-msg').textContent='✅ Uploaded: '+d.filename;$('pdf').value='';loadBooks()}catch(e){$('up-msg').textContent='❌ '+e.message}}
async function loadBooks(){try{const d=await api('/study/api/books');const bs=d.books||[];$('books').innerHTML=bs.length?bs.map(b=>'<div class="card"><b>'+esc(b)+'</b></div>').join(''):'<p class="muted">No books yet.</p>';const sel=$('j-book');sel.innerHTML='<option value="">— select book —</option>'+bs.map(b=>'<option>'+esc(b)+'</option>').join('')}catch(e){$('books').innerHTML='<p class="muted">Error loading.</p>'}}
async function createJob(){const book=$('j-book').value,chapter=$('j-chapter').value.trim(),pages=$('j-pages').value.trim();if(!book||!chapter||!pages){$('job-msg').textContent='Fill book, chapter name and pages.';return}$('job-msg').textContent='Creating…';try{const d=await api('/study/api/jobs','POST',{pdf:book,chapter:chapter,pages:pages});$('job-msg').textContent='✅ Job queued: '+d.id;$('j-chapter').value='';$('j-pages').value='';loadJobs()}catch(e){$('job-msg').textContent='❌ '+e.message}}
async function loadJobs(){try{const d=await api('/study/api/jobs');const js=d.jobs||[];$('jobs').innerHTML=js.length?js.map(j=>'<div class="card"><b>'+esc(j.chapter)+'</b> <span class="badge '+j.status+'">'+j.status+'</span><br><span class="muted">'+esc(j.pdf)+' • pages '+esc(j.pages)+' • '+esc(j.id)+'</span>'+(j.error?'<br><span style="color:#c62828">'+esc(j.error)+'</span>':'')+'</div>').join(''):'<p class="muted">No jobs yet.</p>'}catch(e){$('jobs').innerHTML='<p class="muted">Error loading.</p>'}}
async function loadVideos(){try{const d=await api('/study/api/videos');const vs=d.videos||[];$('videos').innerHTML=vs.length?vs.map(v=>'<div class="card"><b>'+esc(v.title)+'</b><br><video controls preload="metadata" src="/study/video/'+encodeURIComponent(v.filename)+'"></video><br><a class="btn dark" href="/study/video/'+encodeURIComponent(v.filename)+'" download>⬇ Download MP4</a> <span class="muted">'+v.size_mb+' MB</span></div>').join(''):'<p class="muted">No videos yet — create a chapter job above.</p>'}catch(e){$('videos').innerHTML='<p class="muted">Error loading.</p>'}}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
loadBooks();loadJobs();loadVideos();setInterval(()=>{loadJobs();loadVideos()},30000);
</script>
</body></html>

"""
