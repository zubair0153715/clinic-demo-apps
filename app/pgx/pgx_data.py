"""Curated pharmacogenomics data for the PGx demo — EDUCATIONAL ONLY.

Sources: CPIC guidelines (cpicpgx.org) and PharmGKB. Star-allele definitions
follow CPIC allele-definition tables (simplified for demo — see SIMPLIFICATIONS).

CPIC guidelines referenced:
- CYP2D6 + codeine/tramadol: Crews KR et al., Clin Pharmacol Ther (CPIC)
- CYP2D6 + tamoxifen: Goetz MP et al. (CPIC)
- CYP2C19 + clopidogrel: Scott SA et al. (CPIC)
- CYP2C9/VKORC1 + warfarin: Johnson JA et al. (CPIC)
- TPMT + thiopurines: Relling MV et al. (CPIC)
- DPYD + fluoropyrimidines: Amstutz U et al. (CPIC)
- SLCO1B1 + simvastatin: Cooper-DeHoff RM et al. (CPIC)
- HLA-B + abacavir: Martin MA et al. (CPIC)
- HLA-B + carbamazepine: Leckband SG et al. (CPIC)
- CYP2B6 + efavirenz: Desta Z et al. (CPIC)
- CYP3A5 + tacrolimus: Birdwell KA et al. (CPIC)
- UGT1A1 + irinotecan: Dean L / CPIC (Hulshof EC et al.)
- UGT1A1 + atazanavir: Gammal RS et al. (CPIC)
- TPMT/NUDT15 + thiopurines: Relling MV et al. (CPIC)
- CYP2D6 + tricyclic antidepressants: Hicks JK et al. (CPIC)
- CYP2D6 + SSRIs (paroxetine/fluvoxamine): Hicks JK et al. (CPIC)
- CYP2D6 + atomoxetine: Brown JT et al. (CPIC)
- CYP2D6 + ondansetron: Bell GC et al. (CPIC)
- CYP2D6 + aripiprazole/risperidone: DPWG
- CYP2C19 + PPIs: Lima JJ et al. (CPIC)
- CYP2C19 + voriconazole: Moriyama B et al. (CPIC)
- CYP2C19 + SSRIs (citalopram/escitalopram/sertraline): Hicks JK et al. (CPIC)
- CYP2C9 + NSAIDs: Theken KN et al. (CPIC)
- CYP2C9 + phenytoin: Caudle KE et al. (CPIC)
- SLCO1B1 + statins: Cooper-DeHoff RM et al. (CPIC)
- ABCG2 + rosuvastatin/allopurinol: Cooper-DeHoff RM et al. / CPIC allopurinol (Saito Y et al.)
- HLA-B*58:01 + allopurinol: Saito Y et al. (CPIC)
- HLA-A*31:01 + carbamazepine: Leckband SG et al. (CPIC)
- CYP2C9 + flurbiprofen/meloxicam/lornoxicam (NSAIDs): Theken KN et al. (CPIC)
- CYP2C9 + fosphenytoin: Caudle KE et al. (CPIC)
- CYP2C9 + siponimod: CPIC
- CYP2D6 + tropisetron: Bell GC et al. (CPIC)
- CYP2D6 + oxycodone: Crews KR et al. (CPIC)
- CFTR + ivacaftor: CPIC (info card — needs CFTR sequencing)

DPWG (Dutch Pharmacogenetics Working Group) pairs — evidence-based Dutch
guidelines, labeled DPWG in the UI:
- CYP2D6 + venlafaxine / haloperidol / zuclopenthixol / metoprolol /
  propafenone / flecainide / pimozide / aripiprazole / risperidone
- CYP2C9 + piroxicam
- DPYD + tegafur
- CYP2C9/VKORC1 + acenocoumarol / phenprocoumon

SIMPLIFICATIONS (documented honestly):
1. CYP2D6 copy-number variants (*1xN, *2xN → ultrarapid metabolizer) CANNOT be
   called from SNP genotypes — needs CNV assay. Demo never reports ultrarapid.
2. Phasing is not performed: when two different variant SNPs are heterozygous,
   we count alleles, not haplotypes (e.g. TPMT *3A in cis vs trans).
3. Only the listed key SNPs are covered; real star-allele calling uses dozens
   (e.g. DPYD *13, c.2846A>T, HapB3 are NOT in this demo).
4. HLA alleles (*57:01, *15:02, *58:01, *31:01) need HLA typing — SNP chips cannot call them
   reliably. Shown as info-only cards, never as results.
5. Phenotype → recommendation mapping is a simplified summary of CPIC, not a
   substitute for the full guideline, a pharmacist, or a clinician.
6. CYP2C19*17 (rs12248560) is included; *17/*17 is reported as "rapid"
   (CPIC calls it ultrarapid — same clinical direction).
7. UGT1A1*28 is a TA-repeat needing fragment analysis; this demo uses the SNP
   proxy rs887829 (strong linkage) and SAYS SO on the gene card.
8. G6PD (rasburicase) is info-only: G6PD deficiency needs an enzyme-activity
   test, SNP screening alone is insufficient — the card explains this.
9. CYP3A5 logic is inverted vs other CYPs: *1 = functional (expresser),
   *3 = no-function. Most people are *3/*3 non-expressers — that is NORMAL.
10. DPWG pairs are Dutch-guideline recommendations, labeled DPWG (blue) vs
    CPIC (green) in the UI. Deliberately NOT included: thioridazine (no DPWG
    guideline found — only FDA-label QT wording), eliglustat (FDA-label CYP2D6
    dosing only, no DPWG guideline confirmed), carvedilol (no DPWG guideline
    confirmed). Honest subset beats a wrong one.
"""

DISCLAIMER = (
    "Educational demo — NOT medical advice. Real pharmacogenomics needs "
    "clinical-grade genotyping; verify every result with CPIC/PharmGKB and a "
    "pharmacist before any clinical use."
)

