"""SehatCheck pages — public, plain-language drug-safety lookup.

Design: clean teal/green health theme, mobile-first, single search box.
Distinct from the MediScribe /drugsafety research prototype (red theme,
PWA, print report): this is the simple public version — one search,
one results page, plain words, honest caveats everywhere.
"""
import html
from datetime import date

from .engine import POPULAR, outcome_share

THEME = "#0f766e"
CAVEAT = ("FAERS reports show <b>correlation, not causation</b> — a report "
          "is not proof the drug caused the event. Serious outcomes are "
          "reported far more often than mild ones, so their share of "
          "reports is much higher than their real-world risk. "
          "<b>NOT medical advice</b> — ask a pharmacist or doctor before "
          "starting, stopping or changing any medicine.")

SOURCE_LINE = ("Source: <a href=\"https://open.fda.gov\">openFDA</a> — "
               "US FDA Adverse Event Reporting System (FAERS, 2004 → today) "
               "and FDA drug labels. Free, no key, no account.")


def _head(title):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — SehatCheck</title>
<meta name="description" content="SehatCheck — free public drug-safety lookup. See reported side effects from FDA data, in plain language. Not medical advice.">
<meta name="theme-color" content="{THEME}">
<style>
*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;background:#f0fdfa;color:#134e4a;line-height:1.6}}
.wrap{{max-width:920px;margin:0 auto;padding:16px}}
header.hero{{background:linear-gradient(135deg,#0f766e,#14b8a6);color:#fff;padding:40px 16px;text-align:center}}
.hero h1{{margin:0 0 8px;font-size:2rem}}.hero p{{margin:6px auto;max-width:620px;opacity:.96}}
.card{{background:#fff;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 2px 10px rgba(15,118,110,.08);border:1px solid #ccfbf1}}
.btn{{display:inline-block;background:{THEME};color:#fff;border:none;border-radius:10px;padding:12px 22px;font-size:1rem;cursor:pointer;text-decoration:none;margin:6px 4px}}
.btn.ghost{{background:#fff;color:{THEME};border:2px solid {THEME}}}
.chip{{display:inline-block;background:#fff;border:2px solid #5eead4;color:#0f766e;border-radius:999px;padding:8px 16px;margin:4px;text-decoration:none;font-weight:600}}
.chip:hover{{background:#ccfbf1}}
.caveat{{background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;padding:12px 16px;font-size:.92rem;margin:14px 0}}
.warnbox{{background:#fef2f2;border:2px solid #dc2626;border-radius:10px;padding:14px 16px;margin:14px 0;color:#7f1d1d}}
.plain{{background:#ecfdf5;border:1px solid #6ee7b7;border-radius:10px;padding:14px 16px;margin:14px 0}}
.methodbox{{background:#f8fafc;border:1px solid #cbd5e1;border-radius:10px;padding:14px 16px;font-size:.9rem;margin:14px 0}}
.searchbox{{display:flex;gap:8px;margin:18px 0;flex-wrap:wrap}}
.searchbox input{{flex:1;min-width:200px;padding:14px;border:2px solid #5eead4;border-radius:10px;font-size:1.05rem}}
.stats{{display:flex;gap:12px;flex-wrap:wrap}}
.stat{{background:#fff;border:1px solid #ccfbf1;border-radius:12px;padding:12px 16px;flex:1;min-width:140px;text-align:center}}
.stat .n{{font-size:1.55rem;font-weight:800;color:#0f766e}}
.stat .n.red{{color:#b91c1c}}
table{{width:100%;border-collapse:collapse;font-size:.92rem}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #ccfbf1}}th{{background:#f0fdfa}}
.bar{{height:10px;background:#ccfbf1;border-radius:6px;overflow:hidden;min-width:80px}}
.bar>div{{height:100%;background:linear-gradient(90deg,#2dd4bf,#0f766e)}}
details{{margin:10px 0}}summary{{cursor:pointer;font-weight:700;color:#0f766e}}
footer{{text-align:center;color:#5f7a77;font-size:.85rem;padding:24px 16px}}
h2{{color:#0f766e}}h3{{color:#115e59}}
.tag{{display:inline-block;background:#ccfbf1;color:#0f766e;border-radius:999px;padding:2px 10px;font-size:.82rem;margin:2px}}
</style></head><body>"""


def _footer(retrieved):
    return (f'<footer><div class="caveat">⚠️ {CAVEAT}</div>'
            f'<p>{SOURCE_LINE}</p>'
            f'<p>Data retrieved {retrieved}. SehatCheck is a free public '
            'information tool — it never diagnoses, prescribes or replaces '
            'a pharmacist or doctor.</p></footer>')


def home_page():
    chips = "".join(
        f'<a class="chip" href="/sehatcheck/search?q={c}">{c}</a>'
        for c in POPULAR)
    body = f"""{_head("SehatCheck — free drug-safety lookup")}
<header class="hero"><div class="wrap">
<h1>🩺 SehatCheck</h1>
<p>Free public drug-safety lookup. Type any medicine — see its reported side effects from FDA data, in plain language. No signup, no card, no account.</p>
</div></header><div class="wrap">
<div class="caveat">⚠️ {CAVEAT}</div>
<div class="card"><h2>Search a medicine</h2>
<form class="searchbox" action="/sehatcheck/search" method="get">
<input name="q" placeholder="e.g. paracetamol, metformin, amoxicillin…" autocomplete="off">
<button class="btn" type="submit">Check safety</button></form>
<div><b>Popular:</b><br>{chips}</div>
<p style="font-size:.9rem;color:#5f7a77">Brand names work too — Panadol, Brufen, Risek, Augmentin and more are mapped to their generic automatically.</p></div>
<div class="card"><h2>How to read the numbers</h2>
<ol>
<li><b>Total reports</b> — how many adverse-event reports mention this drug in the FDA database (2004 → today).</li>
<li><b>Top reported effects</b> — the side effects mentioned most often. "Most reported" does not mean "most likely for you".</li>
<li><b>Serious outcomes</b> — reports that mention death, hospitalisation or disability. These are reported far more often than mild effects, so their share looks bigger than the real risk.</li>
<li><b>FDA label</b> — the official boxed warnings and adverse reactions from the drug's label.</li>
</ol></div>
<div class="methodbox"><b>📊 What this data is — and is not</b><ul>
<li>FAERS is a <b>voluntary reporting</b> system. Anyone can report; reports are <b>not verified</b> and do <b>not prove</b> the drug caused the event.</li>
<li>People usually report when something went wrong — so serious outcomes are <b>over-represented</b>.</li>
<li>Data is <b>US-centric</b>. Pakistan has no public adverse-event API; Pakistani brands are mapped to generics for lookup.</li>
<li>Counts change as new reports arrive. Always confirm with the official label and a pharmacist or doctor.</li></ul></div>
{_footer(date.today().isoformat())}</div></body></html>"""
    return body


def _outcome_stat(label, count, total, red=False):
    share = outcome_share(count, total)
    share_txt = f"{share}%" if share is not None else "—"
    cls = "n red" if red else "n"
    return (f'<div class="stat"><div class="{cls}">{count:,}</div>'
            f'<div>{label}<br><small>{share_txt} of reports</small></div></div>')


def results_page(q, res):
    total = res["total_reports"]
    serious = res["serious_reports"]
    spct = outcome_share(serious, total)
    spct_txt = f"{spct}%" if spct is not None else "—"
    rxns = res["top_reactions"]
    mx = rxns[0][1] if rxns else 1
    rows = "".join(
        f"<tr><td>{html.escape(t.title())}</td><td>{c:,}</td>"
        f"<td>{outcome_share(c, total)}%</td>"
        f'<td><div class="bar"><div style="width:{100 * c / mx:.1f}%"></div></div></td></tr>'
        for t, c in rxns)
    lab = res["label"]
    boxed = (f'<div class="warnbox"><b>⛔ BOXED WARNING — from the FDA label</b><br>'
             f'{html.escape(lab["boxed_warning"])}</div>' if lab["boxed_warning"] else "")
    forms = ("".join(f'<span class="tag">{html.escape(f)}</span>'
                     for f in lab["dosage_forms"]) if lab["dosage_forms"] else "—")
    brands = ("".join(f'<span class="tag">{html.escape(b)}</span>'
                      for b in lab["brand_names"][:12]) if lab["brand_names"] else "—")
    label_sec = ""
    if lab["adverse_reactions"]:
        label_sec += (f'<details><summary>📄 Label: Adverse Reactions</summary>'
                      f'<p>{html.escape(lab["adverse_reactions"][:3000])}'
                      f'{"…" if len(lab["adverse_reactions"]) > 3000 else ""}</p></details>')
    if lab["warnings"]:
        label_sec += (f'<details><summary>⚠️ Label: Warnings</summary>'
                      f'<p>{html.escape(lab["warnings"][:3000])}'
                      f'{"…" if len(lab["warnings"]) > 3000 else ""}</p></details>')
    if lab["dosage_and_administration"]:
        label_sec += (f'<details><summary>💊 Label: Dosage &amp; Administration</summary>'
                      f'<p>{html.escape(lab["dosage_and_administration"][:2000])}'
                      f'{"…" if len(lab["dosage_and_administration"]) > 2000 else ""}</p></details>')
    if not label_sec:
        label_sec = ('<p><i>No label sections found for this name — try the '
                     'generic name.</i></p>')
    note_html = (f'<div class="card">🔄 {html.escape(res["note"])}</div>'
                 if res.get("note") else "")
    retrieved = date.today().isoformat()
    data_date = res.get("last_updated") or "unknown"
    o = res["outcomes"]
    plain = (f'In plain words: out of <b>{total:,} reports</b> mentioning '
             f'{html.escape(res["display"])}, <b>{serious:,} ({spct_txt})</b> '
             f'were marked serious. <b>{o["death"]:,}</b> mention death, '
             f'<b>{o["hospitalization"]:,}</b> mention hospitalisation and '
             f'<b>{o["disability"]:,}</b> mention disability — one report can '
             f'list more than one outcome, so these do not add up to the '
             f'serious total. These are <b>shares of reports, not your personal '
             f'risk</b>: serious events get reported far more often than mild ones.')
    body = f"""{_head(res["display"] + " — SehatCheck")}
<header class="hero"><div class="wrap">
<h1>🩺 {html.escape(res["display"])}</h1>
<p>Public drug-safety report from FDA data</p>
<form class="searchbox" action="/sehatcheck/search" method="get">
<input name="q" value="{html.escape(q)}" autocomplete="off">
<button class="btn" type="submit">Check another</button></form>
</div></header><div class="wrap">
<div class="caveat">⚠️ {CAVEAT}</div>
{note_html}{boxed}
<div class="card"><h2>📊 FAERS report summary</h2>
<div class="stats">
<div class="stat"><div class="n">{total:,}</div><div>total reports</div></div>
<div class="stat"><div class="n">{serious:,}</div><div>serious ({spct_txt})</div></div>
</div>
<h3>Serious outcomes mentioned</h3>
<div class="stats">
{_outcome_stat("Death", o["death"], total, red=True)}
{_outcome_stat("Hospitalisation", o["hospitalization"], total)}
{_outcome_stat("Disability", o["disability"], total)}
</div>
<p style="font-size:.85rem;color:#5f7a77">One report can mention several outcomes — the three counts overlap and do not add up to the serious total. Data: FAERS 2004 → today, last updated {html.escape(data_date)}.</p>
<div class="plain"><b>In plain words:</b> {plain}</div></div>
<div class="card"><h2>Most reported side effects</h2>
<table><tr><th>Effect</th><th>Reports</th><th>Share</th><th></th></tr>{rows}</table>
<p style="font-size:.85rem;color:#5f7a77">"Most reported" means mentioned most often in reports — not "most likely to happen to you".</p></div>
<div class="card"><h2>FDA label</h2>
<p><b>Dosage forms:</b> {forms}</p>
<p><b>Also sold as:</b> {brands}</p>
{label_sec}</div>
<div class="card" style="text-align:center">
<a class="btn ghost" href="/sehatcheck">← New search</a></div>
<div class="methodbox"><b>📊 How to read this page</b><ul>
<li>FAERS reports are <b>voluntary and unverified</b> — reporting does not prove causation.</li>
<li>Serious outcomes are <b>over-reported</b>; mild effects are under-reported.</li>
<li>Outcome counts <b>overlap</b> — do not add death + hospitalisation + disability.</li>
<li>US-centric data (2004 →). Always confirm with the official label and a pharmacist or doctor.</li></ul></div>
{_footer(retrieved)}</div></body></html>"""
    return body


def error_page(q, message):
    qe = html.escape(q or "")
    body = f"""{_head("No data — SehatCheck")}
<header class="hero"><div class="wrap"><h1>🔍 No safety data found</h1></div></header>
<div class="wrap">
<div class="caveat">⚠️ {CAVEAT}</div>
<div class="card"><h2>{html.escape(message)}</h2>
<p>Tips: check the spelling, or try the <b>generic</b> name (e.g. <i>paracetamol</i> instead of <i>Panadol</i>, <i>ibuprofen</i> instead of <i>Brufen</i>).</p>
<form class="searchbox" action="/sehatcheck/search" method="get">
<input name="q" value="{qe}" autocomplete="off">
<button class="btn" type="submit">Try again</button></form>
<a class="btn ghost" href="/sehatcheck">← Back to home</a></div>
{_footer(date.today().isoformat())}</div></body></html>"""
    return body
