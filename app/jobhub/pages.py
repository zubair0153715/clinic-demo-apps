"""Auto-Apply Hub pages — dashboard + profile form (unlisted route)."""

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1a1a1a;line-height:1.55;background:#f7f8fa}
.wrap{max-width:960px;margin:0 auto;padding:0 18px 60px}
header{background:#0b3d2e;color:#fff;padding:28px 0 22px}
header h1{margin:0 0 4px;font-size:1.5rem}
header p{margin:0;opacity:.9}
h2{color:#0b3d2e;margin:26px 0 10px;font-size:1.15rem}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin-top:18px}
.card{background:#fff;border:1px solid #e3e6e8;border-radius:12px;padding:14px}
.card b{font-size:1.5rem;color:#0b3d2e;display:block}
.card span{font-size:.85rem;color:#555}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #eee;font-size:.92rem;vertical-align:top}
th{background:#eef5f1;color:#0b3d2e}
tr:last-child td{border-bottom:0}
.score{display:inline-block;min-width:34px;text-align:center;font-weight:700;border-radius:8px;padding:2px 8px;color:#fff}
.score.hi{background:#15803d}.score.mid{background:#b45309}.score.lo{background:#6b7280}
.tag{display:inline-block;font-size:.78rem;font-weight:600;border-radius:999px;padding:2px 9px;background:#eef5f1;color:#0b3d2e}
.tag.pk{background:#dbeafe;color:#1e40af}.tag.sa{background:#dcfce7;color:#166534}.tag.ae{background:#fef3c7;color:#92400e}
.tag.remote{background:#ede9fe;color:#5b21b6}
a{color:#0b6b4f}
.muted{color:#666;font-size:.9rem}
.note{background:#fffbe6;border:1px solid #f5d76e;border-radius:12px;padding:12px 16px;font-size:.92rem}
.btn{display:inline-block;background:#0b3d2e;color:#fff;font-weight:700;padding:9px 18px;border-radius:9px;text-decoration:none}
.btn.ghost{background:#fff;color:#0b3d2e;border:2px solid #0b3d2e}
form label{display:block;font-weight:600;margin:14px 0 4px}
form input,form textarea,form select{width:100%;padding:9px 10px;border:1px solid #ccc;border-radius:8px;font-size:1rem;box-sizing:border-box}
form .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.empty{background:#fff;border:1px dashed #ccc;border-radius:12px;padding:18px;color:#666}
"""

DASH = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Auto-Apply Hub — Jobs in Pakistan, Saudi Arabia, UAE</title>
<style>__CSS__</style></head><body>
<header><div class="wrap"><h1>🤖 Auto-Apply Hub</h1>
<p>Job applications on autopilot — Pakistan · Saudi Arabia · UAE. Your AI agent team scouts, scores, tailors and applies while you focus on your Pharm-D.</p></div></header>
<div class="wrap">
<div class="cards">
<div class="card"><b>__APPLIED_TODAY__ / __CAP__</b><span>applied today (cap)</span></div>
<div class="card"><b>__NEW_MATCHES__</b><span>new matches</span></div>
<div class="card"><b>__QUEUED__</b><span>waiting for your approval</span></div>
<div class="card"><b>__APPLIED_TOTAL__</b><span>total applications</span></div>
<div class="card"><b>__PROFILE__</b><span>profile complete</span></div>
</div>
<p style="margin-top:14px"><a class="btn" href="/jobhub/profile">✏️ Edit profile &amp; CV data</a>
<a class="btn ghost" href="/jobhub/profile" style="margin-left:8px">Profile: __NAME__ · __EMAIL__</a></p>
<div class="note"><b>How this works:</b> __MODE_TEXT__</div>
__LINKEDIN_NOTE__

<h2>👥 Agent team — follow-ups, replies, deadlines</h2>
__TEAM__

<h2>🎯 Today's matches</h2>
__MATCHES__

<h2>⏳ Approval queue — needs you</h2>
__QUEUE__

<h2>✅ Applied</h2>
__APPLIED__

<h2>🔑 One-time login checklist</h2>
__CHECKLIST__

<p class="muted" style="margin-top:26px">Scope: Pakistan, Saudi Arabia, UAE (+ worldwide-remote Track B/C). Tracks: A bio-AI / regulatory · B AI automation / Python / data · C internships. No application is counted as sent until the employer's own page or email confirms it. A success dialog/page = submitted; no confirmation email/page = unconfirmed, and the log says so.</p>
</div></body></html>"""

PROFILE_FORM = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Auto-Apply Hub — Edit profile</title>
<style>__CSS__</style></head><body>
<header><div class="wrap"><h1>✏️ Your profile vault</h1>
<p>Fill once — the agent team uses this for every application. Your CV file stays at ~/workspace/job-hunt/Zubair-Ahmed-CV.pdf; keep it updated there too.</p></div></header>
<div class="wrap">
<p><a href="/jobhub">← Back to dashboard</a></p>
<form method="post" action="/jobhub/profile">
<div class="row"><div><label>Full name (legal)</label><input name="name" value="__NAME__"></div>
<div><label>Name on CV</label><input name="cv_name" value="__CV_NAME__"></div></div>
<div class="row"><div><label>Email</label><input name="email" value="__EMAIL__"></div>
<div><label>Phone</label><input name="phone" value="__PHONE__"></div></div>
<div class="row"><div><label>City</label><input name="city" value="__CITY__"></div>
<div><label>Country</label><input name="country" value="__COUNTRY__"></div></div>
<div class="row"><div><label>Date of birth</label><input name="dob" value="__DOB__"></div>
<div><label>Degree</label><input name="degree" value="__DEGREE__"></div></div>
<div class="row"><div><label>Institution</label><input name="institution" value="__INSTITUTION__"></div>
<div><label>Session</label><input name="session" value="__SESSION__"></div></div>
<div class="row"><div><label>Start year</label><input name="start_year" value="__START_YEAR__"></div>
<div><label>Education status</label><input name="education_status" value="__EDU_STATUS__"></div></div>
<label>Skills (comma separated)</label><textarea name="skills" rows="3">__SKILLS__</textarea>
<div class="row"><div><label>GitHub</label><input name="github" value="__GITHUB__"></div>
<div><label>LinkedIn</label><input name="linkedin" value="__LINKEDIN__"></div></div>
<div class="row"><div><label>PharmaReg AI</label><input name="pharmareg" value="__PHARMAREG__"></div>
<div><label>LeadForge AI</label><input name="leadforge" value="__LEADFORGE__"></div></div>
<label>Relocation &amp; sponsorship</label><input name="relocation" value="__RELOCATION__">
<div class="row"><div><label>Daily application cap</label><input name="daily_cap" value="__DAILY_CAP__"></div></div>
<p><button class="btn" type="submit" style="border:0;cursor:pointer">💾 Save profile</button></p>
</form>
<p class="muted">Saved profiles sync back to the VM vault (profile.json) on the next Scout run. Never put CNIC, passport or bank details here — applications never need them at this stage.</p>
</div></body></html>"""


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _country_tag(c):
    c = (c or "").upper()
    if c == "PK":
        return '<span class="tag pk">🇵🇰 Pakistan</span>'
    if c == "SA":
        return '<span class="tag sa">🇸🇦 Saudi</span>'
    if c == "AE":
        return '<span class="tag ae">🇦🇪 UAE</span>'
    return '<span class="tag remote">🌍 Remote</span>'


def _score_badge(score):
    try:
        s = int(score)
    except Exception:
        s = 0
    cls = "hi" if s >= 70 else ("mid" if s >= 50 else "lo")
    return f'<span class="score {cls}">{s}</span>'


def _status_tag(status):
    return f'<span class="tag">{_esc(status or "new")}</span>'


def _linkify(escaped):
    import re
    return re.sub(r'(https?://[^\s<]+)',
                  r'<a href="\1" target="_blank" rel="noopener">\1</a>',
                  escaped)


def _mode_text(config):
    if (config or {}).get("auto_apply_mode") == "full":
        return ("<b>⚡ FULL AUTO is ON</b> — the Hub applies by itself, no "
                "per-application approval. The Scout finds roles, the "
                "Matcher scores fit, the Tailor writes a cover note from "
                "your real portfolio, and the Applier submits JD-verified "
                "matches automatically (email directly; guest forms, "
                "session-backed portals and LinkedIn Easy Apply via "
                "browser tasks). Max 4 applications/day across all "
                "channels. Anything needing a fresh account, a CAPTCHA, or "
                "your input lands in the approval queue below.")
    return ("the Scout finds new roles across PK/SA/UAE boards every "
            "morning, the Matcher scores fit, the Tailor writes a cover "
            "note from your real portfolio, and the Applier submits "
            "automatically <b>only</b> where no login is needed (email or "
            "guest form). Anything needing your login, a CAPTCHA, or "
            "LinkedIn lands in the approval queue below. Max 4 "
            "applications/day.")


def _linkedin_note(config):
    li = (config or {}).get("linkedin") or {}
    if not (config or {}).get("linkedin_auto_apply"):
        return ('<div class="note"><b>LinkedIn auto-apply: OFF</b> — '
                'LinkedIn roles stay in the approval queue (account-ban '
                'risk).</div>')
    if li.get("paused"):
        return ('<div class="note" style="background:#fde8e8;border-color:'
                '#e02424"><b>⛔ LinkedIn auto-apply: PAUSED</b> — a '
                'restriction warning, verification challenge, or CAPTCHA '
                'was hit. LinkedIn applying is stopped until you say '
                'resume. Other channels are unaffected.</div>')
    return ('<div class="note" style="background:#fff3e0;border-color:'
            '#f59e0b"><b>⚠️ LinkedIn auto-apply: ON</b> — enabled '
            '2026-11-03 23:52 PKT by your explicit order, after the '
            'account restriction/ban risk warning. Easy Apply only, '
            'strong fits (score ≥ 75), max 1 per run, human-like pacing. '
            'Any restriction warning, verification challenge, or CAPTCHA '
            'pauses LinkedIn immediately — the Hub never pushes through.'
            '</div>')


def _checklist_html(checklist):
    if not (checklist or "").strip():
        return ('<div class="empty">Login checklist not synced yet — it '
                'arrives with the next sync from the Hub.</div>')
    body = _linkify(_esc(checklist)).replace("\n", "<br>\n")
    return ('<div class="note" style="background:#fff">%s</div>' % body)


def _team_html(team):
    team = team or {}
    if not team:
        return ('<div class="empty">Team state not synced yet — it arrives '
                'with the next sync from the Hub.</div>')
    parts = []
    replies = team.get("replies") or {}
    if replies:
        rows = []
        for _mid, r in sorted(replies.items()):
            status = r.get("status") or "no_reply"
            urgent = (' <b style="color:#b91c1c">⚠️ INTERVIEW — act today</b>'
                      if status == "interview" else "")
            rows.append("<tr><td><b>{t}</b><br><span class='muted'>{c}</span></td>"
                        "<td>{s}{u}</td><td class='muted'>{sub}</td></tr>".format(
                            t=_esc(r.get("title")), c=_esc(r.get("company")),
                            s=_esc(status), u=urgent,
                            sub=_esc(r.get("subject") or "—")))
        parts.append("<h3 style='margin:14px 0 6px'>📬 Employer replies</h3>"
                     "<table><tr><th>Application</th><th>Status</th>"
                     "<th>Latest message</th></tr>" + "".join(rows) + "</table>")
    due = team.get("followups_due") or []
    if due:
        rows = []
        for f in due:
            rows.append("<tr><td><b>{t}</b><br><span class='muted'>{c}</span></td>"
                        "<td>{d} day(s) ago</td><td>{r}</td></tr>".format(
                            t=_esc(f.get("title")), c=_esc(f.get("company")),
                            d=f.get("days_since"),
                            r=_esc(f.get("reason") or
                                  ("ready to send" if f.get("can_send")
                                   else "waiting"))))
        parts.append("<h3 style='margin:14px 0 6px'>✉️ Follow-ups due</h3>"
                     "<table><tr><th>Application</th><th>Applied</th>"
                     "<th>State</th></tr>" + "".join(rows) + "</table>")
    else:
        parts.append("<p class='muted'>✉️ No follow-ups due — newest "
                     "applications are under 7 days old.</p>")
    deadlines = team.get("deadlines") or []
    if deadlines:
        rows = []
        for d in deadlines:
            hot = (" <b style='color:#b91c1c'>⚠️ soon</b>"
                   if d.get("level") in ("due_1d", "due_3d", "due_7d") else "")
            rows.append("<tr><td><b>{l}</b></td><td>{date}</td>"
                        "<td>{n} day(s) left{hot}</td><td class='muted'>{note}</td></tr>".format(
                            l=_esc(d.get("label")), date=_esc(d.get("date")),
                            n=d.get("days_left"), hot=hot,
                            note=_esc(d.get("note"))))
        parts.append("<h3 style='margin:14px 0 6px'>⏰ Deadlines</h3>"
                     "<table><tr><th>What</th><th>Date</th><th>Left</th>"
                     "<th>Note</th></tr>" + "".join(rows) + "</table>")
    packs = team.get("interview_packs") or []
    offers = team.get("offers") or []
    if packs or offers:
        rows = []
        for p in packs:
            rows.append("<tr><td>🎤 Interview prep</td><td><b>{t}</b> @ {c}</td>"
                        "<td class='muted'>{d}</td></tr>".format(
                            t=_esc(p.get("title")), c=_esc(p.get("company")),
                            d=_esc(p.get("created"))))
        for o in offers:
            rows.append("<tr><td>💰 Offer check</td><td><b>{t}</b> @ {c}</td>"
                        "<td class='muted'>{d}</td></tr>".format(
                            t=_esc(o.get("title")), c=_esc(o.get("company")),
                            d=_esc(o.get("created"))))
        parts.append("<h3 style='margin:14px 0 6px'>📁 Prep packs &amp; offer checks</h3>"
                     "<table><tr><th>Kind</th><th>Role</th><th>Created</th></tr>"
                     + "".join(rows) + "</table>")
    as_of = team.get("as_of_pkt")
    if as_of:
        parts.append("<p class='muted'>Team state as of %s PKT. Interview "
                     "packs and offer checks live in the job-hunt goal "
                     "workspace (files/interview-prep, files/offer-checks)."
                     "</p>" % _esc(as_of))
    return "".join(parts)


def render_dashboard(counts, matches, queue, applied, profile,
                     config=None, checklist="", team=None):
    if matches:
        rows = []
        for m in matches[:50]:
            rows.append(
                "<tr><td><b>{title}</b><br><span class='muted'>{company}</span></td>"
                "<td>{country}</td><td>{track}</td><td>{score}</td>"
                "<td>{channel}</td><td>{status}</td>"
                "<td><a href='{url}' target='_blank' rel='noopener'>View ↗</a></td></tr>".format(
                    title=_esc(m.get("title")), company=_esc(m.get("company")),
                    country=_country_tag(m.get("country")),
                    track=_esc(m.get("track")), score=_score_badge(m.get("fit_score")),
                    channel=_esc(m.get("channel")), status=_status_tag(m.get("status")),
                    url=_esc(m.get("url"))))
        matches_html = ("<table><tr><th>Role</th><th>Country</th><th>Track</th>"
                        "<th>Fit</th><th>Channel</th><th>Status</th><th></th></tr>"
                        + "".join(rows) + "</table>")
    else:
        matches_html = ('<div class="empty">No matches yet — the Scout runs every '
                        'morning. First run after deploy will fill this in.</div>')
    if queue:
        qrows = []
        for q in queue:
            qrows.append(
                "<tr><td><b>{mid}</b></td><td>{reason}</td><td>{action}</td>"
                "<td class='muted'>{when}</td></tr>".format(
                    mid=_esc(q.get("match_id")), reason=_esc(q.get("reason")),
                    action=_esc(q.get("action_needed")),
                    when=_esc(q.get("created_at"))))
        queue_html = ("<table><tr><th>Role</th><th>Why it waits</th>"
                      "<th>What you need to do</th><th>Since</th></tr>"
                      + "".join(qrows) + "</table>")
    else:
        queue_html = ('<div class="empty">Nothing waiting — portal-gated and '
                      'LinkedIn roles will appear here when the Scout finds them.</div>')
    if applied:
        arows = []
        for a in applied:
            arows.append(
                "<tr><td><b>{title}</b><br><span class='muted'>{company}</span></td>"
                "<td>{channel}</td><td>{when}</td><td>{conf}</td></tr>".format(
                    title=_esc(a.get("title")), company=_esc(a.get("company")),
                    channel=_esc(a.get("channel")), when=_esc(a.get("applied_at")),
                    conf=_esc(a.get("confirmation") or "—")))
        applied_html = ("<table><tr><th>Role</th><th>Channel</th><th>Applied</th>"
                        "<th>Confirmation</th></tr>" + "".join(arows) + "</table>")
    else:
        applied_html = ('<div class="empty">No applications recorded through the '
                        'Hub yet. Older applications live in the job-hunt log.</div>')
    return (DASH.replace("__CSS__", CSS)
            .replace("__MODE_TEXT__", _mode_text(config))
            .replace("__LINKEDIN_NOTE__", _linkedin_note(config))
            .replace("__TEAM__", _team_html(team))
            .replace("__CHECKLIST__", _checklist_html(checklist))
            .replace("__APPLIED_TODAY__", str(counts["applied_today"]))
            .replace("__CAP__", str(counts["daily_cap"]))
            .replace("__NEW_MATCHES__", str(counts["new_matches"]))
            .replace("__QUEUED__", str(counts["queued"]))
            .replace("__APPLIED_TOTAL__", str(counts["applied_total"]))
            .replace("__PROFILE__", str(counts["profile_complete"]))
            .replace("__NAME__", _esc(profile.get("name")))
            .replace("__EMAIL__", _esc(profile.get("email")))
            .replace("__MATCHES__", matches_html)
            .replace("__QUEUE__", queue_html)
            .replace("__APPLIED__", applied_html))


def render_profile_form(profile):
    html = PROFILE_FORM.replace("__CSS__", CSS)
    mapping = {
        "__NAME__": "name", "__CV_NAME__": "cv_name", "__EMAIL__": "email",
        "__PHONE__": "phone", "__CITY__": "city", "__COUNTRY__": "country",
        "__DOB__": "dob", "__DEGREE__": "degree",
        "__INSTITUTION__": "institution", "__SESSION__": "session",
        "__START_YEAR__": "start_year", "__EDU_STATUS__": "education_status",
        "__SKILLS__": "skills", "__GITHUB__": "github",
        "__LINKEDIN__": "linkedin", "__PHARMAREG__": "pharmareg",
        "__LEADFORGE__": "leadforge", "__RELOCATION__": "relocation",
        "__DAILY_CAP__": "daily_cap",
    }
    for token, key in mapping.items():
        html = html.replace(token, _esc(profile.get(key, "")))
    return html
