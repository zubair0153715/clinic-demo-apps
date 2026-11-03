"""Larkana Property pages — Urdu-first UI with an English toggle.

Brand: Larkana Property (لاڑکانہ پراپرٹی) — an original, Larkana-only
property board. No copied branding from any existing portal.
"""

from . import db
import html


def esc(s):
    """Escape user-supplied text for HTML (prevents stored XSS)."""
    return html.escape(str(s or ""), quote=True)

CSS = """
body{font-family:system-ui,'Noto Nastaliq Urdu','Noto Naskh Arabic',Tahoma,sans-serif;margin:0;color:#1a1a1a;line-height:1.7;background:#f6f7f4}
.wrap{max-width:980px;margin:0 auto;padding:0 18px 60px}
header{background:#14532d;color:#fff;padding:26px 0 20px}
header h1{margin:0 0 4px;font-size:1.6rem}
header p{margin:0;opacity:.92}
.lang{float:left}
.lang a{color:#fff;opacity:.85;text-decoration:none;font-weight:700}
.btn{display:inline-block;background:#14532d;color:#fff;font-weight:700;padding:10px 20px;border-radius:9px;text-decoration:none;border:0;cursor:pointer;font-size:1rem}
.btn.ghost{background:#fff;color:#14532d;border:2px solid #14532d}
.btn.wa{background:#25d366;color:#fff}
.btn.danger{background:#b91c1c}
.card{background:#fff;border:1px solid #e3e6e0;border-radius:12px;padding:16px;margin:12px 0}
.card h3{margin:0 0 6px}
.card h3 a{color:#14532d;text-decoration:none}
.price{font-size:1.25rem;font-weight:800;color:#14532d}
.muted{color:#666;font-size:.9rem}
.tag{display:inline-block;font-size:.8rem;font-weight:700;border-radius:999px;padding:2px 10px;background:#e8f5ec;color:#14532d;margin-left:6px}
.tag.sale{background:#dcfce7;color:#166534}.tag.wanted{background:#fef3c7;color:#92400e}
.note{background:#fffbe6;border:1px solid #f5d76e;border-radius:12px;padding:12px 16px;font-size:.92rem;margin:16px 0}
.warn{background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;padding:12px 16px;font-size:.92rem;margin:16px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
form label{display:block;font-weight:700;margin:14px 0 4px}
form input,form textarea,form select{width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-size:1rem;box-sizing:border-box}
form .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.empty{background:#fff;border:1px dashed #bbb;border-radius:12px;padding:26px;text-align:center;color:#666}
img.thumb{width:100%;height:180px;object-fit:cover;border-radius:10px}
img.big{width:100%;max-height:420px;object-fit:cover;border-radius:12px}
.filters{background:#fff;border:1px solid #e3e6e0;border-radius:12px;padding:14px 16px;margin:16px 0}
.filters form{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;align-items:end}
.filters label{font-size:.85rem;font-weight:700;margin:0 0 2px}
.filters input,.filters select{padding:8px}
footer{margin-top:40px;color:#666;font-size:.85rem;text-align:center}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden}
th,td{padding:9px 10px;text-align:right;border-bottom:1px solid #eee;font-size:.9rem;vertical-align:top}
th{background:#eef5ef;color:#14532d}
"""

