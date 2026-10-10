"""Live official data sources for the LeadForge discovery pipeline.

UniProt (targets), ChEMBL (bioactivities), PubChem (compound verification +
properties). All free, no keys. 24h in-memory cache.
"""
import json
import time
import urllib.parse
import urllib.request

_CACHE = {}
_CACHE_TTL = 24 * 3600
_UA = {"User-Agent": "LeadForge-research/1.0 (academic research prototype)"}


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _cached(key, fn):
    now = time.time()
    if key in _CACHE and now - _CACHE[key][0] < _CACHE_TTL:
        return _CACHE[key][1]
    try:
        payload = {"ok": True, "data": fn()}
    except Exception as e:
        payload = {"ok": False, "error": str(e)[:300]}
    _CACHE[key] = (now, payload)
    return payload


# ---------------- UniProt ----------------
def uniprot_target(query):
    """Gene/protein name -> best UniProtKB hit (human preferred)."""
    def fn():
        q = urllib.parse.quote(query.strip())
        url = (f"https://rest.uniprot.org/uniprotkb/search?query={q}&format=json"
               f"&size=5&fields=accession,id,gene_names,protein_name,organism_name,length,cc_function,sequence")
        d = _get(url)
        results = d.get("results") or []
        if not results:
            return None
        # prefer human
        results.sort(key=lambda r: 0 if "Homo sapiens" in str((r.get("organism") or {}).get("scientificName", "")) else 1)
        r = results[0]
        func = ""
        for c in r.get("comments") or []:
            if c.get("commentType") == "FUNCTION":
                texts = c.get("texts") or []
                if texts:
                    func = texts[0].get("value", "")
                break
        genes = r.get("genes") or []
        gene = ""
        if genes and genes[0].get("geneName"):
            gene = genes[0]["geneName"].get("value", "")
        return {
            "accession": r.get("primaryAccession"),
            "entry": r.get("uniProtKBCrossReferences") or r.get("id"),
            "gene": gene,
            "protein": (r.get("proteinDescription") or {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
            "organism": (r.get("organism") or {}).get("scientificName", ""),
            "length": r.get("sequence", {}).get("length"),
            "function": func[:800],
            "uniprot_url": f"https://www.uniprot.org/uniprotkb/{r.get('primaryAccession')}/entry",
        }
    return _cached("uniprot:" + query.strip().lower(), fn)


# ---------------- ChEMBL ----------------
def chembl_targets(query):
    """Text search -> ChEMBL targets."""
    def fn():
        q = urllib.parse.quote(query.strip())
        d = _get(f"https://www.ebi.ac.uk/chembl/api/data/target.json?q={q}&limit=10")
        return [_slim_target(t) for t in (d.get("targets") or [])]
    return _cached("ctarget:" + query.strip().lower(), fn)


def chembl_target_by_uniprot(accession):
    """Precise: UniProt accession -> ChEMBL target(s) via target components."""
    def fn():
        acc = urllib.parse.quote(accession.strip(), safe="")
        d = _get(f"https://www.ebi.ac.uk/chembl/api/data/target.json?"
                 f"target_components__accession={acc}&limit=10")
        return [_slim_target(t) for t in (d.get("targets") or [])]
    return _cached("ctacc:" + accession.strip().upper(), fn)


def _slim_target(t):
    return {
        "chembl_id": t.get("target_chembl_id"),
        "name": t.get("pref_name"),
        "type": t.get("target_type"),
        "organism": t.get("organism"),
        "components": len(t.get("target_components") or []),
    }


def chembl_bioactivities(target_chembl_id, limit=50):
    """Top bioactivities for a target, sorted by pChEMBL desc."""
    def fn():
        tid = urllib.parse.quote(target_chembl_id.strip(), safe="")
        url = (f"https://www.ebi.ac.uk/chembl/api/data/activity.json?"
               f"target_chembl_id={tid}&pchembl_value__gte=5&limit={limit}"
               f"&order_by=-pchembl_value")
        d = _get(url)
        out = []
        seen = set()
        for a in (d.get("activities") or []):
            smi = a.get("canonical_smiles")
            if not smi or smi in seen:
                continue
            seen.add(smi)
            out.append({
                "molecule_chembl_id": a.get("molecule_chembl_id"),
                "smiles": smi,
                "pchembl": a.get("pchembl_value"),
                "activity_type": a.get("standard_type"),
                "value": a.get("standard_value"),
                "units": a.get("standard_units"),
                "assay_chembl_id": a.get("assay_chembl_id"),
            })
            if len(out) >= limit:
                break
        return out
    return _cached("cbio:" + target_chembl_id.strip(), fn)


def chembl_molecule(chembl_id):
    def fn():
        cid = urllib.parse.quote(chembl_id.strip(), safe="")
        d = _get(f"https://www.ebi.ac.uk/chembl/api/data/molecule/{cid}.json")
        return {
            "chembl_id": d.get("molecule_chembl_id"),
            "name": d.get("pref_name"),
            "smiles": (d.get("molecule_structures") or {}).get("canonical_smiles"),
            "max_phase": d.get("max_phase"),
            "therapeutic_flag": d.get("therapeutic_flag"),
        }
    return _cached("cmol:" + chembl_id.strip(), fn)


# ---------------- PubChem ----------------
_PUG_PROPS = ("MolecularWeight,XLogP,HBondDonorCount,HBondAcceptorCount,"
              "TPSA,RotatableBondCount,HeavyAtomCount,IUPACName,CanonicalSMILES")


def pubchem_by_name(name):
    def fn():
        q = urllib.parse.quote(name.strip())
        d = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/{_PUG_PROPS}/JSON")
        props = (d.get("PropertyTable") or {}).get("Properties") or []
        if not props:
            return None
        p = props[0]
        syn = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{p['CID']}/synonyms/JSON")
        syns = (((syn.get("InformationList") or {}).get("Information") or [{}])[0].get("Synonym")) or []
        smi = p.get("CanonicalSMILES") or p.get("ConnectivitySMILES")
        return {"cid": p["CID"], "smiles": smi, "props": p,
                "synonyms": syns[:8],
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{p['CID']}"}
    return _cached("pcname:" + name.strip().lower(), fn)


def pubchem_by_smiles(smiles):
    def fn():
        q = urllib.parse.quote(smiles.strip(), safe="")
        d = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{q}/property/{_PUG_PROPS}/JSON")
        props = (d.get("PropertyTable") or {}).get("Properties") or []
        if not props:
            return None
        p = props[0]
        return {"cid": p["CID"], "smiles": smiles, "props": p,
                "url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{p['CID']}"}
    return _cached("pcsmi:" + smiles.strip().lower(), fn)


def pubchem_similar(smiles, threshold=80, max_records=30):
    """PubChem 2D similarity search (fastsimilarity). Returns CIDs + scores."""
    def fn():
        q = urllib.parse.quote(smiles.strip(), safe="")
        d = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity/smiles/{q}/cids/JSON?Threshold={threshold}&MaxRecords={max_records}")
        return d.get("IdentifierList", {}).get("CID") or []
    return _cached(f"pcsim:{smiles.strip().lower()}:{threshold}", fn)
