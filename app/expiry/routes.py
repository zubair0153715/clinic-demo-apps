"""ExpiryGuard: medicine-expiry tracker for pharmacies.

v1: single-pharmacy, no auth. WhatsApp/SMS alerts are the planned next step
(pending the owner's Meta WhatsApp API setup).
"""
import html as _html
import logging
from datetime import date, datetime

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional

from . import db

log = logging.getLogger("expiry.routes")
router = APIRouter(prefix="/expiry")

BRAND = "ExpiryGuard"
TAGLINE = "Never lose money to expired stock again"


def days_left(expiry: str) -> Optional[int]:
    try:
        d = datetime.strptime(expiry, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return (d - date.today()).days


def bucket(days: Optional[int]) -> str:
    if days is None:
        return "unknown"
    if days < 0:
        return "expired"
    if days <= 30:
        return "soon30"
    if days <= 90:
        return "soon90"
    return "ok"


BUCKET_LABEL = {
    "expired": "EXPIRED",
    "soon30": "≤ 30 days",
    "soon90": "31–90 days",
    "ok": "OK",
    "unknown": "?",
}
BUCKET_CLASS = {
    "expired": "b-exp",
    "soon30": "b-30",
    "soon90": "b-90",
    "ok": "b-ok",
    "unknown": "b-ok",
}


def load_items(search: str = ""):
    if search:
        rows = db.qall(
            "SELECT * FROM items WHERE name LIKE ? OR batch LIKE ? ORDER BY expiry ASC",
            (f"%{search}%", f"%{search}%"),
        )
    else:
        rows = db.qall("SELECT * FROM items ORDER BY expiry ASC")
    items = []
    for r in rows:
        d = dict(r)
        dl = days_left(d["expiry"])
        d["days"] = dl
        d["bucket"] = bucket(dl)
        items.append(d)
    # urgency first: expired, soon30, soon90, ok
    order = {"expired": 0, "soon30": 1, "soon90": 2, "ok": 3, "unknown": 4}
    items.sort(key=lambda x: (order[x["bucket"]], x["expiry"]))
    return items


def stats(items):
    total = len(items)
    expired = sum(1 for i in items if i["bucket"] == "expired")
    near = sum(1 for i in items if i["bucket"] == "soon30")
    at_risk = sum(
        (i["qty"] or 0) * (i["price"] or 0)
        for i in items
        if i["bucket"] in ("expired", "soon30") and i["price"]
    )
    return {"total": total, "expired": expired, "near": near, "at_risk": at_risk}


def esc(s) -> str:
    return _html.escape(str(s if s is not None else ""))


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>__BRAND__ — __TAGLINE__</title>
<style>
:root{--red:#c0392b;--amber:#d68910;--green:#1e8449;--ink:#1a1a1a;--mut:#666}
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;color:var(--ink);background:#f7f9f8}
.wrap{max-width:720px;margin:0 auto;padding:16px}
header{background:#0b3d2e;color:#fff;padding:22px 0}
header h1{margin:0;font-size:1.4rem}
header p{margin:6px 0 0;opacity:.9;font-size:.95rem}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:14px 0}
.stat{background:#fff;border:1px solid #e3e3e3;border-radius:10px;padding:10px;text-align:center}
.stat b{display:block;font-size:1.25rem}
.stat span{font-size:.72rem;color:var(--mut)}
.stat.red b{color:var(--red)}.stat.amber b{color:var(--amber)}.stat.green b{color:var(--green)}
.card{background:#fff;border:1px solid #e3e3e3;border-radius:12px;padding:14px;margin:12px 0}
.card h3{margin:0 0 10px;font-size:1rem}
label{font-size:.8rem;color:var(--mut);display:block;margin:8px 0 3px}
input,select{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:1rem}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.btn{display:inline-block;background:#0b3d2e;color:#fff;border:0;border-radius:10px;padding:12px 18px;font-size:1rem;font-weight:700;cursor:pointer;width:100%;margin-top:12px}
.btn.sm{width:auto;padding:6px 12px;font-size:.85rem;margin:0}
.btn.danger{background:var(--red)}
.btn.warn{background:#fff;color:var(--ink);border:1px solid #ccc}
.toolbar{display:flex;gap:8px;margin:12px 0}
.toolbar input{flex:1}
.item{border-left:6px solid #ccc;background:#fff;border-radius:10px;padding:10px 12px;margin:8px 0;display:flex;justify-content:space-between;gap:8px;align-items:center}
.item .nm{font-weight:700}
.item .meta{font-size:.82rem;color:var(--mut)}
.b-exp{border-color:var(--red)}.b-30{border-color:var(--red)}.b-90{border-color:var(--amber)}.b-ok{border-color:var(--green)}
.pill{display:inline-block;font-size:.72rem;font-weight:800;border-radius:20px;padding:3px 10px;color:#fff;margin-top:4px}
.b-exp .pill,.b-30 .pill{background:var(--red)}
.b-90 .pill{background:var(--amber)}
.b-ok .pill{background:var(--green)}
.actions{display:flex;gap:6px;flex-shrink:0}
.empty{text-align:center;color:var(--mut);padding:30px 10px}
footer{color:var(--mut);font-size:.78rem;padding:18px 0 30px;text-align:center;line-height:1.5}
.searchrow{display:flex;gap:8px}
.searchrow .btn{width:auto;margin-top:0}
</style></head><body>
<header><div class="wrap"><h1>🛡️ __BRAND__</h1><p>__TAGLINE__</p></div></header>
<div class="wrap">
<div class="stats">
<div class="stat"><b>__TOTAL__</b><span>items tracked</span></div>
<div class="stat red"><b>__EXPIRED__</b><span>expired</span></div>
<div class="stat amber"><b>__NEAR__</b><span>≤ 30 days</span></div>
<div class="stat green"><b>Rs __ATRISK__</b><span>value at risk</span></div>
</div>
<div class="card"><h3>➕ Add stock</h3>
<form method="post" action="/expiry/add" id="addform">
<input type="hidden" name="item_id" id="f_id" value="">
<label>Medicine name *</label><input name="name" id="f_name" required maxlength="120" placeholder="e.g. Augmentin 625mg">
<div class="row2"><div><label>Batch no *</label><input name="batch" id="f_batch" required maxlength="60" placeholder="e.g. B-2214"></div>
<div><label>Expiry date *</label><input name="expiry" id="f_expiry" type="date" required></div></div>
<div class="row2"><div><label>Quantity</label><input name="qty" id="f_qty" type="number" min="0" step="1" value="0"></div>
<div><label>Price/unit (Rs, optional)</label><input name="price" id="f_price" type="number" min="0" step="0.01" placeholder=""></div></div>
<button class="btn" type="submit" id="f_submit">Add item</button>
<button class="btn warn" type="button" id="f_cancel" style="display:none" onclick="resetForm()">Cancel edit</button>
</form></div>
<div class="toolbar"><form method="get" action="/expiry" class="searchrow" style="flex:1;display:flex;gap:8px">
<input name="q" placeholder="🔍 Search by name or batch…" value="__Q__" style="flex:1">
<button class="btn" type="submit">Go</button></form></div>
__ITEMS__
<footer>Data is stored on this demo server and may be lost if the server restarts — keep your purchase records too.<br>
WhatsApp expiry alerts are coming next. Built by Zubair Ahmed.</footer>
</div>
<script>
function editItem(id,name,batch,expiry,qty,price){
document.getElementById('f_id').value=id;
document.getElementById('f_name').value=name;
document.getElementById('f_batch').value=batch;
document.getElementById('f_expiry').value=expiry;
document.getElementById('f_qty').value=qty;
document.getElementById('f_price').value=price||'';
document.getElementById('f_submit').textContent='Save changes';
document.getElementById('f_cancel').style.display='block';
window.scrollTo({top:0,behavior:'smooth'});
}
function resetForm(){
document.getElementById('addform').reset();
document.getElementById('f_id').value='';
document.getElementById('f_submit').textContent='Add item';
document.getElementById('f_cancel').style.display='none';
}
async function delItem(id){
if(!confirm('Delete this item?'))return;
await fetch('/expiry/api/items/'+id,{method:'DELETE'});
location.reload();
}
</script></body></html>"""


def render(items, q: str) -> str:
    import json as _json
    s = stats(items)
    if items:
        rows = []
        for i in items:
            dl = i["days"]
            dl_txt = f"{dl} days left" if dl is not None and dl >= 0 else (
                f"expired {-dl}d ago" if dl is not None else "bad date")
            price_txt = f"Rs {i['price']:,.0f}/unit" if i["price"] else ""
            qty_txt = f"{(i['qty'] or 0):g}"
            js = ",".join([_json.dumps(i["name"]), _json.dumps(i["batch"]),
                           _json.dumps(i["expiry"]), str(i["qty"] or 0),
                           _json.dumps(str(i["price"] or ""))])
            rows.append(
                f'<div class="item {BUCKET_CLASS[i["bucket"]]}">'
                f'<div><div class="nm">{esc(i["name"])}</div>'
                f'<div class="meta">Batch {esc(i["batch"])} · Exp {esc(i["expiry"])} · '
                f'Qty {qty_txt} {price_txt}</div>'
                f'<span class="pill">{BUCKET_LABEL[i["bucket"]]} · {dl_txt}</span></div>'
                f'<div class="actions">'
                f'<button class="btn sm warn" onclick=\'editItem({i["id"]},{js})\'>Edit</button>'
                f'<button class="btn sm danger" onclick="delItem({i["id"]})">Del</button>'
                f'</div></div>'
            )
        items_html = "\n".join(rows)
    else:
        items_html = '<div class="empty">No items yet — add your first batch above. 🎉</div>'
    return (PAGE.replace("__BRAND__", BRAND).replace("__TAGLINE__", TAGLINE)
            .replace("__TOTAL__", str(s["total"]))
            .replace("__EXPIRED__", str(s["expired"]))
            .replace("__NEAR__", str(s["near"]))
            .replace("__ATRISK__", f"{s['at_risk']:,.0f}")
            .replace("__Q__", esc(q)).replace("__ITEMS__", items_html))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def dashboard(q: str = ""):
    return HTMLResponse(render(load_items(q.strip()), q.strip()))


def _clean_date(expiry: str) -> str:
    expiry = (expiry or "").strip()[:10]
    datetime.strptime(expiry, "%Y-%m-%d")  # raises ValueError if bad
    return expiry


@router.post("/add")
def add_item(name: str = Form(""), batch: str = Form(""), expiry: str = Form(""),
             qty: float = Form(0), price: str = Form(""),
             item_id: str = Form("")):
    name = name.strip()[:120]
    batch = batch.strip()[:60]
    if not name or not batch:
        raise HTTPException(status_code=400, detail="name_and_batch_required")
    try:
        expiry = _clean_date(expiry)
    except ValueError:
        raise HTTPException(status_code=400, detail="bad_expiry_date")
    qty = max(0, qty or 0)
    price_v = None
    if str(price).strip():
        try:
            price_v = max(0, float(price))
        except ValueError:
            raise HTTPException(status_code=400, detail="bad_price")
    if item_id.strip():
        db.q("UPDATE items SET name=?, batch=?, expiry=?, qty=?, price=? WHERE id=?",
             (name, batch, expiry, qty, price_v, int(item_id)))
    else:
        db.q("INSERT INTO items (name, batch, expiry, qty, price, created_at)"
             " VALUES (?,?,?,?,?,?)", (name, batch, expiry, qty, price_v, db.now()))
    return RedirectResponse("/expiry", status_code=303)


class ItemIn(BaseModel):
    name: str
    batch: str = ""
    expiry: str
    qty: float = 0
    price: Optional[float] = None


@router.post("/api/items")
def api_add(inp: ItemIn):
    name = inp.name.strip()[:120]
    if not name:
        raise HTTPException(status_code=400, detail="name_required")
    try:
        expiry = _clean_date(inp.expiry)
    except ValueError:
        raise HTTPException(status_code=400, detail="bad_expiry_date")
    cur = db.q("INSERT INTO items (name, batch, expiry, qty, price, created_at)"
               " VALUES (?,?,?,?,?,?)",
               (name, inp.batch.strip()[:60], expiry, max(0, inp.qty or 0),
                max(0, inp.price) if inp.price is not None else None, db.now()))
    return JSONResponse({"ok": True, "id": cur.lastrowid})


@router.get("/api/items")
def api_list(q: str = ""):
    items = load_items(q.strip())
    return {"items": items, "stats": stats(items)}


@router.delete("/api/items/{item_id}")
def api_delete(item_id: int):
    db.q("DELETE FROM items WHERE id=?", (item_id,))
    return {"ok": True}