STR = {
    "title": {"ur": "لاڑکانہ پراپرٹی", "en": "Larkana Property"},
    "tagline": {"ur": "لاڑکانہ کی اپنی پراپرٹی مارکیٹ — مکان، پلاٹ، دکان، فلیٹ",
                "en": "Larkana's own property market — houses, plots, shops, flats"},
    "browse": {"ur": "پراپرٹی دیکھیں", "en": "Browse properties"},
    "post": {"ur": "اپنی پراپرٹی لگائیں", "en": "Post your property"},
    "search": {"ur": "تلاش کریں", "en": "Search"},
    "how_title": {"ur": "یہ کیسے کام کرتا ہے؟",
                  "en": "How does this work?"},
    "how_body": {"ur": "یہ پلیٹ فارم خریدار اور بیچنے والے کو ملاتا ہے۔ آپ اپنی پراپرٹی مفت لگائیں — ہر اشتہار پہلے ہماری منظوری سے گزرتا ہے، پھر سب کو نظر آتا ہے۔ خریدار براہِ راست بیچنے والے سے واٹس ایپ یا فون پر رابطہ کرتا ہے۔",
                 "en": "This platform connects buyers and sellers. Post your property for free — every listing is approved by us first, then shown to everyone. Buyers contact the seller directly on WhatsApp or by phone."},
    "warn_title": {"ur": "اہم احتیاط",
                   "en": "Important — please read"},
    "warn_body": {"ur": "یہ پلیٹ فارم ملکیت (title) کی قانونی تصدیق نہیں کرتا اور نہ ٹوکن یا ایڈوانس رقم سنبھالتا ہے۔ کوئی بھی رقم دینے سے پہلے کاغذات (فرد / رجسٹری) خود چیک کریں۔ لین دین خریدار اور بیچنے والے کے درمیان ہوتا ہے۔",
                  "en": "This platform does NOT verify legal title and does NOT handle token or advance money. Always check the documents (Fard / registry) yourself before paying anything. Any deal is between buyer and seller."},
    "empty": {"ur": "ابھی کوئی منظور شدہ پراپرٹی نہیں ہے۔",
              "en": "No approved properties yet."},
    "empty_cta": {"ur": "پہلی پراپرٹی لگائیں — یہ مفت ہے!",
                  "en": "Post the first property — it's free!"},
    "sale": {"ur": "برائے فروخت", "en": "For sale"},
    "wanted": {"ur": "خریداری درکار", "en": "Wanted"},
    "house": {"ur": "مکان", "en": "House"},
    "plot": {"ur": "پلاٹ", "en": "Plot"},
    "shop": {"ur": "دکان", "en": "Shop"},
    "flat": {"ur": "فلیٹ", "en": "Flat"},
    "commercial": {"ur": "کمرشل", "en": "Commercial"},
    "sqyd": {"ur": "مربع گز", "en": "sq yd"},
    "marla": {"ur": "مرلہ", "en": "marla"},
    "kanal": {"ur": "کنال", "en": "kanal"},
    "bedrooms": {"ur": "کمرے", "en": "bedrooms"},
    "whatsapp": {"ur": "واٹس ایپ پر رابطہ کریں", "en": "Contact on WhatsApp"},
    "call": {"ur": "کال کریں", "en": "Call"},
    "seller": {"ur": "بیچنے والا", "en": "Seller"},
    "locality": {"ur": "علاقہ", "en": "Locality"},
    "all_types": {"ur": "تمام اقسام", "en": "All types"},
    "all_localities": {"ur": "تمام علاقے", "en": "All localities"},
    "all_purposes": {"ur": "فروخت / درکار", "en": "Sale / Wanted"},
    "min_price": {"ur": "کم سے کم قیمت", "en": "Min price"},
    "max_price": {"ur": "زیادہ سے زیادہ قیمت", "en": "Max price"},
    "keyword": {"ur": "لفظ تلاش کریں", "en": "Keyword"},
    "back": {"ur": "← واپس تمام پراپرٹی", "en": "← Back to all properties"},
    "posted_title": {"ur": "آپ کی پراپرٹی موصول ہو گئی!",
                     "en": "Your property was received!"},
    "posted_body": {"ur": "آپ کا اشتہار منظوری کے لیے بھیج دیا گیا ہے۔ منظور ہوتے ہی سب کو نظر آئے گا۔ جعلی یا غلط اشتہار منظور نہیں کیے جاتے۔",
                    "en": "Your listing has been sent for approval. Once approved, everyone will see it. Fake or incorrect listings are not approved."},
    "admin_title": {"ur": "ایڈمن — اشتہارات کی منظوری",
                    "en": "Admin — approve listings"},
    "admin_key": {"ur": "ایڈمن کی", "en": "Admin key"},
    "approve": {"ur": "منظور کریں", "en": "Approve"},
    "reject": {"ur": "مسترد کریں", "en": "Reject"},
    "delete": {"ur": "حذف کریں", "en": "Delete"},
    "pending": {"ur": "منظوری کے منتظر", "en": "Pending approval"},
    "no_pending": {"ur": "کوئی اشتہار منظوری کا منتظر نہیں۔",
                    "en": "No listings waiting for approval."},
    "wrong_key": {"ur": "غلط ایڈمن کی۔", "en": "Wrong admin key."},
    "form_title": {"ur": "اپنی پراپرٹی لگائیں — مفت",
                   "en": "Post your property — free"},
    "form_note": {"ur": "تمام اشتہار پہلے منظور کیے جاتے ہیں۔ درست معلومات لکھیں — غلط یا جعلی اشتہار مسترد کر دیا جائے گا۔",
                  "en": "Every listing is approved first. Give correct information — wrong or fake listings will be rejected."},
    "f_title": {"ur": "عنوان (مثلاً: 5 مرلہ مکان، سچل کالونی)",
                "en": "Title (e.g. 5 marla house, Sachal Colony)"},
    "f_purpose": {"ur": "فروخت یا درکار؟", "en": "For sale or wanted?"},
    "f_type": {"ur": "قسم", "en": "Type"},
    "f_locality": {"ur": "علاقہ", "en": "Locality"},
    "f_other_locality": {"ur": "دوسرا علاقہ (اگر فہرست میں نہ ہو)",
                         "en": "Other locality (if not in the list)"},
    "f_address": {"ur": "پتہ / گلی / نزد", "en": "Address / street / nearby"},
    "f_price": {"ur": "قیمت (روپے)", "en": "Price (PKR)"},
    "f_size": {"ur": "رقبہ", "en": "Size"},
    "f_bedrooms": {"ur": "کمروں کی تعداد (مکان/فلیٹ کے لیے)",
                   "en": "Bedrooms (house/flat)"},
    "f_desc": {"ur": "تفصیل", "en": "Description"},
    "f_name": {"ur": "آپ کا نام", "en": "Your name"},
    "f_phone": {"ur": "فون / واٹس ایپ نمبر (مثلاً 0300-1234567)",
                "en": "Phone / WhatsApp number (e.g. 0300-1234567)"},
    "f_photos": {"ur": "تصاویر (زیادہ سے زیادہ 3، ہر ایک 2MB تک)",
                 "en": "Photos (max 3, each up to 2MB)"},
    "submit": {"ur": "اشتہار بھیجیں", "en": "Submit listing"},
    "live_n": {"ur": "منظور شدہ پراپرٹی", "en": "live properties"},
}


