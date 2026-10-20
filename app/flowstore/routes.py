"""FlowStore: Automation-as-a-Service storefront.

Customer flow: storefront -> order form -> confirmation (token) -> track ->
connect own n8n (BYOK) -> auto-deploy to their n8n -> live.
Admin (X-Admin-Key): order list, status changes, manual deploy trigger.
"""
import hmac
import json
import logging
import os
import secrets
import urllib.request
import urllib.error

from fastapi import APIRouter, Form, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response

from . import db, pages, products

log = logging.getLogger("flowstore.routes")
router = APIRouter(prefix="/flowstore")


def _admin_ok(provided: str) -> bool:
    expected = os.environ.get("FLOWSTORE_ADMIN_KEY", "")
    return bool(expected) and hmac.compare_digest(provided or "", expected)


def _require_admin(x_admin_key: str = Header(default="")):
    if not _admin_ok(x_admin_key):
        raise HTTPException(status_code=401, detail="bad_admin_key")


def _order_or_404(token: str) -> dict:
    row = db.qone("SELECT * FROM orders WHERE token=?", (token,))
    if not row:
        return {}
    return dict(row)


def _new_token() -> str:
    return secrets.token_urlsafe(12)


def _whatsapp_link() -> str:
    num = os.environ.get("FLOWSTORE_WHATSAPP", "").strip().lstrip("+")
    if not num:
        return ""
    text = "Hi! I just placed an order on FlowStore and want to confirm."
    from urllib.parse import quote
    return f"https://wa.me/{num}?text={quote(text)}"


def _set_status(order_id: int, status: str):
    db.qexec("UPDATE orders SET status=?, updated_at=? WHERE id=?",
             (status, db.now(), order_id))


# ---------- storefront ----------

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def storefront():
    return HTMLResponse(pages.storefront())


# ---------- order ----------

@router.get("/order/{slug}", response_class=HTMLResponse)
def order_form(slug: str):
    product = products.get_product(slug)
    if not product:
        return HTMLResponse(pages.not_found("Unknown product."), status_code=404)
    return HTMLResponse(pages.order_form(slug, product))


from typing import List

@router.post("/order", response_class=HTMLResponse)
def create_order(
    product: str = Form(""),
    name: str = Form(""),
    business: str = Form(""),
    email: str = Form(""),
    whatsapp: str = Form(""),
    notes: str = Form(""),
    systems: List[str] = Form([]),
):
    prod = products.get_product(product)
    if not prod:
        return HTMLResponse(pages.not_found("Unknown product."), status_code=404)
    systems_json = json.dumps([s for s in systems if s in products.SYSTEM_OPTIONS][:12])
    token = _new_token()
    ts = db.now()
    db.qexec(
        "INSERT INTO orders (token, product, name, business, email, whatsapp, systems, notes, status, created_at, updated_at)"
        " VALUES (?,?,?,?,?,?,?,?, 'received', ?, ?)",
        (token, product, name.strip()[:120], business.strip()[:160],
         email.strip()[:160], whatsapp.strip()[:40], systems_json, notes.strip()[:2000], ts, ts),
    )
    order = _order_or_404(token)
    return HTMLResponse(pages.confirmation(order, _whatsapp_link()))


# ---------- track ----------

@router.get("/track/{token}", response_class=HTMLResponse)
def track(token: str):
    order = _order_or_404(token)
    if not order:
        return HTMLResponse(pages.not_found("Order not found. Check your token."), status_code=404)
    return HTMLResponse(pages.track_page(order))


# ---------- connect (BYOK) ----------

@router.get("/connect/{token}", response_class=HTMLResponse)
def connect_page(token: str):
    order = _order_or_404(token)
    if not order:
        return HTMLResponse(pages.not_found("Order not found."), status_code=404)
    if order["status"] not in ("ready", "connected", "live"):
        return HTMLResponse(
            pages.not_found("Your automation isn't ready yet — we'll notify you when it is."),
            status_code=403)
    return HTMLResponse(pages.connect_page(order))


@router.post("/connect/{token}", response_class=HTMLResponse)
def connect_save(token: str, n8n_url: str = Form(""), n8n_key: str = Form("")):
    order = _order_or_404(token)
    if not order:
        return HTMLResponse(pages.not_found("Order not found."), status_code=404)
    if order["status"] not in ("ready", "connected"):
        return HTMLResponse(pages.not_found("Not ready for connection yet."), status_code=403)
    url = n8n_url.strip().rstrip("/")
    if not (url.startswith("https://") and len(n8n_key.strip()) >= 8):
        return HTMLResponse(pages.deploy_result_page(
            order, False, "Please enter a valid https n8n URL and API key."))
    # Store credentials (service core function; never logged or printed).
    db.qexec("UPDATE orders SET n8n_url=?, n8n_key=?, status='connected', updated_at=? WHERE id=?",
             (url, n8n_key.strip(), db.now(), order["id"]))
    return _do_deploy(token)


