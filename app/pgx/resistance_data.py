"""Curated antibiotic-resistance data for the PGx resistance module — EDUCATIONAL ONLY.

This is an HONEST EDUCATIONAL SUBSET (~29 genes), not a clinical database.
Real resistance prediction uses tools like ResFinder/AMRFinderPlus on whole
genomes plus culture-based S/I/R testing. Gene detection is TRIAGE ONLY:
the final antibiotic decision always needs a culture S/I/R report + clinician.

"match" lists lowercase substrings matched against antibiotic names.
"species" lists species keys where the gene is clinically relevant
("all" = relevant everywhere).
"""

DISCLAIMER_RES = (
    "Educational demo — NOT medical advice. Resistance-gene detection is "
    "TRIAGE ONLY: the final antibiotic choice always needs a culture-based "
    "S/I/R susceptibility report and a clinician. Genes shown here are an "
    "educational subset, not a complete resistance database."
)

# species key -> {name, antibiotics (commonly used list)}
SPECIES = {
    "saureus": {
        "name": "Staphylococcus aureus",
        "antibiotics": ["Penicillin G", "Oxacillin", "Cefazolin", "Ceftriaxone",
                        "Vancomycin", "Clindamycin", "Erythromycin",
                        "Trimethoprim-sulfamethoxazole", "Doxycycline",
                        "Linezolid", "Daptomycin", "Gentamicin"]},
    "ecoli": {
        "name": "Escherichia coli",
        "antibiotics": ["Ampicillin", "Amoxicillin-clavulanate", "Cefazolin",
                        "Ceftriaxone", "Ciprofloxacin", "Nitrofurantoin",
                        "Fosfomycin", "Trimethoprim-sulfamethoxazole",
                        "Gentamicin", "Meropenem", "Colistin"]},
    "kpneumo": {
        "name": "Klebsiella pneumoniae",
        "antibiotics": ["Ceftriaxone", "Cefepime", "Ciprofloxacin",
                        "Gentamicin", "Amikacin", "Meropenem",
                        "Trimethoprim-sulfamethoxazole", "Colistin",
                        "Tigecycline"]},
    "paeruginosa": {
        "name": "Pseudomonas aeruginosa",
        "antibiotics": ["Piperacillin-tazobactam", "Ceftazidime", "Cefepime",
                        "Meropenem", "Ciprofloxacin", "Gentamicin", "Amikacin",
                        "Colistin"]},
    "enterococcus": {
        "name": "Enterococcus spp.",
        "antibiotics": ["Ampicillin", "Vancomycin", "Gentamicin (high-dose synergy)",
                        "Linezolid", "Daptomycin", "Nitrofurantoin"]},
    "mtb": {
        "name": "Mycobacterium tuberculosis",
        "antibiotics": ["Isoniazid", "Rifampin", "Pyrazinamide", "Ethambutol",
                        "Moxifloxacin"]},
    "other": {
        "name": "Other / unknown species",
        "antibiotics": ["Penicillin G", "Ampicillin", "Ceftriaxone",
                        "Ciprofloxacin", "Azithromycin", "Doxycycline",
                        "Vancomycin", "Gentamicin", "Meropenem",
                        "Trimethoprim-sulfamethoxazole"]},
}

# category -> list of genes (for grouped checkboxes)
GENE_CATEGORIES = [
    ("Beta-lactams", ["mecA", "mecC", "blaKPC", "blaNDM", "blaOXA-48",
                      "blaVIM", "blaIMP", "blaCTX-M", "blaSHV", "blaTEM",
                      "ampC"]),
    ("Glycopeptides", ["vanA", "vanB"]),
    ("Macrolides / lincosamides", ["ermA", "ermB", "mefA"]),
    ("Tetracyclines", ["tetM", "tetK"]),
    ("Fluoroquinolones", ["gyrA", "parC", "qnr"]),
    ("Aminoglycosides", ["rmtB", "armA"]),
    ("Anti-TB drugs", ["rpoB", "katG", "inhA"]),
    ("Other", ["mcr-1", "dfrA", "sul1"]),
]

