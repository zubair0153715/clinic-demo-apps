"""LabLink (/lablink) — shared HTML layout, CSS and inline SVG diagrams."""
import html

BASE = "/lablink"

CSS = """
*{box-sizing:border-box}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#16211c;
 background:#f3f6f4;line-height:1.55;padding-bottom:78px}
a{color:#0b3d2e}
header.top{background:#0b3d2e;color:#fff;padding:14px 18px;position:sticky;top:0;z-index:20;
 display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,.15)}
header.top .brand{font-weight:800;font-size:1.1rem;letter-spacing:.3px}
header.top .brand small{display:block;font-weight:400;font-size:.72rem;opacity:.85}
header.top .who{font-size:.8rem;text-align:right;opacity:.95}
header.top .who a{color:#bfe8d2}
.wrap{max-width:920px;margin:0 auto;padding:16px}
.card{background:#fff;border:1px solid #dce5df;border-radius:14px;padding:16px;margin:0 0 14px;
 box-shadow:0 1px 3px rgba(11,61,46,.05)}
.card h2,.card h3{margin:0 0 8px;color:#0b3d2e}
.chip{display:inline-block;background:#e3f2e9;color:#0b3d2e;border-radius:999px;padding:2px 10px;
 font-size:.75rem;font-weight:600;margin:0 6px 6px 0}
.chip.red{background:#fde3e3;color:#8c1d1d}
.chip.amber{background:#fdf3d7;color:#7a5a00}
.chip.blue{background:#e2ecfd;color:#1d3f8c}
.btn{display:inline-block;background:#0b3d2e;color:#fff;font-weight:700;padding:10px 18px;border-radius:10px;
 text-decoration:none;border:0;cursor:pointer;font-size:.95rem}
.btn.alt{background:#fff;color:#0b3d2e;border:2px solid #0b3d2e}
.btn.small{padding:6px 12px;font-size:.85rem}
.btn.red{background:#8c1d1d}
input,select,textarea{width:100%;padding:10px;border:1px solid #c9d4cd;border-radius:9px;font:inherit;
 background:#fff;margin:0 0 10px}
textarea{min-height:90px}
label{font-weight:600;font-size:.88rem;display:block;margin:4px 0 3px;color:#24463a}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{border-bottom:1px solid #e3eae5;padding:7px 8px;text-align:left;vertical-align:top}
th{color:#0b3d2e;background:#f0f6f2}
.search{display:flex;gap:8px}
.search input{margin:0}
.search .btn{white-space:nowrap}
.muted{color:#5c6f66;font-size:.88rem}
.err{background:#fde3e3;border:1px solid #e9a3a3;color:#8c1d1d;border-radius:10px;padding:10px 12px;margin:0 0 12px}
.ok{background:#e3f2e9;border:1px solid #9fd3b4;color:#0b3d2e;border-radius:10px;padding:10px 12px;margin:0 0 12px}
nav.bottom{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid #dce5df;
 display:flex;justify-content:space-around;z-index:30;padding:6px 2px calc(6px + env(safe-area-inset-bottom))}
nav.bottom a{text-decoration:none;color:#5c6f66;font-size:.68rem;text-align:center;flex:1;padding:2px 0}
nav.bottom a .ic{display:block;font-size:1.25rem;line-height:1.2}
nav.bottom a.on{color:#0b3d2e;font-weight:700}
nav.bottom a .badge{background:#c0392b;color:#fff;border-radius:999px;font-size:.62rem;padding:0 5px;
 position:relative;top:-8px;left:-4px}
.diagram{background:#eef5f1;border:1px dashed #9db8aa;border-radius:12px;padding:18px;text-align:center;color:#0b3d2e}
.diagram svg{max-width:340px;width:100%;height:auto}
.comment{border-top:1px solid #e3eae5;padding:8px 0 2px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.dayblock{margin:0 0 14px}
details{border:1px solid #e3eae5;border-radius:10px;padding:10px 12px;margin:0 0 10px;background:#fff}
summary{font-weight:600;cursor:pointer;color:#0b3d2e}
.auth-wrap{max-width:430px;margin:36px auto;padding:0 16px}
ol.proc li{margin:0 0 7px}
h1.pagetitle{color:#0b3d2e;font-size:1.35rem;margin:4px 0 14px}
.rowflex{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
"""

NAV = [
    ("home", "🏠", "Home"),
    ("experiments", "🧪", "Experiments"),
    ("labs", "🔬", "Labs"),
    ("library", "📚", "Library"),
    ("timetable", "🗓️", "Timetable"),
    ("notifications", "🔔", "Alerts"),
    ("profile", "👤", "Profile"),
]


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def layout(title, user, active, body, unread=0):
    who = ""
    if user:
        who = (f'<div class="who">{esc(user["name"])}<br>'
               f'<small>{esc(user["role"].title())}'
               + (f' · {esc(user["batch"])}' if user.get("batch") else "")
               + "</small></div>")
    nav = ""
    if user:
        items = []
        for key, ic, label in NAV:
            badge = ""
            if key == "notifications" and unread:
                badge = f'<span class="badge">{unread}</span>'
            items.append(
                f'<a href="{BASE}/{key}" class="{"on" if active == key else ""}">'
                f'<span class="ic">{ic}</span>{label}{badge}</a>')
        nav = '<nav class="bottom">' + "".join(items) + "</nav>"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — LabLink | SMBBMU Larkana</title>
