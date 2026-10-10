"""PGx demo routes — educational pharmacogenomics prototype.

EDUCATIONAL ONLY — not medical advice. See pgx_data.py for data sources
(CPIC/PharmGKB) and documented simplifications.
"""
import json
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from . import pgx_data as D
from . import resistance_data as R

router = APIRouter()
_HERE = Path(__file__).parent
_STRUCT_CACHE = _HERE / "struct_cache"
_STRUCT_CACHE.mkdir(exist_ok=True)

THEME = "#0f7665"

# ---------------------------------------------------------------- parsers ---
def parse_genotypes(text):
    """Auto-detect VCF vs 23andMe raw. Returns (dict rsID->'AG', format_name)."""
    head = text[:2000]
    is_vcf = ("##fileformat" in head) or ("\n#CHROM" in head) or head.startswith("#CHROM")
    genos = {}
    if is_vcf:
        sample_col = None
        fmt_keys = []
        for line in text.splitlines():
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                h = line.lstrip("#").split("\t")
                if "FORMAT" in h:
                    fi = h.index("FORMAT")
                    sample_col = fi + 1
                    # FORMAT keys come per-record; capture per record below
                continue
            if not line.strip() or sample_col is None:
                continue
            c = line.split("\t")
            if len(c) <= sample_col or len(c) < 8:
                continue
            rid, ref, alt = c[2], c[3].upper(), c[4].upper().split(",")[0]
            if not rid.startswith("rs"):
                continue
            fkeys = c[sample_col - 1].split(":")
            svals = c[sample_col].split(":")
            try:
                gt = svals[fkeys.index("GT")]
            except (ValueError, IndexError):
                continue
            gt = gt.replace("|", "/")
            if gt in ("./.", ".|."):
                continue
            alleles = gt.split("/")
            if len(alleles) != 2 or not all(a in ("0", "1") for a in alleles):
                continue  # skip multiallelic / weird
            bases = {"0": ref, "1": alt}
            g = "".join(sorted(bases[a] for a in alleles))
            # keep first occurrence only
            genos.setdefault(rid, g)
        return genos, "VCF"
    # 23andMe raw: rsid \t chromosome \t position \t genotype
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            parts = line.split()
        if len(parts) < 4:
            continue
        rid, geno = parts[0], parts[3].strip().upper()
        if not rid.startswith("rs") or geno in ("--", ""):
            continue
        if len(geno) == 2 and all(b in "ACGT" for b in geno):
            genos.setdefault(rid, "".join(sorted(geno)))
    return genos, "23andMe"


# -------------------------------------------------------------- analysis ---
SEV_RANK = {"ok": 0, "caution": 1, "avoid": 2}


def _resolve_rule(rule, gene_key):
    """Resolve a drug rule to (severity, text).

    Single-gene rules use rule["gene"]; multi-gene rules use rule["genes"]
    (list) — worst severity across tested genes wins, texts combined.
    """
    if rule.get("info_only"):
        return "info", rule["info"]
    combo = rule.get("combo")
    if combo == "warfarin":  # warfarin: CYP2C9 + VKORC1 special combination
        return D.warfarin_rule(gene_key.get("CYP2C9", "unknown"),
                               gene_key.get("VKORC1", "unknown"))
    if combo == "coumarin":  # acenocoumarol/phenprocoumon: same gene pair, DPWG
        return D.coumarin_rule(rule["drug"], gene_key.get("CYP2C9", "unknown"),
                               gene_key.get("VKORC1", "unknown"))
    genes = rule.get("genes") or [rule["gene"]]
    hits = []
    for g in genes:
        key = gene_key.get(g, "unknown")
        if key == "unknown":
            continue
        sev, text = rule["map"].get(key, rule["map"]["unknown"])
        hits.append((g, sev, text))
    if not hits:
        sev, text = rule["map"]["unknown"]
        return sev, text
    worst = max(hits, key=lambda h: SEV_RANK[h[1]])
    if len(genes) == 1:
        return worst[1], worst[2]
    flagged = [f"{g}: {t}" for g, s, t in hits if s != "ok"]
    text = " ".join(flagged) if flagged else worst[2]
    return worst[1], text