RES_GENES = [
    # --- beta-lactams ---
    {"gene": "mecA",
     "mechanism": "Makes an altered penicillin-binding protein (PBP2a) that beta-lactams cannot bind.",
     "match": ["penicillin", "oxacillin", "methicillin", "ampicillin",
               "cephalosporin", "cefazolin", "ceftriaxone", "cefepime",
               "ceftazidime", "carbapenem", "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["saureus"],
     "note": "The MRSA marker. Nearly all beta-lactams fail — vancomycin, linezolid or daptomycin are the usual alternatives (confirm by culture)."},
    {"gene": "mecC",
     "mechanism": "mecA-like altered PBP — same beta-lactam failure.",
     "match": ["penicillin", "oxacillin", "methicillin", "ampicillin",
               "cephalosporin", "cefazolin", "ceftriaxone", "cefepime",
               "ceftazidime", "carbapenem", "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["saureus"],
     "note": "Rarer MRSA variant — missed by some mecA-only PCR tests."},
    {"gene": "blaKPC",
     "mechanism": "Carbapenemase enzyme — destroys penicillins, cephalosporins AND carbapenems.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "cefepime", "ceftazidime",
               "carbapenem", "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "KPC-producing CRE. Options are limited (e.g. ceftazidime-avibactam) — infectious-disease specialist territory."},
    {"gene": "blaNDM",
     "mechanism": "Metallo-carbapenemase — destroys nearly all beta-lactams.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "cefepime", "ceftazidime",
               "carbapenem", "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "NDM is NOT blocked by avibactam — even fewer options than KPC. Urgent infection-control situation."},
    {"gene": "blaOXA-48",
     "mechanism": "OXA-type carbapenemase — weakens carbapenems, destroys penicillins.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "carbapenem",
               "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "other"],
     "note": "Can look 'susceptible' on routine tests while failing in the patient — needs confirmatory testing."},
    {"gene": "blaVIM",
     "mechanism": "Metallo-carbapenemase — destroys penicillins, cephalosporins, carbapenems.",
     "match": ["penicillin", "ampicillin", "cephalosporin", "cefazolin",
               "ceftriaxone", "cefepime", "ceftazidime", "carbapenem",
               "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["paeruginosa", "ecoli", "kpneumo", "other"],
     "note": "Common in Pseudomonas — leaves very few beta-lactam options."},
    {"gene": "blaIMP",
     "mechanism": "Metallo-carbapenemase — same destructive range as VIM.",
     "match": ["penicillin", "ampicillin", "cephalosporin", "cefazolin",
               "ceftriaxone", "cefepime", "ceftazidime", "carbapenem",
               "meropenem", "piperacillin"],
     "severity": "avoid", "species": ["paeruginosa", "ecoli", "kpneumo", "other"],
     "note": "Treat like VIM — specialist management needed."},
    {"gene": "blaCTX-M",
     "mechanism": "Extended-spectrum beta-lactamase (ESBL) — destroys penicillins and 3rd-generation cephalosporins.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "ceftazidime", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "other"],
     "note": "The classic ESBL marker. Carbapenems (meropenem) usually still work — but confirm by culture, and never assume."},
    {"gene": "blaSHV",
     "mechanism": "ESBL-type enzyme — same range as CTX-M in its ESBL variants.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "ceftazidime", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "other"],
     "note": "ESBL family — treat like CTX-M until culture says otherwise."},
    {"gene": "blaTEM",
     "mechanism": "ESBL-type enzyme in its extended-spectrum variants.",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "ceftazidime", "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "other"],
     "note": "ESBL family — treat like CTX-M until culture says otherwise."},
    {"gene": "ampC",
     "mechanism": "Cephalosporinase — destroys penicillins and most cephalosporins (including 3rd-gen).",
     "match": ["penicillin", "ampicillin", "amoxicillin", "cephalosporin",
               "cefazolin", "ceftriaxone", "ceftazidime", "cefepime",
               "piperacillin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "Can be switched ON during therapy (inducible) — an initially 'susceptible' result can turn resistant mid-treatment."},
    # --- glycopeptides ---
    {"gene": "vanA",
     "mechanism": "Rebuilds the vancomycin target (D-Ala-D-Lac instead of D-Ala-D-Ala) — vancomycin cannot bind.",
     "match": ["vancomycin", "teicoplanin"],
     "severity": "avoid", "species": ["enterococcus", "saureus"],
     "note": "The VRE/VRSA marker. Linezolid or daptomycin are the usual alternatives (confirm by culture)."},
    {"gene": "vanB",
     "mechanism": "Same target change as vanA, but usually inducible and vancomycin-only.",
     "match": ["vancomycin"],
     "severity": "avoid", "species": ["enterococcus"],
     "note": "Teicoplanin often still works against vanB — but confirm by culture, never assume."},
    # --- macrolides / lincosamides ---
    {"gene": "ermA",
     "mechanism": "Methylates the ribosome — macrolides and clindamycin cannot bind (MLSb).",
     "match": ["erythromycin", "macrolide", "azithromycin", "clarithromycin",
               "clindamycin"],
     "severity": "avoid", "species": ["saureus", "other"],
     "note": "Clindamycin resistance can be INDUCIBLE — looks susceptible until treatment starts (D-test needed)."},
    {"gene": "ermB",
     "mechanism": "Ribosomal methylation — same MLSb pattern as ermA.",
     "match": ["erythromycin", "macrolide", "azithromycin", "clarithromycin",
               "clindamycin"],
     "severity": "avoid", "species": ["saureus", "enterococcus", "other"],
     "note": "Very common in enterococci and streptococci."},
    {"gene": "mefA",
     "mechanism": "Efflux pump that throws macrolides out of the cell (M phenotype).",
     "match": ["erythromycin", "macrolide", "azithromycin", "clarithromycin"],
     "severity": "avoid", "species": ["saureus", "other"],
     "note": "Clindamycin usually STILL works with mefA (unlike erm) — confirm by culture."},
    # --- tetracyclines ---
    {"gene": "tetM",
     "mechanism": "Ribosomal protection protein — tetracyclines cannot lock onto the ribosome.",
     "match": ["tetracycline", "doxycycline", "tigecycline", "minocycline"],
     "severity": "avoid", "species": ["saureus", "enterococcus", "other"],
     "note": "The most widespread tetracycline-resistance gene worldwide."},
    {"gene": "tetK",
     "mechanism": "Efflux pump for tetracyclines.",
     "match": ["tetracycline", "doxycycline", "minocycline"],
     "severity": "avoid", "species": ["saureus", "other"],
     "note": "Tigecycline often still works against tetK — confirm by culture."},
    # --- fluoroquinolones ---
    {"gene": "gyrA",
     "mechanism": "Mutation in DNA gyrase — the fluoroquinolone target is reshaped.",
     "match": ["ciprofloxacin", "levofloxacin", "moxifloxacin",
               "fluoroquinolone"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "saureus", "mtb", "other"],
     "note": "Usually needs a parC partner mutation for HIGH-level resistance — one mutation alone may only raise the MIC."},
    {"gene": "parC",
     "mechanism": "Mutation in topoisomerase IV — second fluoroquinolone target.",
     "match": ["ciprofloxacin", "levofloxacin", "moxifloxacin",
               "fluoroquinolone"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "saureus", "other"],
     "note": "gyrA + parC together = high-level fluoroquinolone resistance."},
    {"gene": "qnr",
     "mechanism": "Protein that shields DNA gyrase — LOW-level fluoroquinolone protection.",
     "match": ["ciprofloxacin", "levofloxacin", "moxifloxacin",
               "fluoroquinolone"],
     "severity": "caution", "species": ["ecoli", "kpneumo", "other"],
     "note": "Low-level on its own, but it helps bacteria survive long enough to develop gyrA/parC mutations."},
    # --- aminoglycosides ---
    {"gene": "rmtB",
     "mechanism": "Methylates 16S rRNA — aminoglycosides cannot bind the ribosome at all.",
     "match": ["gentamicin", "amikacin", "tobramycin", "aminoglycoside"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "Wipes out nearly ALL aminoglycosides at once, including amikacin."},
    {"gene": "armA",
     "mechanism": "16S rRNA methylase — same pan-aminoglycoside effect as rmtB.",
     "match": ["gentamicin", "amikacin", "tobramycin", "aminoglycoside"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "Often travels together with NDM carbapenemases — a nightmare combination."},
    # --- anti-TB ---
    {"gene": "rpoB",
     "mechanism": "Mutation in RNA polymerase — rifampin cannot bind.",
     "match": ["rifampin", "rifampicin"],
     "severity": "avoid", "species": ["mtb"],
     "note": "Rifampin resistance is the standard marker for MDR-TB — triggers the full MDR treatment protocol."},
    {"gene": "katG",
     "mechanism": "Isoniazid is a prodrug — katG activates it. Mutated katG means no activation.",
     "match": ["isoniazid"],
     "severity": "avoid", "species": ["mtb"],
     "note": "High-level isoniazid resistance — the drug never even turns on."},
    {"gene": "inhA",
     "mechanism": "Mutation in isoniazid's target — low-level resistance.",
     "match": ["isoniazid"],
     "severity": "caution", "species": ["mtb"],
     "note": "Low-level — higher isoniazid doses sometimes still work, decided by the TB specialist."},
    # --- other ---
    {"gene": "mcr-1",
     "mechanism": "Modifies lipid A in the outer membrane — colistin's target disappears.",
     "match": ["colistin", "polymyxin"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "paeruginosa", "other"],
     "note": "Colistin is a last-resort drug — mcr-1 leaves almost nothing in reserve. Infection-control emergency."},
    {"gene": "dfrA",
     "mechanism": "Altered DHFR enzyme — trimethoprim cannot block folate synthesis.",
     "match": ["trimethoprim"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "saureus", "other"],
     "note": "Knocks out the trimethoprim half of TMP-SMX."},
    {"gene": "sul1",
     "mechanism": "Altered DHPS enzyme — sulfamethoxazole cannot block folate synthesis.",
     "match": ["sulfamethoxazole"],
     "severity": "avoid", "species": ["ecoli", "kpneumo", "saureus", "other"],
     "note": "Knocks out the sulfamethoxazole half of TMP-SMX — together with dfrA the whole combination fails."},
]


def _norm(name):
    """Normalize a gene name for matching: lowercase, alnum only."""
    return "".join(c for c in name.lower() if c.isalnum())


GENE_INDEX = {_norm(g["gene"]): g for g in RES_GENES}


def analyze_resistance(species_key, gene_names):
    """Return report dict for a species + list of detected gene names."""
    species = SPECIES.get(species_key, SPECIES["other"])
    matched, unknown = [], []
    for name in gene_names:
        g = GENE_INDEX.get(_norm(name))
        if g:
            if g not in matched:
                matched.append(g)
        elif name.strip():
            unknown.append(name.strip())
    # keep only genes relevant to this species (or "all")
    relevant = [g for g in matched
                if "all" in g["species"] or species_key in g["species"]
                or species_key == "other"]
    irrelevant = [g for g in matched if g not in relevant]

    cards = []
    for abx in species["antibiotics"]:
        low = abx.lower()
        hits = [g for g in relevant
                if any(kw in low for kw in g["match"])]
        avoids = [g for g in hits if g["severity"] == "avoid"]
        cautions = [g for g in hits if g["severity"] == "caution"]
        if avoids:
            sev = "avoid"
        elif cautions:
            sev = "caution"
        else:
            sev = "ok"
        cards.append({"antibiotic": abx, "severity": sev,
                      "genes": [g["gene"] for g in hits],
                      "mechanisms": list({g["mechanism"] for g in hits})})
    return {"species": species["name"], "cards": cards,
            "genes_found": [g["gene"] for g in relevant],
            "genes_irrelevant": [g["gene"] for g in irrelevant],
            "genes_unknown": unknown,
            "n_avoid": sum(1 for c in cards if c["severity"] == "avoid"),
            "n_caution": sum(1 for c in cards if c["severity"] == "caution"),
            "n_ok": sum(1 for c in cards if c["severity"] == "ok")}
