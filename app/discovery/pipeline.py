"""LeadForge end-to-end pipeline orchestrator.

Target -> known ligands (ChEMBL) -> query verify (PubChem) ->
similarity screen (RDKit) -> ADMET panel (Lipinski/Veber, PAINS, ToxGuard) ->
ranked lead report. Every step cites its live source.
"""
from . import sources as S
from . import chem as C
from . import tox as T


def lead_score(similarity, desc, pains_alerts, tox_probs):
    """Transparent 0-100 composite. Documented, not a black box."""
    s = 0.0
    detail = {}
    sim_pts = round(min(similarity, 1.0) * 40, 1)
    s += sim_pts
    detail["similarity_40"] = sim_pts
    lip = 20 if desc and desc["lipinski_pass"] else 0
    s += lip
    detail["lipinski_20"] = lip
    veb = 10 if desc and desc["veber_pass"] else 0
    s += veb
    detail["veber_10"] = veb
    pa = 10 if pains_alerts == [] else 0
    s += pa
    detail["pains_clean_10"] = pa
    if tox_probs:
        vals = [v for v in tox_probs.values() if v is not None]
        avg = sum(vals) / len(vals) if vals else 0.5
        tx = round((1 - avg) * 20, 1)
    else:
        tx = 10.0
    s += tx
    detail["tox_low_20"] = tx
    return round(s, 1), detail