def t(key, lang):
    return STR.get(key, {}).get(lang, STR.get(key, {}).get("en", key))


def fmt_price(pkr, lang="ur"):
    try:
        p = int(pkr)
    except Exception:
        return ""
    if lang == "ur":
        if p >= 10_000_000:
            v = p / 10_000_000
            return f"روپے {v:g} کروڑ"
        if p >= 100_000:
            v = p / 100_000
            return f"روپے {v:g} لاکھ"
        return f"روپے {p:,}"
    if p >= 10_000_000:
        return f"Rs {p / 10_000_000:g} crore"
    if p >= 100_000:
        return f"Rs {p / 100_000:g} lakh"
    return f"Rs {p:,}"


def _lang_toggle(lang, path):
    other = "en" if lang == "ur" else "ur"
    label = "English" if lang == "ur" else "اردو"
    sep = "&" if "?" in path else "?"
    return f'<span class="lang"><a href="{path}{sep}lang={other}">{label}</a></span>'


def _header(lang, path, subtitle=None):
    sub = subtitle or t("tagline", lang)
    return (f'<header><div class="wrap">{_lang_toggle(lang, path)}'
            f'<h1>🏠 {t("title", lang)}</h1><p>{sub}</p></div></header>')


def _shell(lang, path, title, body, noindex=False):
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    direction = "rtl" if lang == "ur" else "ltr"
    return (f'<!doctype html><html lang="{lang}" dir="{direction}"><head>'
            f'<meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1">{robots}'
            f'<title>{title} — {t("title", lang)}</title>'
            f'<style>{CSS}</style></head><body>{body}'
            f'<footer><div class="wrap">🏠 {t("title", lang)} — '
            f'{"لاڑکانہ، سندھ — صرف لاڑکانہ شہر" if lang == "ur" else "Larkana, Sindh — Larkana city only"}</div></footer>'
            f'</body></html>')