# ---------------------------------------------------------------------------
# SNP definitions: rsID -> {gene, ref, alt, alt_means, function}
# function: "no" (no-function allele), "decreased", "sensitivity" (VKORC1)
# ---------------------------------------------------------------------------
SNPS = {
    # CYP2D6
    "rs3892097": {"gene": "CYP2D6", "ref": "G", "alt": "A",
                  "star": "*4", "function": "no",
                  "note": "CYP2D6*4 (1846G>A) — no-function allele"},
    "rs1065852": {"gene": "CYP2D6", "ref": "C", "alt": "T",
                  "star": "*10", "function": "decreased",
                  "note": "CYP2D6*10 (100C>T) — decreased-function allele"},
    # CYP2C19
    "rs4244285": {"gene": "CYP2C19", "ref": "G", "alt": "A",
                  "star": "*2", "function": "no",
                  "note": "CYP2C19*2 (681G>A) — no-function allele"},
    "rs4986893": {"gene": "CYP2C19", "ref": "G", "alt": "A",
                  "star": "*3", "function": "no",
                  "note": "CYP2C19*3 (636G>A) — no-function allele"},
    # CYP2C9
    "rs1799853": {"gene": "CYP2C9", "ref": "C", "alt": "T",
                  "star": "*2", "function": "decreased",
                  "note": "CYP2C9*2 (430C>T) — decreased-function allele"},
    "rs1057910": {"gene": "CYP2C9", "ref": "A", "alt": "C",
                  "star": "*3", "function": "no",
                  "note": "CYP2C9*3 (1075A>C) — no-function allele"},
    # VKORC1
    "rs9923231": {"gene": "VKORC1", "ref": "G", "alt": "A",
                  "star": None, "function": "sensitivity",
                  "note": "VKORC1 -1639G>A — A allele = higher warfarin sensitivity"},
    # TPMT
    "rs1142345": {"gene": "TPMT", "ref": "A", "alt": "G",
                  "star": "*3C", "function": "no",
                  "note": "TPMT*3C (719A>G) — no-function allele"},
    "rs1800460": {"gene": "TPMT", "ref": "G", "alt": "A",
                  "star": "*3B", "function": "no",
                  "note": "TPMT*3B (460G>A) — no-function allele"},
    # DPYD
    "rs3918290": {"gene": "DPYD", "ref": "G", "alt": "A",
                  "star": "*2A", "function": "no",
                  "note": "DPYD*2A (IVS14+1G>A) — no-function allele"},
    # SLCO1B1
    "rs4149056": {"gene": "SLCO1B1", "ref": "T", "alt": "C",
                  "star": None, "function": "decreased",
                  "note": "SLCO1B1 521T>C — C allele = decreased transporter function"},
    # CYP2C19 *17 (increased function)
    "rs12248560": {"gene": "CYP2C19", "ref": "C", "alt": "T",
                   "star": "*17", "function": "increased",
                   "note": "CYP2C19*17 (-806C>T) — increased-function allele"},
    # CYP2B6
    "rs3745274": {"gene": "CYP2B6", "ref": "G", "alt": "T",
                  "star": "*6", "function": "decreased",
                  "note": "CYP2B6*6 (516G>T) — decreased-function allele"},
    "rs2279343": {"gene": "CYP2B6", "ref": "A", "alt": "G",
                  "star": "*4", "function": "increased",
                  "note": "CYP2B6*4 (785A>G) — increased-function allele"},
    # CYP3A5
    "rs776746": {"gene": "CYP3A5", "ref": "A", "alt": "G",
                 "star": "*3", "function": "no",
                 "note": "CYP3A5*3 (6986A>G) — no-function allele (*1 = functional)"},
    # UGT1A1
    "rs887829": {"gene": "UGT1A1", "ref": "C", "alt": "T",
                 "star": "*28 proxy", "function": "decreased",
                 "note": "UGT1A1*28 PROXY (SNP rs887829, strong linkage) — *28 itself is a TA repeat needing fragment analysis"},
    "rs4148323": {"gene": "UGT1A1", "ref": "G", "alt": "A",
                  "star": "*6", "function": "decreased",
                  "note": "UGT1A1*6 (211G>A) — decreased-function allele"},
    # NUDT15
    "rs116855232": {"gene": "NUDT15", "ref": "C", "alt": "T",
                    "star": "*3", "function": "no",
                    "note": "NUDT15*3 (415C>T, R139C) — no-function allele"},
    # ABCG2
    "rs2231142": {"gene": "ABCG2", "ref": "C", "alt": "A",
                  "star": None, "function": "decreased",
                  "note": "ABCG2 421C>A (Q141K) — A allele = decreased transporter function"},
}

GENE_INFO = {
    "CYP2D6": {"name": "CYP2D6",
               "desc": "Liver enzyme that activates codeine/tramadol into their active form and breaks down tamoxifen. About 5–10% of people are poor metabolizers.",
               "cpic": "CPIC guideline: CYP2D6 and codeine/tramadol (Crews et al.)"},
    "CYP2C19": {"name": "CYP2C19",
                "desc": "Liver enzyme that activates clopidogrel (a blood thinner). Poor metabolizers get almost no effect from it — a major cause of stent failure.",
                "cpic": "CPIC guideline: CYP2C19 and clopidogrel (Scott et al.)"},
    "CYP2C9": {"name": "CYP2C9",
               "desc": "Liver enzyme that clears warfarin (blood thinner). Slow variants mean warfarin builds up → bleeding risk.",
               "cpic": "CPIC guideline: CYP2C9/VKORC1 and warfarin (Johnson et al.)"},
    "VKORC1": {"name": "VKORC1",
               "desc": "The actual target of warfarin (vitamin-K recycling). The -1639A variant makes people extra sensitive to warfarin.",
               "cpic": "CPIC guideline: CYP2C9/VKORC1 and warfarin (Johnson et al.)"},
    "TPMT": {"name": "TPMT",
             "desc": "Enzyme that detoxifies thiopurine drugs (azathioprine). Poor metabolizers can suffer life-threatening bone-marrow suppression on normal doses.",
             "cpic": "CPIC guideline: TPMT and thiopurines (Relling et al.)"},
    "DPYD": {"name": "DPYD",
             "desc": "Enzyme that clears fluorouracil (chemo). Deficiency → severe, sometimes fatal toxicity on standard doses.",
             "cpic": "CPIC guideline: DPYD and fluoropyrimidines (Amstutz et al.)"},
    "SLCO1B1": {"name": "SLCO1B1",
                "desc": "Transporter that pulls statins into the liver. The 521C variant raises blood statin levels → muscle pain/myopathy risk.",
                "cpic": "CPIC guideline: SLCO1B1 and statins (Cooper-DeHoff et al.)"},
    "CYP2B6": {"name": "CYP2B6",
               "desc": "Liver enzyme that clears efavirenz (HIV drug) and sertraline. The *6 variant slows it down → drug builds up.",
               "cpic": "CPIC guideline: CYP2B6 and efavirenz (Desta et al.)"},
    "CYP3A5": {"name": "CYP3A5",
               "desc": "Liver enzyme that clears tacrolimus (transplant anti-rejection drug). *1 carriers ('expressers') burn through it fast and need higher doses.",
               "cpic": "CPIC guideline: CYP3A5 and tacrolimus (Birdwell et al.)"},
    "UGT1A1": {"name": "UGT1A1",
               "desc": "Liver enzyme that detoxifies irinotecan (chemo) and atazanavir (HIV drug). Low activity → severe side effects. *28 detected here via SNP proxy rs887829.",
               "cpic": "CPIC guidelines: UGT1A1 and irinotecan / atazanavir"},
    "NUDT15": {"name": "NUDT15",
               "desc": "Second thiopurine-detox gene alongside TPMT — especially important in Asian ancestry. Poor metabolizers risk life-threatening marrow toxicity.",
               "cpic": "CPIC guideline: TPMT/NUDT15 and thiopurines (Relling et al.)"},
    "ABCG2": {"name": "ABCG2",
              "desc": "Efflux transporter affecting rosuvastatin levels and allopurinol response. The Q141K variant reduces its function.",
              "cpic": "CPIC: SLCO1B1/ABCG2 and statins; ABCG2 and allopurinol"},
}


def _alt_count(genotype, ref, alt):
    """Count alt alleles in a 2-letter genotype like 'AG'. Returns None if unknown."""
    if not genotype or len(genotype) != 2:
        return None
    g = genotype.upper()
    if any(b not in (ref, alt) for b in g):
        return None  # unexpected base (e.g. no-call handled before)
    return sum(1 for b in g if b == alt)


