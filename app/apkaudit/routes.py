"""SecureAPK — automated APK security audit + fix bundle. Route: /apkaudit"""
import html
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse, FileResponse

from app.apkaudit import db, auth, explain
from app.apkaudit import engine_audit as AUD
from app.apkaudit import engine_fix as FIX

router = APIRouter()

MAX_APK_MB = 50
WHATSAPP_PRO = ("https://wa.me/923116925020?text="
                "Hi!%20I%20want%20SecureAPK%20Pro%20%28%2429%2Fmonth%29.%20My%20account%20email%20is%3A%20")

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.6;background:#fff}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
header{background:#101828;color:#fff;padding:52px 0}
header h1{margin:0 0 10px;font-size:2rem}
header p{opacity:.9;max-width:640px;margin:0 0 22px}
.btn{display:inline-block;background:#12b76a;color:#fff;font-weight:700;padding:12px 26px;border-radius:10px;text-decoration:none;margin:4px 8px 4px 0;border:0;cursor:pointer;font-size:1rem}
.btn.ghost{background:transparent;color:#fff;border:2px solid #fff}
.btn.dark{background:#101828}
.btn.small{padding:8px 16px;font-size:.9rem}
section{padding:36px 0;border-bottom:1px solid #eee}
h2{margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}
.card{border:1px solid #e5e5e5;border-radius:12px;padding:18px;background:#fff}
.badge{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.8rem;font-weight:700;color:#fff}
.finding{border:1px solid #e5e5e5;border-left:6px solid #999;border-radius:10px;padding:16px;margin:14px 0;background:#fff}
details{margin:10px 0;border:1px solid #e5e5e5;border-radius:10px;padding:12px 16px}
summary{font-weight:600;cursor:pointer}
footer{padding:26px 0;color:#666;font-size:.9rem}
input[type=text],input[type=email],input[type=password]{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;margin:6px 0 12px;font-size:1rem;box-sizing:border-box}
.score{font-size:2.6rem;font-weight:800}
table{border-collapse:collapse;width:100%;margin:12px 0}
td,th{border:1px solid #e5e5e5;padding:8px 10px;text-align:left;font-size:.92rem}
th{background:#f8fafc}
.nav{background:#101828;color:#fff;padding:10px 0;font-size:.95rem}
.nav a{color:#fff;text-decoration:none;margin-right:18px}
.nav .wrap{display:flex;justify-content:space-between;align-items:center}
.alert{background:#fef3c7;border:1px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:14px 0}
"""

NAV = """<div class="nav"><div class="wrap"><div><a href="/apkaudit"><b>SecureAPK</b></a>
<a href="/apkaudit/scan">Scan</a><a href="/apkaudit/dashboard">Dashboard</a></div>
<div>{right}</div></div></div>"""


def _nav_right(user):
    if user:
        return (f"<span style='opacity:.8;margin-right:12px'>{html.escape(user['email'])} "
                f"({html.escape(user['plan'])})</span>"
                f"<a href='/apkaudit/api/logout'>Logout</a>")
    return "<a href='/apkaudit/scan'>Login / Sign up</a>"


def _user(request: Request):
    return auth.user_from_token(request.cookies.get("apkaudit_token", ""))


def _page(title, user, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — SecureAPK</title>
<meta name="description" content="SecureAPK: upload your Android APK, get an automated security audit with plain-language findings and a ready-to-apply fix bundle.">
<style>{CSS}</style></head><body>
{NAV.format(right=_nav_right(user))}
{body}
<footer><div class="wrap">SecureAPK — automated APK security audits for developers. Static analysis only.
Only scan apps you own or have written permission to test.</div></div></footer>
</body></html>"""


# ---------------------------------------------------------------- landing ---
@router.get("/apkaudit", response_class=HTMLResponse)
@router.get("/apkaudit/", response_class=HTMLResponse)
def landing(request: Request):
    user = _user(request)
    body = f"""
<header><div class="wrap">
<h1>Is your Android app leaking secrets?</h1>
<p>Upload your APK. In seconds, SecureAPK audits it for hardcoded API keys, dangerous permissions,
insecure network settings and 20+ other issues — then hands you a <b>fix bundle</b> your developer
can apply today. Built for indie developers and small teams who can't afford a $5,000 pentest.</p>
<a class="btn" href="/apkaudit/scan">Scan my APK — free</a>
<a class="btn ghost" href="#pricing">See pricing</a>
</div></header>
<section><div class="wrap"><h2>How it works</h2><div class="grid">
<div class="card"><b>1. Upload</b><br>Drop your APK (up to 50MB). We check it's a real Android package.</div>
<div class="card"><b>2. Audit</b><br>Static analysis: manifest flags, permissions, exported components, hardcoded secrets, trackers, signing cert — each rated High / Medium / Low with a 0–100 risk score.</div>
<div class="card"><b>3. Fix</b><br>Download the fix bundle: corrected manifest, HTTPS-only network config, and per-finding instructions with copy-paste code.</div>
</div></div></section>
<section><div class="wrap"><h2>What it finds</h2><div class="grid">
<div class="card"><span class="badge" style="background:#c0392b">High</span><br><b>Hardcoded API keys &amp; secrets</b><br>Keys baked into your app that anyone can extract and abuse — on your bill.</div>
<div class="card"><span class="badge" style="background:#d68910">Medium</span><br><b>Cleartext HTTP traffic</b><br>Data sent without encryption, readable on any shared network.</div>
<div class="card"><span class="badge" style="background:#d68910">Medium</span><br><b>Over-broad permissions</b><br>Full storage access or install-packages rights your feature may not need.</div>
<div class="card"><span class="badge" style="background:#1e8449">Low</span><br><b>Backup, SDK age, trackers</b><br>Smaller hygiene issues, each with a one-line fix.</div>
</div></div></section>
<section id="pricing"><div class="wrap"><h2>Pricing</h2><div class="grid">
<div class="card"><b>Free</b><br><span style="font-size:1.6rem;font-weight:800">$0</span><br>3 scans / month<br>Full audit report<br>Fix bundle download<br><br><a class="btn dark small" href="/apkaudit/scan">Start free</a></div>
<div class="card" style="border:2px solid #12b76a"><b>Pro</b><br><span style="font-size:1.6rem;font-weight:800">$29</span>/month<br>Unlimited scans<br>Everything in Free<br>Priority re-scans<br><br><a class="btn small" href="{WHATSAPP_PRO}">Activate via WhatsApp</a></div>
</div><p style="color:#666;font-size:.9rem">Pro is activated manually after you message us on WhatsApp — no card needed upfront, cancel anytime.</p></div></section>
<section><div class="wrap"><h2>Honest limits</h2>
<details><summary>What can't SecureAPK find?</summary>
It's <b>static analysis only</b> — it reads your app's package without running it. It can't catch runtime bugs,
server-side vulnerabilities, or logic flaws. Think of it as a first-pass hygiene check, not a full pentest.</details>
<details><summary>Whose apps may I scan?</summary>
Only apps you <b>own or have written permission to test</b> — your own apps, your client's apps (with their OK),
or open-source apps. Don't upload someone else's commercial app.</details>
<details><summary>Do you keep my APK?</summary>
Uploaded APKs are stored only so you can re-download the fix bundle, and are <b>auto-deleted after 7 days</b>.
Reports stay in your dashboard.</details>
<details><summary>Is my code sent anywhere?</summary>
No. Analysis runs on our own server. An optional AI pass rephrases findings in plain language —
never with your source code, only the finding titles.</details>
</div></section>
"""
    return HTMLResponse(_page("APK security audit + fix bundle", user, body))


# ------------------------------------------------------------------ auth ---
@router.get("/apkaudit/scan", response_class=HTMLResponse)
def scan_page(request: Request):
    user = _user(request)
    if not user:
        return HTMLResponse(_page("Login", None, f"""<section><div class="wrap" style="max-width:440px">
<h2>Login or create your free account</h2>
<div class="card"><h3 style="margin-top:0">Login</h3>
<form method="post" action="/apkaudit/api/login">
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password" required>
<button class="btn dark" type="submit">Login</button></form></div>
<div class="card" style="margin-top:14px"><h3 style="margin-top:0">Sign up (free)</h3>
<form method="post" action="/apkaudit/api/signup">
<input type="text" name="name" placeholder="Your name" required>
<input type="email" name="email" placeholder="Email" required>
<input type="password" name="password" placeholder="Password (8+ chars)" required>
<button class="btn" type="submit">Create account</button></form>
<p style="color:#666;font-size:.85rem">Free plan: 3 scans/month. No card required.</p></div>
</div></section>"""))
    left = auth.scans_left(user)
    quota = "unlimited" if left == "unlimited" else f"{left} of 3 free scans left this month"
    return HTMLResponse(_page("Scan APK", user, f"""<section><div class="wrap" style="max-width:560px">
<h2>Upload your APK</h2>
<p style="color:#666">{quota} &nbsp;·&nbsp; plan: <b>{html.escape(user['plan'])}</b></p>
<div class="card"><form method="post" action="/apkaudit/api/scan" enctype="multipart/form-data">
<input type="file" name="apk" accept=".apk" required style="margin:10px 0">
<p style="color:#666;font-size:.85rem">Max 50MB. Only upload apps you own or have permission to test.</p>
<button class="btn" type="submit">Run security audit</button></form></div>
<p style="color:#666;font-size:.9rem">Need more scans? <a href="{WHATSAPP_PRO}">Get Pro ($29/mo) via WhatsApp</a></p>
</div></section>"""))


@router.post("/apkaudit/api/signup")
def api_signup(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        u = auth.create_user(name, email, password)
    except ValueError as e:
        msg = "That email is already registered — try logging in." if str(e) == "email_taken" \
            else "Password must be at least 8 characters."
        return HTMLResponse(_page("Sign up", None, f"<section><div class='wrap'><div class='alert'>{msg}</div>"
                                                   f"<a href='/apkaudit/scan'>← back</a></div></section>"))
    resp = RedirectResponse("/apkaudit/scan", status_code=303)
    resp.set_cookie("apkaudit_token", auth.new_session(u["id"]), max_age=30 * 86400, httponly=True)
    return resp


@router.post("/apkaudit/api/login")
def api_login(email: str = Form(...), password: str = Form(...)):
    u = auth.authenticate(email, password)
    if not u:
        return HTMLResponse(_page("Login", None, "<section><div class='wrap'><div class='alert'>"
                                                "Wrong email or password.</div>"
                                                "<a href='/apkaudit/scan'>← back</a></div></section>"))
    resp = RedirectResponse("/apkaudit/scan", status_code=303)
    resp.set_cookie("apkaudit_token", auth.new_session(u["id"]), max_age=30 * 86400, httponly=True)
    return resp


@router.get("/apkaudit/api/logout")
def api_logout(request: Request):
    auth.destroy_session(request.cookies.get("apkaudit_token", ""))
    resp = RedirectResponse("/apkaudit", status_code=303)
    resp.delete_cookie("apkaudit_token")
    return resp


# ------------------------------------------------- scan/report/fix/dashboard/admin ---
def _is_apk(path: str) -> bool:
    try:
        with open(path, "rb") as fh:
            magic = fh.read(4)
        if magic != b"PK\x03\x04":
            return False
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        return any(n.endswith("AndroidManifest.xml") for n in names)
    except Exception:
        return False


def _cleanup_old_uploads():
    """Delete stored APKs older than 7 days (reports stay)."""
    cutoff = db.now() - 7 * 86400
    try:
        for row in db.qall("SELECT id, apk_path, fixzip_path FROM scans WHERE created_at < ?", (cutoff,)):
            for p in (row["apk_path"], row["fixzip_path"] if "fixzip_path" in row.keys() else ""):
                if p and os.path.isfile(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
            db.q("UPDATE scans SET apk_path='', fixzip_path='' WHERE id=?", (row["id"],))
    except Exception:
        pass


@router.post("/apkaudit/api/scan")
async def api_scan(request: Request, apk: UploadFile = File(...)):
    user = _user(request)
    if not user:
        return RedirectResponse("/apkaudit/scan", status_code=303)
    if not auth.can_scan(user):
        return HTMLResponse(_page("Scan limit", user,
            f"""<section><div class="wrap"><div class="alert">You've used your 3 free scans this month.</div>
            <a class="btn" href="{WHATSAPP_PRO}">Get Pro ($29/mo) via WhatsApp</a></div></section>"""))

    # save upload with size cap
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".apk")
    size = 0
    try:
        while True:
            chunk = await apk.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_APK_MB * 1024 * 1024:
                tmp.close(); os.unlink(tmp.name)
                return HTMLResponse(_page("Too large", user,
                    f"<section><div class='wrap'><div class='alert'>APK is over {MAX_APK_MB}MB.</div>"
                    "<a href='/apkaudit/scan'>← back</a></div></section>"))
            tmp.write(chunk)
    finally:
        tmp.close()
    if not _is_apk(tmp.name):
        os.unlink(tmp.name)
        return HTMLResponse(_page("Invalid file", user,
            "<section><div class='wrap'><div class='alert'>That doesn't look like an Android APK file.</div>"
            "<a href='/apkaudit/scan'>← back</a></div></section>"))

    # run the audit in a SUBPROCESS: androguard peaks at ~400MB per parse and
    # Python won't return that memory to the OS — a second in-process scan
    # OOM-kills small containers (observed: 502 + DB wipe). The subprocess
    # exits and the OS reclaims everything.
    t0 = time.time()
    audit_json = tmp.name + "-audit.json"
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "app.apkaudit.engine_audit",
             tmp.name, "-o", tmp.name + "-audit.md", "--json"],
            capture_output=True, text=True, timeout=300)
        if proc.returncode != 0 or not os.path.isfile(audit_json):
            raise RuntimeError(proc.stderr[-500:] if proc.stderr else "no output")
        with open(audit_json, encoding="utf-8") as fh:
            result = json.load(fh)
    except Exception as e:
        for p in (tmp.name, audit_json, tmp.name + "-audit.md"):
            try:
                os.unlink(p)
            except OSError:
                pass
        return HTMLResponse(_page("Scan failed", user,
            f"<section><div class='wrap'><div class='alert'>Couldn't analyze that APK ({html.escape(type(e).__name__)}). "
            "It may be corrupted, too large for this container, or use an unsupported format.</div>"
            "<a href='/apkaudit/scan'>← back</a></div></section>"))
    finally:
        for p in (audit_json, tmp.name + "-audit.md"):
            try:
                os.unlink(p)
            except OSError:
                pass
    elapsed = round(time.time() - t0, 1)

    info, findings = result["info"], result["findings"]
    findings = explain.enrich(findings)
    findings = explain.gemini_rewrite(findings)

    n = {"High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        n[f["severity"]] = n.get(f["severity"], 0) + 1

    cur = db.q(
        """INSERT INTO scans (user_id, filename, package, app_name, version, risk_score,
           risk_band, n_high, n_medium, n_low, findings_json, month, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user["id"], (apk.filename or "app.apk")[:120], info.get("package", ""),
         info.get("app_name", ""), info.get("version", ""), info.get("risk_score", 0),
         info.get("risk_band", "Low"), n["High"], n["Medium"], n["Low"],
         json.dumps({"info": info, "findings": findings, "notes": result.get("notes", []),
                     "elapsed": elapsed}),
         db.current_month(), db.now()))
    scan_id = cur.lastrowid
    dest = os.path.join(db.uploads_dir(), f"scan_{scan_id}.apk")
    shutil.move(tmp.name, dest)
    db.q("UPDATE scans SET apk_path=? WHERE id=?", (dest, scan_id))
    # build the fix bundle ONCE here (reuses the analyze result) so downloads
    # never trigger a second expensive in-container scan (OOM risk)
    try:
        tmpd = tempfile.mkdtemp(prefix="apkaudit_fix_")
        bundle = FIX.build_fix_bundle(dest, os.path.join(tmpd, "fixes"), result=result)
        fixzip = os.path.join(db.uploads_dir(), f"fixbundle_{scan_id}.zip")
        with zipfile.ZipFile(fixzip, "w", zipfile.ZIP_DEFLATED) as z:
            for _root, _, _files in os.walk(bundle["outdir"]):
                for _fn in _files:
                    _full = os.path.join(_root, _fn)
                    z.write(_full, os.path.relpath(_full, bundle["outdir"]))
        shutil.rmtree(tmpd, ignore_errors=True)
        db.q("UPDATE scans SET fixzip_path=? WHERE id=?", (fixzip, scan_id))
    except Exception:
        pass  # bundle can be generated on demand at download time
    _cleanup_old_uploads()
    return RedirectResponse(f"/apkaudit/report/{scan_id}", status_code=303)


def _sev_badge(sev):
    c = explain.SEV_COLOR.get(sev, "#999")
    return f"<span class='badge' style='background:{c}'>{sev}</span>"


@router.get("/apkaudit/report/{scan_id}", response_class=HTMLResponse)
def report(request: Request, scan_id: int):
    user = _user(request)
    row = db.qone("SELECT * FROM scans WHERE id=?", (scan_id,))
    if not row:
        return HTMLResponse(_page("Not found", user,
            "<section><div class='wrap'><div class='alert'>Report not found.</div></div></section>"),
            status_code=404)
    if not user or (row["user_id"] != user["id"]):
        return RedirectResponse("/apkaudit/scan", status_code=303)
    data = json.loads(row["findings_json"])
    info, findings, notes = data["info"], data["findings"], data.get("notes", [])
    band = info.get("risk_band", "Low")
    bcolor = explain.SEV_COLOR.get(band, "#1e8449")

    cards = []
    for i, f in enumerate(findings, 1):
        bg = explain.SEV_BG.get(f["severity"], "#fff")
        cards.append(f"""<div class="finding" style="border-left-color:{explain.SEV_COLOR.get(f['severity'], '#999')};background:{bg}">
{_sev_badge(f['severity'])} <b>{html.escape(f['title'])}</b>
<p style="margin:8px 0"><b>What it means:</b> {html.escape(f.get('plain_what', ''))}</p>
<p style="margin:8px 0;color:#555"><b>Why it matters:</b> {html.escape(f.get('plain_why', ''))}</p>
<details><summary>Technical detail + fix</summary>
<p><code>{html.escape(f.get('detail', ''))}</code></p>
<p><b>Fix:</b> {html.escape(f.get('recommendation', ''))}</p></details></div>""")
    findings_html = "\n".join(cards) if cards else "<p>No issues found — clean bill of health.</p>"

    trackers = info.get("trackers") or {}
    tracker_html = (", ".join(html.escape(t) for t in trackers) if trackers else "None detected")

    body = f"""<section><div class="wrap">
<p><a href="/apkaudit/dashboard">← Dashboard</a></p>
<h2>Security audit — {html.escape(info.get('app_name') or info.get('package', 'APK'))}</h2>
<div class="grid"><div class="card" style="text-align:center">
<div class="score" style="color:{bcolor}">{info.get('risk_score', 0)}/100</div>
<div>{_sev_badge(band)} risk</div>
<div style="color:#666;font-size:.85rem;margin-top:6px">scanned in {data.get('elapsed', '?')}s · static analysis</div></div>
<div class="card"><table>
<tr><th>Package</th><td><code>{html.escape(info.get('package', ''))}</code></td></tr>
<tr><th>Version</th><td>{html.escape(info.get('version', ''))}</td></tr>
<tr><th>Target SDK</th><td>{html.escape(str(info.get('target_sdk', '')))}</td></tr>
<tr><th>Signed</th><td>{html.escape(str(info.get('signed', '')))}</td></tr>
<tr><th>Trackers</th><td>{tracker_html}</td></tr>
</table></div></div>
<p><b>{row['n_high']}</b> High · <b>{row['n_medium']}</b> Medium · <b>{row['n_low']}</b> Low findings</p>
<p><a class="btn" href="/apkaudit/fixbundle/{scan_id}">⬇ Download fix bundle</a></p>
{findings_html}
</div></section>"""
    return HTMLResponse(_page(f"Audit report — {info.get('app_name', 'APK')}", user, body))


@router.get("/apkaudit/fixbundle/{scan_id}")
def fixbundle(request: Request, scan_id: int):
    user = _user(request)
    row = db.qone("SELECT * FROM scans WHERE id=?", (scan_id,))
    if not row or not user or row["user_id"] != user["id"]:
        return RedirectResponse("/apkaudit/scan", status_code=303)
    fname = f"secureapk-fixes-{row['package'] or 'app'}.zip"
    fz = row["fixzip_path"] if "fixzip_path" in row.keys() else ""
    if fz and os.path.isfile(fz):
        return FileResponse(fz, media_type="application/zip", filename=fname)
    # fallback for rows created before caching: build on demand (APK may be gone)
    apk_path = row["apk_path"]
    if not apk_path or not os.path.isfile(apk_path):
        return HTMLResponse(_page("Expired", user,
            "<section><div class='wrap'><div class='alert'>The uploaded APK has expired (auto-deleted after 7 days). "
            "Re-upload it to generate a fresh fix bundle — your report is still below.</div>"
            f"<a class='btn dark' href='/apkaudit/report/{scan_id}'>View report</a></div></section>"))
    tmpdir = tempfile.mkdtemp(prefix="apkaudit_fix_")
    try:
        bundle = FIX.build_fix_bundle(apk_path, os.path.join(tmpdir, "fixes"))
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return HTMLResponse(_page("Fix failed", user,
            f"<section><div class='wrap'><div class='alert'>Couldn't build the fix bundle ({html.escape(type(e).__name__)}).</div>"
            "<a href='/apkaudit/scan'>← back</a></div></section>"))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(bundle["outdir"]):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, bundle["outdir"]))
    shutil.rmtree(tmpdir, ignore_errors=True)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename={fname}"})


@router.get("/apkaudit/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = _user(request)
    if not user:
        return RedirectResponse("/apkaudit/scan", status_code=303)
    rows = db.qall("SELECT * FROM scans WHERE user_id=? ORDER BY id DESC", (user["id"],))
    items = []
    for r in rows:
        items.append(f"""<tr><td>{time.strftime('%Y-%m-%d', time.gmtime(r['created_at']))}</td>
<td>{html.escape(r['app_name'] or r['package'] or r['filename'])}</td>
<td><b style="color:{explain.SEV_COLOR.get(r['risk_band'], '#333')}">{r['risk_score']}/100</b></td>
<td>{r['n_high']}H / {r['n_medium']}M / {r['n_low']}L</td>
<td><a href="/apkaudit/report/{r['id']}">Report</a> · <a href="/apkaudit/fixbundle/{r['id']}">Fixes</a></td></tr>""")
    table = ("<table><tr><th>Date</th><th>App</th><th>Score</th><th>Findings</th><th></th></tr>"
             + "\n".join(items) + "</table>") if items else "<p>No scans yet.</p>"
    left = auth.scans_left(user)
    quota = "unlimited scans" if left == "unlimited" else f"{left} of 3 free scans left this month"
    body = f"""<section><div class="wrap"><h2>Dashboard</h2>
<p>Plan: <b>{html.escape(user['plan'])}</b> · {quota}</p>
<p><a class="btn" href="/apkaudit/scan">+ New scan</a>
<a class="btn ghost dark" style="color:#101828;border-color:#101828" href="{WHATSAPP_PRO}">Upgrade to Pro</a></p>
{table}</div></section>"""
    return HTMLResponse(_page("Dashboard", user, body))


# ------------------------------------------------------------------ admin ---
@router.get("/apkaudit/admin", response_class=HTMLResponse)
def admin(request: Request, key: str = ""):
    if not auth.admin_key_ok(key or request.headers.get("X-Admin-Key", "")):
        return HTMLResponse("forbidden", status_code=403)
    users = auth.list_users()
    urows = []
    for u in users:
        urows.append(f"""<tr><td>{u['id']}</td><td>{html.escape(u['name'])}</td><td>{html.escape(u['email'])}</td>
<td>{u['plan']}</td><td>{u['scans_month']}/mo · {u['scans_total']} total</td><td>{'yes' if u['is_active'] else 'no'}</td>
<td><form method="post" action="/apkaudit/admin/plan?key={html.escape(key)}" style="display:inline">
<input type="hidden" name="user_id" value="{u['id']}">
<select name="plan"><option value="free">free</option><option value="pro">pro</option></select>
<button type="submit">set</button></form></td></tr>""")
    scans = db.qall("""SELECT s.id, s.created_at, u.email, s.app_name, s.package, s.risk_score, s.risk_band
                       FROM scans s JOIN users u ON s.user_id=u.id ORDER BY s.id DESC LIMIT 100""")
    srows = "".join(
        f"<tr><td>{s['id']}</td><td>{time.strftime('%m-%d %H:%M', time.gmtime(s['created_at']))}</td>"
        f"<td>{html.escape(s['email'])}</td><td>{html.escape(s['app_name'] or s['package'])}</td>"
        f"<td>{s['risk_score']}</td><td>{s['risk_band']}</td></tr>" for s in scans)
    body = f"""<section><div class="wrap"><h2>SecureAPK admin</h2>
<h3>Users ({len(users)})</h3>
<table><tr><th>ID</th><th>Name</th><th>Email</th><th>Plan</th><th>Scans</th><th>Active</th><th>Set plan</th></tr>
{"".join(urows)}</table>
<h3>Recent scans</h3>
<table><tr><th>ID</th><th>When</th><th>User</th><th>App</th><th>Score</th><th>Band</th></tr>{srows}</table>
</div></section>"""
    return HTMLResponse(_page("Admin", None, body))


@router.post("/apkaudit/admin/plan")
async def admin_plan(request: Request, key: str = ""):
    if not auth.admin_key_ok(key or request.headers.get("X-Admin-Key", "")):
        return HTMLResponse("forbidden", status_code=403)
    form = await request.form()
    try:
        auth.set_plan(int(form.get("user_id", 0)), str(form.get("plan", "")))
    except ValueError:
        pass
    return RedirectResponse(f"/apkaudit/admin?key={key}", status_code=303)