def _rule_source(rule):
    """Badge source for a drug rule: explicit 'source' wins, else derived
    from the citation string (older rules predate the badge system)."""
    s = rule.get("source")
    if s:
        return s
    c = rule.get("cpic", "")
    if c.startswith("DPWG"):
        return "DPWG"
    if c.startswith("FDA"):
        return "FDA"
    return "CPIC"


def analyze(genotypes):
    genes = []
    for gene in D.GENE_INFO:
        dip, ph, key, expl = D.call_gene(gene, genotypes)
        info = D.GENE_INFO[gene]
        genes.append({"gene": gene, "diplotype": dip, "phenotype": ph,
                      "key": key, "explanation": expl,
                      "desc": info["desc"], "cpic": info["cpic"],
                      "structure": D.gene_structure(gene, genotypes)})
    gene_key = {g["gene"]: g["key"] for g in genes}

    drugs = []
    for rule in D.DRUG_RULES:
        sev, text = _resolve_rule(rule, gene_key)
        drugs.append({"drug": rule["drug"], "use": rule["use"],
                      "severity": sev, "text": text, "cpic": rule["cpic"],
                      "source": _rule_source(rule)})

    variants = []
    for rsid, geno in sorted(genotypes.items()):
        if rsid in D.SNPS:
            s = D.SNPS[rsid]
            n = sum(1 for b in geno if b == s["alt"])
            variants.append({"rsid": rsid, "gene": s["gene"], "genotype": geno,
                             "alleles": f"{n} × {s['alt']} ({s['star'] or 'variant'})",
                             "note": s["note"]})
    return {"genes": genes, "drugs": drugs, "variants": variants,
            "n_genotyped": len(genotypes),
            "n_panel": sum(1 for r in genotypes if r in D.SNPS)}