def call_gene(gene, genotypes):
    """Return (diplotype, phenotype, phenotype_key, explanation).

    genotypes: dict rsID -> 2-letter genotype (e.g. 'AG'), missing = not tested.
    phenotype_key: one of normal/intermediate/poor/sensitive/high/unknown.
    """
    def ac(rsid):
        s = SNPS[rsid]
        return _alt_count(genotypes.get(rsid), s["ref"], s["alt"])

    if gene == "CYP2D6":
        n4 = ac("rs3892097") or 0
        n10 = ac("rs1065852") or 0
        known = "rs3892097" in genotypes or "rs1065852" in genotypes
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No CYP2D6 variants found in the file.")
        if n4 >= 2:
            dip, ph, key = "*4/*4", "Poor metabolizer", "poor"
        elif n4 == 1 and n10 >= 1:
            dip, ph, key = "*4/*10", "Intermediate metabolizer", "intermediate"
        elif n4 == 1:
            dip, ph, key = "*1/*4", "Intermediate metabolizer", "intermediate"
        elif n10 >= 2:
            dip, ph, key = "*10/*10", "Intermediate metabolizer", "intermediate"
        elif n10 == 1:
            dip, ph, key = "*1/*10", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"Diplotype {dip}: " +
                ("both copies broken — codeine/tramadol will barely work." if key == "poor" else
                 "one copy reduced — lower activation of codeine/tramadol." if key == "intermediate" else
                 "both copies normal — standard activation.") +
                " (Copy-number variants not tested — ultrarapid cannot be ruled out.)")
        return (dip, ph, key, expl)

    if gene == "CYP2C19":
        n2 = ac("rs4244285") or 0
        n3 = ac("rs4986893") or 0
        n17 = ac("rs12248560") or 0
        known = ("rs4244285" in genotypes or "rs4986893" in genotypes
                 or "rs12248560" in genotypes)
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No CYP2C19 variants found in the file.")
        nofunc = n2 + n3
        if nofunc >= 2:
            dip, ph, key = "*2/*2 (or *2/*3)", "Poor metabolizer", "poor"
        elif nofunc == 1 and n17 >= 1:
            dip, ph, key = "*2/*17 (or *3/*17)", "Intermediate metabolizer", "intermediate"
        elif nofunc == 1:
            dip, ph, key = "*1/*2 (or *1/*3)", "Intermediate metabolizer", "intermediate"
        elif n17 >= 2:
            dip, ph, key = "*17/*17", "Rapid metabolizer", "rapid"
        elif n17 == 1:
            dip, ph, key = "*1/*17", "Rapid metabolizer", "rapid"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"Diplotype {dip}: " +
                ("almost no clopidogrel activation — stent/heart-attack risk on standard therapy." if key == "poor" else
                 "reduced clopidogrel activation." if key == "intermediate" else
                 "faster than normal CYP2C19 activity — some drugs (voriconazole, PPIs) may wear off too quickly." if key == "rapid" else
                 "normal CYP2C19 activity."))
        return (dip, ph, key, expl)

    if gene == "CYP2C9":
        n2 = ac("rs1799853") or 0
        n3 = ac("rs1057910") or 0
        known = "rs1799853" in genotypes or "rs1057910" in genotypes
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No CYP2C9 variants found in the file.")
        func = 2 - (n2 + n3)  # functional copies (simplified: *2 counts as lost)
        if func <= 0:
            dip, ph, key = "*2/*2, *2/*3 or *3/*3", "Poor metabolizer", "poor"
        elif func == 1:
            dip, ph, key = "*1/*2 or *1/*3", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"Diplotype {dip}: " +
                ("warfarin cleared very slowly — bleeding risk on normal doses." if key == "poor" else
                 "warfarin cleared slowly — lower doses usually needed." if key == "intermediate" else
                 "normal warfarin clearance."))
        return (dip, ph, key, expl)

    if gene == "VKORC1":
        c = ac("rs9923231")
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs9923231 not found in the file.")
        if c >= 2:
            dip, ph, key = "AA", "High sensitivity", "high"
        elif c == 1:
            dip, ph, key = "GA", "Intermediate sensitivity", "sensitive"
        else:
            dip, ph, key = "GG", "Normal sensitivity", "normal"
        expl = (f"Genotype {dip}: " +
                ("very sensitive to warfarin — much lower doses needed." if key == "high" else
                 "more sensitive to warfarin than average." if key == "sensitive" else
                 "average warfarin sensitivity."))
        return (dip, ph, key, expl)

    if gene == "TPMT":
        n = (ac("rs1142345") or 0) + (ac("rs1800460") or 0)
        known = "rs1142345" in genotypes or "rs1800460" in genotypes
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No TPMT variants found in the file.")
        if n >= 2:
            dip, ph, key = "two no-function alleles", "Poor metabolizer", "poor"
        elif n == 1:
            dip, ph, key = "one no-function allele", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"{dip}: " +
                ("thiopurines can cause life-threatening marrow toxicity — avoid standard doses." if key == "poor" else
                 "start thiopurines at reduced dose with monitoring." if key == "intermediate" else
                 "normal thiopurine detoxification."))
        return (dip, ph, key, expl)

    if gene == "DPYD":
        c = ac("rs3918290")
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs3918290 not found in the file.")
        if c >= 2:
            dip, ph, key = "*2A/*2A", "Poor metabolizer", "poor"
        elif c == 1:
            dip, ph, key = "*1/*2A", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"{dip}: " +
                ("fluorouracil/capecitabine can cause severe toxicity — avoid standard dosing." if key == "poor" else
                 "reduce fluoropyrimidine starting dose." if key == "intermediate" else
                 "normal fluoropyrimidine clearance.") +
                " (Only *2A tested here; *13 and other variants not covered.)")
        return (dip, ph, key, expl)

    if gene == "SLCO1B1":
        c = ac("rs4149056")
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs4149056 not found in the file.")
        if c >= 2:
            dip, ph, key = "CC", "Poor function", "poor"
        elif c == 1:
            dip, ph, key = "CT", "Decreased function", "intermediate"
        else:
            dip, ph, key = "TT", "Normal function", "normal"
        expl = (f"Genotype {dip}: " +
                ("statin blood levels high — myopathy risk; avoid simvastatin." if key == "poor" else
                 "higher simvastatin exposure — limit dose or switch statin." if key == "intermediate" else
                 "normal statin transport."))
        return (dip, ph, key, expl)

    if gene == "CYP2B6":
        n6 = ac("rs3745274") or 0   # *6 decreased
        n4 = ac("rs2279343") or 0   # *4 increased
        known = "rs3745274" in genotypes or "rs2279343" in genotypes
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No CYP2B6 variants found in the file.")
        if n6 >= 2:
            dip, ph, key = "*6/*6", "Poor metabolizer", "poor"
        elif n6 == 1 and n4 >= 1:
            dip, ph, key = "*6/*4", "Intermediate metabolizer", "intermediate"
        elif n6 == 1:
            dip, ph, key = "*1/*6", "Intermediate metabolizer", "intermediate"
        elif n4 >= 1:
            dip, ph, key = "*1/*4 (or *4/*4)", "Rapid metabolizer", "rapid"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"Diplotype {dip}: " +
                ("efavirenz cleared very slowly — high CNS side-effect risk on standard dose." if key == "poor" else
                 "efavirenz cleared slowly — monitor for side effects." if key == "intermediate" else
                 "faster efavirenz clearance." if key == "rapid" else
                 "normal efavirenz clearance."))
        return (dip, ph, key, expl)

    if gene == "CYP3A5":
        # INVERTED logic: *1 = functional, *3 = no-function. *3/*3 (non-expresser) is normal.
        c = ac("rs776746")  # alt G = *3
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs776746 not found in the file.")
        if c == 0:
            dip, ph, key = "*1/*1", "Expresser", "expresser"
        elif c == 1:
            dip, ph, key = "*1/*3", "Expresser", "expresser"
        else:
            dip, ph, key = "*3/*3", "Non-expresser", "normal"
        expl = (f"Diplotype {dip}: " +
                ("you MAKE functional CYP3A5 — tacrolimus is cleared fast, so standard doses run too LOW (rejection risk). About 1.5–2× the starting dose is the guideline direction." if key == "expresser" else
                 "you make almost no CYP3A5 (like most people) — standard tacrolimus starting doses apply."))
        return (dip, ph, key, expl)

    if gene == "UGT1A1":
        n28 = ac("rs887829") or 0   # *28 proxy
        n6 = ac("rs4148323") or 0   # *6
        known = "rs887829" in genotypes or "rs4148323" in genotypes
        if not known:
            return ("not tested", "Unknown", "unknown",
                    "No UGT1A1 variants found in the file.")
        n = n28 + n6
        if n >= 2:
            dip, ph, key = "two decreased-function alleles", "Poor metabolizer", "poor"
        elif n == 1:
            dip, ph, key = "one decreased-function allele", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"{dip}: " +
                ("irinotecan can cause severe neutropenia/diarrhea — dose reduction needed; atazanavir may cause jaundice." if key == "poor" else
                 "mildly reduced detoxification — watch irinotecan toxicity." if key == "intermediate" else
                 "normal UGT1A1 activity.") +
                " (*28 read via SNP proxy rs887829 — confirm with fragment analysis before clinical use.)")
        return (dip, ph, key, expl)

    if gene == "NUDT15":
        c = ac("rs116855232")
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs116855232 not found in the file.")
        if c >= 2:
            dip, ph, key = "*3/*3", "Poor metabolizer", "poor"
        elif c == 1:
            dip, ph, key = "*1/*3", "Intermediate metabolizer", "intermediate"
        else:
            dip, ph, key = "*1/*1", "Normal metabolizer", "normal"
        expl = (f"Diplotype {dip}: " +
                ("thiopurines can cause life-threatening marrow toxicity — avoid standard doses." if key == "poor" else
                 "start thiopurines at reduced dose with monitoring." if key == "intermediate" else
                 "normal thiopurine detoxification via NUDT15.") +
                " (Check TPMT too — BOTH genes matter for thiopurines.)")
        return (dip, ph, key, expl)

    if gene == "ABCG2":
        c = ac("rs2231142")
        if c is None:
            return ("not tested", "Unknown", "unknown",
                    "rs2231142 not found in the file.")
        if c >= 2:
            dip, ph, key = "AA", "Poor function", "poor"
        elif c == 1:
            dip, ph, key = "CA", "Decreased function", "intermediate"
        else:
            dip, ph, key = "CC", "Normal function", "normal"
        expl = (f"Genotype {dip}: " +
                ("rosuvastatin blood levels run high — use a lower dose; allopurinol may work less well." if key == "poor" else
                 "somewhat higher rosuvastatin exposure." if key == "intermediate" else
                 "normal ABCG2 transporter function."))
        return (dip, ph, key, expl)

    return ("not tested", "Unknown", "unknown", "Gene not in demo panel.")