<meta name="robots" content="noindex">
<style>{CSS}</style></head><body>
<header class="top"><div class="brand">🔗 LabLink<small>SMBBMU Larkana · Pharm-D Labs &amp; Library</small></div>{who}</header>
<div class="wrap">{body}</div>
{nav}
</body></html>"""


def _svg(inner, label):
    return (f'<svg viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{esc(label)}">{inner}</svg>')


_S = 'stroke="#0b3d2e" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"'
_F = 'fill="#bfe8d2" stroke="#0b3d2e" stroke-width="2.5"'

DIAGRAMS = {
    "beaker": _svg(
        f'<path d="M75 15 h50 M82 15 v30 L55 105 a6 6 0 0 0 6 8 h78 a6 6 0 0 0 6-8 L118 45 V15" {_S}/>'
        f'<path d="M66 80 h68 l7 25 H59 z" fill="#7fc7a5" opacity=".65"/>'
        '<text x="100" y="126" text-anchor="middle" font-size="9" fill="#0b3d2e">Beaker — dissolve &amp; heat gently</text>',
        "Beaker diagram"),
    "bottle": _svg(
        f'<rect x="82" y="12" width="36" height="12" rx="3" {_F}/>'
        f'<path d="M88 24 h24 v14 l10 14 v56 a8 8 0 0 1 -8 8 H86 a8 8 0 0 1 -8-8 V52 l10-14 z" {_F}/>'
        '<rect x="88" y="66" width="24" height="30" fill="#fff" stroke="#0b3d2e" stroke-width="1.5"/>'
        '<text x="100" y="80" text-anchor="middle" font-size="7" fill="#0b3d2e">SHAKE</text>'
        '<text x="100" y="90" text-anchor="middle" font-size="7" fill="#0b3d2e">WELL</text>'
        '<text x="100" y="126" text-anchor="middle" font-size="9" fill="#0b3d2e">Shake lotion bottle</text>',
        "Bottle diagram"),
    "flask": _svg(
        f'<path d="M88 12 h24 M94 12 v26 L64 100 a8 8 0 0 0 7 12 h58 a8 8 0 0 0 7-12 L106 38 V12" {_S}/>'
        f'<path d="M74 84 h52 l8 20 H66 z" fill="#7fc7a5" opacity=".65"/>'
        '<path d="M40 118 q10 -6 20 0 t20 0 t20 0 t20 0 t20 0 t20 0" stroke="#3a7bd5" stroke-width="2" fill="none"/>'
        '<text x="100" y="128" text-anchor="middle" font-size="9" fill="#0b3d2e">Water bath 50–60 °C</text>',
        "Flask on water bath diagram"),
    "tablet": _svg(
        f'<rect x="55" y="78" width="90" height="34" rx="6" {_F}/>'
        f'<path d="M92 20 v34 M84 54 h16 l4 24 H96 z" {_S}/>'
        '<ellipse cx="70" cy="42" rx="13" ry="6" fill="#fff" stroke="#0b3d2e" stroke-width="2"/>'
        '<ellipse cx="128" cy="42" rx="13" ry="6" fill="#fff" stroke="#0b3d2e" stroke-width="2"/>'
        '<ellipse cx="100" cy="60" rx="13" ry="6" fill="#fff" stroke="#0b3d2e" stroke-width="2"/>'
        '<text x="100" y="128" text-anchor="middle" font-size="9" fill="#0b3d2e">Granules → compression → tablets</text>',
        "Tablet compression diagram"),
    "funnel": _svg(
        f'<circle cx="100" cy="42" r="30" {_F}/>'
        f'<path d="M100 72 v22 M92 94 h16 v14 a4 4 0 0 1 -4 4 h-8 a4 4 0 0 1 -4-4 z" {_S}/>'
        '<path d="M74 34 a30 30 0 0 1 52 0 z" fill="#7fc7a5" opacity=".8"/>'
        '<path d="M72 52 a30 30 0 0 0 56 0 z" fill="#3a7bd5" opacity=".45"/>'
        '<text x="100" y="128" text-anchor="middle" font-size="9" fill="#0b3d2e">Separating funnel — two layers</text>',
        "Separating funnel diagram"),
    "heart": _svg(
        '<path d="M100 108 C60 84 48 62 48 44 a24 24 0 0 1 44-12 a24 24 0 0 1 8-6 a24 24 0 0 1 8 6 a24 24 0 0 1 44 12 c0 18-12 40-52 64z" '
        'fill="#f6c6c6" stroke="#8c1d1d" stroke-width="2.5"/>'
        '<path d="M100 26 v-12 M88 20 q12 -10 24 0" stroke="#0b3d2e" stroke-width="2.5" fill="none"/>'
        '<text x="100" y="128" text-anchor="middle" font-size="9" fill="#0b3d2e">Cannula → ventricle → lever</text>',
        "Frog heart perfusion diagram"),
    "microscope": _svg(
        f'<path d="M118 18 a10 10 0 1 1 -14 10 l-26 34" {_S}/>'
        f'<rect x="60" y="66" width="58" height="8" rx="3" {_F}/>'
        f'<path d="M84 74 v22 M64 108 h72 M74 96 h52 v12 H74 z" {_S}/>'
        '<circle cx="100" cy="70" r="3.5" fill="#f2b705"/>'
        '<text x="100" y="128" text-anchor="middle" font-size="9" fill="#0b3d2e">Section on stage, x10/x40</text>',
        "Microscope diagram"),
}


def diagram_box(key):
    svg = DIAGRAMS.get(key or "")
    if not svg:
        svg = _svg('<rect x="45" y="30" width="110" height="66" rx="10" fill="#dcebe2" stroke="#0b3d2e" stroke-width="2"/>'
                   '<text x="100" y="68" text-anchor="middle" font-size="11" fill="#0b3d2e">diagram</text>',
                   "diagram")
    return f'<div class="diagram">{svg}</div>'
