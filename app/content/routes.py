"""Content Engine app — single-user AI short-video studio. Route: /content

Chat-first UI (Zubair's ask): the front door is a chat — "ye video bana kar
lao" and the agent brings the video back. No login, no plans.

Thin app + VM worker queue (medexplain-render pattern): the container never
renders video. Heavy work (TTS + ffmpeg) runs on the VM via content_worker.py,
bridged over the worker API below.
"""
import html
import hmac
import json
import os
import shutil
import time

from fastapi import APIRouter, Request, Form, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse

from app.content import db
from app.content import agent

router = APIRouter()

WORKER_KEY = os.environ.get("CONTENT_WORKER_KEY", "")
RESULT_TTL_DAYS = 30

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.5;background:#e5ddd5}
.wrap{max-width:760px;margin:0 auto;padding:0 14px}
.nav{background:#1e1b4b;color:#fff;padding:10px 0;font-size:.95rem;position:sticky;top:0;z-index:5}
.nav a{color:#fff;text-decoration:none;margin-right:18px;font-weight:700}
.chathead{background:#075e54;color:#fff;padding:14px 0}
.chathead h1{margin:0;font-size:1.25rem}
.chathead p{margin:4px 0 0;opacity:.9;font-size:.9rem}
#thread{padding:18px 0 90px}
.msg{max-width:82%;padding:10px 14px;border-radius:14px;margin:8px 0;word-wrap:break-word;font-size:.95rem}
.msg.user{background:#dcf8c6;margin-left:auto;border-bottom-right-radius:4px}
.msg.agent{background:#fff;margin-right:auto;border-bottom-left-radius:4px;box-shadow:0 1px 1px rgba(0,0,0,.12)}
.msg .meta{font-size:.72rem;color:#888;margin-top:4px}
.msg video{max-width:100%;border-radius:8px;background:#000;margin-top:6px}
.msg .dl a{display:inline-block;background:#1e1b4b;color:#fff;font-size:.8rem;font-weight:700;
padding:6px 12px;border-radius:8px;text-decoration:none;margin:6px 6px 0 0}
.msg .dl a.s{background:#7c3aed}
#composer{position:fixed;bottom:0;left:0;right:0;background:#f0f0f0;padding:10px 0;border-top:1px solid #ddd}
#composer .wrap{display:flex;gap:8px}
#composer input{flex:1;padding:12px;border:1px solid #ccc;border-radius:24px;font-size:1rem;outline:none}
#composer button{background:#075e54;color:#fff;border:0;border-radius:24px;padding:0 22px;font-size:1rem;font-weight:700;cursor:pointer}
.panel{background:#fff;border-radius:12px;padding:18px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.1)}
input[type=text],select{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;margin:6px 0 12px;font-size:1rem;box-sizing:border-box}
details{margin:10px 0;border:1px solid #e5e5e5;border-radius:10px;padding:12px 16px;background:#fff}
summary{font-weight:600;cursor:pointer}
footer{padding:26px 0;color:#666;font-size:.9rem;background:#fff}
.btn{display:inline-block;background:#7c3aed;color:#fff;font-weight:700;padding:10px 22px;border-radius:10px;
text-decoration:none;margin:4px 8px 4px 0;border:0;cursor:pointer;font-size:1rem}
.btn.small{padding:8px 16px;font-size:.9rem}.btn.danger{background:#dc2626}.btn.dark{background:#1e1b4b}
table{border-collapse:collapse;width:100%;margin:12px 0;background:#fff}
td,th{border:1px solid #e5e5e5;padding:8px 10px;text-align:left;font-size:.92rem}
th{background:#f8fafc}
.status{font-weight:700}
.st-queued{color:#b45309}.st-working{color:#2563eb}.st-ready{color:#7c3aed}.st-failed{color:#dc2626}
.alert{background:#fef3c7;border:1px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:14px 0}
pre{white-space:pre-wrap}
"""


def _page(title, body):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Content Engine</title>
<meta name="description" content="Content Engine: AI short-video studio. Chat an agent, get a video.">
<style>{CSS}</style></head><body>
<div class="nav"><div class="wrap"><a href="/content">💬 Content Engine</a>
<a href="/content/library">📼 Meri videos</a></div></div>
{body}
<script>
let lastId = 0;
function esc(s){{return s;}}
function addMsg(m){{
  const t = document.getElementById('thread');
  if(!t) return;
  if(m.id > lastId) lastId = m.id;
  const d = document.createElement('div');
  d.className = 'msg ' + m.role;
  d.innerHTML = m.html;
  t.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}}
async function fetchNew(){{
  try{{
    const r = await fetch('/content/api/messages?after=' + lastId);
    const j = await r.json();
    j.messages.forEach(addMsg);
  }}catch(e){{}}
}}
async function sendMsg(e){{
  e.preventDefault();
  const inp = document.getElementById('chatinput');
  const text = inp.value.trim();
  if(!text) return false;
  inp.value = '';
  const r = await fetch('/content/api/chat', {{
    method:'POST',
    headers:{{'Content-Type':'application/x-www-form-urlencoded'}},
    body:'text=' + encodeURIComponent(text)
  }});
  const j = await r.json();
  j.messages.forEach(addMsg);
  return false;
}}
document.addEventListener('DOMContentLoaded', () => {{
  document.querySelectorAll('#thread .msg').forEach(el => {{
    lastId = Math.max(lastId, parseInt(el.dataset.mid || 0));
  }});
  setInterval(fetchNew, 4000);
  fetchNew();
}});
</script>
</body></html>"""


def _check_worker(x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    if not WORKER_KEY or not hmac.compare_digest(x_worker_key or "", WORKER_KEY):
        raise HTTPException(status_code=403, detail="forbidden")


def _prune_old_results():
    base = db.results_dir()
    cutoff = time.time() - RESULT_TTL_DAYS * 86400
    try:
        for vid in os.listdir(base):
            d = os.path.join(base, vid)
            if os.path.isdir(d) and os.path.getmtime(d) < cutoff:
                shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass


def _status_label(v):
    return {"ready_for_approval": "ready"}.get(v["status"], v["status"]).replace("_", " ")


def _result_files(vid):
    d = db.results_dir(vid)
    files = {}
    for name in ("final.mp4", "final_1x1.mp4", "final_16x9.mp4", "seo.json",
                 "manifest.json", "qc_report.json", "thumbnail.png", "captions.srt",
                 "UPLOAD_CHECKLIST.md"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            files[name] = p
    return files


def _video_card(vid):
    """HTML for a delivered video inside a chat message."""
    v = db.get_video(vid)
    if not v:
        return "<i>Video not found.</i>"
    files = _result_files(vid)
    qc = f"{v['qc_score']:.0f}/100" if v["qc_score"] is not None else "--"
    if v["status"] != "ready_for_approval":
        return (f"⏳ <b>{html.escape(v['topic'][:80])}</b><br>"
                f"Status: <span class='status st-{v['status']}'>{html.escape(_status_label(v))}</span>"
                f"{f' (stage: {html.escape(v['stage'])})' if v['stage'] else ''}")
    preview = (f"<video controls src='/content/v/{vid}/dl/final.mp4'></video><br>"
               if "final.mp4" in files else "")
    btns = ""
    labels = {"final.mp4": "📱 9:16", "final_1x1.mp4": "⬛ 1:1", "final_16x9.mp4": "📺 16:9",
              "seo.json": "📝 SEO pack", "UPLOAD_CHECKLIST.md": "✅ Upload checklist"}
    for f, label in labels.items():
        if f in files:
            btns += f"<a href='/content/v/{vid}/dl/{f}'>{label}</a>"
    btns += f"<a class='s' href='/content/v/{vid}'>🔍 Full page</a>"
    return (f"<b>🎬 {html.escape(v['topic'][:80])}</b> · QC {qc}<br>"
            f"{preview}<div class='dl'>{btns}</div>")


def _msg_html(m):
    """Pre-rendered HTML for a chat message (used by the polling API)."""
    when = time.strftime("%H:%M", time.gmtime(m["created_at"]))
    if m["kind"] == "video":
        body = _video_card(m["vid"])
    elif m["kind"] == "status":
        # status messages are built server-side with topics html-escaped already
        body = m["text"].replace("\n", "<br>")
    else:
        body = html.escape(m["text"]).replace("\n", "<br>")
    body += f"<div class='meta'>{when}</div>"
    return {"id": m["id"], "role": m["role"],
            "html": body}


def _say(role, kind, text, vid=""):
    m = db.add_message(role, kind, text, vid)
    return _msg_html(m)


def _welcome_seed():
    if not db.list_messages(limit=1):
        s = db.get_settings()
        db.add_message("agent", "text",
            "Assalam-o-Alaikum! 🎬 Mein aapka video agent hoon.\n"
            "Mujhe bolo: **'X pe video bana kar lao'** — aur video tayar karke launga.\n"
            "'help' likho agar guide chahiye." +
            (f"\nMeri niche: {s['niche']}" if s["niche"] else ""))


# --------------------------------------------------------------- chat page ---
@router.get("/content", response_class=HTMLResponse)
@router.get("/content/", response_class=HTMLResponse)
def index(request: Request):
    _prune_old_results()
    _welcome_seed()
    s = db.get_settings()
    msgs = db.list_messages(limit=200)
    thread = "".join(
        f"<div class='msg {m['role']}' data-mid='{m['id']}'>{_msg_html(m)['html']}</div>"
        for m in msgs)
    auto_checked = "checked" if s["weekly_auto"] else ""
    lang_opts = "".join(
        f"<option value='{v}' {'selected' if s['language'] == v else ''}>{l}</option>"
        for v, l in (("en", "English"), ("ur", "Urdu")))
    body = f"""
<div class="chathead"><div class="wrap">
<h1>🎬 Content Engine</h1>
<p>Chat karo — video tayar karke launga. Topic in, video out.</p>
</div></div>
<div class="wrap">
<div id="thread">{thread}</div>
</div>
<div id="composer"><div class="wrap">
<form onsubmit="return sendMsg(event)" style="display:flex;gap:8px;width:100%">
<input id="chatinput" type="text" placeholder="e.g. dental implants pe video bana kar lao" autocomplete="off">
<button type="submit">➤</button>
</form></div></div>
<div class="wrap">
<div class="panel" style="margin-top:14px">
<details><summary>⚙️ Settings (niche · language · voice · weekly auto)</summary>
<form method="post" action="/content/api/settings">
<label>Niche / topic theme</label>
<input type="text" name="niche" value="{html.escape(s['niche'])}" placeholder="e.g. AI tools for small business">
<label>Video language</label>
<select name="language">{lang_opts}</select>
<label>Voice (optional — voice name, blank = default)</label>
<input type="text" name="voice" value="{html.escape(s['voice'])}" placeholder="e.g. male, female, narrator">
<label><input type="checkbox" name="weekly_auto" value="1" {auto_checked} style="width:auto">
<b>Auto-generate weekly</b> — one video/week from my niche, delivered in chat</label><br>
<button class="btn dark small" type="submit">Save</button>
</form>
</details>
<details><summary>⚠️ Honest limits — padhna zaroori</summary>
<ul>
<li>Rendering queue par hoti hai — <b>5–20 minute</b> lagte hain (status chat me milega).</li>
<li><b>AI text-to-video nahi</b> — AI-assisted: research, script, AI images + voiceover.</li>
<li><b>Auto-publishing nahi</b> — video download karo, TikTok/IG/YouTube par khud upload karo.</li>
<li>Files <b>30 din</b> baad auto-delete — save karna zaroori.</li>
</ul>
</details>
</div>
<footer>Content Engine — topic in, platform-ready video + SEO pack out.</footer>
</div>"""
    return HTMLResponse(_page("Content Engine", body))


@router.post("/content/api/settings")
def api_settings(niche: str = Form(None), language: str = Form(None),
                 voice: str = Form(None), weekly_auto: str = Form(None)):
    db.save_settings(niche=niche, language=language, voice=voice,
                     weekly_auto=(weekly_auto == "1") if weekly_auto is not None else None)
    s = db.get_settings()
    m = db.add_message("agent", "text",
        f"✅ Settings save ho gayi:\n"
        f"• Niche: {s['niche'] or '—'}\n"
        f"• Language: {'Urdu' if s['language'] == 'ur' else 'English'}\n"
        f"• Voice: {s['voice'] or 'default'}\n"
        f"• Weekly auto: {'ON 🤖' if s['weekly_auto'] else 'off'}")
    return RedirectResponse("/content/", status_code=303)


# ------------------------------------------------------------ chat brain ---
@router.post("/content/api/chat")
def api_chat(text: str = Form("")):
    t = (text or "").strip()[:2000]
    if not t:
        return {"messages": []}
    db.add_message("user", "text", t)
    out = []
    r = agent.parse(t)
    intent = r["intent"]
    s = db.get_settings()

    if intent == "help":
        out.append(_say("agent", "text", agent.help_text()))

    elif intent == "list":
        vids = db.list_videos(limit=6)
        if not vids:
            out.append(_say("agent", "text",
                "📼 Abhi koi video nahi hai. 'X pe video banao' likho — mein bana dunga!"))
        else:
            out.append(_say("agent", "text", f"📼 Aapki {len(vids)} videos:"))
            for v in vids:
                if v["status"] == "ready_for_approval":
                    out.append(_say("agent", "video", "", vid=v["id"]))
                else:
                    out.append(_say("agent", "status",
                        f"<b>{html.escape(v['topic'][:80])}</b><br>"
                        f"Status: <span class='status st-{v['status']}'>"
                        f"{html.escape(_status_label(v))}</span>"
                        f"{f' (stage: {html.escape(v['stage'])})' if v['stage'] else ''}"))

    elif intent == "status":
        busy = db.qone("SELECT * FROM videos WHERE status IN ('queued','working')"
                       " ORDER BY created_at DESC LIMIT 1")
        if busy:
            v = dict(busy)
            stage = f" (stage: {v['stage']})" if v["stage"] else ""
            out.append(_say("agent", "status",
                f"⏳ <b>{html.escape(v['topic'][:80])}</b><br>"
                f"<span class='status st-{v['status']}'>{html.escape(_status_label(v))}</span>{stage}<br>"
                "Usually 5–20 min. Tayyar hote hi yahan bata dunga!"))
        else:
            latest = db.qone("SELECT * FROM videos ORDER BY created_at DESC LIMIT 1")
            if latest:
                v = dict(latest)
                if v["status"] == "ready_for_approval":
                    out.append(_say("agent", "video", "✅ Ye wali tayar hai:", vid=v["id"]))
                else:
                    out.append(_say("agent", "text",
                        f"Last video '{v['topic'][:60]}' — {_status_label(v)}. Nayi chahiye? Topic batao!"))
            else:
                out.append(_say("agent", "text",
                    "📼 Abhi koi video nahi hai. 'X pe video banao' likho!"))

    elif intent == "set_niche":
        db.save_settings(niche=r["niche"])
        out.append(_say("agent", "text",
            f"✅ Niche save: **{r['niche']}**\nAb auto-videos isi theme se banengi."))

    elif intent == "set_language":
        db.save_settings(language=r["language"])
        out.append(_say("agent", "text",
            f"✅ Language: **{'Urdu' if r['language'] == 'ur' else 'English'}**\n"
            "Agli videos isi language me hongi."))

    elif intent == "set_voice":
        db.save_settings(voice=r["voice"])
        out.append(_say("agent", "text",
            f"✅ Voice: **{r['voice']}** — agli videos me use hogi."))

    elif intent == "new_video":
        v = db.create_video(r["topic"], s["niche"])
        out.append(_say("agent", "text",
            f"⏳ **Ban rahi hai:** {r['topic']}\n"
            f"5–20 minute lagega. Tayyar hote hi yahan launga! 🎬",
            vid=v["id"]))

    elif intent == "new_video_ask":
        out.append(_say("agent", "text",
            "Video kis topic par banau? 🤔\nJaise: 'dental implants pe video banao'"))

    else:  # fallback — ask one clarifying question, never guess
        out.append(_say("agent", "text",
            "Samjha nahi — mein ye kar sakta hoon:\n"
            "🎬 'X pe video banao' — nayi video\n"
            "⏳ 'meri video kahan tak pahunchi?' — status\n"
            "📼 'meri videos dikhao' — library\n"
            "⚙️ 'meri niche dental clinic hai' · 'language urdu' · 'voice male'\n"
            "'help' likho agar poori guide chahiye."))

    return {"messages": out}


@router.get("/content/api/messages")
def api_messages(after: int = 0):
    return {"messages": [_msg_html(m) for m in db.list_messages(after=after)]}


# ---------------------------------------------------------------- library ---
@router.get("/content/library", response_class=HTMLResponse)
def library():
    _prune_old_results()
    videos = db.list_videos()
    cards = ""
    for v in videos:
        when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(v["created_at"]))
        qc = f"{v['qc_score']:.0f}" if v["qc_score"] is not None else "—"
        auto_tag = " 🤖" if v["auto"] else ""
        if v["status"] == "ready_for_approval":
            action = f"<a href='/content/v/{v['id']}'>Preview &amp; download</a>"
        elif v["status"] in ("queued", "working"):
            action = f"<span style='color:#666'>rendering{v['stage'] and ' (' + html.escape(v['stage']) + ')'}</span>"
        elif v["status"] == "failed":
            action = f"<span style='color:#dc2626' title='{html.escape((v['error'] or '')[:200])}'>failed</span>"
        else:
            action = "—"
        cards += (f"<tr><td>{html.escape(v['topic'][:55])}{auto_tag}</td>"
                  f"<td><span class='status st-{v['status']}'>{html.escape(_status_label(v))}</span></td>"
                  f"<td>{qc}</td><td>{when}</td><td>{action}</td></tr>")
    if not cards:
        cards = "<tr><td colspan='5' style='color:#666'>No videos yet.</td></tr>"
    body = f"""<div class="wrap"><div class="panel">
<h2 style="margin-top:0">📼 Meri videos</h2>
<table><tr><th>Topic</th><th>Status</th><th>QC</th><th>Created</th><th></th></tr>{cards}</table>
<p><a href="/content/">← Chat par wapas</a></p>
</div><footer>Videos auto-delete after 30 days.</footer></div>"""
    return HTMLResponse(_page("Meri videos", body))


# ------------------------------------------------------- video pages ---
@router.get("/content/v/{vid}", response_class=HTMLResponse)
def video_detail(vid: str):
    v = db.get_video(vid)
    if not v:
        return HTMLResponse(_page("Not found", "<div class='wrap'><div class='panel'>Video not found.</div></div>"), status_code=404)
    files = _result_files(vid)
    when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(v["created_at"]))
    qc = f"{v['qc_score']:.0f}/100" if v['qc_score'] is not None else "--"

    if v["status"] in ("queued", "working"):
        main = (f"<div class='alert'><b><span class='status st-{v['status']}'>"
                f"{html.escape(_status_label(v))}</span></b> — rendering in the production queue"
                f"{f' (stage: {html.escape(v['stage'])})' if v['stage'] else ''}. "
                "Usually 5–20 minutes.</div><meta http-equiv='refresh' content='30'>")
    elif v["status"] == "failed":
        main = (f"<div class='alert'><b>Failed</b> at stage '{html.escape(v['stage'])}'.<br>"
                f"<code>{html.escape((v['error'] or '')[:500])}</code></div>")
    elif v["status"] == "ready_for_approval":
        dl = "".join(f"<a class='btn dark small' href='/content/v/{vid}/dl/{f}'>{f}</a> " for f in files)
        seo_note = ""
        if "seo.json" in files:
            try:
                seo = json.load(open(files["seo.json"]))
                tags = ' '.join(seo.get('hashtags', [])[:8])
                seo_note = (f"<div class='panel'><b>Suggested title:</b> {html.escape(str(seo.get('title', ''))[:200])}<br>"
                            f"<b>Hashtags:</b> {html.escape(tags)}</div>")
            except Exception:
                pass
        main = f"""
{f"<video controls src='/content/v/{vid}/dl/final.mp4' style='max-height:480px;max-width:100%'></video>" if 'final.mp4' in files else ''}
{seo_note}
<h3>Downloads</h3><p>{dl}</p>
<form method="post" action="/content/v/{vid}/delete" onsubmit="return confirm('Delete this video and its files?')">
<button class="btn danger small" type="submit">Delete video</button></form>
<p style="color:#666;font-size:.9rem">Files auto-delete after 30 days — download what you want to keep.</p>"""
    else:
        main = ""

    body = f"""<div class="wrap"><div class="panel">
<h2 style="margin-top:0">{html.escape(v['topic'][:80])}</h2>
<p style="color:#666">Status: <span class='status st-{v['status']}'>{html.escape(_status_label(v))}</span>
 · QC: {qc} · Created {when}</p>
{main}
<p><a href="/content/">← Chat</a> · <a href="/content/library">Library</a></p>
</div></div>"""
    return HTMLResponse(_page("Video", body))


@router.post("/content/v/{vid}/delete")
def video_delete(vid: str):
    v = db.get_video(vid)
    if v:
        shutil.rmtree(db.results_dir(vid), ignore_errors=True)
        db.delete_video(vid)
        for m in db.qall("SELECT id FROM messages WHERE vid=?", (vid,)):
            db.delete_message(m["id"])
    return RedirectResponse("/content/", status_code=303)


@router.get("/content/v/{vid}/dl/{fname}")
def video_download(vid: str, fname: str):
    v = db.get_video(vid)
    if not v:
        raise HTTPException(404)
    allowed = {"final.mp4", "final_1x1.mp4", "final_16x9.mp4", "seo.json", "manifest.json",
               "qc_report.json", "thumbnail.png", "captions.srt", "UPLOAD_CHECKLIST.md"}
    if fname not in allowed:
        raise HTTPException(404)
    p = os.path.join(db.results_dir(vid), fname)
    if not os.path.exists(p):
        return HTMLResponse(_page("Expired",
                                  "<div class='wrap'><div class='alert'>This file has expired "
                                  "(results auto-delete after 30 days).</div></div>"), status_code=410)
    media = "video/mp4" if fname.endswith(".mp4") else None
    return FileResponse(p, filename=fname, media_type=media)


# -------------------------------------------------------------- worker API ---
@router.get("/content/api/worker/next")
def worker_next(x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    # Stale-claim recovery: a worker that died mid-render leaves 'working'
    # rows; reclaim them after 45 minutes so jobs don't stall forever.
    stale = db.now() - 45 * 60
    row = db.qone(
        "SELECT * FROM videos WHERE status='queued' "
        "OR (status='working' AND updated_at < ?) ORDER BY created_at ASC LIMIT 1",
        (stale,))
    if not row:
        return {"job": None}
    v = dict(row)
    db.set_video_status(v["id"], "working", "claimed")
    # Client's global settings travel with the job: niche, language, voice.
    v["settings"] = db.get_settings()
    return {"job": v}


@router.post("/content/api/worker/jobs/{vid}/status")
async def worker_job_status(request: Request, vid: str,
                            x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    try:
        s = await request.json()
    except Exception:
        s = {}
    status = str(s.get("status", ""))
    stage = str(s.get("stage", ""))
    error = str(s.get("error", ""))
    qc_score = s.get("qc_score")
    if status not in ("working", "ready_for_approval", "failed"):
        raise HTTPException(400, "bad status")
    prev = db.get_video(vid)
    if not prev:
        raise HTTPException(404)
    db.set_video_status(vid, status, stage, error, qc_score)
    topic = prev["topic"][:70]
    # Progress lands in chat as agent messages (only on real transitions).
    if status == "working" and prev["status"] != "working":
        db.add_message("agent", "status",
            f"🔄 **Rendering shuru:** {topic}<br>"
            f"Stage: {stage or '—'}. 5–20 minute lagenge.")
    elif status == "ready_for_approval" and prev["status"] != "ready_for_approval":
        db.add_message("agent", "text", f"✅ **Video tayar!** '{topic}' — ye raha:")
        db.add_message("agent", "video", "", vid=vid)
    elif status == "failed" and prev["status"] != "failed":
        db.add_message("agent", "text",
            f"❌ **'{topic}' fail ho gayi** (stage: {stage}).\n"
            f"Wajah: {error[:300]}")
    return {"ok": True}


@router.post("/content/api/worker/result/{vid}")
async def worker_result(request: Request, vid: str,
                        x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    _check_worker(x_worker_key)
    v = db.get_video(vid)
    if not v:
        raise HTTPException(404)
    form = await request.form()
    d = db.results_dir(vid)
    saved = []
    allowed = {"final.mp4", "final_1x1.mp4", "final_16x9.mp4", "seo.json", "manifest.json",
               "qc_report.json", "thumbnail.png", "captions.srt", "UPLOAD_CHECKLIST.md"}
    for key, up in form.multi_items():
        if key == "file":
            name = os.path.basename(up.filename or "file")
            if name in allowed:
                with open(os.path.join(d, name), "wb") as f:
                    shutil.copyfileobj(up.file, f)
                saved.append(name)
    qc_score = None
    qp = os.path.join(d, "qc_report.json")
    if os.path.exists(qp):
        try:
            qc_score = json.load(open(qp)).get("score")
        except Exception:
            pass
    db.set_video_status(vid, "ready_for_approval", "done", qc_score=qc_score)
    db.add_message("agent", "text", f"✅ **Video tayar!** '{v['topic'][:70]}' — ye raha:")
    db.add_message("agent", "video", "", vid=vid)
    return {"ok": True, "saved": saved}


@router.post("/content/api/worker/autoqueue")
def worker_autoqueue(x_worker_key: str = Header(default="", alias="X-Worker-Key")):
    """Queue one weekly auto-video if the toggle is ON and none in the last 7 days."""
    _check_worker(x_worker_key)
    _prune_old_results()
    s = db.get_settings()
    if not s["weekly_auto"]:
        return {"ok": True, "queued": []}
    week_ago = db.now() - 7 * 86400
    recent = db.qone("SELECT id FROM videos WHERE auto=1 AND created_at>?", (week_ago,))
    if recent:
        return {"ok": True, "queued": []}
    v = db.create_video("", s["niche"], auto=True)
    db.add_message("agent", "status",
        f"🤖 **Weekly auto-video queue ho gayi:** '{v['topic'][:70]}'<br>"
        "Tayyar hote hi yahan bata dunga.")
    return {"ok": True, "queued": [v["id"]]}