# ---------------------------------------------------------------------------
# Drug rules: each maps gene phenotype -> recommendation.
# severity: ok (green) / caution (yellow) / avoid (red) / info (blue)
# Single-gene rules use "gene"; multi-gene rules use "genes" (worst severity wins).
# ---------------------------------------------------------------------------

# Shared maps for multi-gene (combo) drugs.
NSAID_MAP = {
    "poor": ("caution", "CAUTION — higher blood levels; guideline: use the LOWEST effective dose for the SHORTEST time."),
    "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
    "normal": ("ok", "Normal clearance expected — standard dosing."),
    "unknown": ("info", "CYP2C9 not tested — no guidance possible."),
}

THIOPURINE_MAP = {
    "poor": ("avoid", "AVOID normal doses — life-threatening bone-marrow toxicity risk. Guidelines: use an alternative drug or a drastically reduced dose with close monitoring."),
    "intermediate": ("caution", "CAUTION — start at 30–70% of the normal dose and monitor blood counts closely."),
    "normal": ("ok", "Normal thiopurine detoxification — standard dosing with routine monitoring."),
    "unknown": ("info", "TPMT/NUDT15 not tested — no guidance possible."),
}

SERTRALINE_MAP = {
    "poor": ("avoid", "Higher sertraline exposure — guideline: start at 50% of the normal dose or consider an alternative antidepressant."),
    "intermediate": ("caution", "CAUTION — start low and titrate slowly, watching for side effects."),
    "rapid": ("caution", "CAUTION — faster clearance; watch for reduced effect."),
    "normal": ("ok", "Normal sertraline handling expected — standard dosing."),
    "unknown": ("info", "CYP2B6/CYP2C19 not tested — no guidance possible."),
}

ROSUVASTATIN_MAP = {
    "poor": ("avoid", "AVOID high rosuvastatin doses — blood levels run high (myopathy risk). Guideline: use a lower dose or a different statin."),
    "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
    "normal": ("ok", "Normal rosuvastatin handling expected — standard dosing."),
    "unknown": ("info", "SLCO1B1/ABCG2 not tested — no guidance possible."),
}


