"""FBR Digital Invoicing integration (SRO 288(I)/2026).

HONEST ARCHITECTURE:
- build_invoice_payload() constructs the FBR-format invoice JSON + QR payload
  from our internal invoice. This is real, deterministic, testable.
- make_qr_png() renders the QR code image (base64) for the printed invoice.
- submit() ONLY attempts a real HTTP submission when settings.fbr_mode == 'live'
  AND the hotel's own IRIS credentials are configured (their signup, their action).
  In 'test' mode (default) nothing is sent; invoices are marked "FBR test —
  not submitted". A live attempt logs the real FBR response; failures are shown
  honestly, never silently marked submitted.
"""
import base64
import io
import json
import time
import urllib.request
import urllib.error

from app.hotelpms import db


def build_invoice_payload(inv: dict, settings: dict) -> dict:
    """Build FBR-format digital invoice JSON from our invoice row."""
    lines = json.loads(inv.get("lines_json") or "[]")
    items = []
    for i, ln in enumerate(lines, 1):
        items.append({
            "sno": i,
            "description": ln.get("description", ""),
            "quantity": ln.get("qty", 1),
            "unitPrice": round(ln.get("unit_price", 0), 2),
            "totalAmount": round(ln.get("amount", 0), 2),
            "taxRate": inv["tax_rate"],
            "taxAmount": round(ln.get("amount", 0) * inv["tax_rate"] / 100, 2),
        })
    return {
        "invoiceType": "sales",
        "invoiceNumber": inv["invoice_no"],
        "fbrInvoiceNumber": inv.get("fbr_invoice_no") or "",
        "invoiceDate": time.strftime("%Y-%m-%dT%H:%M:%S",
                                     time.gmtime(inv["created_at"])),
        "seller": {
            "name": settings.get("hotel_name", ""),
            "address": settings.get("hotel_address", ""),
            "ntn": settings.get("ntn", ""),
            "strn": settings.get("strn", ""),
        },
        "buyer": {
            "name": inv.get("guest_name", "Walk-in Guest"),
            "cnic": inv.get("guest_cnic", ""),
        },
        "items": items,
        "subTotal": round(inv["subtotal"], 2),
        "taxRate": inv["tax_rate"],
        "taxAmount": round(inv["tax_amount"], 2),
        "grandTotal": round(inv["total"], 2),
        "paymentMethod": inv.get("payment_method", "cash"),
    }


def qr_payload_text(inv: dict, settings: dict) -> str:
    """Compact QR payload printed on the invoice (FBR-style verification string)."""
    return json.dumps({
        "inv": inv["invoice_no"],
        "fbr": inv.get("fbr_invoice_no") or "TEST-NOT-SUBMITTED",
        "seller_ntn": settings.get("ntn", ""),
        "date": time.strftime("%Y-%m-%d", time.gmtime(inv["created_at"])),
        "total": round(inv["total"], 2),
        "tax": round(inv["tax_amount"], 2),
    }, separators=(",", ":"))


def make_qr_png(payload: str) -> str:
    """Return base64 PNG data URI of the QR code."""
    import qrcode
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _log_attempt(invoice_id: int, attempt_no: int, request_json: str,
                 http_code: int, response_text: str, ok: bool):
    db.q("""INSERT INTO fbr_log (invoice_id, attempt_no, request_json, http_code,
            response_text, ok, created_at) VALUES (?,?,?,?,?,?,?)""",
         (invoice_id, attempt_no, request_json[:4000], http_code,
          response_text[:2000], 1 if ok else 0, db.now()))


def _post_once(url: str, payload: dict, user: str, pw: str):
    """Single HTTP POST attempt. Returns (http_code, body_text)."""
    req = urllib.request.Request(
        url.rstrip("/") + "/invoices",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "X-IRIS-User": user,
                 "X-IRIS-Password": pw},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status, resp.read().decode()[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:2000]
    except Exception as e:
        return 0, f"Connection error: {e}"


def submit(invoice_id: int, max_attempts: int = 3) -> dict:
    """Attempt live FBR submission with retry + backoff. Never faked.

    Each attempt is logged to fbr_log (request + response). In 'test' mode
    (default) nothing is sent; invoice stays 'test'.
    """
    s = db.get_settings()
    inv = db.qone("SELECT * FROM invoices WHERE id=?", (invoice_id,))
    if not inv:
        return {"ok": False, "error": "invoice_not_found"}
    inv = dict(inv)
    if s["fbr_mode"] != "live":
        db.q("UPDATE invoices SET fbr_status='test' WHERE id=?", (invoice_id,))
        return {"ok": False, "error": "test_mode",
                "detail": "FBR mode is TEST — invoice not submitted. "
                          "Set FBR mode to LIVE + enter your IRIS credentials in Settings."}
    if not s["fbr_iris_user"] or not s["fbr_iris_pass"] or not s["fbr_api_url"]:
        msg = "IRIS username/password/API URL missing in Settings."
        db.q("UPDATE invoices SET fbr_status='failed', fbr_response=? WHERE id=?",
             (msg, invoice_id))
        _log_attempt(invoice_id, 0, "", 0, msg, False)
        return {"ok": False, "error": "no_credentials", "detail": msg}
    payload = build_invoice_payload(inv, s)
    last = {"ok": False, "http": 0, "response": ""}
    for attempt in range(1, max_attempts + 1):
        code, body = _post_once(s["fbr_api_url"], payload,
                               s["fbr_iris_user"], s["fbr_iris_pass"])
        ok = code in (200, 201, 202)
        _log_attempt(invoice_id, attempt, json.dumps(payload), code, body, ok)
        last = {"ok": ok, "http": code, "response": body}
        if ok:
            try:
                fbr_no = json.loads(body).get("fbrInvoiceNumber", "") or ""
            except Exception:
                fbr_no = ""
            db.q("""UPDATE invoices SET fbr_status='submitted', fbr_response=?,
                    fbr_invoice_no=? WHERE id=?""",
                 (f"HTTP {code}: {body}", fbr_no, invoice_id))
            return {"ok": True, "http": code, "fbr_invoice_no": fbr_no,
                    "response": body, "attempts": attempt}
        if attempt < max_attempts:
            time.sleep(2 ** attempt)  # backoff: 2s, 4s
    # All attempts failed — record honestly, never mark submitted
    db.q("UPDATE invoices SET fbr_status='failed', fbr_response=? WHERE id=?",
         (f"HTTP {last['http']} after {max_attempts} attempts: {last['response']}",
          invoice_id))
    return {"ok": False, "error": "all_attempts_failed",
            "http": last["http"], "response": last["response"],
            "attempts": max_attempts}