# ------------------------------------------------------------------- html ---
def _page(title, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — PGx Demo</title>
<link rel="manifest" href="/pgx/manifest.json">
<meta name="theme-color" content="{THEME}">
<link rel="apple-touch-icon" href="/pgx/icon-192.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<style>
:root{{--t:{THEME}}}
*{{box-sizing:border-box}}body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;margin:0;background:#f0fdfa;color:#134e4a;line-height:1.55}}
.wrap{{max-width:960px;margin:0 auto;padding:16px}}
header.hero{{background:linear-gradient(135deg,#0f7665,#14b8a6);color:#fff;padding:36px 16px;text-align:center}}
.hero h1{{margin:0 0 8px;font-size:1.9rem}}.hero p{{margin:6px auto;max-width:640px;opacity:.95}}
.card{{background:#fff;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 2px 10px rgba(15,118,101,.08);border:1px solid #ccfbf1}}
.btn{{display:inline-block;background:var(--t);color:#fff;border:none;border-radius:10px;padding:12px 22px;font-size:1rem;cursor:pointer;text-decoration:none;margin:6px 4px}}
.btn.ghost{{background:#fff;color:var(--t);border:2px solid var(--t)}}
.badge{{display:inline-block;padding:3px 12px;border-radius:999px;font-size:.8rem;font-weight:700}}
.b-green{{background:#dcfce7;color:#166534}}.b-yellow{{background:#fef9c3;color:#854d0e}}.b-red{{background:#fee2e2;color:#991b1b}}.b-blue{{background:#dbeafe;color:#1e40af}}.b-gray{{background:#e5e7eb;color:#374151}}
.sev-ok{{border-left:6px solid #16a34a}}.sev-caution{{border-left:6px solid #ca8a04}}.sev-avoid{{border-left:6px solid #dc2626}}.sev-info{{border-left:6px solid #2563eb}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}
.disclaimer{{background:#fffbeb;border:1px solid #fcd34d;border-radius:10px;padding:12px 16px;font-size:.9rem;margin:14px 0}}
table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{text-align:left;padding:8px;border-bottom:1px solid #ccfbf1}}th{{background:#f0fdfa}}
input[type=file]{{margin:10px 0}}
.steps{{counter-reset:s}}.step{{display:flex;gap:12px;margin:10px 0}}.step::before{{counter-increment:s;content:counter(s);background:var(--t);color:#fff;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}}
footer{{text-align:center;color:#5f716d;font-size:.85rem;padding:24px 16px}}
h2{{color:#0f7665}}code{{background:#f0fdfa;padding:2px 6px;border-radius:6px}}
</style>{extra_head}</head>
<body>{body}
<script>if("serviceWorker" in navigator){{navigator.serviceWorker.register("/pgx/sw.js").catch(()=>{{}});}}</script>
</body></html>"""

DISCLAIMER_HTML = f"""<div class="disclaimer">⚠️ <b>Educational demo — NOT medical advice.</b> {D.DISCLAIMER}</div>"""

# 3Dmol.js (CDN) + lazy viewer logic for the report page only.
REPORT_HEAD = """<script src="https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.1.0/3Dmol-min.js"></script>
<script>
function toggle3D(gene){
  var box=document.getElementById('v3d-'+gene);
  var btn=document.getElementById('btn3d-'+gene);
  var msg=document.getElementById('msg3d-'+gene);
  if(!box||!btn) return;
  if(box.dataset.loaded==='1'){
    var show=box.style.display==='none';
    box.style.display=show?'block':'none';
    btn.innerHTML=show?'🧬 Hide 3D structure':'🧬 View 3D structure';
    return;
  }
  var cfg=JSON.parse(document.getElementById('cfg3d-'+gene).textContent);
  function fail(){
    msg.style.display='block';
    msg.innerHTML='⚠️ Could not load the 3D model (offline or blocked). <a href="'+cfg.af_url+'" target="_blank" rel="noopener">Open in AlphaFold DB ↗</a>';
    box.style.display='none';
    btn.innerHTML='🧬 View 3D structure';
  }
  box.style.display='block';
  btn.innerHTML='🧬 Hide 3D structure';
  try{
    if(typeof $3Dmol==='undefined') throw new Error('3dmol missing');
    fetch(cfg.cif).then(function(r){ if(!r.ok) throw new Error('fetch '+r.status); return r.text(); })
    .then(function(cif){
      var viewer=$3Dmol.createViewer(box,{backgroundColor:'#f8fafc'});
      viewer.addModel(cif,'cif');
      viewer.setStyle({},{cartoon:{color:'spectrum',thickness:0.35}});
      (cfg.highlights||[]).forEach(function(h){
        var col=h.found?'#dc2626':'#9ca3af';
        viewer.addStyle({resi:h.pos},{sphere:{color:col,radius:h.found?1.4:0.9}});
        try{
          var atoms=viewer.selectedAtoms({resi:h.pos});
          if(atoms.length){
            var c={x:0,y:0,z:0},i;
            for(i=0;i<atoms.length;i++){c.x+=atoms[i].x;c.y+=atoms[i].y;c.z+=atoms[i].z;}
            c.x/=atoms.length;c.y/=atoms.length;c.z/=atoms.length;
            viewer.addLabel((h.found?'\\u0001F534 ':'\\u000026AA ')+h.label,
              {position:c,fontSize:11,fontColor:'#ffffff',backgroundColor:'#111827',
               backgroundOpacity:0.8,showBackground:true});
          }
        }catch(e){}
      });
      viewer.zoomTo(); viewer.render(); viewer.zoom(0.85);
      box.dataset.loaded='1';
    }).catch(fail);
  }catch(e){ fail(); }
}
</script>"""

LANDING_BODY = f"""<header class="hero">
<h1>🧬 PGx Demo</h1>
<p>Upload your DNA variant file — see how your genes affect <b>50+ medicines</b>. Educational pharmacogenomics, powered by CPIC guidelines.</p>
</header><div class="wrap">
{DISCLAIMER_HTML}
<div class="card"><h2>🧬 Human DNA → drug response</h2>
<p>Your genes decide how medicines work in <b>your</b> body — which dose helps, which drug harms.</p>
<form action="/pgx/api/analyze" method="post" enctype="multipart/form-data">
<p><b>Option 1:</b> Upload a <code>.vcf</code> or 23andMe raw <code>.txt</code> file<br>
<input type="file" name="file" accept=".vcf,.txt,.tsv"></p>
<p><button class="btn" type="submit">Analyze my DNA</button></p>
</form>
<form action="/pgx/api/analyze" method="post">
<input type="hidden" name="sample" value="1">
<p><b>Option 2:</b> No file? <button class="btn ghost" type="submit">🧪 Try sample DNA</button>
<a class="btn ghost" href="/pgx/sample.vcf" download>⬇ sample.vcf</a></p>
</form></div>
<div class="card"><h2>How it works (real-life example)</h2>
<div class="step"><div><b>1. DNA in:</b> A heart patient gets a stent and a DNA test. The file lists variants like <code>rs4244285</code>.</div></div>
<div class="step"><div><b>2. Star alleles:</b> We translate variants → star alleles, e.g. <code>CYP2C19 *2/*2</code>.</div></div>
<div class="step"><div><b>3. Phenotype:</b> <code>*2/*2</code> = <b>poor metabolizer</b> — the enzyme barely works.</div></div>
<div class="step"><div><b>4. Drug rule (CPIC):</b> Poor metabolizers can't activate <b>clopidogrel</b> → guideline says use ticagrelor instead. This exact scenario causes real stent failures worldwide.</div></div>
</div>
<div class="card"><h2>🦠 Bacterial DNA → antibiotic resistance</h2>
<p>Infection? Check the <b>bacteria's</b> genes — see which antibiotics still work and which are useless against it.</p>
<p><a class="btn" href="/pgx/resistance">Open resistance module →</a></p></div>
<div class="card"><h2>Gene panel (12 genes → 70 medicines)</h2>
<div class="grid">
<div><b>CYP2D6</b> — codeine, tramadol, tamoxifen, antidepressants (incl. venlafaxine), antipsychotics, metoprolol, ondansetron</div>
<div><b>CYP2C19</b> — clopidogrel, PPIs, voriconazole, SSRIs</div>
<div><b>CYP2C9</b> + <b>VKORC1</b> — warfarin, acenocoumarol, phenprocoumon, NSAIDs, phenytoin, siponimod</div>
<div><b>TPMT</b> + <b>NUDT15</b> — azathioprine, mercaptopurine, thioguanine</div>
<div><b>DPYD</b> — fluorouracil, capecitabine, tegafur</div>
<div><b>SLCO1B1</b> + <b>ABCG2</b> — statins, allopurinol</div>
<div><b>CYP2B6</b> — efavirenz, sertraline</div>
<div><b>CYP3A5</b> — tacrolimus</div>
<div><b>UGT1A1</b> — irinotecan, atazanavir</div>
</div>
<p style="font-size:.9rem">Every medicine card carries a source badge: <span class="badge b-green">CPIC</span> international guidelines or <span class="badge b-blue">DPWG</span> Dutch guidelines — both evidence-based clinical sources.</p>
<p style="font-size:.9rem">HLA alleles (abacavir, carbamazepine, allopurinol, phenytoin) &amp; G6PD (rasburicase) are shown as info cards — they need dedicated lab tests, not SNP chips.</p></div>
{DISCLAIMER_HTML}
</div><footer>PGx Demo · educational prototype · data: CPIC/DPWG/PharmGKB · not medical advice</footer>"""


def _report_html(res):
    sev_badge = {"ok": ("b-green", "Usual response"), "caution": ("b-yellow", "Use caution"),
                 "avoid": ("b-red", "Avoid / change"), "info": ("b-blue", "Not tested")}
    gene_cards = ""
    for g in res["genes"]:
        badge = {"normal": "b-green", "intermediate": "b-yellow",
                 "sensitive": "b-yellow", "poor": "b-red",
                 "high": "b-red", "unknown": "b-blue",
                 "expresser": "b-yellow"}.get(g["key"], "b-blue")
        v3d = ""
        st = g.get("structure")
        if st:
            cfg_json = json.dumps(
                {"cif": st["cif"], "af_url": st["af_url"],
                 "highlights": st["highlights"]}).replace("</", "<\\/")
            note_html = (f'<p style="font-size:.85rem;color:#5f716d">🧬 {st["note"]}</p>'
                         if st["note"] else "")
            legend = ""
            if st["highlights"]:
                legend = ('<p style="font-size:.8rem;color:#5f716d">'
                          '🔴 red sphere = variant found in <b>your</b> DNA'
                          ' &nbsp;·&nbsp; ⚪ gray = key residue shown for reference</p>')
            v3d = (f'<div style="margin-top:10px">'
                   f'<button class="btn ghost" id="btn3d-{g["gene"]}" '
                   f'style="padding:8px 16px;font-size:.9rem" '
                   f'onclick="toggle3D(\'{g["gene"]}\')">🧬 View 3D structure</button>'
                   f'<div id="v3d-{g["gene"]}" style="display:none;width:100%;height:280px;'
                   f'position:relative;border-radius:10px;overflow:hidden;'
                   f'border:1px solid #ccfbf1;margin-top:8px;background:#f8fafc"></div>'
                   f'<div id="msg3d-{g["gene"]}" style="display:none;margin-top:8px;font-size:.9rem"></div>'
                   f'{legend}{note_html}'
                   f'<script type="application/json" id="cfg3d-{g["gene"]}">{cfg_json}</script>'
                   f'<p style="font-size:.85rem;margin:6px 0 0">'
                   f'<a href="{st["af_url"]}" target="_blank" rel="noopener">Open in AlphaFold DB ↗</a> '
                   f'<span style="color:#5f716d">— AlphaFold-predicted protein structure</span></p>'
                   f'</div>')
        gene_cards += f"""<div class="card"><b>{g['gene']}</b> <span class="badge {badge}">{g['phenotype']}</span>
<p style="margin:6px 0"><code>{g['diplotype']}</code></p><p>{g['explanation']}</p>
<p style="font-size:.85rem;color:#5f716d">{g['desc']}<br><i>{g['cpic']}</i></p>{v3d}</div>"""

    drug_cards = ""
    src_badge = {"CPIC": ("b-green", "CPIC"), "DPWG": ("b-blue", "DPWG"),
                 "FDA": ("b-gray", "FDA label")}
    for d in res["drugs"]:
        cls, label = sev_badge[d["severity"]]
        scls, slabel = src_badge.get(d["source"], ("b-gray", d["source"]))
        drug_cards += f"""<div class="card sev-{d['severity']}"><b>{d['drug']}</b> <span class="badge {cls}">{label}</span> <span class="badge {scls}">{slabel}</span>
<p style="font-size:.9rem;color:#5f716d;margin:4px 0">{d['use']}</p><p>{d['text']}</p>
<p style="font-size:.8rem;color:#5f716d"><i>{d['cpic']}</i></p></div>"""

    var_rows = ""
    for v in res["variants"]:
        var_rows += f"<tr><td><code>{v['rsid']}</code></td><td>{v['gene']}</td><td><code>{v['genotype']}</code></td><td>{v['alleles']}</td></tr>"
    if not var_rows:
        var_rows = '<tr><td colspan="4">No panel variants found in this file.</td></tr>'

    n_red = sum(1 for d in res["drugs"] if d["severity"] == "avoid")
    n_yel = sum(1 for d in res["drugs"] if d["severity"] == "caution")
    n_cpic = sum(1 for d in res["drugs"] if d["source"] == "CPIC")
    n_dpwg = sum(1 for d in res["drugs"] if d["source"] == "DPWG")
    n_fda = sum(1 for d in res["drugs"] if d["source"] == "FDA")
    src_line = f"{len(res['drugs'])} medicines checked ({n_cpic} CPIC · {n_dpwg} DPWG" + \
               (f" · {n_fda} FDA label" if n_fda else "") + ")"
    summary = f"""<div class="card"><h2 style="margin-top:0">Your PGx summary</h2>
<p><span class="badge b-red">{n_red} avoid</span> <span class="badge b-yellow">{n_yel} caution</span>
<span class="badge b-green">{sum(1 for d in res['drugs'] if d['severity']=='ok')} usual</span></p>
<p style="font-size:.9rem">{src_line}</p>
<p style="font-size:.9rem">{res['n_panel']} panel variants found out of {res['n_genotyped']} genotyped markers.</p></div>"""

    legend = """<p style="font-size:.9rem"><b>Guideline sources:</b>
<span class="badge b-green">CPIC</span> = international pharmacogenomics guidelines (US-led consortium) ·
<span class="badge b-blue">DPWG</span> = Dutch Pharmacogenetics Working Group guidelines ·
<span class="badge b-gray">FDA label</span> = US drug-label requirement.
Both CPIC and DPWG are evidence-based clinical sources.</p>"""

    body = f"""<header class="hero"><h1>🧬 Your PGx Report</h1><p>Educational demo — not medical advice</p></header>
<div class="wrap">{DISCLAIMER_HTML}{summary}
<h2>Genes</h2><div class="grid">{gene_cards}</div>
<h2>Medicines</h2>{legend}{drug_cards}
<h2>Variants found</h2><div class="card"><table><tr><th>rsID</th><th>Gene</th><th>Genotype</th><th>Alleles</th></tr>{var_rows}</table></div>
{DISCLAIMER_HTML}
<p><a class="btn ghost" href="/pgx">← Analyze another file</a></p></div>
<footer>PGx Demo · educational prototype · verify with CPIC/PharmGKB + pharmacist</footer>"""
    return _page("Your PGx Report", body, REPORT_HEAD)


# ------------------------------------------------------------------ routes ---
@router.get("/pgx", response_class=HTMLResponse)
def pgx_page():
    return HTMLResponse(content=_page("Pharmacogenomics Demo", LANDING_BODY))


@router.get("/pgx/struct/{uniprot}.cif")
def pgx_structure(uniprot: str):
    """Same-origin proxy for AlphaFold CIF files.

    Why: alphafold.ebi.ac.uk sends no CORS headers (browser fetch fails) and
    model versions rotate (v4 -> v6 ...). We resolve the CURRENT cif URL via
    the AlphaFold API server-side, cache it locally, and serve same-origin.
    """
    uid = "".join(c for c in uniprot.upper() if c.isalnum())[:12]
    cached = _STRUCT_CACHE / f"AF-{uid}.cif"
    if cached.exists() and cached.stat().st_size > 10000:
        return Response(content=cached.read_bytes(), media_type="chemical/x-cif")
    try:
        with urllib.request.urlopen(
                f"https://alphafold.ebi.ac.uk/api/prediction/{uid}",
                timeout=25) as r:
            preds = json.loads(r.read().decode("utf-8"))
        cif_url = "".join(preds[0].get("cifUrl", []))
        if not cif_url.startswith("https://"):
            raise ValueError("no cif url")
        with urllib.request.urlopen(cif_url, timeout=60) as r:
            data = r.read()
        if len(data) < 10000 or not data.startswith(b"data_") or b"_atom_site" not in data:
            raise ValueError("bad cif")
        cached.write_bytes(data)
        return Response(content=data, media_type="chemical/x-cif")
    except Exception:
        return Response(content="unavailable", status_code=404)


@router.get("/pgx/sample.vcf")
def pgx_sample():
    p = _HERE / "sample.vcf"
    return Response(content=p.read_bytes(), media_type="text/vcf",
                    headers={"Content-Disposition": "attachment; filename=sample.vcf"})


@router.post("/pgx/api/analyze")
async def pgx_analyze(request: Request):
    ctype = request.headers.get("content-type", "")
    genotypes, fmt = {}, "empty"
    if "multipart/form-data" in ctype or "application/x-www-form-urlencoded" in ctype:
        form = await request.form()
        if form.get("sample") == "1":
            text = (_HERE / "sample.vcf").read_text(encoding="utf-8")
            genotypes, fmt = parse_genotypes(text)
        elif "multipart/form-data" in ctype:
            up = form.get("file")
            if up is None or not hasattr(up, "read"):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)
            raw = await up.read()
            try:
                text = raw.decode("utf-8", errors="ignore")
            except Exception:
                return JSONResponse({"error": "Could not read file"}, status_code=400)
            if len(text) > 10_000_000:
                return JSONResponse({"error": "File too large (10MB max)"}, status_code=400)
            genotypes, fmt = parse_genotypes(text)
        else:
            return JSONResponse({"error": "No file uploaded (use the upload form or sample DNA)"}, status_code=400)
    else:
        # allow JSON/form fallback: {"sample": true}
        try:
            data = await request.json()
        except Exception:
            data = {}
        if isinstance(data, dict) and data.get("sample"):
            text = (_HERE / "sample.vcf").read_text(encoding="utf-8")
            genotypes, fmt = parse_genotypes(text)

    res = analyze(genotypes)
    res["format"] = fmt
    # JSON if explicitly requested
    accept = request.headers.get("accept", "")
    if "application/json" in accept or request.query_params.get("format") == "json":
        return JSONResponse(res)
    return HTMLResponse(content=_report_html(res))


# ------------------------------------------------- resistance module ---
def _resistance_form_html():
    species_opts = "".join(
        f'<option value="{k}">{v["name"]}</option>'
        for k, v in R.SPECIES.items())
    groups = ""
    for cat, genes in R.GENE_CATEGORIES:
        boxes = "".join(
            f'<label style="display:inline-block;margin:4px 8px 4px 0;font-size:.92rem">'
            f'<input type="checkbox" name="gene" value="{g}"> <code>{g}</code></label>'
            for g in genes)
        groups += f"<h3 style='margin:14px 0 4px'>{cat}</h3><div>{boxes}</div>"
    body = f"""<header class="hero"><h1>🦠 Antibiotic Resistance Module</h1>
<p>Enter the <b>bacteria</b> and its detected resistance genes — see which antibiotics still work.</p></header>
<div class="wrap">
<div class="disclaimer">⚠️ <b>Educational demo — NOT medical advice.</b> {R.DISCLAIMER_RES}</div>
<div class="card"><h2>1. Bacteria</h2>
<form action="/pgx/resistance/analyze" method="post">
<p><select name="species" style="font-size:1rem;padding:10px;border-radius:10px;border:1px solid #99f6e4;max-width:100%">{species_opts}</select></p>
<h2>2. Resistance genes detected (lab report)</h2>
{groups}
<p style="margin-top:12px"><b>Or type gene names</b> (comma-separated):<br>
<input type="text" name="freetext" placeholder="e.g. mecA, blaKPC" style="width:100%;padding:10px;border-radius:10px;border:1px solid #99f6e4;margin-top:6px"></p>
<p><button class="btn" type="submit">Analyze resistance</button>
<a class="btn ghost" href="/pgx">← Back to PGx</a></p>
</form></div>
<div class="card"><h2>Try an example</h2>
<form action="/pgx/resistance/analyze" method="post">
<input type="hidden" name="species" value="saureus">
<input type="hidden" name="gene" value="mecA">
<p>Staph aureus + <code>mecA</code> (MRSA) → <button class="btn ghost" type="submit">Run example</button></p>
</form>
<p style="font-size:.9rem">Real labs detect these genes by PCR or whole-genome sequencing (tools like ResFinder). This demo covers an educational subset of ~{len(R.RES_GENES)} genes.</p></div>
<div class="disclaimer">⚠️ <b>Gene detection is triage only.</b> The final antibiotic decision always needs a culture-based S/I/R susceptibility report and a clinician.</div>
</div><footer>PGx Demo · resistance module · educational prototype · not medical advice</footer>"""
    return _page("Antibiotic Resistance", body)


def _resistance_report_html(res):
    sev_badge = {"ok": ("b-green", "Likely works"), "caution": ("b-yellow", "Use caution"),
                 "avoid": ("b-red", "Avoid — resistant")}
    cards = ""
    for c in res["cards"]:
        cls, label = sev_badge[c["severity"]]
        genes = (f'<p style="font-size:.85rem;margin:4px 0">🧬 {", ".join(f"<code>{g}</code>" for g in c["genes"])}</p>'
                 if c["genes"] else "")
        mechs = (f'<p style="font-size:.85rem;color:#5f716d">{" ".join(c["mechanisms"])}</p>'
                 if c["mechanisms"] else "")
        cards += f"""<div class="card sev-{c['severity']}"><b>{c['antibiotic']}</b> <span class="badge {cls}">{label}</span>{genes}{mechs}</div>"""
    found = "".join(f'<span class="badge b-red" style="margin:2px"><code>{g}</code></span>' for g in res["genes_found"])
    irr = "".join(f'<span class="badge b-blue" style="margin:2px"><code>{g}</code></span>' for g in res["genes_irrelevant"])
    unk = "".join(f'<span class="badge b-yellow" style="margin:2px"><code>{g}</code></span>' for g in res["genes_unknown"])
    extra = ""
    if irr:
        extra += f"<p style='font-size:.9rem'>Not relevant for this species: {irr}</p>"
    if unk:
        extra += f"<p style='font-size:.9rem'>Not in the demo database: {unk}</p>"
    summary = f"""<div class="card"><h2 style="margin-top:0">{res['species']}</h2>
<p><span class="badge b-red">{res['n_avoid']} avoid</span> <span class="badge b-yellow">{res['n_caution']} caution</span>
<span class="badge b-green">{res['n_ok']} likely work</span></p>
<p style="font-size:.9rem">Resistance genes detected: {found or '<i>none</i>'}</p>{extra}</div>"""
    body = f"""<header class="hero"><h1>🦠 Resistance Report</h1><p>{res['species']} — educational demo, not medical advice</p></header>
<div class="wrap">
<div class="disclaimer">⚠️ <b>Gene detection is triage only.</b> {R.DISCLAIMER_RES}</div>
{summary}<h2>Antibiotics</h2>{cards}
<div class="disclaimer">⚠️ Final antibiotic choice needs a culture-based <b>S/I/R</b> susceptibility report + clinician. This demo covers an educational subset of resistance genes.</div>
<p><a class="btn ghost" href="/pgx/resistance">← Analyze another</a> <a class="btn ghost" href="/pgx">PGx home</a></p></div>
<footer>PGx Demo · resistance module · educational prototype · not medical advice</footer>"""
    return _page("Resistance Report", body)


@router.get("/pgx/resistance", response_class=HTMLResponse)
def resistance_page():
    return HTMLResponse(content=_resistance_form_html())


@router.post("/pgx/resistance/analyze")
async def resistance_analyze(request: Request):
    form = await request.form()
    species = form.get("species", "other")
    genes = form.getlist("gene")
    freetext = form.get("freetext", "") or ""
    genes += [g.strip() for g in freetext.replace(";", ",").split(",") if g.strip()]
    res = R.analyze_resistance(species, genes)
    accept = request.headers.get("accept", "")
    if "application/json" in accept or request.query_params.get("format") == "json":
        return JSONResponse(res)
    return HTMLResponse(content=_resistance_report_html(res))


@router.get("/pgx/manifest.json")
def pgx_manifest():
    p = _HERE / "manifest.json"
    return Response(content=p.read_bytes(), media_type="application/manifest+json")


@router.get("/pgx/sw.js")
def pgx_sw():
    p = _HERE / "sw.js"
    return Response(content=p.read_bytes(), media_type="application/javascript")


@router.get("/pgx/icon-192.png")
def pgx_icon192():
    return Response(content=(_HERE / "icon-192.png").read_bytes(), media_type="image/png")


@router.get("/pgx/icon-512.png")
def pgx_icon512():
    return Response(content=(_HERE / "icon-512.png").read_bytes(), media_type="image/png")
