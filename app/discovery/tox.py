"""ToxGuard kNN read-across: predict 12 Tox21 assay outcomes for a new SMILES
by weighted voting among the k most similar Tox21 compounds (Tanimoto).

This is the same read-across principle used in regulatory toxicology —
honest about being similarity-based, not a deep model.
"""
import gzip
import os
import threading

from . import chem as _chem

_lock = threading.RLock()
_DATA = None  # (assays, [(smiles, fp, labels)])
K = 15


def _load():
    global _DATA
    with _lock:
        if _DATA is not None:
            return _DATA
        here = os.path.dirname(os.path.abspath(__file__))
        # tox21 data lives in the workspace toxguard dir; fall back to local data/
        candidates = [
            "/home/hatch/workspace/toxguard/data/tox21.csv.gz",
            os.path.join(os.path.dirname(here), "data", "tox21.csv.gz"),
            os.path.join(here, "data", "tox21.csv.gz"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)
        if not path:
            _DATA = ([], [])
            return _DATA
        import csv
        assays, rows = None, []
        with gzip.open(path, "rt") as f:
            for i, row in enumerate(csv.DictReader(f)):
                if assays is None:
                    assays = [c for c in row.keys() if c not in ("mol_id", "smiles")]
                smi = (row.get("smiles") or "").strip()
                if not smi:
                    continue
                m = _chem.mol_from_smiles(smi)
                if m is None:
                    continue
                labels = {}
                for a in assays:
                    v = (row.get(a) or "").strip()
                    labels[a] = int(v) if v in ("0", "1") else None
                rows.append((smi, _chem.fp(m), labels))
                if len(rows) >= 8000:
                    break
        _DATA = (assays or [], rows)
        return _DATA


def predict(smiles, k=K):
    """Returns {assay: prob_active} + neighbor info, or None if SMILES invalid."""
    assays, rows = _load()
    if not rows:
        return {"ok": False, "error": "tox21_data_missing"}
    q = _chem.mol_from_smiles(smiles)
    if q is None:
        return {"ok": False, "error": "bad_smiles"}
    qfp = _chem.fp(q)
    scored = []
    for smi, f, labels in rows:
        s = _chem.tanimoto(qfp, f)
        scored.append((s, smi, labels))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:k]
    # exact match? return measured values
    if top and top[0][0] >= 0.999:
        return {"ok": True, "mode": "measured", "match_smiles": top[0][1],
                "assays": {a: top[0][2][a] for a in assays},
                "max_similarity": 1.0}
    probs = {}
    for a in assays:
        num = den = 0.0
        for s, smi, labels in top:
            v = labels[a]
            if v is None:
                continue
            w = s + 0.05
            num += w * v
            den += w
        probs[a] = round(num / den, 3) if den else None
    return {"ok": True, "mode": "knn_readacross", "k": k,
            "max_similarity": round(top[0][0], 3),
            "neighbors": [{"smiles": s, "similarity": round(x, 3)} for x, s, _ in top[:5]],
            "assays": probs}


def assay_names():
    assays, _ = _load()
    return assays