def run_pipeline(target_query, query_smiles=None, query_name=None, top_n=25,
                 dock_top_n=5):
    steps = []

    # ---- 1. target ----
    uni = S.uniprot_target(target_query)
    chembl_ts = S.chembl_targets(target_query)
    target = {
        "query": target_query,
        "uniprot": uni["data"] if uni["ok"] else None,
        "uniprot_error": uni.get("error"),
        "chembl_targets": chembl_ts["data"] if chembl_ts["ok"] else [],
    }
    steps.append({"step": 1, "name": "Target identification",
                  "source": "UniProtKB + ChEMBL (live)",
                  "status": "ok" if target["uniprot"] else "no_hit"})
    if not target["uniprot"]:
        return {"ok": False, "steps": steps, "error": "target_not_found"}

    # ---- 2. known ligands ----
    # precise: UniProt accession -> ChEMBL target, fallback to text search
    acc = target["uniprot"].get("accession")
    chembl_id = None
    if acc:
        by_acc = S.chembl_target_by_uniprot(acc)
        cands = [t for t in (by_acc["data"] if by_acc["ok"] else []) if t.get("chembl_id")]
        # prefer single-protein human target
        def _rank(t):
            return (0 if t.get("type") == "SINGLE PROTEIN" else 1,
                    0 if t.get("organism") == "Homo sapiens" else 1)
        cands.sort(key=_rank)
        if cands:
            chembl_id = cands[0]["chembl_id"]
            target["chembl_target"] = cands[0]
    if not chembl_id:
        gene = (target["uniprot"].get("gene") or "").upper()
        cands = [t for t in target["chembl_targets"] if t.get("chembl_id")]
        pick = None
        for t in cands:
            if gene and gene in (t.get("name") or "").upper():
                pick = t
                break
        pick = pick or (cands[0] if cands else None)
        if pick:
            chembl_id = pick["chembl_id"]
            target["chembl_target"] = pick
    ligands = []
    if chembl_id:
        bio = S.chembl_bioactivities(chembl_id, limit=60)
        if bio["ok"]:
            ligands = bio["data"]
    steps.append({"step": 2, "name": "Known ligand retrieval",
                  "source": f"ChEMBL bioactivities for {chembl_id or 'n/a'} (live)",
                  "status": "ok" if ligands else "no_data",
                  "count": len(ligands)})

    # ---- 3. query compound ----
    query = None
    if query_smiles:
        pc = S.pubchem_by_smiles(query_smiles)
        if pc["ok"] and pc["data"]:
            query = {"input": query_smiles, **pc["data"], "via": "smiles"}
    if query is None and query_name:
        pc = S.pubchem_by_name(query_name)
        if pc["ok"] and pc["data"]:
            query = {"input": query_name, **pc["data"], "via": "name"}
    steps.append({"step": 3, "name": "Query compound verification",
                  "source": "PubChem PUG REST (live)",
                  "status": "ok" if query else "not_provided_or_not_found"})

    # ---- 4. similarity screen ----
    ranked = []
    if query and ligands:
        q_smi = query.get("smiles") or query_smiles
        refs = [l["smiles"] for l in ligands if l.get("smiles")]
        sims = C.similarity_to(q_smi, refs)
        lig_by_smi = {l["smiles"]: l for l in ligands}
        for rs, score in sims[:top_n]:
            lig = lig_by_smi.get(rs, {})
            ranked.append({"smiles": rs, "similarity": score,
                           "chembl_id": lig.get("molecule_chembl_id"),
                           "pchembl": lig.get("pchembl"),
                           "activity": f"{lig.get('activity_type')} {lig.get('value')} {lig.get('units') or ''}".strip()})
    steps.append({"step": 4, "name": "Similarity screen vs known actives",
                  "source": "RDKit Morgan fingerprints, Tanimoto",
                  "status": "ok" if ranked else ("target_only" if ligands else "skipped"),
                  "count": len(ranked)})

    # ---- 5+6. ADMET + scoring ----
    leads = []
    if query:
        q_smi = query.get("smiles") or query_smiles
        desc = C.descriptors(q_smi)
        pa = C.pains(q_smi)
        tx = T.predict(q_smi)
        tox_probs = tx["assays"] if tx.get("ok") else None
        score, detail = lead_score(1.0, desc, pa or [], tox_probs)
        leads.append({"rank": 1, "label": "QUERY", "smiles": q_smi,
                      "similarity": 1.0, "score": score, "score_detail": detail,
                      "descriptors": desc, "pains": pa,
                      "tox": {"mode": tx.get("mode"), "max_similarity": tx.get("max_similarity"),
                              "assays": tox_probs},
                      "pubchem": {"cid": query.get("cid"), "url": query.get("url")},
                      "known_activity": None})
    for i, r in enumerate(ranked):
        desc = C.descriptors(r["smiles"])
        pa = C.pains(r["smiles"])
        tx = T.predict(r["smiles"])
        tox_probs = tx["assays"] if tx.get("ok") else None
        score, detail = lead_score(r["similarity"], desc, pa or [], tox_probs)
        leads.append({"rank": i + 2, "label": r["chembl_id"] or f"hit-{i+1}",
                      "smiles": r["smiles"], "similarity": r["similarity"],
                      "score": score, "score_detail": detail,
                      "descriptors": desc, "pains": pa,
                      "tox": {"mode": tx.get("mode"), "assays": tox_probs},
                      "known_activity": {"pchembl": r["pchembl"], "activity": r["activity"]}})
    # no query: rank known actives by measured potency + ADMET (target-only mode)
    if not query and ligands:
        for l in ligands[:top_n]:
            smi = l.get("smiles")
            if not smi:
                continue
            desc = C.descriptors(smi)
            pa = C.pains(smi)
            tx = T.predict(smi)
            tox_probs = tx["assays"] if tx.get("ok") else None
            score, detail = lead_score(0.0, desc, pa or [], tox_probs)
            # potency component replaces similarity: pChEMBL scaled to 0-40
            try:
                pch = float(l.get("pchembl") or 0)
            except (TypeError, ValueError):
                pch = 0.0
            pot_pts = round(min(max(pch, 0), 12) / 12 * 40, 1)
            score = round(score - detail["similarity_40"] + pot_pts, 1)
            detail["potency_pchembl_40"] = pot_pts
            del detail["similarity_40"]
            leads.append({"rank": 0, "label": l.get("molecule_chembl_id") or "hit",
                          "smiles": smi, "similarity": None,
                          "score": score, "score_detail": detail,
                          "descriptors": desc, "pains": pa,
                          "tox": {"mode": tx.get("mode"), "assays": tox_probs},
                          "known_activity": {"pchembl": l.get("pchembl"),
                                             "activity": f"{l.get('activity_type')} {l.get('value')} {l.get('units') or ''}".strip()}})
    leads.sort(key=lambda x: x["score"], reverse=True)
    for i, l in enumerate(leads):
        l["rank"] = i + 1
    steps.append({"step": 5, "name": "ADMET + safety panel",
                  "source": "RDKit (Lipinski/Veber/PAINS) + ToxGuard Tox21 kNN (12 assays)",
                  "status": "ok" if leads else "skipped"})
    steps.append({"step": 6, "name": "Lead ranking",
                  "source": "composite score: similarity×40 + Lipinski×20 + Veber×10 + PAINS×10 + tox×20",
                  "status": "ok" if leads else "skipped", "count": len(leads)})

    # ---- 7. structure-based docking (AutoDock Vina, top leads) ----
    docking = None
    if leads and dock_top_n > 0:
        try:
            from . import dock as D
            acc = (target.get("uniprot") or {}).get("accession")
            if acc:
                docking = D.dock_leads(leads, acc, top_n=min(dock_top_n, len(leads)))
                if docking.get("ok"):
                    aff = {r["label"]: r.get("affinity_kcal_mol")
                           for r in docking["results"]}
                    for l in leads:
                        if l["label"] in aff:
                            l["docking_kcal_mol"] = aff[l["label"]]
        except Exception as e:
            docking = {"ok": False, "error": str(e)[:200]}
    steps.append({"step": 7, "name": "Molecular docking",
                  "source": "AutoDock Vina vs PDB structure (RCSB, live)",
                  "status": ("ok" if docking and docking.get("ok") else
                             "skipped" if not dock_top_n else "failed"),
                  "pdb_id": (docking or {}).get("pdb_id")})

    return {"ok": True, "steps": steps, "target": target, "ligands_found": len(ligands),
            "leads": leads, "docking": docking,
            "disclaimer": ("Computational research only. Scores are triage heuristics, not "
                           "efficacy or safety proof. Wet-lab validation required. Not medical advice.")}