def _locality_options(selected="", lang="ur"):
    opts = [f'<option value="">{t("all_localities", lang)}</option>']
    for loc in db.LOCALITIES:
        sel = " selected" if loc == selected else ""
        opts.append(f'<option value="{loc}"{sel}>{loc}</option>')
    opts.append('<option value="__other__">'
                + ("دوسرا علاقہ…" if lang == "ur" else "Other locality…")
                + '</option>')
    return "".join(opts)


def _type_options(selected="", lang="ur", all_label=True):
    opts = []
    if all_label:
        opts.append(f'<option value="">{t("all_types", lang)}</option>')
    for p in db.PTYPES:
        sel = " selected" if p == selected else ""
        opts.append(f'<option value="{p}"{sel}>{t(p, lang)}</option>')
    return "".join(opts)


def _purpose_options(selected="", lang="ur", all_label=True):
    opts = []
    if all_label:
        opts.append(f'<option value="">{t("all_purposes", lang)}</option>')
    for p in db.PURPOSES:
        sel = " selected" if p == selected else ""
        opts.append(f'<option value="{p}"{sel}>{t(p, lang)}</option>')
    return "".join(opts)


def render_browse(listings, filters, lang, base_path="/larkana-property"):
    f = filters or {}
    cards = ""
    for d in listings:
        photo = ""
        if d.get("photos"):
            photo = (f'<img class="thumb" src="{base_path}/photos/'
                     f'{d["photos"][0]}" alt="">')
        purpose = t(d["purpose"], lang)
        cards += (
            f'<div class="card">{photo}'
            f'<h3><a href="{base_path}/{d["id"]}?lang={lang}">{esc(d["title"])}</a></h3>'
            f'<div class="price">{fmt_price(d["price"], lang)}</div>'
            f'<div class="muted">{t(d["ptype"], lang)} · {esc(d["locality"])} · '
            f'{d.get("size_value", 0):g} {t(d.get("size_unit", "sqyd"), lang)}'
            + (f' · {d.get("bedrooms", 0)} {t("bedrooms", lang)}'
               if d.get("bedrooms") else "")
            + f'</div><span class="tag {d["purpose"]}">{purpose}</span>'
            f'</div>')
    if not listings:
        cards = (f'<div class="empty"><b>{t("empty", lang)}</b><br><br>'
                 f'<a class="btn" href="{base_path}/post?lang={lang}">'
                 f'{t("empty_cta", lang)}</a></div>')
    live = len(listings)
    body = (_header(lang, base_path)
            + f'<div class="wrap">'
            f'<p style="margin-top:16px"><a class="btn" href="{base_path}/post?lang={lang}">+ {t("post", lang)}</a> '
            f'<span class="muted">{live} {t("live_n", lang)}</span></p>'
            f'<div class="filters"><form method="get" action="{base_path}">'
            f'<input type="hidden" name="lang" value="{lang}">'
            f'<div><label>{t("keyword", lang)}</label>'
            f'<input name="q" value="{esc(f.get("q", ""))}"></div>'
            f'<div><label>{t("f_type", lang)}</label>'
            f'<select name="ptype">{_type_options(f.get("ptype", ""), lang)}</select></div>'
            f'<div><label>{t("f_purpose", lang)}</label>'
            f'<select name="purpose">{_purpose_options(f.get("purpose", ""), lang)}</select></div>'
            f'<div><label>{t("locality", lang)}</label>'
            f'<select name="locality">{_locality_options(f.get("locality", ""), lang)}</select></div>'
            f'<div><label>{t("min_price", lang)}</label>'
            f'<input name="min_price" inputmode="numeric" value="{esc(f.get("min_price", ""))}"></div>'
            f'<div><label>{t("max_price", lang)}</label>'
            f'<input name="max_price" inputmode="numeric" value="{esc(f.get("max_price", ""))}"></div>'
            f'<div><button class="btn" type="submit">{t("search", lang)}</button></div>'
            f'</form></div>'
            f'<div class="note"><b>{t("how_title", lang)}</b><br>{t("how_body", lang)}</div>'
            f'<div class="warn"><b>⚠️ {t("warn_title", lang)}</b><br>{t("warn_body", lang)}</div>'
            f'<div class="grid">{cards}</div></div>')
    return _shell(lang, base_path, t("browse", lang), body)