def _tca_rule(drug):
    """Tricyclic antidepressants share the CPIC CYP2D6 pattern."""
    return {"drug": drug, "use": "Tricyclic antidepressant (CYP2D6-cleared)",
            "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & tricyclic antidepressants (Hicks et al.)",
            "map": {
                "poor": ("avoid", f"AVOID {drug} if possible — very high blood levels and toxicity risk in poor metabolizers. Guideline: choose an alternative or cut the dose by 50% with blood-level monitoring."),
                "intermediate": ("caution", "CAUTION — guideline: reduce the dose by 25% with monitoring."),
                "normal": ("ok", "Normal handling expected — standard dosing."),
                "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}}


def _ppi_rule(drug):
    """Proton-pump inhibitors share the CPIC CYP2C19 pattern."""
    return {"drug": drug, "use": "Acid-reflux drug (CYP2C19-cleared)",
            "gene": "CYP2C19", "cpic": "CPIC: CYP2C19 & proton-pump inhibitors (Lima et al.)",
            "map": {
                "poor": ("caution", f"CAUTION — {drug} works STRONGER and longer for you; standard dose is effective, and it can often be reduced after healing."),
                "intermediate": ("ok", "Normal response expected — standard dosing."),
                "rapid": ("caution", f"CAUTION — {drug} may wear off too fast; a higher dose or a different acid drug may be needed."),
                "normal": ("ok", "Normal response expected — standard dosing."),
                "unknown": ("info", "CYP2C19 not tested — no guidance possible.")}}


DRUG_RULES = [
    {"drug": "Clopidogrel", "use": "Blood thinner after heart stent / heart attack",
     "gene": "CYP2C19", "cpic": "CPIC: CYP2C19 & clopidogrel (Scott et al.)",
     "map": {
         "poor": ("avoid", "AVOID clopidogrel — it will barely work for you. Guidelines recommend prasugrel or ticagrelor instead (if no contraindication)."),
         "intermediate": ("avoid", "AVOID clopidogrel if possible — reduced effect. Guidelines recommend prasugrel or ticagrelor instead."),
         "normal": ("ok", "Normal response expected — standard clopidogrel dosing."),
         "unknown": ("info", "CYP2C19 not tested — no guidance possible.")}},
    {"drug": "Codeine", "use": "Painkiller (prodrug — needs CYP2D6 to work)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & codeine (Crews et al.)",
     "map": {
         "poor": ("avoid", "AVOID codeine — your body barely converts it to morphine, so it won't relieve pain. Use a non-CYP2D6 painkiller."),
         "intermediate": ("caution", "CAUTION — reduced pain relief likely; a different analgesic may work better."),
         "normal": ("ok", "Normal conversion to morphine expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Tramadol", "use": "Painkiller (partly CYP2D6-activated)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & tramadol (Crews et al.)",
     "map": {
         "poor": ("avoid", "AVOID tramadol — poor activation in poor metabolizers; choose an alternative."),
         "intermediate": ("caution", "CAUTION — may be less effective; monitor response."),
         "normal": ("ok", "Normal activation expected."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Tamoxifen", "use": "Breast-cancer hormonal therapy (needs CYP2D6 activation)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & tamoxifen (Goetz et al.)",
     "map": {
         "poor": ("avoid", "AVOID tamoxifen if possible — poor activation lowers benefit; guidelines suggest an aromatase inhibitor instead (with ovarian suppression if premenopausal)."),
         "intermediate": ("caution", "CAUTION — consider aromatase inhibitor alternative per guideline."),
         "normal": ("ok", "Normal activation — standard tamoxifen 20 mg/day."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Warfarin", "use": "Blood thinner (dose tuned by CYP2C9 + VKORC1)",
     "gene": "CYP2C9", "gene2": "VKORC1",
     "cpic": "CPIC: CYP2C9/VKORC1 & warfarin (Johnson et al.)",
     "combo": "warfarin"},
    {"drug": "Azathioprine", "use": "Immunosuppressant (TPMT + NUDT15 detoxify it)",
     "genes": ["TPMT", "NUDT15"],
     "cpic": "CPIC: TPMT/NUDT15 & thiopurines (Relling et al.)",
     "map": THIOPURINE_MAP},
    {"drug": "Mercaptopurine (6-MP)", "use": "Leukemia / IBD drug (TPMT + NUDT15 detoxify it)",
     "genes": ["TPMT", "NUDT15"],
     "cpic": "CPIC: TPMT/NUDT15 & thiopurines (Relling et al.)",
     "map": THIOPURINE_MAP},
    {"drug": "Thioguanine", "use": "Leukemia drug (TPMT + NUDT15 detoxify it)",
     "genes": ["TPMT", "NUDT15"],
     "cpic": "CPIC: TPMT/NUDT15 & thiopurines (Relling et al.)",
     "map": THIOPURINE_MAP},
    {"drug": "Fluorouracil (5-FU)", "use": "Chemotherapy (needs DPD enzyme to clear)",
     "gene": "DPYD", "cpic": "CPIC: DPYD & fluoropyrimidines (Amstutz et al.)",
     "map": {
         "poor": ("avoid", "AVOID standard 5-FU dosing — severe/fatal toxicity risk in DPD deficiency. Alternative chemo preferred."),
         "intermediate": ("caution", "CAUTION — reduce starting dose by ~50% with close toxicity monitoring."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "DPYD not tested — no guidance possible.")}},
    {"drug": "Capecitabine", "use": "Oral chemo, converts to 5-FU (needs DPD to clear)",
     "gene": "DPYD", "cpic": "CPIC: DPYD & fluoropyrimidines (Amstutz et al.)",
     "map": {
         "poor": ("avoid", "AVOID standard dosing — severe toxicity risk; alternative preferred."),
         "intermediate": ("caution", "CAUTION — reduce starting dose by ~50%."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "DPYD not tested — no guidance possible.")}},
    {"drug": "Simvastatin", "use": "Cholesterol drug (SLCO1B1 controls liver uptake)",
     "gene": "SLCO1B1", "cpic": "CPIC: SLCO1B1 & simvastatin (Cooper-DeHoff et al.)",
     "map": {
         "poor": ("avoid", "AVOID simvastatin — high myopathy/rhabdomyolysis risk. Use rosuvastatin or pravastatin instead."),
         "intermediate": ("caution", "CAUTION — limit simvastatin to 20 mg/day or switch to rosuvastatin/pravastatin."),
         "normal": ("ok", "Normal statin transport — standard dosing."),
         "unknown": ("info", "SLCO1B1 not tested — no guidance possible.")}},
    {"drug": "Abacavir", "use": "HIV drug — needs HLA-B*57:01 screening",
     "gene": None, "cpic": "CPIC: HLA-B & abacavir (Martin et al.)",
     "info_only": True,
     "info": "HLA-B*57:01 causes life-threatening hypersensitivity to abacavir. SNP chips (like 23andMe) CANNOT call HLA alleles reliably — this needs dedicated HLA typing in a lab. Never start abacavir without a real HLA-B*57:01 test."},
    {"drug": "Carbamazepine", "use": "Epilepsy drug — HLA-B*15:02 risk in Asians",
     "gene": None, "cpic": "CPIC: HLA-B & carbamazepine (Leckband et al.)",
     "info_only": True,
     "info": "HLA-B*15:02 strongly predicts Stevens-Johnson syndrome with carbamazepine, especially in South/East Asian ancestry. The SNP proxy (rs144012689) is imperfect — proper HLA typing is required before prescribing to at-risk patients."},
    # ------------------------- CYP2B6 -------------------------
    {"drug": "Efavirenz", "use": "HIV drug (CYP2B6-cleared)",
     "gene": "CYP2B6", "cpic": "CPIC: CYP2B6 & efavirenz (Desta et al.)",
     "map": {
         "poor": ("avoid", "AVOID the standard 600 mg dose — very high blood levels with CNS side effects (dizziness, vivid dreams, low mood). Guideline: consider an alternative HIV regimen or a TDM-guided lower dose."),
         "intermediate": ("caution", "CAUTION — higher exposure; watch for CNS side effects."),
         "rapid": ("ok", "Normal-to-fast clearance expected — standard dosing with viral-load monitoring."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "CYP2B6 not tested — no guidance possible.")}},
    # ------------------------- CYP3A5 -------------------------
    {"drug": "Tacrolimus", "use": "Transplant anti-rejection drug (CYP3A5-cleared)",
     "gene": "CYP3A5", "cpic": "CPIC: CYP3A5 & tacrolimus (Birdwell et al.)",
     "map": {
         "expresser": ("caution", "CAUTION — you clear tacrolimus FAST: guideline starting dose is 1.5–2× higher than standard, then adjusted by blood levels. Standard doses risk organ REJECTION."),
         "normal": ("ok", "Non-expresser (like most people) — standard starting dose with routine blood-level monitoring."),
         "unknown": ("info", "CYP3A5 not tested — no guidance possible.")}},
    # ------------------------- UGT1A1 -------------------------
    {"drug": "Irinotecan", "use": "Chemotherapy (UGT1A1-detoxified)",
     "gene": "UGT1A1", "cpic": "CPIC: UGT1A1 & irinotecan",
     "map": {
         "poor": ("avoid", "AVOID full dose — severe neutropenia/diarrhea risk. Guideline: reduce the starting dose (e.g. by ~30%) with close monitoring, or choose an alternative."),
         "intermediate": ("caution", "CAUTION — watch closely for neutropenia and diarrhea."),
         "normal": ("ok", "Normal detoxification expected — standard dosing."),
         "unknown": ("info", "UGT1A1 not tested — no guidance possible.")}},
    {"drug": "Atazanavir", "use": "HIV drug (UGT1A1-affected)",
     "gene": "UGT1A1", "cpic": "CPIC: UGT1A1 & atazanavir (Gammal et al.)",
     "map": {
         "poor": ("caution", "CAUTION — high jaundice (bilirubin) risk; guideline suggests considering an alternative HIV drug."),
         "intermediate": ("caution", "CAUTION — bilirubin may rise; usually harmless but monitor."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "UGT1A1 not tested — no guidance possible.")}},
    # ------------------------- ABCG2 -------------------------
    {"drug": "Rosuvastatin", "use": "Cholesterol drug (SLCO1B1 + ABCG2 transport)",
     "genes": ["SLCO1B1", "ABCG2"],
     "cpic": "CPIC: SLCO1B1/ABCG2 & statins (Cooper-DeHoff et al.)",
     "map": ROSUVASTATIN_MAP},
    {"drug": "Allopurinol", "use": "Gout drug (ABCG2 affects response)",
     "gene": "ABCG2", "cpic": "CPIC: ABCG2 & allopurinol",
     "map": {
         "poor": ("caution", "CAUTION — reduced response likely (Q141K); may need a higher dose or an alternative. SEPARATELY: an HLA-B*58:01 lab test is REQUIRED before starting (SJS risk) — see the HLA card below."),
         "intermediate": ("caution", "CAUTION — response may be reduced; monitor uric acid. HLA-B*58:01 lab test still required before starting."),
         "normal": ("ok", "Normal ABCG2 function — standard dosing. HLA-B*58:01 lab test still required before starting."),
         "unknown": ("info", "ABCG2 not tested — no guidance possible.")}},
    # ------------------------- CYP2C9 additions -------------------------
    {"drug": "Celecoxib", "use": "Pain/inflammation drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "cpic": "CPIC: CYP2C9 & NSAIDs (Theken et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; guideline: use the LOWEST effective dose for the SHORTEST time."),
         "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "CYP2C9 not tested — no guidance possible.")}},
    {"drug": "Ibuprofen", "use": "Pain/inflammation drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "cpic": "CPIC: CYP2C9 & NSAIDs (Theken et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; guideline: use the LOWEST effective dose for the SHORTEST time."),
         "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "CYP2C9 not tested — no guidance possible.")}},
    {"drug": "Phenytoin", "use": "Epilepsy drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "cpic": "CPIC: CYP2C9 & phenytoin (Caudle et al.)",
     "map": {
         "poor": ("caution", "CAUTION — phenytoin builds up; guideline: cut the maintenance dose by 25–50% with blood-level monitoring."),
         "intermediate": ("caution", "CAUTION — consider a 25% dose reduction with monitoring."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "CYP2C9 not tested — no guidance possible.")}},
    # ------------------------- CYP2C19 additions -------------------------
    _ppi_rule("Omeprazole"),
    _ppi_rule("Lansoprazole"),
    _ppi_rule("Pantoprazole"),
    {"drug": "Voriconazole", "use": "Antifungal (CYP2C19-cleared)",
     "gene": "CYP2C19", "cpic": "CPIC: CYP2C19 & voriconazole (Moriyama et al.)",
     "map": {
         "poor": ("caution", "CAUTION — high blood levels and toxicity risk; guideline: use a lower dose with drug-level monitoring."),
         "intermediate": ("ok", "Standard dosing with routine monitoring."),
         "rapid": ("avoid", "AVOID if possible — likely subtherapeutic levels; guideline prefers an alternative antifungal."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2C19 not tested — no guidance possible.")}},
    {"drug": "Escitalopram", "use": "Antidepressant (CYP2C19-cleared)",
     "gene": "CYP2C19", "cpic": "CPIC: CYP2C19 & SSRIs (Hicks et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher exposure; guideline: start at 50% of the normal dose or consider an alternative."),
         "intermediate": ("ok", "Standard starting dose."),
         "rapid": ("avoid", "AVOID if possible — likely poor response; guideline prefers an alternative antidepressant."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2C19 not tested — no guidance possible.")}},
    {"drug": "Citalopram", "use": "Antidepressant (CYP2C19-cleared)",
     "gene": "CYP2C19", "cpic": "CPIC: CYP2C19 & SSRIs (Hicks et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher exposure; guideline: start at 50% of the normal dose or consider an alternative."),
         "intermediate": ("ok", "Standard starting dose."),
         "rapid": ("avoid", "AVOID if possible — likely poor response; guideline prefers an alternative antidepressant."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2C19 not tested — no guidance possible.")}},
    {"drug": "Sertraline", "use": "Antidepressant (CYP2B6 + CYP2C19-cleared)",
     "genes": ["CYP2B6", "CYP2C19"],
     "cpic": "CPIC: CYP2C19 & sertraline; CYP2B6 & sertraline (Hicks et al.)",
     "map": SERTRALINE_MAP},
    # ------------------------- CYP2D6 additions -------------------------
    _tca_rule("Amitriptyline"),
    _tca_rule("Nortriptyline"),
    _tca_rule("Doxepin"),
    _tca_rule("Imipramine"),
    _tca_rule("Clomipramine"),
    _tca_rule("Desipramine"),
    _tca_rule("Trimipramine"),
    {"drug": "Paroxetine", "use": "Antidepressant (CYP2D6-cleared)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & paroxetine/fluvoxamine (Hicks et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; guideline: consider an alternative or a lower starting dose."),
         "intermediate": ("ok", "Standard starting dose."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Fluvoxamine", "use": "Antidepressant/OCD drug (CYP2D6-cleared)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & paroxetine/fluvoxamine (Hicks et al.)",
     "map": {
         "poor": ("caution", "CAUTION — guideline: reduce the dose by 25–50% or choose an alternative."),
         "intermediate": ("ok", "Standard starting dose."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Atomoxetine", "use": "ADHD drug (CYP2D6-cleared)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & atomoxetine (Brown et al.)",
     "map": {
         "poor": ("caution", "CAUTION — much higher exposure; guideline: lower starting dose with slower increases."),
         "intermediate": ("caution", "CAUTION — monitor for side effects; titrate slowly."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Aripiprazole", "use": "Antipsychotic (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & aripiprazole",
     "map": {
         "poor": ("caution", "CAUTION — FDA label: use HALF the usual dose in poor metabolizers."),
         "intermediate": ("ok", "Standard dosing with monitoring."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Risperidone", "use": "Antipsychotic (CYP2D6-cleared)",
     "gene": "CYP2D6", "cpic": "DPWG: CYP2D6 & risperidone",
     "map": {
         "poor": ("caution", "CAUTION — higher active levels; a lower dose is usually needed."),
         "intermediate": ("caution", "CAUTION — monitor for side effects; dose may need lowering."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Ondansetron", "use": "Anti-nausea drug (CYP2D6-affected)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & ondansetron (Bell et al.)",
     "map": {
         "poor": ("avoid", "AVOID if possible — poor metabolizers get LESS anti-nausea effect; guideline prefers granisetron."),
         "intermediate": ("ok", "Standard dosing."),
         "normal": ("ok", "Normal response expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Hydrocodone", "use": "Painkiller (needs CYP2D6 to activate)",
     "gene": "CYP2D6", "cpic": "CPIC: CYP2D6 & opioids (Crews et al., principle as codeine)",
     "map": {
         "poor": ("avoid", "AVOID — your body barely activates it, so pain relief will be poor; choose a non-CYP2D6 painkiller."),
         "intermediate": ("caution", "CAUTION — may be less effective; monitor pain relief."),
         "normal": ("ok", "Normal activation expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    # ------------------------- SLCO1B1 additions -------------------------
    {"drug": "Pravastatin", "use": "Cholesterol drug (SLCO1B1 transport)",
     "gene": "SLCO1B1", "cpic": "CPIC: SLCO1B1 & statins (Cooper-DeHoff et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; consider a lower dose."),
         "intermediate": ("ok", "Small effect — standard dosing."),
         "normal": ("ok", "Normal transport — standard dosing."),
         "unknown": ("info", "SLCO1B1 not tested — no guidance possible.")}},
    {"drug": "Pitavastatin", "use": "Cholesterol drug (SLCO1B1 transport)",
     "gene": "SLCO1B1", "cpic": "CPIC: SLCO1B1 & statins (Cooper-DeHoff et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; consider a lower dose."),
         "intermediate": ("ok", "Small effect — standard dosing."),
         "normal": ("ok", "Normal transport — standard dosing."),
         "unknown": ("info", "SLCO1B1 not tested — no guidance possible.")}},
    {"drug": "Fluvastatin", "use": "Cholesterol drug (SLCO1B1 transport)",
     "gene": "SLCO1B1", "cpic": "CPIC: SLCO1B1 & statins (Cooper-DeHoff et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher blood levels; consider a lower dose."),
         "intermediate": ("ok", "Small effect — standard dosing."),
         "normal": ("ok", "Normal transport — standard dosing."),
         "unknown": ("info", "SLCO1B1 not tested — no guidance possible.")}},
    {"drug": "Atorvastatin", "use": "Cholesterol drug (SLCO1B1 transport)",
     "gene": "SLCO1B1", "cpic": "CPIC: SLCO1B1 & statins (Cooper-DeHoff et al.)",
     "map": {
         "poor": ("caution", "CAUTION — higher exposure; consider a lower dose or rosuvastatin/pravastatin."),
         "intermediate": ("ok", "Small effect — standard dosing."),
         "normal": ("ok", "Normal transport — standard dosing."),
         "unknown": ("info", "SLCO1B1 not tested — no guidance possible.")}},
    # ------------------------- G6PD (info only) -------------------------
    {"drug": "Rasburicase", "use": "Gout/tumor-lysis drug — G6PD deficiency risk",
     "gene": None, "cpic": "FDA label: G6PD & rasburicase",
     "info_only": True,
     "info": "G6PD deficiency makes red blood cells burst (hemolysis) with rasburicase — can be fatal. A SNP chip CANNOT rule this out: you need a G6PD ENZYME ACTIVITY blood test in a lab. Never give rasburicase without it."},
    # ------------------------- HLA info cards -------------------------
    {"drug": "Allopurinol (HLA-B*58:01)", "use": "Gout drug — HLA-B*58:01 hypersensitivity screen",
     "gene": None, "cpic": "CPIC: HLA-B & allopurinol (Saito et al.)",
     "info_only": True,
     "info": "HLA-B*58:01 strongly predicts Stevens-Johnson syndrome / toxic epidermal necrolysis with allopurinol — especially in Han Chinese, Thai, and Korean ancestry. SNP chips cannot call HLA alleles — dedicated lab HLA typing is required before starting allopurinol in at-risk patients."},
    {"drug": "Phenytoin / Oxcarbazepine (HLA-B*15:02)", "use": "Epilepsy drugs — HLA-B*15:02 SJS screen",
     "gene": None, "cpic": "CPIC: HLA-B & phenytoin (Karnes et al.)",
     "info_only": True,
     "info": "HLA-B*15:02 predicts Stevens-Johnson syndrome with phenytoin and oxcarbazepine in Asian ancestry (same allele as the carbamazepine risk). Needs lab HLA typing — SNP chips can't do it."},
    {"drug": "Carbamazepine (HLA-A*31:01)", "use": "Epilepsy drug — HLA-A*31:01 hypersensitivity screen",
     "gene": None, "cpic": "CPIC: HLA-A & carbamazepine (Leckband et al.)",
     "info_only": True,
     "info": "HLA-A*31:01 predicts carbamazepine hypersensitivity (including Stevens-Johnson syndrome) — reported in European and Japanese ancestry. Needs lab HLA typing — SNP chips can't do it."},
    # ------------------------- CPIC: more CYP2C9 NSAIDs -------------------------
    {"drug": "Flurbiprofen", "use": "Pain/inflammation drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "CPIC", "cpic": "CPIC: CYP2C9 & NSAIDs (Theken et al.)",
     "map": NSAID_MAP},
    {"drug": "Meloxicam", "use": "Arthritis pain drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "CPIC", "cpic": "CPIC: CYP2C9 & NSAIDs (Theken et al.)",
     "map": NSAID_MAP},
    {"drug": "Lornoxicam", "use": "Pain/inflammation drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "CPIC", "cpic": "CPIC: CYP2C9 & NSAIDs (Theken et al.)",
     "map": NSAID_MAP},
    {"drug": "Fosphenytoin", "use": "Epilepsy drug — IV prodrug of phenytoin (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "CPIC", "cpic": "CPIC: CYP2C9 & fosphenytoin/phenytoin (Caudle et al.)",
     "map": {
         "poor": ("caution", "CAUTION — fosphenytoin converts to phenytoin, which builds up; guideline: cut the maintenance dose by 25–50% with blood-level monitoring. NOTE: an HLA-B*15:02 lab test is also required before use (SJS risk) — see the HLA info card below."),
         "intermediate": ("caution", "CAUTION — consider a 25% dose reduction with monitoring."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "CYP2C9 not tested — no guidance possible.")}},
    {"drug": "Siponimod", "use": "Multiple-sclerosis drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "CPIC", "cpic": "CPIC: CYP2C9 & siponimod",
     "map": {
         "poor": ("avoid", "AVOID — CONTRAINDICATED in CYP2C9 poor metabolizers (*3/*3): drug levels run dangerously high."),
         "intermediate": ("caution", "CAUTION — use the lower 1 mg/day maintenance dose instead of the usual 2 mg."),
         "normal": ("ok", "Normal handling expected — standard 2 mg/day maintenance dose."),
         "unknown": ("info", "CYP2C9 not tested — no guidance possible.")}},
    {"drug": "Tropisetron", "use": "Anti-nausea drug (CYP2D6-affected)",
     "gene": "CYP2D6", "source": "CPIC", "cpic": "CPIC: CYP2D6 & ondansetron/tropisetron (Bell et al.)",
     "map": {
         "poor": ("avoid", "AVOID if possible — poor metabolizers get LESS anti-nausea effect; guideline prefers granisetron."),
         "intermediate": ("ok", "Standard dosing."),
         "normal": ("ok", "Normal response expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Oxycodone", "use": "Painkiller (partly CYP2D6-activated to oxymorphone)",
     "gene": "CYP2D6", "source": "CPIC", "cpic": "CPIC: CYP2D6 & opioids (Crews et al.)",
     "map": {
         "poor": ("avoid", "AVOID — poor activation means weak pain relief; choose a non-CYP2D6 painkiller."),
         "intermediate": ("caution", "CAUTION — may be less effective; monitor pain relief."),
         "normal": ("ok", "Normal activation expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Ivacaftor", "use": "Cystic-fibrosis drug — only works with specific CFTR variants",
     "gene": None, "source": "CPIC", "cpic": "CPIC: CFTR & ivacaftor",
     "info_only": True,
     "info": "Ivacaftor only helps cystic-fibrosis patients carrying specific CFTR gating variants (e.g. G551D). This needs full CFTR gene sequencing in a lab — a SNP chip (23andMe-style) CANNOT determine CFTR variant status. This card can never judge ivacaftor eligibility."},
    # ------------------------- DPWG additions -------------------------
    {"drug": "Venlafaxine", "use": "Antidepressant (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & venlafaxine",
     "map": {
         "poor": ("avoid", "AVOID if possible — DPWG: very high blood levels in poor metabolizers; choose an alternative antidepressant or use a much lower dose."),
         "intermediate": ("caution", "CAUTION — DPWG: consider a lower dose and monitor for side effects."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Haloperidol", "use": "Antipsychotic (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & haloperidol",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: use at most HALF the normal dose in poor metabolizers (higher side-effect risk)."),
         "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Zuclopenthixol", "use": "Antipsychotic (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & zuclopenthixol",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: use a reduced dose in poor metabolizers (higher side-effect risk)."),
         "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Metoprolol", "use": "Heart drug / blood pressure (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & metoprolol",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: much higher blood levels; use a lower dose and watch for very slow heartbeat or low blood pressure."),
         "intermediate": ("caution", "CAUTION — monitor heart rate and blood pressure; the dose may need lowering."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Propafenone", "use": "Heart-rhythm drug (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & propafenone",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: use a lower dose in poor metabolizers (higher blood levels)."),
         "intermediate": ("caution", "CAUTION — monitor for side effects; dose may need lowering."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Flecainide", "use": "Heart-rhythm drug (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & flecainide",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: use a lower dose in poor metabolizers, with ECG monitoring."),
         "intermediate": ("caution", "CAUTION — monitor for side effects; dose may need lowering."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Pimozide", "use": "Antipsychotic (CYP2D6-cleared)",
     "gene": "CYP2D6", "source": "DPWG", "cpic": "DPWG: CYP2D6 & pimozide",
     "map": {
         "poor": ("caution", "CAUTION — DPWG: use a lower dose in poor metabolizers (higher blood levels; QT heart-rhythm risk)."),
         "intermediate": ("caution", "CAUTION — consider a lower starting dose."),
         "normal": ("ok", "Normal handling expected — standard dosing."),
         "unknown": ("info", "CYP2D6 not tested — no guidance possible.")}},
    {"drug": "Piroxicam", "use": "Pain/inflammation drug (CYP2C9-cleared)",
     "gene": "CYP2C9", "source": "DPWG", "cpic": "DPWG: CYP2C9 & piroxicam",
     "map": NSAID_MAP},
    {"drug": "Tegafur", "use": "Chemotherapy, converts to 5-FU (needs DPD to clear)",
     "gene": "DPYD", "source": "DPWG", "cpic": "DPWG: DPYD & tegafur",
     "map": {
         "poor": ("avoid", "AVOID standard dosing — severe toxicity risk in DPD deficiency (DPWG)."),
         "intermediate": ("caution", "CAUTION — DPWG: reduce the starting dose with close monitoring."),
         "normal": ("ok", "Normal clearance expected — standard dosing."),
         "unknown": ("info", "DPYD not tested — no guidance possible.")}},
    {"drug": "Acenocoumarol", "use": "Blood thinner (dose tuned by CYP2C9 + VKORC1)",
     "source": "DPWG", "cpic": "DPWG: CYP2C9/VKORC1 & acenocoumarol",
     "combo": "coumarin"},
    {"drug": "Phenprocoumon", "use": "Blood thinner (dose tuned by CYP2C9 + VKORC1)",
     "source": "DPWG", "cpic": "DPWG: CYP2C9/VKORC1 & phenprocoumon",
     "combo": "coumarin"},
]


def warfarin_rule(pheno_cyp2c9, pheno_vkorc1):
    """Combine CYP2C9 + VKORC1 into a warfarin recommendation (simplified CPIC)."""
    k9, kV = pheno_cyp2c9, pheno_vkorc1
    if k9 == "unknown" or kV == "unknown":
        return ("info", "CYP2C9/VKORC1 not fully tested — use clinical warfarin dosing with INR monitoring.")
    if k9 == "poor" or kV == "high":
        return ("avoid", "HIGH SENSITIVITY — warfarin needs a much lower starting dose (often 25–50% less) with frequent INR checks. A pharmacist must supervise initiation.")
    if k9 == "intermediate" or kV == "sensitive":
        return ("caution", "INCREASED SENSITIVITY — consider a lower starting dose (e.g. 3–4 mg/day instead of 5) and close INR monitoring.")
    return ("ok", "Normal sensitivity expected — standard warfarin initiation (e.g. 5 mg/day) with routine INR monitoring.")


def coumarin_rule(drug, pheno_cyp2c9, pheno_vkorc1):
    """DPWG-style simplified guidance for acenocoumarol/phenprocoumon
    (mirrors the warfarin CYP2C9+VKORC1 logic)."""
    k9, kV = pheno_cyp2c9, pheno_vkorc1
    if k9 == "unknown" or kV == "unknown":
        return ("info", f"CYP2C9/VKORC1 not fully tested — {drug} needs INR-guided dosing by a clinician.")
    if k9 == "poor" or kV == "high":
        return ("avoid", f"HIGH SENSITIVITY — {drug} needs a much lower starting dose with frequent INR checks (DPWG recommends genotype-guided dosing). A pharmacist must supervise initiation.")
    if k9 == "intermediate" or kV == "sensitive":
        return ("caution", f"INCREASED SENSITIVITY — consider a lower starting dose of {drug} with close INR monitoring (DPWG).")
    return ("ok", f"Normal sensitivity expected — standard {drug} initiation with routine INR monitoring.")


SEVERITY_LABEL = {"ok": "Usual response", "caution": "Use caution",
                  "avoid": "Avoid / change", "info": "Not tested"}
SEVERITY_COLOR = {"ok": "green", "caution": "yellow", "avoid": "red", "info": "blue"}

# ---------------------------------------------------------------------------
# 3D structure info (AlphaFold DB). UniProt accessions are the canonical
# reviewed entries; residue numbers follow UniProt canonical sequence numbering
# (AlphaFold model numbering matches it).
# Residue effects (missense/nonsense) are standard PGx annotations:
#   CYP2C9 *2 (rs1799853) = R144C; *3 (rs1057910) = I359L
#   CYP2C19 *3 (rs4986893) = W212X (premature stop at residue 212)
#   TPMT *3C (rs1142345) = Y240C; *3B (rs1800460) = A154T
#   SLCO1B1 521T>C (rs4149056) = V174A
# Splice/non-coding variants change no amino acid — noted in the UI instead.
# ---------------------------------------------------------------------------
STRUCT_UNIPROT = {
    "CYP2D6": "P10635",
    "CYP2C19": "P33261",
    "CYP2C9": "P11712",
    "VKORC1": "Q9BQB6",
    "TPMT": "P51580",
    "DPYD": "Q12882",
    "SLCO1B1": "Q9Y6L6",
    "CYP2B6": "P20813",
    "CYP3A5": "P20815",
    "UGT1A1": "P22309",
    "NUDT15": "Q9NV35",
    "ABCG2": "Q9UNQ0",
}

# rsID -> (residue number, short label) for coding variants
STRUCT_RESIDUES = {
    "rs4986893": (212, "W212X — premature stop (CYP2C19*3)"),
    "rs1799853": (144, "R144C (CYP2C9*2)"),
    "rs1057910": (359, "I359L (CYP2C9*3)"),
    "rs1142345": (240, "Y240C (TPMT*3C)"),
    "rs1800460": (154, "A154T (TPMT*3B)"),
    "rs4149056": (174, "V174A (SLCO1B1 521C)"),
    "rs3745274": (172, "Q172H (CYP2B6*6)"),
    "rs2279343": (262, "K262R (CYP2B6*4)"),
    "rs4148323": (71, "G71R (UGT1A1*6)"),
    "rs116855232": (139, "R139C (NUDT15*3)"),
    "rs2231142": (141, "Q141K (ABCG2 421A)"),
}

STRUCT_NOTES = {
    "CYP2D6": "CYP2D6*4 (rs3892097) is a splice defect — it breaks the mRNA, so no single amino acid changes. Structure shown for reference.",
    "CYP2C19": "CYP2C19*2 (rs4244285) is a splice defect (no protein change). CYP2C19*17 sits in the promoter (non-coding). CYP2C19*3 creates a premature stop at residue 212 — highlighted red when found in your DNA.",
    "VKORC1": "rs9923231 sits in the gene promoter (non-coding) — it changes how much protein is made, not the protein's shape. Structure shown for reference.",
    "DPYD": "DPYD*2A (rs3918290) is a splice defect — the mRNA is mis-spliced, so no single residue changes. Structure shown for reference.",
    "CYP3A5": "CYP3A5*3 (rs776746) is a splice defect — no amino-acid change. The *1 (functional) vs *3 (broken) difference is at the mRNA level. Structure shown for reference.",
    "UGT1A1": "UGT1A1*28 is a promoter TA-repeat (non-coding) — read here via SNP proxy. UGT1A1*6 (G71R) changes residue 71 — highlighted red when found in your DNA.",
    "NUDT15": "NUDT15*3 (R139C) changes residue 139 — highlighted red when found in your DNA.",
    "ABCG2": "ABCG2 Q141K changes residue 141 — highlighted red when found in your DNA.",
    "CYP2B6": "CYP2B6*6 (Q172H) and *4 (K262R) change residues 172 and 262 — highlighted red when found in your DNA.",
}


def gene_structure(gene, genotypes):
    """Return 3D-viewer config for a gene card.

    highlights: [{pos, label, found}] — found=True means the user carries the
    variant (>=1 alt allele); red spheres. found=False = key position shown in
    gray for reference.
    """
    uniprot = STRUCT_UNIPROT.get(gene)
    if not uniprot:
        return None
    highlights = []
    for rsid, s in SNPS.items():
        if s["gene"] != gene or rsid not in STRUCT_RESIDUES:
            continue
        pos, label = STRUCT_RESIDUES[rsid]
        n = _alt_count(genotypes.get(rsid), s["ref"], s["alt"])
        highlights.append({"pos": pos, "label": label, "found": bool(n)})
    # found residues first
    highlights.sort(key=lambda h: (not h["found"], h["pos"]))
    return {
        "uniprot": uniprot,
        # Same-origin proxy (avoids CORS + version rot on alphafold.ebi.ac.uk)
        "cif": f"/pgx/struct/{uniprot}.cif",
        "af_url": f"https://alphafold.ebi.ac.uk/entry/{uniprot}",
        "highlights": highlights,
        "note": STRUCT_NOTES.get(gene),
    }
