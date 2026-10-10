"""RDKit cheminformatics for LeadForge: fingerprints, similarity, drug-likeness."""
from rdkit import Chem
from rdkit.Chem import Descriptors, FilterCatalog, Lipinski, rdFingerprintGenerator, rdMolDescriptors

_MORGAN = None
_PAINS = None


def _morgan():
    global _MORGAN
    if _MORGAN is None:
        _MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    return _MORGAN


def _pains_catalog():
    global _PAINS
    if _PAINS is None:
        params = FilterCatalog.FilterCatalogParams()
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_A)
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_B)
        params.AddCatalog(FilterCatalog.FilterCatalogParams.FilterCatalogs.PAINS_C)
        _PAINS = FilterCatalog.FilterCatalog(params)
    return _PAINS


def mol_from_smiles(smiles):
    try:
        m = Chem.MolFromSmiles((smiles or "").strip())
        return m
    except Exception:
        return None


def fp(mol, radius=2, nbits=2048):
    return _morgan().GetFingerprint(mol)


def tanimoto(fp1, fp2):
    from rdkit.DataStructs import TanimotoSimilarity
    return TanimotoSimilarity(fp1, fp2)


def descriptors(smiles):
    """Lipinski/Veber panel. Returns None if SMILES invalid."""
    m = mol_from_smiles(smiles)
    if m is None:
        return None
    mw = Descriptors.MolWt(m)
    logp = Descriptors.MolLogP(m)
    hbd = Lipinski.NumHDonors(m)
    hba = Lipinski.NumHAcceptors(m)
    tpsa = rdMolDescriptors.CalcTPSA(m)
    rot = Lipinski.NumRotatableBonds(m)
    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    return {
        "mw": round(mw, 2), "logp": round(logp, 2), "hbd": hbd, "hba": hba,
        "tpsa": round(tpsa, 2), "rotatable": rot,
        "lipinski_violations": violations,
        "lipinski_pass": violations <= 1,
        "veber_pass": rot <= 10 and tpsa <= 140,
        "formula": rdMolDescriptors.CalcMolFormula(m),
    }


def pains(smiles):
    """Returns list of matched PAINS alerts (empty = clean)."""
    m = mol_from_smiles(smiles)
    if m is None:
        return None
    matches = _pains_catalog().GetMatches(m)
    out = []
    for mt in matches:
        try:
            out.append(mt.GetProp("_Name"))
        except Exception:
            out.append("PAINS alert")
    return sorted(set(out))


def similarity_to(smiles, ref_smiles_list):
    """Tanimoto of query vs each ref SMILES. Returns [(smiles, score)]."""
    q = mol_from_smiles(smiles)
    if q is None:
        return []
    qfp = fp(q)
    out = []
    for rs in ref_smiles_list:
        rm = mol_from_smiles(rs)
        if rm is None:
            continue
        out.append((rs, round(tanimoto(qfp, fp(rm)), 3)))
    out.sort(key=lambda x: x[1], reverse=True)
    return out