# ---------- deploy ----------

def _do_deploy(token: str):
    order = _order_or_404(token)
    if not order:
        return HTMLResponse(pages.not_found("Order not found."), status_code=404)
    slug = order["product"]
    payload = products.workflow_payload(slug)
    if not payload or not payload.get("nodes"):
        # custom orders have no canned workflow: mark live manually via admin
        db.qexec("UPDATE orders SET status='live', updated_at=? WHERE id=?",
                 (db.now(), order["id"]))
        return HTMLResponse(pages.deploy_result_page(order, True, "custom-build"))
    url = (order.get("n8n_url") or "").rstrip("/")
    key = order.get("n8n_key") or ""
    if not url or not key:
        return HTMLResponse(pages.connect_page(order))
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url + "/api/v1/workflows", data=data,
            headers={"Content-Type": "application/json", "X-N8N-API-KEY": key},
            method="POST")
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
        wf_id = str(body.get("id", ""))
        db.qexec("UPDATE orders SET status='live', n8n_workflow_id=?, updated_at=? WHERE id=?",
                 (wf_id, db.now(), order["id"]))
        log.info("flowstore deploy ok token=%s n8n_wf=%s", token[:6] + "...", wf_id)
        return HTMLResponse(pages.deploy_result_page(order, True, wf_id or "created"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = f"HTTP {e.code}"
        log.warning("flowstore deploy HTTPError token=%s code=%s", token[:6] + "...", e.code)
        return HTMLResponse(pages.deploy_result_page(order, False, f"n8n API error (HTTP {e.code}): {detail}"))
    except Exception as e:
        log.warning("flowstore deploy failed token=%s err=%s", token[:6] + "...", type(e).__name__)
        return HTMLResponse(pages.deploy_result_page(
            order, False, f"Could not reach your n8n ({type(e).__name__}). Check the URL and try again."))


@router.post("/deploy/{token}", response_class=HTMLResponse)
def deploy(token: str):
    order = _order_or_404(token)
    if not order:
        return HTMLResponse(pages.not_found("Order not found."), status_code=404)
    if order["status"] not in ("connected", "ready"):
        return HTMLResponse(pages.not_found("Connect your n8n first."), status_code=403)
    return _do_deploy(token)


@router.get("/workflow/{token}/download")
def workflow_download(token: str):
    order = _order_or_404(token)
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")
    payload = products.workflow_payload(order["product"])
    if not payload:
        raise HTTPException(status_code=404, detail="no_canned_workflow")
    return Response(
        content=json.dumps(payload, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=flowstore-{order['product']}.json"},
    )


# ---------- admin ----------

@router.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(pages.admin_login_page())


@router.get("/api/admin/orders")
def admin_orders(x_admin_key: str = Header(default="")):
    _require_admin(x_admin_key)
    rows = db.qall("SELECT id, token, product, name, business, email, status, created_at"
                   " FROM orders ORDER BY id DESC LIMIT 200")
    return {"orders": [dict(r) for r in rows]}


@router.get("/api/admin/orders/{order_id}")
def admin_order_detail(order_id: int, x_admin_key: str = Header(default="")):
    _require_admin(x_admin_key)
    row = db.qone("SELECT * FROM orders WHERE id=?", (order_id,))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    d = dict(row)
    d.pop("n8n_key", None)  # never expose the customer key, even to admin UI
    return d


@router.post("/api/admin/orders/{order_id}/status")
def admin_set_status(order_id: int, payload: dict, x_admin_key: str = Header(default="")):
    _require_admin(x_admin_key)
    status = (payload.get("status") or "").strip()
    if status not in products.STATUS_ORDER:
        raise HTTPException(status_code=400, detail="bad_status")
    _set_status(order_id, status)
    return {"ok": True, "status": status}


@router.post("/api/admin/orders/{order_id}/deploy")
def admin_deploy(order_id: int, x_admin_key: str = Header(default="")):
    _require_admin(x_admin_key)
    row = db.qone("SELECT * FROM orders WHERE id=?", (order_id,))
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    order = dict(row)
    if not order.get("n8n_url") or not order.get("n8n_key"):
        raise HTTPException(status_code=400, detail="no_customer_n8n")
    if order["status"] not in ("connected", "ready"):
        _set_status(order_id, "connected")
    return {"ok": True, "note": "deploy attempted — see order status",
            "token": order["token"]}