def render_detail(d, lang, base_path="/larkana-property"):
    photos = ""
    for name in d.get("photos") or []:
        photos += (f'<img class="big" src="{base_path}/photos/{name}" '
                   f'alt="" style="margin-bottom:10px">')
    wa = ""
    if d.get("phone_digits"):
        text = ("Assalam-o-Alaikum, I saw your property on Larkana Property: "
                f'{d["title"]} ({d["locality"]}) — {fmt_price(d["price"], "en")}. '
                "Is it still available?")
        import urllib.parse
        wa = (f'<a class="btn wa" href="https://wa.me/{d["phone_digits"]}'
              f'?text={urllib.parse.quote(text)}" target="_blank" rel="noopener">'
              f'💬 {t("whatsapp", lang)}</a> ')
    desc = esc(d.get("description") or "").replace("\n", "<br>")
    body = (_header(lang, base_path)
            + f'<div class="wrap">'
            f'<p style="margin-top:16px"><a href="{base_path}?lang={lang}">{t("back", lang)}</a></p>'
            + photos
            + f'<h2>{esc(d["title"])} <span class="tag {d["purpose"]}">{t(d["purpose"], lang)}</span></h2>'
            f'<div class="price">{fmt_price(d["price"], lang)}</div>'
            f'<p class="muted">{t(d["ptype"], lang)} · {esc(d["locality"])} · '
            f'{d.get("size_value", 0):g} {t(d.get("size_unit", "sqyd"), lang)}'
            + (f' · {d.get("bedrooms", 0)} {t("bedrooms", lang)}'
               if d.get("bedrooms") else "")
            + f'</p>'
            + (f'<p><b>{t("f_address", lang)}:</b> {esc(d.get("address", ""))}</p>'
               if d.get("address") else "")
            + (f'<p>{desc}</p>' if desc else "")
            + f'<div class="card"><b>{t("seller", lang)}:</b> {esc(d["seller_name"])}<br>'
            + wa
            + f'<a class="btn ghost" href="tel:{esc(d["phone"])}">📞 {t("call", lang)}: {esc(d["phone"])}</a>'
            + f'</div>'
            f'<div class="warn"><b>⚠️ {t("warn_title", lang)}</b><br>{t("warn_body", lang)}</div>'
            f'</div>')
    return _shell(lang, base_path, d["title"], body)


def render_post_form(lang, error="", base_path="/larkana-property"):
    err = f'<div class="warn">{error}</div>' if error else ""
    body = (_header(lang, base_path)
            + f'<div class="wrap"><h2>{t("form_title", lang)}</h2>'
            f'<div class="note">{t("form_note", lang)}</div>{err}'
            f'<form method="post" action="{base_path}/post?lang={lang}" enctype="multipart/form-data">'
            f'<label>{t("f_title", lang)}</label>'
            f'<input name="title" required maxlength="120">'
            f'<div class="row"><div><label>{t("f_purpose", lang)}</label>'
            f'<select name="purpose">{_purpose_options("", lang, all_label=False)}</select></div>'
            f'<div><label>{t("f_type", lang)}</label>'
            f'<select name="ptype">{_type_options("", lang, all_label=False)}</select></div></div>'
            f'<div class="row"><div><label>{t("locality", lang)}</label>'
            f'<select name="locality" id="loc">{_locality_options("", lang)}</select></div>'
            f'<div><label>{t("f_other_locality", lang)}</label>'
            f'<input name="locality_other" id="loc_other" maxlength="60"></div></div>'
            f'<label>{t("f_address", lang)}</label>'
            f'<input name="address" maxlength="160">'
            f'<div class="row"><div><label>{t("f_price", lang)}</label>'
            f'<input name="price" inputmode="numeric" required></div>'
            f'<div><label>{t("f_size", lang)}</label>'
            f'<div style="display:flex;gap:8px"><input name="size_value" inputmode="decimal" style="flex:2">'
            f'<select name="size_unit" style="flex:1">'
            f'<option value="sqyd">{t("sqyd", lang)}</option>'
            f'<option value="marla">{t("marla", lang)}</option>'
            f'<option value="kanal">{t("kanal", lang)}</option>'
            f'</select></div></div></div>'
            f'<label>{t("f_bedrooms", lang)}</label>'
            f'<input name="bedrooms" inputmode="numeric" value="0">'
            f'<label>{t("f_desc", lang)}</label>'
            f'<textarea name="description" rows="4" maxlength="1000"></textarea>'
            f'<div class="row"><div><label>{t("f_name", lang)}</label>'
            f'<input name="seller_name" required maxlength="60"></div>'
            f'<div><label>{t("f_phone", lang)}</label>'
            f'<input name="phone" required maxlength="20" dir="ltr" style="text-align:right"></div></div>'
            f'<label>{t("f_photos", lang)}</label>'
            f'<input type="file" name="photos" accept="image/jpeg,image/png,image/webp" multiple>'
            f'<p style="margin-top:18px"><button class="btn" type="submit">{t("submit", lang)}</button> '
            f'<a class="btn ghost" href="{base_path}?lang={lang}">{t("back", lang)}</a></p>'
            f'</form></div>')
    return _shell(lang, base_path, t("form_title", lang), body)


