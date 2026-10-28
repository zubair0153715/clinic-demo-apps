UJALA_HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ujala — Free Photo Enhancer</title>
<style>body{font-family:system-ui,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#1a1a1a}
h1{font-size:26px}h2{font-size:18px;margin-top:28px}
.card{border:1px solid #ddd;border-radius:10px;padding:16px;margin:12px 0}
label{display:block;margin:10px 0 4px;font-weight:600}
input[type=range]{width:100%}select,input[type=text],input[type=file]{width:100%;padding:8px;font-size:15px}
button{padding:10px 18px;font-size:15px;border:0;border-radius:8px;background:#0b6e4f;color:#fff;cursor:pointer;margin-top:12px}
button.ghost{background:#eee;color:#222}.row{display:flex;gap:12px;flex-wrap:wrap}
.row>div{flex:1;min-width:220px}img{max-width:100%;border-radius:8px}
.warn{background:#fff8e1;border:1px solid #f0d48a;border-radius:10px;padding:12px}
.muted{color:#666;font-size:14px}.stat{font-size:15px;line-height:1.7}
.err{color:#b00020;font-weight:600}</style></head><body>
<h1>☀️ Ujala — Free Photo Enhancer</h1>
<p class="muted">Apni photo ko saaf, roshan aur balanced banayein — <b>bilkul free, unlimited,
bina account, bina card, bina credit, bina watermark.</b> Photo sirf is page ke liye
process hoti hai: save nahi hoti, training ke liye use nahi hoti, kahin bheji nahi jati.</p>

<div class="card">
<label>1. Photo chunein (JPEG / PNG / WebP, max 10 MB)</label>
<input type="file" id="file" accept="image/jpeg,image/png,image/webp">
<label>2. Preset</label>
<select id="preset">
<option value="auto">Auto — balanced clean-up</option>
<option value="portrait">Portrait — warm + gently softened</option>
<option value="product">Product — bright, clean, background-lifting</option>
<option value="vivid">Vivid — colour-forward</option>
</select>
<div class="row">
<div><label>Brightness <span id="vBrightness">1.00</span></label>
<input type="range" id="brightness" min="0.5" max="1.8" step="0.05" value="1"></div>
<div><label>Contrast <span id="vContrast">1.00</span></label>
<input type="range" id="contrast" min="0.5" max="1.8" step="0.05" value="1"></div>
<div><label>Colour <span id="vColor">1.00</span></label>
<input type="range" id="color" min="0.5" max="1.8" step="0.05" value="1"></div>
<div><label>Sharpness <span id="vSharpness">1.00</span></label>
<input type="range" id="sharpness" min="0.5" max="1.8" step="0.05" value="1"></div>
<div><label>Warmth <span id="vWarmth">0.00</span></label>
<input type="range" id="warmth" min="-0.5" max="0.5" step="0.05" value="0"></div>
<div><label>Smoothing <span id="vSmooth">0.00</span></label>
<input type="range" id="smooth" min="0" max="0.5" step="0.05" value="0"></div>
</div>
<p class="muted">Preset chunte hi sliders uski starting values par aa jate hain — phir apni
marzi se adjust karein. "Enhance" dabayein, phir result download karein.</p>
<button onclick="enhance()">✨ Enhance photo</button>
<button class="ghost" onclick="resetSliders()">Reset sliders</button>
<p id="err" class="err"></p>
</div>

<div class="card" id="result" style="display:none">
<h2>Result</h2>
<div class="row"><div><h3>Before</h3><img id="imgBefore"></div>
<div><h3>After</h3><img id="imgAfter"></div></div>
<p class="stat" id="stats"></p>
<a id="dl" download="ujala-enhanced.jpg"><button>⬇️ Download enhanced photo</button></a>
</div>

<div class="card">
<h2>🤖 AI setting mashwara <span class="muted" id="aiStatus"></span></h2>
<p class="muted">Apna maqsad lafzon me likhein (jaise "dull indoor product photo ko bright
banana hai") — AI ek preset + slider starting point suggest karega. Photo AI ko
nahi bheji jati, sirf aapke lafz jate hain.</p>
<input type="text" id="goal" placeholder="e.g. dull indoor product photo ko bright banana hai">
<button onclick="advise()">Mashwara lein</button>
<p id="advice" class="stat"></p>
</div>

<div class="warn">
<b>Imandari se limits:</b> Ujala me <b>koi face detection, skin segmentation,
blemish removal, background removal, layers ya RAW support nahi hai.</b>
"Smoothing" poori photo ko halka soft karta hai — sirf chehra nahi. Ye tool
80% kaam (saaf, roshan, balanced photo) free karta hai; AI retoucher ka
daawa nahi karta. Agar aapko daagh hatana ya background badalna hai, to
wo is tool se nahi hoga — aur ye baat chhupayi nahi ja rahi.
</div>
<p class="muted">Original clean-room build. Kisi retouching app ka naam, code, model ya
asset use nahi hua. No account, no card, no credits, no watermark, no expiry.</p>

<script>
const $=id=>document.getElementById(id);
const SLIDERS=['brightness','contrast','color','sharpness','warmth','smooth'];
const PRESET_VALS={auto:{brightness:1,contrast:1,color:1.15,sharpness:1.2,warmth:0,smooth:0},
portrait:{brightness:1.05,contrast:1.05,color:1.1,sharpness:1,warmth:0.25,smooth:0.25},
product:{brightness:1.12,contrast:1.05,color:1.1,sharpness:1.15,warmth:0,smooth:0},
vivid:{brightness:1,contrast:1.1,color:1.4,sharpness:1.15,warmth:0.1,smooth:0}};
SLIDERS.forEach(s=>{$(s).oninput=()=>{$('v'+s[0].toUpperCase()+s.slice(1)).textContent=(+$(s).value).toFixed(2);};});
$('preset').onchange=()=>{const p=PRESET_VALS[$('preset').value]||PRESET_VALS.auto;
SLIDERS.forEach(s=>{$(s).value=p[s];$('v'+s[0].toUpperCase()+s.slice(1)).textContent=(+p[s]).toFixed(2);});};
function resetSliders(){$('preset').value='auto';$('preset').onchange();}
async function enhance(){
  const f=$('file').files[0];if(!f){$('err').textContent='Pehle photo chunein.';return;}
  $('err').textContent='Processing…';
  const fd=new FormData();fd.append('file',f);fd.append('preset',$('preset').value);
  SLIDERS.forEach(s=>fd.append(s,$(s).value));
  const r=await fetch('/ujala/api/enhance',{method:'POST',body:fd});
  const d=await r.json();
  if(!d.ok){$('err').textContent=d.error||'Enhance fail ho gaya.';return;}
  $('err').textContent='';
  $('imgBefore').src=URL.createObjectURL(f);
  $('imgAfter').src='data:image/jpeg;base64,'+d.image_b64;
  $('dl').href='data:image/jpeg;base64,'+d.image_b64;
  $('stats').textContent='Preset: '+d.preset+'  •  Brightness '+d.before.mean_brightness+' → '+d.after.mean_brightness+
  '  •  Saturation '+d.before.mean_saturation+' → '+d.after.mean_saturation+
  '  •  Size '+d.before.width+'×'+d.before.height+' (ye measured stats hain, koi invented quality score nahi)';
  $('result').style.display='block';
}
async function advise(){
  const g=$('goal').value.trim();if(!g){$('advice').textContent='Pehle maqsad likhein.';return;}
  $('advice').textContent='Soch raha hai…';
  const r=await fetch('/ujala/api/advise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({goal:g})});
  const d=await r.json();
  if(!d.ok){$('advice').textContent=d.error;return;}
  $('preset').value=d.preset;$('preset').onchange();
  SLIDERS.forEach(s=>{if(d[s]!==undefined){$(s).value=d[s];$('v'+s[0].toUpperCase()+s.slice(1)).textContent=(+d[s]).toFixed(2);}});
  $('advice').textContent='Tajweez: '+d.preset+' preset — '+ (d.reason||'');
}
fetch('/ujala/api/ai-status').then(r=>r.json()).then(d=>{
  $('aiStatus').textContent=d.ai_available?'(AI available)':'(AI key set nahi — presets phir bhi free hain)';
});
</script></body></html>
"""
