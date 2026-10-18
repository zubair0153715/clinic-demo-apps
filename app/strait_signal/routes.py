"""Strait Signal status + events endpoints.

Unlisted: no navigation links point here. Owner-only style — these are
operational endpoints for the venture owner, not public pages. The
status payload reports key_set as a boolean ONLY; the key value is
never exposed.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .state import STATE

router = APIRouter(prefix="/strait-signal")


@router.get("/", include_in_schema=False)
def index():
    return RedirectResponse("/strait-signal/live", status_code=302)


@router.get("/live", include_in_schema=False, response_class=HTMLResponse)
def live():
    return HTMLResponse(LIVE_HTML)


LIVE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strait Signal — Live</title>
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#0b1620;color:#e8f0f5;padding:16px}
  h1{font-size:22px;margin:0 0 4px}
  .sub{color:#9fb3c0;font-size:13px;margin-bottom:16px}
  .badge{display:inline-block;padding:8px 16px;border-radius:999px;font-weight:700;font-size:16px;margin:8px 0}
  .badge.streaming{background:#14532d;color:#bbf7d0}
  .badge.idle{background:#5b4300;color:#fde68a}
  .badge.backoff{background:#5b4300;color:#fde68a}
  .badge.error{background:#5f2120;color:#fecaca}
  .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:16px 0}
  .card{background:#132637;border-radius:12px;padding:12px}
  .card .label{font-size:12px;color:#9fb3c0;text-transform:uppercase;letter-spacing:.04em}
  .card .value{font-size:22px;font-weight:700;margin-top:4px;word-break:break-word}
  .card .small{font-size:12px;color:#9fb3c0;margin-top:2px}
  .note{font-size:13px;color:#9fb3c0;background:#132637;border-radius:12px;padding:12px;margin:16px 0}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th,td{text-align:left;padding:8px 6px;border-bottom:1px solid #234}
  th{color:#9fb3c0}
  .cand{display:inline-block;background:#5f2120;color:#fecaca;border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700}
  .err{color:#fecaca;font-size:13px}
  #updated{font-size:12px;color:#9fb3c0}
  a{color:#7cc4ff}
</style>
</head>
<body>
<h1>Strait Signal &mdash; Live</h1>
<div class="sub">Hormuz AIS collector &middot; auto-refreshes every 30 seconds</div>
<div id="badge" class="badge idle">LOADING&hellip;</div>
<div class="grid">
  <div class="card"><div class="label">API key</div><div class="value" id="keySet">&mdash;</div></div>
  <div class="card"><div class="label">Messages seen</div><div class="value" id="messages">&mdash;</div></div>
  <div class="card"><div class="label">Vessels seen</div><div class="value" id="vessels">&mdash;</div></div>
  <div class="card"><div class="label">Events found</div><div class="value" id="eventsCount">&mdash;</div></div>
  <div class="card"><div class="label">Last message</div><div class="value" id="lastMsg" style="font-size:14px">&mdash;</div></div>
  <div class="card"><div class="label">Last event</div><div class="value" id="lastEvent" style="font-size:14px">&mdash;</div></div>
</div>
<div id="errorBox" class="note err" style="display:none"></div>
<div class="note" id="prov">Candidate events only. Each event is derived from the collected AIS messages; no vessel is labelled sanctioned.</div>
<h2 style="font-size:17px">Detected events</h2>
<table>
  <thead><tr><th>Type</th><th>Details</th><th>Status</th></tr></thead>
  <tbody id="eventsBody"><tr><td colspan="3">Loading&hellip;</td></tr></tbody>
</table>
<p id="updated"></p>
<script>
function fmt(t){ if(!t) return "—"; try{ return new Date(t).toLocaleString(); }catch(e){ return t; } }
function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
async function refresh(){
  try{
    var s = await (await fetch("/strait-signal/status")).json();
    var badge = document.getElementById("badge");
    var st = (s.status||"idle").toLowerCase();
    badge.className = "badge " + (st==="streaming" ? "streaming" : st==="error" ? "error" : "idle");
    badge.textContent = st==="streaming" ? "● STREAMING" : st==="error" ? "● ERROR" : "● " + st.toUpperCase();
    document.getElementById("keySet").textContent = s.key_set ? "set ✓" : "not set";
    document.getElementById("messages").textContent = s.messages_seen ?? 0;
    document.getElementById("vessels").textContent = s.vessels_seen ?? 0;
    document.getElementById("eventsCount").textContent = s.events_count ?? 0;
    document.getElementById("lastMsg").textContent = fmt(s.last_message_at_utc);
    document.getElementById("lastEvent").textContent = fmt(s.last_event_at_utc);
    var eb = document.getElementById("errorBox");
    if(s.last_error){ eb.style.display="block"; eb.textContent = "Last error: " + s.last_error; }
    else { eb.style.display="none"; }

    var ev = await (await fetch("/strait-signal/events")).json();
    document.getElementById("prov").textContent = ev.provenance || document.getElementById("prov").textContent;
    var rows = [];
    (ev.gap_events||[]).forEach(function(g){
      rows.push("<tr><td>AIS gap</td><td>" + esc(JSON.stringify(g)) + "</td><td><span class='cand'>CANDIDATE — needs human review</span></td></tr>");
    });
    (ev.sts_candidates||[]).forEach(function(c){
      rows.push("<tr><td>Possible ship-to-ship transfer</td><td>" + esc(JSON.stringify(c)) + "</td><td><span class='cand'>CANDIDATE — needs human review</span></td></tr>");
    });
    document.getElementById("eventsBody").innerHTML = rows.length ? rows.join("") : "<tr><td colspan='3'>No events yet. Gap detection needs ~6 hours of coverage.</td></tr>";
    document.getElementById("updated").textContent = "Updated: " + new Date().toLocaleString();
  }catch(e){
    document.getElementById("badge").className = "badge error";
    document.getElementById("badge").textContent = "● ERROR LOADING DATA";
    document.getElementById("eventsBody").innerHTML = "<tr><td colspan='3'>Could not load data. Try refreshing.</td></tr>";
  }
}
refresh();
setInterval(refresh, 30000);
</script>
</body>
</html>"""


@router.get("/status")
def status():
    return JSONResponse(STATE.status_payload())


@router.get("/events")
def events():
    return JSONResponse({
        "collector": "strait_signal",
        "generated_at_utc": STATE.events["generated_at_utc"],
        "messages_read": STATE.events["messages_read"],
        "position_reports_kept": STATE.events["position_reports_kept"],
        "vessels_seen": STATE.events["vessels_seen"],
        "provenance": "Candidate events only. Each event is derived from the "
                      "collected AIS messages; no vessel is labelled sanctioned.",
        "gap_events": STATE.events["gap_events"],
        "sts_candidates": STATE.events["sts_candidates"],
    })