def render_submitted(lang, base_path="/larkana-property"):
    body = (_header(lang, base_path)
            + f'<div class="wrap"><div class="card" style="margin-top:20px">'
            f'<h2>✅ {t("posted_title", lang)}</h2><p>{t("posted_body", lang)}</p>'
            f'<p><a class="btn" href="{base_path}?lang={lang}">{t("browse", lang)}</a></p>'
            f'</div></div>')
    return _shell(lang, base_path, t("posted_title", lang), body)


def render_admin(lang, base_path="/larkana-property"):
    body = (_header(lang, base_path)
            + f'<div class="wrap"><h2>{t("admin_title", lang)}</h2>'
            f'<div class="card"><label>{t("admin_key", lang)}</label>'
            f'<input id="k" type="password" style="width:100%;padding:10px;'
            f'border:1px solid #ccc;border-radius:8px" dir="ltr">'
            f'<p style="margin-top:10px"><button class="btn" onclick="loadList()">'
            f'{t("pending", lang)}</button></p></div>'
            f'<div id="list"></div>'
            f'<script>'
            f'function esc(s){{return String(s==null?"":s).replace(/&/g,"&amp;")'
            f'.replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}}'
            f'async function loadList(){{'
            f'const k=document.getElementById("k").value;'
            f'const r=await fetch("{base_path}/api/admin/list?status=pending",'
            f'{{headers:{{"X-Admin-Key":k}}}});'
            f'const j=await r.json();'
            f'if(!j.ok){{document.getElementById("list").innerHTML='
            f'"<div class=\\"warn\\">{t("wrong_key", lang)}</div>";return;}}'
            f'if(!j.listings.length){{document.getElementById("list").innerHTML='
            f'"<div class=\\"empty\\">{t("no_pending", lang)}</div>";return;}}'
            f'let h="<table><tr><th>Title</th><th>Price</th><th>Locality</th><th></th></tr>";'
            f'for(const d of j.listings){{'
            f'h+="<tr><td><b>"+esc(d.title)+"</b><br><small>"+esc(d.ptype)+" · "+esc(d.locality)+" · "+esc(d.seller_name)+" · "+esc(d.phone)+"</small><br><small>"+esc(d.description||"")+"</small></td><td>"+esc(d.price)+"</td><td>"+esc(d.locality)+"</td><td><button class=\\"btn\\" onclick=\\"act(\'"+d.id+"\',\'approve\')\\">{t("approve", lang)}</button> <button class=\\"btn danger\\" onclick=\\"act(\'"+d.id+"\',\'reject\')\\">{t("reject", lang)}</button></td></tr>";}}'
            f'h+="</table>";document.getElementById("list").innerHTML=h;}}'
            f'async function act(id,op){{'
            f'const k=document.getElementById("k").value;'
            f'await fetch("{base_path}/api/admin/"+id+"/"+op,'
            f'{{method:"POST",headers:{{"X-Admin-Key":k}}}});loadList();}}'
            f'</script></div>')
    return _shell(lang, base_path, t("admin_title", lang), body, noindex=True)
