ISHTEHAR_HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ishtehar — Free AI Ad-Creative Studio</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:980px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{font-size:26px;margin-bottom:2px} .sub{color:#555;margin-top:0}
.card{border:1px solid #ddd;border-radius:12px;padding:14px;margin:12px 0}
label{display:block;font-weight:600;margin:10px 0 4px}
input[type=text],select,textarea{width:100%;padding:9px;border:1px solid #bbb;border-radius:8px;box-sizing:border-box;font-size:15px}
button{background:#0b6e4f;color:#fff;border:0;border-radius:8px;padding:10px 16px;font-size:15px;cursor:pointer;margin:4px 4px 0 0}
button.ghost{background:#eee;color:#222} button:disabled{opacity:.5}
.variant{border:1px solid #ddd;border-radius:12px;padding:12px;margin:10px 0}
.variant h3{margin:0 0 6px} .score{font-weight:700;color:#0b6e4f}
.flag{color:#a33;background:#fff3f3;border:1px solid #e5b4b4;border-radius:8px;padding:6px 8px;margin:6px 0;font-size:14px}
.field{margin:6px 0} .field b{font-size:13px;color:#444} .field span{font-size:13px;color:#888}
.field p{margin:2px 0;font-size:16px;white-space:pre-wrap}
.muted{color:#666;font-size:14px} .ok{color:#0b6e4f} .bad{color:#a33}
details{margin:8px 0} summary{cursor:pointer;font-weight:600}
.plat{display:inline-block;margin:2px 6px 2px 0}
</style></head><body>
<h1>📣 Ishtehar</h1>
<p class="sub">Free AI ad-creative studio — no account, no card, no credits, unlimited brands.
Write one brief, get platform-correct ad variants for Meta, Google, LinkedIn and WhatsApp,
with a transparent score and a compliance check before anything ships.</p>
<p class="muted">Honest scope: Ishtehar writes ad copy and creative briefs. It does not run campaigns,
manage bids, or track ROAS — that layer still needs a human or an agency. Not affiliated
with AdCreative.ai or any other ad tool.</p>

<div class="card">
<h2 style="margin-top:0">1 · Your brief</h2>
<label>Brand profile (saved in your browser only)
<select id="brandSel"><option value="">— New brand —</option></select>
<button class="ghost" onclick="saveBrand()">💾 Save brand</button>
<button class="ghost" onclick="delBrand()">🗑 Delete</button></label>
<label>Brand / product *<input type="text" id="product" placeholder="e.g. Herbal Hair Oil"></label>
<label>Main benefit *<input type="text" id="benefit" placeholder="e.g. stops hair fall in 4 weeks"></label>
<label>Audience *<input type="text" id="audience" placeholder="e.g. women 25–45 in Lahore"></label>
<label>Offer (optional)<input type="text" id="offer" placeholder="e.g. 20% off + free delivery this week"></label>
<label>Call to action<input type="text" id="cta" placeholder="e.g. Order on WhatsApp now"></label>
<label>Language
<select id="lang"><option value="en">English</option><option value="ru">Roman-Urdu</option></select></label>
<label>Platforms</label>
<span class="plat"><input type="checkbox" class="plat" value="meta" checked> Meta</span>
<span class="plat"><input type="checkbox" class="plat" value="google" checked> Google</span>
<span class="plat"><input type="checkbox" class="plat" value="linkedin" checked> LinkedIn</span>
<span class="plat"><input type="checkbox" class="plat" value="whatsapp" checked> WhatsApp</span>
<br><br>
<button onclick="build(0)">✨ Generate ad variants</button>
<button class="ghost" onclick="build((window._seed||0)+1)">🔀 Shuffle angles</button>
<button class="ghost" onclick="downloadCsv()">⬇ CSV export</button>
<button class="ghost" onclick="window.print()">🖨 Print</button>
<span id="aiBadge" class="muted"></span>
</div>

<div id="summary"></div>
<div id="results"></div>

<script>
const $=id=>document.getElementById(id);
let lastReq=null, aiOK=false;
fetch('/ishtehar/api/ai-status').then(r=>r.json()).then(d=>{
  aiOK=d.ai_available;
  $('aiBadge').textContent = aiOK ? ' · AI rewrite available ✓' : ' · AI rewrite off (no key — rule engine works fully)';
});
function brands(){ try{return JSON.parse(localStorage.getItem('ishtehar_brands')||'{}')}catch(e){return{}} }
function refreshBrands(){
  const b=brands(), sel=$('brandSel');
  sel.innerHTML='<option value="">— New brand —</option>'+Object.keys(b).map(k=>`<option>${k}</option>`).join('');
}
function saveBrand(){
  const name=$('product').value.trim(); if(!name) return alert('Brand / product likhain pehle.');
  const b=brands();
  b[name]={product:$('product').value,benefit:$('benefit').value,audience:$('audience').value,offer:$('offer').value,cta:$('cta').value,lang:$('lang').value};
  localStorage.setItem('ishtehar_brands',JSON.stringify(b)); refreshBrands(); alert('Brand saved: '+name);
}
function delBrand(){
  const name=$('brandSel').value; if(!name) return;
  const b=brands(); delete b[name]; localStorage.setItem('ishtehar_brands',JSON.stringify(b)); refreshBrands();
}
$('brandSel').onchange=()=>{
  const b=brands()[$('brandSel').value]; if(!b) return;
  $('product').value=b.product||''; $('benefit').value=b.benefit||''; $('audience').value=b.audience||'';
  $('offer').value=b.offer||''; $('cta').value=b.cta||''; $('lang').value=b.lang||'en';
};
refreshBrands();
function req(){
  return {product:$('product').value,benefit:$('benefit').value,audience:$('audience').value,
    offer:$('offer').value,cta:$('cta').value,lang:$('lang').value,
    platforms:[...document.querySelectorAll('.plat:checked')].map(c=>c.value),seed:window._seed||0};
}
async function build(seed){
  if(seed!==undefined) window._seed=seed;
  const r=req(); lastReq=r;
  if(!r.product.trim()||!r.benefit.trim()||!r.audience.trim()) return alert('Product, benefit aur audience zaroori hain.');
  $('results').innerHTML='<p class="muted">Generating…</p>';
  const res=await fetch('/ishtehar/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});
  const d=await res.json();
  const s=d.summary;
  $('summary').innerHTML='<div class="card"><b>Summary:</b> '+Object.entries(s).map(([k,v])=>
    `${k}: ${v.count} variants · best ${v.best}/100`+(v.flagged?` · <span class="bad">${v.flagged} flagged</span>`:'')).join(' &nbsp;|&nbsp; ')+'</div>';
  $('results').innerHTML=d.variants.map((v,i)=>{
    const fields=Object.entries(v.fields).map(([k,t])=>
      `<div class="field"><b>${k}</b> <span>(${t.length}/${v.limits[k]} chars)</span><p>${esc(t)}</p></div>`).join('');
    const flags=v.flags.map(f=>`<div class="flag">⚠ ${esc(f.message)}</div>`).join('');
    const scoreParts=Object.entries(v.score).filter(([k])=>k!=='total').map(([k,val])=>`${k}: ${val}`).join(' · ');
    return `<div class="variant"><h3>${esc(v.platform_label)} — ${esc(v.angle_label)}
      <span class="score">${v.score.total}/100</span></h3>${fields}${flags}
      <details><summary>Score breakdown</summary><p class="muted">${esc(scoreParts)}</p></details>
      ${v.truncated?'<p class="bad">Note: text was trimmed to fit the platform limit.</p>':''}
      <button class="ghost" onclick="copyVariant(${i})">📋 Copy all fields</button>
      ${aiOK?`<button class="ghost" onclick="aiRewrite(${i})">✨ AI rewrite</button>`:''}</div>`;
  }).join('');
  window._variants=d.variants;
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')}
function copyVariant(i){
  const v=window._variants[i];
  const txt=Object.entries(v.fields).map(([k,t])=>k.toUpperCase()+': '+t).join('\n');
  navigator.clipboard.writeText(txt).then(()=>alert('Copied!'));
}
async function aiRewrite(i){
  const v=window._variants[i];
  const res=await fetch('/ishtehar/api/ai-rewrite',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({fields:v.fields,platform_label:v.platform_label,lang:lastReq.lang})});
  const d=await res.json();
  if(d.error) return alert('AI error: '+d.error);
  v.fields=d.fields;
  // re-render only this variant's fields
  const card=document.querySelectorAll('.variant')[i];
  card.querySelectorAll('.field p').forEach((p,j)=>{ p.textContent=Object.values(d.fields)[j]; });
  alert('AI rewrite applied (limits still enforced by the platform table).');
}
async function downloadCsv(){
  const r=req(); if(!r.product.trim()) return alert('Brief likhain pehle.');
  const res=await fetch('/ishtehar/api/download-csv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(r)});
  const blob=await res.blob(); const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='ishtehar-ads.csv'; a.click();
}
</script></body></html>
"""
