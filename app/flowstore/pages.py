"""FlowStore HTML pages — mobile-friendly, inline CSS, no external deps."""
import html
import json

from .products import PRODUCTS, CUSTOM, SYSTEM_OPTIONS, STATUS_LABELS, STATUS_ORDER

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;background:#0f172a;color:#e2e8f0;line-height:1.6}
.wrap{max-width:720px;margin:0 auto;padding:20px 16px 60px}
.hero{text-align:center;padding:36px 12px 24px}
.hero h1{font-size:30px;color:#fff}
.hero h1 .flow{color:#38bdf8}
.hero p{color:#94a3b8;margin-top:8px;font-size:15px}
.card{background:#1e293b;border:1px solid #334155;border-radius:14px;padding:20px;margin:14px 0}
.card h2{color:#fff;font-size:19px;margin-bottom:4px}
.card .tag{color:#38bdf8;font-size:14px;font-weight:600}
.card p{color:#cbd5e1;font-size:14px;margin:8px 0}
.card .for{color:#94a3b8;font-size:13px}
.price{margin:10px 0;font-size:15px}
.price b{color:#4ade80;font-size:20px}
.price span{color:#94a3b8;font-size:13px}
.btn{display:inline-block;background:#0284c7;color:#fff;padding:12px 26px;border-radius:10px;text-decoration:none;font-weight:700;font-size:16px;border:0;cursor:pointer;margin-top:10px}
.btn:hover{background:#0369a1}
.btn.ghost{background:transparent;border:1px solid #38bdf8;color:#38bdf8}
.btn.small{padding:8px 16px;font-size:14px}
.demo{display:inline-block;margin-left:10px;color:#38bdf8;font-size:14px}
label{display:block;color:#cbd5e1;font-size:14px;margin:12px 0 4px;font-weight:600}
input[type=text],input[type=email],input[type=url],input[type=password],textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #334155;background:#0f172a;color:#fff;font-size:15px}
textarea{min-height:110px;resize:vertical}
.checks label{display:flex;align-items:center;gap:10px;font-weight:400;margin:8px 0;cursor:pointer}
.checks input{width:18px;height:18px;accent-color:#0284c7}
.token{background:#0f172a;border:1px dashed #38bdf8;border-radius:10px;padding:14px;text-align:center;font-size:20px;letter-spacing:2px;color:#38bdf8;font-weight:700;margin:14px 0}
.timeline{margin:18px 0}
.step{display:flex;gap:12px;margin:12px 0;align-items:flex-start}
.dot{width:28px;height:28px;border-radius:50%;background:#334155;color:#94a3b8;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}
.step.done .dot{background:#16a34a;color:#fff}
.step.now .dot{background:#0284c7;color:#fff;box-shadow:0 0 0 4px rgba(2,132,199,.25)}
.step .t b{color:#fff;font-size:15px}
.step .t span{display:block;color:#94a3b8;font-size:13px}
.note{background:#1e293b;border-left:3px solid #f59e0b;padding:12px 14px;border-radius:0 10px 10px 0;margin:14px 0;font-size:14px;color:#cbd5e1}
.ok{background:#1e293b;border-left:3px solid #16a34a;padding:12px 14px;border-radius:0 10px 10px 0;margin:14px 0;font-size:14px;color:#cbd5e1}
.err{background:#1e293b;border-left:3px solid #ef4444;padding:12px 14px;border-radius:0 10px 10px 0;margin:14px 0;font-size:14px;color:#fca5a5}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid #334155;color:#cbd5e1}
th{color:#94a3b8;font-size:12px;text-transform:uppercase}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:700;background:#334155;color:#e2e8f0}
.badge.live{background:#16a34a;color:#fff}
.badge.ready{background:#0284c7;color:#fff}
.footer{text-align:center;color:#64748b;font-size:12px;margin-top:40px}
a{color:#38bdf8}
ol.steps{margin:10px 0 10px 20px;color:#cbd5e1;font-size:14px}
ol.steps li{margin:6px 0}
code{background:#0f172a;padding:2px 6px;border-radius:6px;font-size:13px;color:#fbbf24}
"""


def layout(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — FlowStore</title>
<style>{CSS}</style></head><body><div class="wrap">{body}
<div class="footer">FlowStore · WhatsApp automations for Gulf businesses</div>
</div></body></html>"""


def storefront() -> str:
    cards = []
    for p in PRODUCTS:
        demo = (f'<a class="demo" href="{html.escape(p["demo"])}" target="_blank">'
                f'{html.escape(p["demo_label"])} →</a>' if p["demo"] else "")
        cards.append(f"""
<div class="card">
  <div class="tag">{html.escape(p["tagline"])}</div>
  <h2>{html.escape(p["name"])}</h2>
  <p>{html.escape(p["desc"])}</p>
  <div class="for">Best for: {html.escape(p["for_who"])}</div>
  <div class="price"><b>${p["setup"]}</b> <span>one-time pilot setup</span>
   + <b>${p["monthly"]}</b><span>/month</span></div>
  <a class="btn" href="/flowstore/order/{p["slug"]}">Order Now</a>{demo}
</div>""")
    cards.append(f"""
<div class="card" style="border-color:#38bdf8">
  <div class="tag">{html.escape(CUSTOM["tagline"])}</div>
  <h2>{html.escape(CUSTOM["name"])}</h2>
  <p>{html.escape(CUSTOM["desc"])}</p>
  <div class="for">Best for: {html.escape(CUSTOM["for_who"])}</div>
  <div class="price"><b>from ${CUSTOM["setup"]}</b> <span>setup</span></div>
  <a class="btn ghost" href="/flowstore/order/custom">Describe Your System</a>
</div>""")
    body = f"""
<div class="hero"><h1><span class="flow">Flow</span>Store</h1>
<p>Done-for-you WhatsApp automations for Gulf businesses.<br>
Pick one, tell us about your business, we build it on <b>your</b> n8n — you own everything.</p></div>
{''.join(cards)}
<div class="note"><b>How it works:</b> ① Order below ② We build & customize within 48 hours
③ You connect your own n8n (free trial) ④ We deploy — it runs on <b>your</b> account, your credits, your data.</div>
"""
    return layout("Automation Store", body)


def order_form(slug: str, product: dict) -> str:
    checks = "".join(
        f'<label><input type="checkbox" name="systems" value="{html.escape(s)}"> {html.escape(s)}</label>'
        for s in SYSTEM_OPTIONS)
    body = f"""
<div class="hero" style="padding-bottom:8px"><h1 style="font-size:24px">Order: {html.escape(product["name"])}</h1>
<p>{html.escape(product["tagline"])}</p>
<div class="price"><b>${product["setup"]}</b> <span>one-time pilot setup</span> + <b>${product["monthly"]}</b><span>/month</span></div></div>
<div class="card">
<form method="post" action="/flowstore/order">
<input type="hidden" name="product" value="{html.escape(slug)}">
<label>Your name *</label><input type="text" name="name" required>
<label>Business name *</label><input type="text" name="business" required>
<label>Email *</label><input type="email" name="email" required>
<label>WhatsApp number *</label><input type="text" name="whatsapp" placeholder="+971 ..." required>
<label>Which systems do you use?</label><div class="checks">{checks}</div>
<label>Tell us about your system / what you want automated</label>
<textarea name="notes" placeholder="e.g. Customers message us on WhatsApp about prices, we reply manually, we miss half of them after 6pm..."></textarea>
<button class="btn" type="submit">Place Order</button>
</form></div>
<div class="note">No payment now — we confirm on WhatsApp first, then build. Custom orders are
tailored to your business within 48 hours.</div>
"""
    return layout(f"Order {product['name']}", body)


def confirmation(order: dict, whatsapp_link: str) -> str:
    wa = (f'<a class="btn" href="{html.escape(whatsapp_link)}" target="_blank">Confirm on WhatsApp</a>'
          if whatsapp_link else "")
    body = f"""
<div class="hero"><h1 style="font-size:26px">Order received ✅</h1>
<p>We'll message you on WhatsApp within a few hours to confirm details.</p></div>
<div class="card">
<div class="tag">Your order token — keep it safe</div>
<div class="token">{html.escape(order["token"])}</div>
<p style="font-size:14px;color:#94a3b8">Track your automation here:</p>
<p><a href="/flowstore/track/{html.escape(order["token"])}">flowstore/track/{html.escape(order["token"])}</a></p>
{wa}
</div>
"""
    return layout("Order confirmed", body)


def track_page(order: dict) -> str:
    idx = STATUS_ORDER.index(order["status"]) if order["status"] in STATUS_ORDER else 0
    steps = []
    descs = {
        "received": "We've got your order and will confirm on WhatsApp.",
        "building": "We're building and customizing your automation (within 48h).",
        "ready": "Built! Connect your own n8n account so we can deploy it for you.",
        "connected": "Your n8n is connected — deploying your workflow now.",
        "live": "Your automation is live and running on your n8n. 🎉",
    }
    for i, s in enumerate(STATUS_ORDER):
        cls = "done" if i < idx else ("now" if i == idx else "")
        num = "✓" if i < idx else str(i + 1)
        steps.append(f'<div class="step {cls}"><div class="dot">{num}</div>'
                     f'<div class="t"><b>{STATUS_LABELS[s]}</b><span>{descs[s]}</span></div></div>')
    cta = ""
    if order["status"] == "ready":
        cta = (f'<a class="btn" href="/flowstore/connect/{html.escape(order["token"])}">'
               f'Connect your n8n →</a>')
    body = f"""
<div class="hero" style="padding-bottom:8px"><h1 style="font-size:24px">Order status</h1>
<p>{html.escape(order["business"])} · <span class="badge {order["status"]}">{STATUS_LABELS.get(order["status"], order["status"])}</span></p></div>
<div class="card"><div class="timeline">{''.join(steps)}</div>{cta}</div>
"""
    return layout("Track order", body)


def connect_page(order: dict) -> str:
    body = f"""
<div class="hero" style="padding-bottom:8px"><h1 style="font-size:24px">Connect your n8n</h1>
<p>Your automation runs on <b>your</b> n8n — your account, your credits, your data.</p></div>
<div class="card">
<ol class="steps">
<li>Open <a href="https://app.n8n.cloud" target="_blank">app.n8n.cloud</a> and start the <b>free 14-day trial</b> (no card needed).</li>
<li>In n8n go to <b>Settings → n8n API</b> and create an API key.</li>
<li>Paste your instance URL and API key below.</li>
</ol>
<div class="note">Your key is used <b>only</b> to deploy this workflow to your n8n.
It is never logged, never shown to anyone, and never used for anything else.</div>
<form method="post" action="/flowstore/connect/{html.escape(order["token"])}">
<label>Your n8n instance URL *</label>
<input type="url" name="n8n_url" placeholder="https://yourname.app.n8n.cloud" required>
<label>Your n8n API key *</label>
<input type="password" name="n8n_key" required>
<button class="btn" type="submit">Connect & Deploy</button>
</form></div>
"""
    return layout("Connect n8n", body)


def deploy_result_page(order: dict, ok: bool, detail: str) -> str:
    if ok:
        body = f"""
<div class="hero"><h1 style="font-size:26px">You're live 🎉</h1>
<p>Your automation was deployed to your n8n and is ready to activate.</p></div>
<div class="ok"><b>Workflow ID:</b> <code>{html.escape(detail)}</code><br>
Open your n8n → Workflows → find <b>{html.escape(order["product"])}</b> →
add your WhatsApp / Calendar credentials → toggle <b>Active</b>.</div>
<a class="btn" href="/flowstore/track/{html.escape(order["token"])}">View status</a>
"""
    else:
        body = f"""
<div class="hero"><h1 style="font-size:24px">Auto-deploy didn't go through</h1>
<p>No worries — 1-click manual import takes 30 seconds:</p></div>
<div class="card">
<ol class="steps">
<li>Download your workflow file: <a class="btn small" href="/flowstore/workflow/{html.escape(order["token"])}/download">Download JSON</a></li>
<li>Open your n8n → Workflows → <b>⋯ → Import from File</b></li>
<li>Choose the downloaded file → it appears, inactive</li>
<li>Add your WhatsApp / Calendar credentials → toggle <b>Active</b></li>
</ol>
<div class="err"><b>Why it failed:</b> {html.escape(detail)}</div>
<div class="note">Tell us on WhatsApp and we'll deploy it for you manually.</div>
</div>
<a class="btn ghost" href="/flowstore/connect/{html.escape(order["token"])}">Try auto-deploy again</a>
"""
    return layout("Deployment", body)


def admin_login_page() -> str:
    return layout("Admin", """
<div class="hero"><h1 style="font-size:24px">FlowStore Admin</h1></div>
<div class="card">
<label>Admin key</label><input type="password" id="k">
<button class="btn" onclick="load()">Open</button>
<div id="out" style="margin-top:16px"></div></div>
<script>
const el=id=>document.getElementById(id);
async function api(p,m,b){const r=await fetch(p,{method:m||'GET',
 headers:{'X-Admin-Key':el('k').value,'Content-Type':'application/json'},
 body:b?JSON.stringify(b):undefined});return r.json()}
async function load(){
 const d=await api('/flowstore/api/admin/orders');
 if(d.error){el('out').innerHTML='<div class="err">'+d.error+'</div>';return}
 let h='<table><tr><th>ID</th><th>Business</th><th>Product</th><th>Status</th><th></th></tr>';
 for(const o of d.orders){
  h+='<tr><td>'+o.id+'</td><td>'+esc(o.business)+'<br><span style="color:#64748b">'+esc(o.name)+' · '+esc(o.email)+'</span></td><td>'+esc(o.product)+'</td><td><span class="badge '+o.status+'">'+o.status+'</span></td><td><button class="btn small" onclick="detail('+o.id+')">View</button></td></tr>'}
 el('out').innerHTML=h+'</table>'}
function esc(s){return String(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function detail(id){
 const o=await api('/flowstore/api/admin/orders/'+id);
 if(o.error){alert(o.error);return}
 const sys=JSON.parse(o.systems||'[]').join(', ');
 el('out').innerHTML='<div class="card"><h2>'+esc(o.business)+'</h2>'
 +'<p>Name: '+esc(o.name)+'<br>Email: '+esc(o.email)+'<br>WhatsApp: '+esc(o.whatsapp)
 +'<br>Systems: '+esc(sys)+'<br>Notes: '+esc(o.notes)+'<br>Token: <code>'+esc(o.token)+'</code>'
 +'<br>n8n: '+esc(o.n8n_url||'-')+'</p>'
 +'<label>Set status</label><div>'
 +['received','building','ready','connected','live'].map(s=>'<button class="btn small" style="margin:4px" onclick="setStatus('+o.id+',\\''+s+'\\')">'+s+'</button>').join('')
 +'</div><br><button class="btn small ghost" onclick="load()">← back</button></div>'}
async function setStatus(id,s){await api('/flowstore/api/admin/orders/'+id+'/status','POST',{status:s});detail(id)}
</script>
""")


def not_found(msg: str) -> str:
    return layout("Not found", f'<div class="hero"><h1>😕</h1><p>{html.escape(msg)}</p>'
                               f'<a class="btn" href="/flowstore">Back to store</a></div>')
