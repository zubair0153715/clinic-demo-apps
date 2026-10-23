"""Tukra single-page UI (inline CSS/JS, no external assets)."""
TUKRA_HTML = """<!DOCTYPE html>
<html lang="ur">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tukra ٹکڑا — Free AI Clip Maker</title>
<style>
:root{--bg:#0f1115;--card:#171b22;--line:#262c36;--txt:#e8ecf1;--mut:#9aa4b2;
--acc:#7c5cff;--acc2:#00d4a4;--warn:#ffb020}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Nastaliq Urdu",sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:20px 16px 60px}
header{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:6px}
.logo{font-size:34px;font-weight:800}
.logo .tk{color:var(--acc)}
.badge{font-size:12px;border:1px solid var(--line);border-radius:20px;padding:4px 12px;color:var(--mut)}
.sub{color:var(--mut);margin:4px 0 18px;line-height:1.6}
.sub b{color:var(--acc2)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}
h2{margin:0 0 10px;font-size:18px}
textarea{width:100%;min-height:150px;background:#0d0f13;color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:12px;font-size:14px;line-height:1.6;resize:vertical}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:12px}
select,input[type=number],input[type=text]{background:#0d0f13;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:9px 12px;font-size:14px}
button{background:var(--acc);color:#fff;border:0;border-radius:10px;padding:11px 20px;font-size:15px;font-weight:700;cursor:pointer}
button.ghost{background:transparent;border:1px solid var(--line);color:var(--txt);padding:8px 14px;font-size:13px;font-weight:600}
button.small{padding:6px 12px;font-size:12px}
button:disabled{opacity:.45;cursor:default}
.hint{font-size:12.5px;color:var(--mut);line-height:1.6;margin-top:8px}
.status{font-size:12.5px;color:var(--mut);margin-top:10px}
.status .on{color:var(--acc2)} .status .off{color:var(--warn)}
.clip{border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0;background:#141821}
.clip .chead{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.rank{background:var(--acc);border-radius:8px;font-weight:800;padding:2px 10px;font-size:13px}
.ctitle{font-size:16px;font-weight:700}
.score{margin-left:auto;color:var(--acc2);font-weight:800}
.aipick{background:#3a2b00;color:var(--warn);font-size:11px;border-radius:6px;padding:2px 8px;font-weight:700}
.hook{color:var(--mut);font-style:italic;margin:8px 0;line-height:1.5}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.chip{font-size:11.5px;background:#0d0f13;border:1px solid var(--line);border-radius:16px;padding:3px 10px;color:var(--mut)}
.chip b{color:var(--acc2)}
.timerow{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0;font-size:13px;color:var(--mut)}
.timerow input{width:90px;padding:6px 8px;font-size:13px}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
pre.cap{background:#0d0f13;border:1px solid var(--line);border-radius:8px;padding:10px;font-size:13px;white-space:pre-wrap;color:var(--txt);margin:8px 0 0;line-height:1.6}
#preview video{width:100%;max-height:60vh;background:#000;border-radius:10px}
.warn{background:#2a2100;border:1px solid #5a4a00;color:var(--warn);border-radius:10px;padding:10px 14px;font-size:13px;margin:10px 0;line-height:1.6}
.err{background:#2a0d0d;border:1px solid #5a1a1a;color:#ff8a8a;border-radius:10px;padding:10px 14px;font-size:13px;margin:10px 0}
footer{color:var(--mut);font-size:12.5px;margin-top:30px;line-height:1.7;border-top:1px solid var(--line);padding-top:16px}
.kbd{background:#0d0f13;border:1px solid var(--line);border-radius:6px;padding:1px 7px;font-size:12px}
</style>
</head>
<body>
<div class="wrap">
<header>
<div class="logo"><span class="tk">Tukra</span> ٹکڑا</div>
<span class="badge">FREE • no credits</span>
<span class="badge">no watermark</span>
<span class="badge">Urdu captions</span>
</header>
<p class="sub">Lambi video/podcast ka <b>transcript ya SRT</b> do — Tukra viral moments
nikalega, <b>samjhaye ga KYUN</b> (har clip ke saath score breakdown), aur
<b>karaoke captions</b> (ASS/SRT/VTT) dega. OpusClip jaisa credit meter
<b>nahi</b>: rule-based detection hamesha unlimited hai.</p>

<div class="card">
<h2>1. Transcript / SRT do</h2>
<textarea id="inp" placeholder="Yahan transcript paste karo…&#10;&#10;Behtar: YouTube Studio → Subtitles → Download .srt — woh yahan paste karo, timing ke saath."></textarea>
<div class="row">
<input type="file" id="file" accept=".txt,.srt,.vtt,.sbv">
<select id="lang" title="Caption/AI language">
<option value="en">English</option>
<option value="ur">Urdu (proper script)</option>
<option value="roman">Roman-Urdu</option>
</select>
<label class="hint" style="margin:0"><input type="checkbox" id="useai" checked> AI moments (Gemini)</label>
<label class="hint" style="margin:0">Clips: <input type="number" id="maxc" value="8" min="1" max="12" style="width:64px"></label>
<button id="go">Clips nikalo</button>
</div>
<div class="hint">Tip: SRT/VTT (timing wali) do ge to karaoke captions + exact cuts milenge.
Sirf text do ge to moments + titles milenge (timing nahi hogi — woh clearly likha hoga).</div>
<div class="status" id="status">…</div>
<div id="warns"></div>
<div id="err"></div>
</div>

<div class="card" id="preview" style="display:none">
<h2>2. Preview (video tumhare browser mein hi chalti hai — upload nahi hoti)</h2>
<div class="row">
<input type="file" id="vid" accept="video/*,audio/*">
<span class="hint" id="pvinfo">Apni video file chuno, phir kisi clip par "Preview" dabao.</span>
</div>
<video id="v" controls playsinline style="margin-top:10px"></video>
</div>

<div class="card" id="out" style="display:none">
<h2>3. Clips <span class="hint" id="ocount"></span></h2>
<div id="clips"></div>
</div>

<footer>
<b>Honest limits:</b> AI moments/titles owner ke free Gemini quota par chalte hain —
quota khatam ho to rule-based detection (hamesha free, unlimited) kaam karti rehti hai.
Word-timing SRT se aati hai; plain-text transcript par timing nahi hoti (koi fake timing nahi banai jati).
MP4 render sirf wahan available hai jahan server par ffmpeg ho — warna ASS/SRT download karke CapCut/VN mein 2 tap mein lagao.
Tumhari files server par save nahi hotin, koi training nahi hoti.
Original build — OpusClip se affiliated nahi.
</footer>
</div>

<script>
const $=id=>document.getElementById(id);
let CLIPS=[], VIDURL=null;

function esc(s){return (s||"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
function fmtT(s){if(s==null)return "—";s=Math.max(0,s);const m=Math.floor(s/60),ss=(s%60);return m+":"+ss.toFixed(1).padStart(4,"0")}

async function init(){
  try{
    const r=await fetch("/tukra/api/ai-status");const j=await r.json();
    $("status").innerHTML="AI moments: <b class='"+(j.ai_available?"on":"off")+"'>"+(j.ai_available?"ON (Gemini)":"OFF — rule-based only")+"</b> · MP4 render: <b class='"+(j.ffmpeg_available?"on":"off")+"'>"+(j.ffmpeg_available?"available":"nahi (ASS/SRT use karo)")+"</b> · Auto-transcript: <b class='"+(j.transcribe_available?"on":"off")+"'>"+(j.transcribe_available?"available":"nahi")+"</b>";
  }catch(e){$("status").textContent="status check fail."}
}
init();

$("file").addEventListener("change",e=>{
  const f=e.target.files[0];if(!f)return;
  const r=new FileReader();r.onload=()=>{$("inp").value=r.result};r.readAsText(f);
});
$("vid").addEventListener("change",e=>{
  const f=e.target.files[0];if(!f)return;
  if(VIDURL)URL.revokeObjectURL(VIDURL);
  VIDURL=URL.createObjectURL(f);$("v").src=VIDURL;
  $("pvinfo").textContent="Video load ho gayi (sirf tumhare browser mein). Ab kisi clip par Preview dabao.";
});

$("go").addEventListener("click",async()=>{
  const content=$("inp").value.trim();
  $("err").innerHTML="";$("warns").innerHTML="";
  if(!content){$("err").innerHTML="<div class='err'>Pehle transcript/SRT paste karo ya file chuno.</div>";return}
  $("go").disabled=true;$("go").textContent="Dhoond raha…";
  try{
    const r=await fetch("/tukra/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({content,lang:$("lang").value,use_ai:$("useai").checked,max_clips:+$("maxc").value||8})});
    const j=await r.json();
    if(j.error){$("err").innerHTML="<div class='err'>"+esc(j.error)+"</div>";return}
    (j.warnings||[]).forEach(w=>{$("warns").innerHTML+="<div class='warn'>"+esc(w)+"</div>"});
    CLIPS=j.clips||[];
    $("ocount").textContent="— "+CLIPS.length+" mile ("+(j.timed?"timing ke saath":"sirf text — timing nahi")+", "+(j.ai?"AI":"rule-based")+"), "+(j.stats?.sentences||0)+" sentences";
    $("out").style.display="block";$("preview").style.display="block";
    renderClips();
  }catch(e){$("err").innerHTML="<div class='err'>Request fail: "+esc(e.message)+"</div>"}
  finally{$("go").disabled=false;$("go").textContent="Clips nikalo"}
});

function renderClips(){
  const box=$("clips");box.innerHTML="";
  CLIPS.forEach((c,i)=>{
    const d=document.createElement("div");d.className="clip";d.id="clipbox-"+c.id;
    const chips=(c.breakdown||[]).map(b=>"<span class='chip'><b>+"+b.points+"</b> "+esc(b.reason)+(b.evidence?" <span class='kbd'>"+esc(b.evidence)+"</span>":"")+"</span>").join("");
    d.innerHTML=
      "<div class='chead'><span class='rank'>#"+(i+1)+"</span>"+
      "<span class='ctitle'>"+esc(c.title||c.hook||"Untitled")+"</span>"+
      (c.ai_pick?"<span class='aipick'>AI PICK</span>":"")+
      "<span class='score'>"+c.score+" pts</span></div>"+
      "<div class='hook'>“"+esc(c.hook||"")+"”</div>"+
      "<div class='chips'>"+chips+"</div>"+
      "<div class='timerow'>"+(c.timed?
        "Start <input type='number' step='0.5' min='0' value='"+c.start+"' id='s-"+c.id+"'> End <input type='number' step='0.5' min='0' value='"+c.end+"' id='e-"+c.id+"'> <span id='dur-"+c.id+"'>"+fmtT(c.end-c.start)+"</span> <button class='ghost small' onclick='retime(\""+c.id+"\")'>Apply</button>"
        :"<span class='badge'>timing nahi — SRT do ge to exact cuts milenge</span>")+"</div>"+
      "<div class='actions'>"+
      (c.timed?"<button class='ghost small' onclick='previewClip(\""+c.id+"\")'>▶ Preview</button>":"")+
      (c.timed?"<button class='ghost small' onclick='dlCap(\""+c.id+"\",\"ass\")'>ASS karaoke</button><button class='ghost small' onclick='dlCap(\""+c.id+"\",\"srt\")'>SRT</button><button class='ghost small' onclick='dlCap(\""+c.id+"\",\"vtt\")'>VTT</button>":"")+
      "<button class='ghost small' onclick='copyText(\""+c.id+"\",\"social\")'>Caption copy</button>"+
      "<button class='ghost small' onclick='copyText(\""+c.id+"\",\"ts\")'>Timestamps copy</button>"+
      "</div><pre class='cap' id='cap-"+c.id+"' style='display:none'></pre>";
    box.appendChild(d);
  });
}

function findClip(id){return CLIPS.find(c=>c.id===id)}

function retime(id){
  const c=findClip(id);if(!c||!c.timed)return;
  const ns=+$("s-"+id).value, ne=+$("e-"+id).value;
  if(!(ne>ns)){alert("End, Start se bara hona chahiye.");return}
  const off=ns-c.start;
  c.words=(c.words||[]).map(w=>[w[0],+(w[1]+off).toFixed(2),+(w[2]+off).toFixed(2)]).filter(w=>w[2]>0&&w[1]<(ne-ns));
  c.start=ns;c.end=ne;
  $("dur-"+id).textContent=fmtT(ne-ns);
}

function vttFromClip(c){
  let out="WEBVTT\\n\\n",i=0;
  const W=4;
  for(let k=0;k<c.words.length;k+=W){
    const ch=c.words.slice(k,k+W);
    const t=s=>{s=Math.max(0,s+c.start);const m=Math.floor(s/60);return "00:"+String(m).padStart(2,"0")+":"+(s%60).toFixed(3).padStart(6,"0")};
    out+=t(ch[0][1])+" --> "+t(ch[ch.length-1][2])+"\\n"+ch.map(w=>w[0]).join(" ")+"\\n\\n";
  }
  return out;
}

function previewClip(id){
  const c=findClip(id);if(!c||!c.timed)return;
  const box=$("cap-"+id);
  if(!VIDURL){box.style.display="block";box.textContent="Preview ke liye upar apni video file chuno (browser mein hi chalegi, upload nahi hogi).\\n\\nKaraoke preview (pehle words):\\n"+c.words.slice(0,24).map(w=>w[0]).join(" ")+" …";return}
  const v=$("v");
  const blob=new Blob([vttFromClip(c)],{type:"text/vtt"});
  const old=v.querySelector("track");if(old)old.remove();
  const tr=document.createElement("track");tr.kind="subtitles";tr.label="Tukra";tr.default=true;
  tr.src=URL.createObjectURL(blob);v.appendChild(tr);
  v.currentTime=c.start;v.play().catch(()=>{});
  box.style.display="block";
  box.textContent="▶ "+fmtT(c.start)+" se chal rahi hai — captions video par nazar aayenge.";
  $("preview").scrollIntoView({behavior:"smooth"});
}

async function dlCap(id,format){
  const c=findClip(id);if(!c)return;
  const r=await fetch("/tukra/api/captions",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({clip:c,format})});
  if(!r.ok){const j=await r.json().catch(()=>({}));alert(j.error||"Download fail");return}
  const blob=await r.blob();const a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download="tukra-"+id+"."+format;a.click();
}

function copyText(id,kind){
  const c=findClip(id);if(!c)return;
  let t="";
  if(kind==="social")t=c.social||"";
  else t=(c.timed?fmtT(c.start)+" → "+fmtT(c.end):"")+" | "+(c.title||c.hook||"");
  navigator.clipboard.writeText(t).then(()=>{alert("Copy ho gaya!")}).catch(()=>{prompt("Copy karo:",t)});
}
</script>
</body>
</html>
"""
