"""Structure-based docking for LeadForge (AutoDock Vina).

Self-contained: downloads the official Vina binary at runtime (no build),
receptor prep via RDKit (Gasteiger charges + AutoDock atom types),
ligand prep via meeko (pure Python). CPU-based; top-N leads only.
Triage-grade — honest about not replacing expert docking setups.
"""
import os
import stat
import subprocess
import urllib.parse
import urllib.request

from rdkit import Chem
from rdkit.Chem import AllChem

_HERE = os.path.dirname(os.path.abspath(__file__))
_CACHE_DIR = os.path.join(_HERE, "data", "pdb_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)

_VINA_URL = ("https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/"
             "v1.2.7/vina_1.2.7_linux_x86_64")
_VINA_BIN = os.path.join(_CACHE_DIR, "vina")

_JUNK_LIGANDS = {"HOH", "WAT", "SO4", "PO4", "GOL", "EDO", "PEG", "PGE", "PG4",
                 "ZN", "MG", "CA", "NA", "CL", "K", "MN", "FE", "NI", "CU", "CO",
                 "IOD", "BR", "FMT", "ACT", "ACE", "DMS", "TRS", "MES", "CIT"}


def _dl(url, dest, timeout=120):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": "LeadForge-research/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def _vina_binary():
    _dl(_VINA_URL, _VINA_BIN)
    st = os.stat(_VINA_BIN)
    os.chmod(_VINA_BIN, st.st_mode | stat.S_IEXEC)
    return _VINA_BIN


def find_pdb_for_uniprot(accession):
    """Best ligand-bound, high-resolution PDB for a UniProt accession.

    UniProtKB PDB cross-references (X-ray, <3.0 A, sorted by resolution);
    verifies a drug-like bound ligand by parsing the PDB directly.
    """
    import json
    url = (f"https://rest.uniprot.org/uniprotkb/{urllib.parse.quote(accession, safe='')}.json"
           f"?fields=xref_pdb")
    req = urllib.request.Request(url, headers={"User-Agent": "LeadForge-research/1.0",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        d = json.loads(resp.read().decode())
    cands = []
    for x in d.get("uniProtKBCrossReferences") or []:
        if x.get("database") != "PDB":
            continue
        props = {pp.get("key"): pp.get("value") for pp in (x.get("properties") or [])}
        if props.get("Method") != "X-ray":
            continue
        try:
            res = float((props.get("Resolution") or "9 A").split()[0])
        except ValueError:
            continue
        if res < 3.0:
            cands.append((res, x["id"]))
    cands.sort()
    for res, pid in cands[:12]:
        try:
            center = _ligand_center(_pdb_path(pid))
            if center:
                return {"pdb_id": pid, "resolution": res, "center": center}
        except Exception:
            continue
    if cands:
        return {"pdb_id": cands[0][1], "resolution": cands[0][0], "center": None}
    return {"pdb_id": None, "resolution": None, "center": None}


def _pdb_path(pdb_id):
    return _dl(f"https://files.rcsb.org/download/{pdb_id}.pdb",
               os.path.join(_CACHE_DIR, f"{pdb_id}.pdb"), timeout=60)


def _ligand_center(pdb_path):
    """Centroid of the first drug-like HETATM ligand (skips waters/ions/cryo junk)."""
    current_res = None
    res_atoms = []
    xs = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("HETATM"):
                res = line[17:20].strip()
                if res in _JUNK_LIGANDS:
                    continue
                if res != current_res:
                    if res_atoms and len(res_atoms) >= 6:
                        xs = res_atoms
                        break
                    current_res = res
                    res_atoms = []
                try:
                    res_atoms.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
                except ValueError:
                    pass
    if res_atoms and len(res_atoms) >= 6 and not xs:
        xs = res_atoms
    if not xs:
        return None
    n = len(xs)
    return [sum(c[i] for c in xs) / n for i in range(3)]


def _ad_type(atom):
    """Simplified AutoDock atom type from RDKit atom."""
    el = atom.GetSymbol()
    if el == "H":
        # polar H = donor-bound
        for nb in atom.GetNeighbors():
            if nb.GetSymbol() in ("N", "O", "S"):
                return "HD"
        return "H"
    if el == "C":
        return "A" if atom.GetIsAromatic() else "C"
    if el == "N":
        return "NA" if atom.GetIsAromatic() else "N"
    if el == "O":
        return "OA"
    if el == "S":
        return "S"
    if el == "P":
        return "P"
    if el in ("F", "Cl", "Br", "I"):
        return el
    return "C"


def _prep_receptor(pdb_path, out_path):
    """PDB -> PDBQT via RDKit: protein atoms only, Hs added, Gasteiger charges,
    simplified AutoDock atom types. Triage-grade, fully self-contained."""
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return out_path
    # keep one altloc variant (A) to avoid duplicate atoms
    seen = set()
    lines = []
    with open(pdb_path) as f:
        for line in f:
            if line.startswith("ATOM"):
                alt = line[16]
                key = line[12:27]
                if alt not in (" ", "A"):
                    continue
                if key in seen:
                    continue
                seen.add(key)
                lines.append(line[:16] + " " + line[17:])
            elif line.startswith("END"):
                break
    mol = Chem.MolFromPDBBlock("".join(lines) + "END\n", removeHs=False)
    if mol is None:
        raise RuntimeError("pdb parse failed")
    mol = Chem.AddHs(mol, addCoords=True)
    AllChem.ComputeGasteigerCharges(mol)
    conf = mol.GetConformer()
    with open(out_path, "w") as f:
        f.write("REMARK LeadForge receptor (RDKit Gasteiger, simplified AD types)\n")
        for i, atom in enumerate(mol.GetAtoms()):
            pos = conf.GetAtomPosition(i)
            try:
                chg = float(atom.GetProp("_GasteigerCharge"))
            except Exception:
                chg = 0.0
            if abs(chg) > 99:
                chg = 0.0
            name = atom.GetPDBResidueInfo().GetName().strip() if atom.GetPDBResidueInfo() else atom.GetSymbol()
            res = atom.GetPDBResidueInfo().GetResidueName().strip() if atom.GetPDBResidueInfo() else "UNK"
            chain = atom.GetPDBResidueInfo().GetChainId().strip() if atom.GetPDBResidueInfo() else "A"
            resseq = atom.GetPDBResidueInfo().GetResidueNumber() if atom.GetPDBResidueInfo() else 1
            el = atom.GetSymbol()
            f.write(f"ATOM  {i+1:5d} {name:^4s} {res:>3s} {chain:1s}{resseq:4d}    "
                    f"{pos.x:8.3f}{pos.y:8.3f}{pos.z:8.3f}{0.0:6.2f}{0.0:6.2f}    "
                    f"{chg:+7.3f} {_ad_type(atom):<2s}\n")
        f.write("TER\nEND\n")
    return out_path


def _prep_ligand(smiles, out_path):
    from meeko import MoleculePreparation, PDBQTWriterLegacy
    m = Chem.MolFromSmiles(smiles)
    if m is None:
        raise ValueError("bad_smiles")
    m = Chem.AddHs(m)
    if AllChem.EmbedMolecule(m, randomSeed=42) != 0:
        raise RuntimeError("conformer_failed")
    AllChem.UFFOptimizeMolecule(m)
    prep = MoleculePreparation()
    setups = prep.prepare(m)
    if not setups:
        raise RuntimeError("ligand setup failed")
    pdbqt_str, is_ok, err = PDBQTWriterLegacy.write_string(setups[0])
    if not is_ok:
        raise RuntimeError(f"ligand prep failed: {err}")
    with open(out_path, "w") as f:
        f.write(pdbqt_str)
    return out_path


def dock(smiles, pdb_id, center, box_size=22.5, exhaustiveness=8, n_poses=3):
    """Dock one ligand with the Vina binary. Returns affinity or error dict."""
    tag = abs(hash(smiles)) % 10**8
    rec_pdbqt = os.path.join(_CACHE_DIR, f"{pdb_id}_rec.pdbqt")
    lig_pdbqt = os.path.join(_CACHE_DIR, f"lig_{tag}.pdbqt")
    out_pdbqt = os.path.join(_CACHE_DIR, f"out_{tag}.pdbqt")
    try:
        vina = _vina_binary()
        pdb_path = _pdb_path(pdb_id)
        _prep_receptor(pdb_path, rec_pdbqt)
        _prep_ligand(smiles, lig_pdbqt)
        cmd = [vina, "--receptor", rec_pdbqt, "--ligand", lig_pdbqt,
               "--center_x", str(center[0]), "--center_y", str(center[1]),
               "--center_z", str(center[2]),
               "--size_x", str(box_size), "--size_y", str(box_size),
               "--size_z", str(box_size),
               "--exhaustiveness", str(exhaustiveness),
               "--num_modes", str(n_poses),
               "--out", out_pdbqt]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            return {"ok": False, "error": f"vina failed: {(r.stderr or '')[:150]}"}
        # parse affinities from stdout table
        affs = []
        in_table = False
        for line in (r.stdout or "").splitlines():
            if "-----+------------" in line:
                in_table = True
                continue
            if in_table:
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    try:
                        affs.append(float(parts[1]))
                    except ValueError:
                        pass
                elif line.strip().startswith("Writing"):
                    break
        if not affs:
            return {"ok": False, "error": "no poses parsed"}
        return {"ok": True, "affinity_kcal_mol": round(affs[0], 2),
                "poses": [round(a, 2) for a in affs], "pdb_id": pdb_id}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    finally:
        for p in (lig_pdbqt, out_pdbqt):
            try:
                os.remove(p)
            except OSError:
                pass


def dock_leads(leads, accession, top_n=5, box_size=22.5):
    """Dock top_n leads against the best PDB for the target accession."""
    info = find_pdb_for_uniprot(accession)
    if not info.get("pdb_id"):
        return {"ok": False, "error": "no_pdb_found", "results": []}
    center = info.get("center")
    if not center:
        return {"ok": False, "error": "no_ligand_site", "pdb_id": info["pdb_id"], "results": []}
    results = []
    for l in leads[:top_n]:
        r = dock(l["smiles"], info["pdb_id"], center, box_size=box_size)
        r["label"] = l.get("label")
        r["rank"] = l.get("rank")
        results.append(r)
    results.sort(key=lambda x: x.get("affinity_kcal_mol", 999))
    return {"ok": True, "pdb_id": info["pdb_id"], "resolution": info["resolution"],
            "center": [round(c, 2) for c in center], "results": results}
