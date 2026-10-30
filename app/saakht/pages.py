"""Saakht page — single-page business-website builder UI (original design)."""

SAAKHT_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saakht — Free Business Website Builder</title>
<style>
body{font-family:system-ui,sans-serif;max-width:760px;margin:0 auto;padding:16px;color:#1a1a1a}
h1{margin-bottom:2px} .sub{color:#555;margin-top:0}
input,textarea,select{width:100%;padding:8px;margin:4px 0 12px;border:1px solid #bbb;border-radius:6px;box-sizing:border-box;font-size:15px}
textarea{min-height:80px} button{padding:10px 18px;border:0;border-radius:6px;background:#0b6e4f;color:#fff;font-size:16px;cursor:pointer}
button.sec{background:#eee;color:#111} .card{border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
.small{color:#555;font-size:13px} table{border-collapse:collapse;width:100%}td{border-bottom:1px solid #eee;padding:6px;vertical-align:top}
iframe{width:100%;height:560px;border:1px solid #999;border-radius:8px}
</style></head><body>
<h1>Saakht — Free Business Website Builder</h1>
<p class="sub">A complete one-page website for your business in under a minute.
No account, no card, no subscription — and you download the file and keep it.</p>
<p class="small"><b>Honest limits, stated plainly:</b> this builds a single-page
brochure site only — no hosting, no domain, no checkout or online store, no
backend, no stock photos (the hero is a colour gradient). The copy is YOUR
facts: Saakht never invents services, prices or claims. Host the downloaded
.html file anywhere free (e.g. GitHub Pages) or hand it to any web host.</p>
<form id="f">
<label>Business name <input name="name" placeholder="Dental Consultants Clinic"></label>
<label>Business type <select name="btype">
<option value="clinic">Clinic</option><option value="dental" selected>Dental clinic</option>
<option value="pharmacy">Pharmacy</option><option value="restaurant">Restaurant</option>
<option value="salon">Salon / barber</option><option value="retail">Store / retail</option>
<option value="realestate">Real estate agency</option><option value="academy">Academy / coaching</option>
<option value="repair">Repair service</option><option value="gym">Gym / fitness</option>
<option value="bakery">Bakery</option><option value="consultancy">Consultancy</option>
<option value="other">Other business</option></select></label>
<label>City <input name="city" placeholder="Larkana"></label>
<label>Phone / WhatsApp number <input name="phone" placeholder="03XX XXXXXXX"></label>
<label>Address (optional) <input name="address" placeholder="Station Road, Larkana"></label>
<label>Tagline (leave blank for a default) <input name="tagline" placeholder="Gentle, affordable dental care for the whole family"></label>
<label>About your business (leave blank for a default) <textarea name="about" placeholder="2-3 lines: what you do, who you serve, what makes you different."></textarea></label>
<label>Services — one per line, "Name — description" or just "Name" (max 12; leave blank for defaults) <textarea name="services" placeholder="Root Canal Treatment — painless, single-visit where possible&#10;Teeth Whitening&#10;Braces — for teens and adults"></textarea></label>
<label>Opening hours — one line each (optional) <textarea name="hours" placeholder="Mon – Sat: 10am – 9pm&#10;Sunday: closed"></textarea></label>
<label>Colour theme <select name="theme">
<option value="teal" selected>Teal</option><option value="navy">Navy</option>
<option value="maroon">Maroon</option><option value="forest">Forest</option>
<option value="plum">Plum</option><option value="charcoal">Charcoal + gold</option></select></label>
<label>Language <select name="language">
<option value="en" selected>English</option><option value="roman">Roman-Urdu</option>
<option value="ur">Urdu (script, RTL)</option></select></label>
<button type="submit">Build my website</button>
<button type="button" class="sec" id="aiBtn">AI-polish my tagline + about (optional)</button>
<span id="aiState" class="small"></span>
</form>
<div id="out"></div>
<script>
const $=s=>document.querySelector(s);
fetch('/saakht/api/ai-status').then(r=>r.json()).then(d=>{
  $('#aiState').textContent = d.ai_available ? 'AI available' : 'AI not set up here — the builder still works fully.';
});
$('#aiBtn').onclick=async()=>{
  const fd=new FormData($('#f'));
  const r=await fetch('/saakht/api/ai-polish',{method:'POST',body:new URLSearchParams({tagline:fd.get('tagline'),about:fd.get('about')})});
  const d=await r.json();
  if(d.ok){ alert('Polished copy (check every line before using it):\\n\\n'+d.polished); }
  else alert(d.error||'AI failed');
};
$('#f').onsubmit=async(e)=>{
  e.preventDefault();
  const r=await fetch('/saakht/api/build',{method:'POST',body:new FormData($('#f'))});
  const d=await r.json();
  if(!d.ok){ alert(d.error); return; }
  const rows=Object.entries(d.seo_breakdown).map(([k,v])=>'<tr><td>'+k+'</td><td>'+v+'</td></tr>').join('');
  window._site=d.html;
  $('#out').innerHTML=
   '<div class="card"><h2>SEO score: '+d.seo_score+'/100</h2><table>'+rows+'</table>'
   +'<p class="small">Title: '+d.title.replace(/</g,'&lt;')+'<br>Meta description ('+d.description.length+' chars): '+d.description.replace(/</g,'&lt;')+'</p>'
   +'<p class="small">Services: '+d.service_count+(d.whatsapp_url ? ' &middot; WhatsApp: '+d.whatsapp_url : '')+'</p>'
   +'<p><button type="button" id="dlBtn">Download website (.html)</button> '
   +'<button type="button" class="sec" id="cpBtn">Copy HTML</button></p></div>'
   +'<div class="card"><h3>Preview</h3><iframe id="prev"></iframe></div>';
  $('#prev').srcdoc=d.html;
  $('#dlBtn').onclick=()=>{ const b=new Blob([window._site],{type:'text/html'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download='my-website.html'; a.click(); };
  $('#cpBtn').onclick=()=>{ navigator.clipboard.writeText(window._site).then(()=>alert('HTML copied.')); };
};
</script></body></html>"""
