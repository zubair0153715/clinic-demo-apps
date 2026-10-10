"""Drug Adverse-Effects Lookup — educational demo (NOT medical advice).

Live data from openFDA (FAERS adverse-event reports + FDA drug labels).
Free keyless endpoints; OPENFDA_API_KEY env var optional for higher limits.
"""
import html
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from . import drugsafety as DS

router = APIRouter()
_HERE = Path(__file__).parent

THEME = "#dc2626"
DISCLAIMER = ("Educational demo, not medical advice. Data is from US FDA "
              "reports and labels — always confirm with the official label "
              "and a pharmacist/doctor.")

POPULAR = ["paracetamol", "ibuprofen", "metformin", "amoxicillin",
           "atorvastatin", "omeprazole"]


def _page(title, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Drug Safety Lookup</title>
<link rel="manifest" href="/drugsafety/manifest.json">
<meta name="theme-color" content="{THEME}">
<link rel="apple-touch-icon" href="/drugsafety/icon-192.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<style>
:root{{--t:{THEME}}}
*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;background:#fef2f2;color:#3f1d1d;line-height:1.55}}
.wrap{{max-width:960px;margin:0 auto;padding:16px}}
header.hero{{background:linear-gradient(135deg,#b91c1c,#ef4444);color:#fff;padding:36px 16px;text-align:center}}
.hero h1{{margin:0 0 8px;font-size:1.9rem}}.hero p{{margin:6px auto;max-width:640px;opacity:.95}}
.card{{background:#fff;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 2px 10px rgba(220,38,38,.08);border:1px solid #fecaca}}
.btn{{display:inline-block;background:var(--t);color:#fff;border:none;border-radius:10px;padding:12px 22px;font-size:1rem;cursor:pointer;text-decoration:none;margin:6px 4px}}
.btn.ghost{{background:#fff;color:var(--t);border:2px solid var(--t)}}
.chip{{display:inline-block;background:#fff;border:2px solid #fca5a5;color:#b91c1c;border-radius:999px;padding:8px 16px;margin:4px;text-decoration:none;font-weight:600}}
.chip:hover{{background:#fee2e2}}
.disclaimer{{background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;padding:12px 16px;font-size:.9rem;margin:14px 0}}
.warnbox{{background:#fef2f2;border:2px solid #dc2626;border-radius:10px;padding:14px 16px;margin:14px 0}}
.methodbox{{background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:14px 16px;font-size:.9rem;margin:14px 0}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #fecaca}}th{{background:#fef2f2}}
.bar{{height:10px;background:#fecaca;border-radius:6px;overflow:hidden;min-width:80px}}
.bar>div{{height:100%;background:linear-gradient(90deg,#f87171,#dc2626)}}
.searchbox{{display:flex;gap:8px;margin:18px 0;flex-wrap:wrap}}
.searchbox input{{flex:1;min-width:200px;padding:14px;border:2px solid #fca5a5;border-radius:10px;font-size:1.05rem}}
.stats{{display:flex;gap:12px;flex-wrap:wrap}}
.stat{{background:#fff;border:1px solid #fecaca;border-radius:12px;padding:12px 18px;flex:1;min-width:140px;text-align:center}}
.stat .n{{font-size:1.6rem;font-weight:800;color:#b91c1c}}
details{{margin:10px 0}}summary{{cursor:pointer;font-weight:700;color:#b91c1c}}
footer{{text-align:center;color:#8a6a6a;font-size:.85rem;padding:24px 16px}}
h2{{color:#b91c1c}}
@media print{{.noprint{{display:none}}body{{background:#fff}}header.hero{{background:#b91c1c}}}}
</style>{extra_head}</head>
<body>{body}
<script>if("serviceWorker" in navigator){{navigator.serviceWorker.register("/drugsafety/sw.js").catch(()=>{{}});}}</script>
</body></html>"""


def _footer():
    return (f'<footer><div class="disclaimer">⚠️ {DISCLAIMER}</div>'
            'Data: <a href="https://open.fda.gov">openFDA</a> (FDA FAERS + drug labels). '
            'Pakistani brands are mapped to generics for lookup — '
            'no Pakistan adverse-event API exists publicly.</footer>')


@router.get("/drugsafety", response_class=HTMLResponse)
def drugsafety_home():
    chips = "".join(
        f'<a class="chip" href="/drugsafety/search?q={c}">{c}</a>'
        for c in POPULAR)
    body = f"""<header class="hero"><div class="wrap">
<h1>💊 Drug Safety Lookup</h1>
<p>Search any medicine — see its reported adverse effects from FDA data, plus label warnings. Pakistani brands work too (Panadol, Brufen, Risek…).</p>
</div></header><div class="wrap">
<div class="disclaimer">⚠️ {DISCLAIMER}</div>
<div class="card"><h2>Search a drug</h2>
<form class="searchbox" action="/drugsafety/search" method="get">
<input name="q" placeholder="e.g. Panadol, ibuprofen, metformin…" autocomplete="off">
<button class="btn" type="submit">Search</button></form>
<div><b>Popular:</b><br>{chips}</div></div>
<div class="card"><h2>How it works</h2>
<ol><li>Type a <b>brand</b> (Pakistani or international) or <b>generic</b> name.</li>
<li>We pull live <b>adverse-event reports</b> (FAERS) and the <b>FDA label</b> via openFDA.</li>
<li>You get ranked side effects, serious-event stats, warnings — and a printable report.</li></ol></div>
<div class="methodbox"><b>📊 Honest methodology</b><ul>
<li>FAERS = <b>voluntarily reported</b> events. A report is <b>not proof</b> the drug caused it.</li>
<li>Serious events are <b>over-reported</b> (mild ones often go unreported).</li>
<li>Data is <b>US-centric</b> (2004 → today). <b>Correlation ≠ causation.</b></li>
<li>No Pakistan adverse-event API exists publicly — Pakistani brands are mapped to generics for lookup.</li></ul></div>
{_footer()}</div>"""
    return HTMLResponse(_page("Drug Safety Lookup", body))


def _results_body(q, res, display, note):
    total = res["total_reports"]
    serious = res["serious_reports"]
    spct = f"{100*serious/total:.1f}%" if total else "—"
    rxns = res["top_reactions"]
    mx = rxns[0][1] if rxns else 1
    rows = "".join(
        f"<tr><td>{html.escape(t.title())}</td>"
        f"<td>{c:,}</td>"
        f'<td><div class="bar"><div style="width:{100*c/mx:.1f}%"></div></div></td></tr>'
        for t, c in rxns)
    lab = res["label"]
    boxed = (f'<div class="warnbox"><b>⛔ BOXED WARNING (FDA label)</b><br>'
             f'{html.escape(lab["boxed_warning"])}</div>' if lab["boxed_warning"] else "")
    ar = lab["adverse_reactions"]
    warns = lab["warnings"]
    label_sec = ""
    if ar:
        label_sec += (f'<details><summary>📄 Label: Adverse Reactions '
                      f'({res["label_name"]})</summary><p>{html.escape(ar[:3000])}'
                      f'{"…" if len(ar) > 3000 else ""}</p></details>')
    if warns:
        label_sec += (f'<details><summary>⚠️ Label: Warnings '
                      f'({res["label_name"]})</summary><p>{html.escape(warns[:3000])}'
                      f'{"…" if len(warns) > 3000 else ""}</p></details>')
    if not label_sec:
        label_sec = ('<p><i>No label sections found for this name — try the '
                     'generic name.</i></p>')
    brand_note = (f'<div class="card">🔄 {html.escape(note)}</div>' if note else "")
    qe = html.escape(q)
    return f"""<header class="hero"><div class="wrap">
<h1>💊 {html.escape(display)}</h1>
<p>Adverse-effect report from FDA data</p>
<form class="searchbox noprint" action="/drugsafety/search" method="get">
<input name="q" value="{qe}" autocomplete="off">
<button class="btn" type="submit">Search</button></form>
</div></header><div class="wrap">
<div class="disclaimer noprint">⚠️ {DISCLAIMER}</div>
{brand_note}{boxed}
<div class="card"><h2>📊 FAERS report summary</h2>
<div class="stats">
<div class="stat"><div class="n">{total:,}</div><div>total reports</div></div>
<div class="stat"><div class="n">{serious:,}</div><div>serious ({spct})</div></div>
</div>
<p style="font-size:.85rem;color:#8a6a6a">FAERS = voluntary reports, 2004 → today. Reporting ≠ proven causation.</p></div>
<div class="card"><h2>Most reported adverse effects</h2>
<table><tr><th>Reaction</th><th>Reports</th><th></th></tr>{rows}</table></div>
<div class="card"><h2>FDA label sections</h2>{label_sec}</div>
<div class="card noprint" style="text-align:center">
<a class="btn" href="/drugsafety/report?q={html.escape(q, quote=True)}">🖨️ Download / Print report</a>
<a class="btn ghost" href="/drugsafety">← New search</a></div>
<div class="methodbox"><b>📊 Honest methodology</b><ul>
<li>FAERS = <b>voluntarily reported</b> events — a report is <b>not proof</b> the drug caused it.</li>
<li>Serious events are <b>over-reported</b>; mild ones often go unreported.</li>
<li>US-centric data (2004 →). <b>Correlation ≠ causation.</b></li>
<li>Always confirm with the official label and a pharmacist/doctor.</li></ul></div>
{_footer()}</div>"""


@router.get("/drugsafety/search", response_class=HTMLResponse)
def drugsafety_search(q: str = ""):
    q = (q or "").strip()
    if not q:
        return HTMLResponse(_page("Drug Safety Lookup",
            '<div class="wrap"><div class="card"><h2>Type a drug name to search.</h2>'
            '<a class="btn" href="/drugsafety">← Back</a></div></div>'))
    display, generic, note = DS.normalize(q)
    res = DS.lookup(generic)
    if not res["ok"]:
        body = f"""<header class="hero"><div class="wrap"><h1>🔍 No data found</h1></div></header>
<div class="wrap"><div class="card">
<h2>{html.escape(res.get('error', 'No data.'))}</h2>
<p>Tips: check the spelling, or try the <b>generic</b> name (e.g. <i>paracetamol</i> instead of <i>Panadol</i>, <i>ibuprofen</i> instead of <i>Brufen</i>).</p>
<a class="btn" href="/drugsafety">← Try again</a></div>{_footer()}</div>"""
        return HTMLResponse(_page("No data", body))
    return HTMLResponse(_page(display, _results_body(q, res, display, note)))


@router.get("/drugsafety/report", response_class=HTMLResponse)
def drugsafety_report(q: str = ""):
    q = (q or "").strip()
    if not q:
        return HTMLResponse(_page("Report", '<div class="wrap"><div class="card">'
            '<a class="btn" href="/drugsafety">← Search first</a></div></div>'))
    display, generic, note = DS.normalize(q)
    res = DS.lookup(generic)
    if not res["ok"]:
        return HTMLResponse(_page("No data",
            f'<div class="wrap"><div class="card"><h2>{html.escape(res["error"])}</h2>'
            '<a class="btn" href="/drugsafety">← Back</a></div></div>'))
    total, serious = res["total_reports"], res["serious_reports"]
    spct = f"{100*serious/total:.1f}%" if total else "—"
    rows = "".join(
        f"<tr><td>{i+1}</td><td>{html.escape(t.title())}</td><td>{c:,}</td></tr>"
        for i, (t, c) in enumerate(res["top_reactions"]))
    lab = res["label"]
    boxed = (f'<div class="warnbox"><b>⛔ BOXED WARNING</b><br>'
             f'{html.escape(lab["boxed_warning"])}</div>' if lab["boxed_warning"] else "")
    ar = f'<h2>Label adverse reactions</h2><p>{html.escape(lab["adverse_reactions"][:4000])}</p>' \
        if lab["adverse_reactions"] else ""
    warns = f'<h2>Label warnings</h2><p>{html.escape(lab["warnings"][:4000])}</p>' \
        if lab["warnings"] else ""
    note_html = f'<p><i>{html.escape(note)}</i></p>' if note else ""
    body = f"""<div class="wrap">
<div class="noprint" style="text-align:center;margin:16px 0">
<button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
<a class="btn ghost" href="/drugsafety/search?q={html.escape(q, quote=True)}">← Back to results</a></div>
<h1>💊 Drug Safety Report: {html.escape(display)}</h1>
<p><i>{html.escape(note)}</i></p>
<div class="disclaimer">⚠️ {DISCLAIMER}</div>
{boxed}
<h2>FAERS summary (US FDA, 2004 → today)</h2>
<table><tr><th>Total reports</th><th>Serious reports</th><th>Serious %</th></tr>
<tr><td>{total:,}</td><td>{serious:,}</td><td>{spct}</td></tr></table>
<h2>Most reported adverse effects</h2>
<table><tr><th>#</th><th>Reaction</th><th>Reports</th></tr>{rows}</table>
{ar}{warns}
<div class="methodbox"><b>Methodology:</b> FAERS adverse events are voluntarily reported —
reporting does not prove causation; serious events are over-reported; data is US-centric.
Always confirm with the official label and a pharmacist/doctor.</div>
<p style="font-size:.8rem;color:#8a6a6a">Generated from openFDA (api.fda.gov). Not medical advice.</p>
</div>"""
    return HTMLResponse(_page(f"Report: {display}", body))


@router.get("/drugsafety/manifest.json")
def drugsafety_manifest():
    return Response(content=(_HERE / "manifest.json").read_bytes(),
                    media_type="application/manifest+json")


@router.get("/drugsafety/sw.js")
def drugsafety_sw():
    return Response(content=(_HERE / "sw.js").read_bytes(),
                    media_type="application/javascript")


@router.get("/drugsafety/icon-{size}.png")
def drugsafety_icon(size: str):
    p = _HERE / f"icon-{size}.png"
    if not p.exists():
        return Response(status_code=404)
    return Response(content=p.read_bytes(), media_type="image/png")
