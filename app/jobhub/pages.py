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
<div class="note"><b>How this works:</b> the Scout finds new roles across PK/SA/UAE boards every morning, the Matcher scores fit, the Tailor writes a cover note from your real portfolio, and the Applier submits automatically <b>only</b> where no login is needed (email or guest form). Anything needing your login, a CAPTCHA, or LinkedIn lands in the approval queue below — nothing is submitted without you. Max 4 applications/day.</div>

<h2>🎯 Today's matches</h2>
__MATCHES__

<h2>⏳ Approval queue — needs you</h2>
__QUEUE__

<h2>✅ Applied</h2>
__APPLIED__

<p class="muted" style="margin-top:26px">Scope: Pakistan, Saudi Arabia, UAE (+ worldwide-remote Track B/C). Tracks: A bio-AI / regulatory · B AI automation / Python / data · C internships. LinkedIn applying stays approval-gated — automation there risks an account ban. No application is counted as sent until the employer's own page or email confirms it.</p>
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


def render_dashboard(counts, matches, queue, applied, profile):
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
