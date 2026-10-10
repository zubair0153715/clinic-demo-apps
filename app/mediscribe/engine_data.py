"""MediScribe drug safety engine data — ported from the v1 JS engine (2026-10-05)."""

DRUGS = [
 {
  "id": "warfarin",
  "n": [
   "warfarin",
   "coumadin"
  ],
  "c": "Anticoagulant"
 },
 {
  "id": "aspirin",
  "n": [
   "aspirin",
   "disprin",
   "ecosprin",
   "acetylsalicylic acid"
  ],
  "c": "Antiplatelet"
 },
 {
  "id": "clopidogrel",
  "n": [
   "clopidogrel",
   "plavix",
   "clopilet"
  ],
  "c": "Antiplatelet"
 },
 {
  "id": "heparin",
  "n": [
   "heparin"
  ],
  "c": "Anticoagulant (injectable)"
 },
 {
  "id": "enoxaparin",
  "n": [
   "enoxaparin",
   "clexane"
  ],
  "c": "LMWH anticoagulant"
 },
 {
  "id": "apixaban",
  "n": [
   "apixaban",
   "eliquis"
  ],
  "c": "DOAC anticoagulant"
 },
 {
  "id": "rivaroxaban",
  "n": [
   "rivaroxaban",
   "xarelto"
  ],
  "c": "DOAC anticoagulant"
 },
 {
  "id": "atenolol",
  "n": [
   "atenolol",
   "tenormin"
  ],
  "c": "Beta-blocker"
 },
 {
  "id": "propranolol",
  "n": [
   "propranolol",
   "inderal"
  ],
  "c": "Beta-blocker (non-selective)"
 },
 {
  "id": "metoprolol",
  "n": [
   "metoprolol",
   "betaloc"
  ],
  "c": "Beta-blocker"
 },
 {
  "id": "amlodipine",
  "n": [
   "amlodipine",
   "norvasc"
  ],
  "c": "Calcium-channel blocker"
 },
 {
  "id": "verapamil",
  "n": [
   "verapamil",
   "isoptin"
  ],
  "c": "Calcium-channel blocker (non-DHP)"
 },
 {
  "id": "diltiazem",
  "n": [
   "diltiazem"
  ],
  "c": "Calcium-channel blocker (non-DHP)"
 },
 {
  "id": "lisinopril",
  "n": [
   "lisinopril"
  ],
  "c": "ACE inhibitor"
 },
 {
  "id": "enalapril",
  "n": [
   "enalapril",
   "enzar"
  ],
  "c": "ACE inhibitor"
 },
 {
  "id": "losartan",
  "n": [
   "losartan"
  ],
  "c": "ARB"
 },
 {
  "id": "valsartan",
  "n": [
   "valsartan"
  ],
  "c": "ARB"
 },
 {
  "id": "spironolactone",
  "n": [
   "spironolactone",
   "aldactone"
  ],
  "c": "K+-sparing diuretic"
 },
 {
  "id": "hctz",
  "n": [
   "hydrochlorothiazide",
   "hctz",
   "thiazide"
  ],
  "c": "Thiazide diuretic"
 },
 {
  "id": "furosemide",
  "n": [
   "furosemide",
   "lasix"
  ],
  "c": "Loop diuretic"
 },
 {
  "id": "digoxin",
  "n": [
   "digoxin",
   "lanoxin"
  ],
  "c": "Cardiac glycoside"
 },
 {
  "id": "amiodarone",
  "n": [
   "amiodarone",
   "cordarone"
  ],
  "c": "Antiarrhythmic"
 },
 {
  "id": "atorvastatin",
  "n": [
   "atorvastatin",
   "lipitor"
  ],
  "c": "Statin"
 },
 {
  "id": "simvastatin",
  "n": [
   "simvastatin"
  ],
  "c": "Statin"
 },
 {
  "id": "rosuvastatin",
  "n": [
   "rosuvastatin",
   "crestor"
  ],
  "c": "Statin"
 },
 {
  "id": "nitroglycerin",
  "n": [
   "nitroglycerin",
   "nitrate",
   "nitrates",
   "isosorbide"
  ],
  "c": "Nitrate"
 },
 {
  "id": "sildenafil",
  "n": [
   "sildenafil",
   "viagra"
  ],
  "c": "PDE5 inhibitor"
 },
 {
  "id": "metformin",
  "n": [
   "metformin",
   "glucophage"
  ],
  "c": "Antidiabetic (biguanide)"
 },
 {
  "id": "glibenclamide",
  "n": [
   "glibenclamide",
   "glyburide",
   "daonil"
  ],
  "c": "Sulfonylurea"
 },
 {
  "id": "insulin",
  "n": [
   "insulin"
  ],
  "c": "Antidiabetic"
 },
 {
  "id": "amoxicillin",
  "n": [
   "amoxicillin"
  ],
  "c": "Penicillin antibiotic"
 },
 {
  "id": "amoxclav",
  "n": [
   "amoxicillin-clavulanate",
   "amoxicillin clavulanate",
   "augmentin"
  ],
  "c": "Penicillin + beta-lactamase inhibitor"
 },
 {
  "id": "ceftriaxone",
  "n": [
   "ceftriaxone",
   "rocephin"
  ],
  "c": "Cephalosporin"
 },
 {
  "id": "cefixime",
  "n": [
   "cefixime"
  ],
  "c": "Cephalosporin"
 },
 {
  "id": "azithromycin",
  "n": [
   "azithromycin",
   "zithromax"
  ],
  "c": "Macrolide"
 },
 {
  "id": "clarithromycin",
  "n": [
   "clarithromycin"
  ],
  "c": "Macrolide"
 },
 {
  "id": "erythromycin",
  "n": [
   "erythromycin"
  ],
  "c": "Macrolide"
 },
 {
  "id": "ciprofloxacin",
  "n": [
   "ciprofloxacin",
   "cipro"
  ],
  "c": "Fluoroquinolone"
 },
 {
  "id": "levofloxacin",
  "n": [
   "levofloxacin"
  ],
  "c": "Fluoroquinolone"
 },
 {
  "id": "doxycycline",
  "n": [
   "doxycycline"
  ],
  "c": "Tetracycline"
 },
 {
  "id": "metronidazole",
  "n": [
   "metronidazole",
   "flagyl"
  ],
  "c": "Nitroimidazole antibiotic"
 },
 {
  "id": "vancomycin",
  "n": [
   "vancomycin"
  ],
  "c": "Glycopeptide antibiotic"
 },
 {
  "id": "gentamicin",
  "n": [
   "gentamicin"
  ],
  "c": "Aminoglycoside"
 },
 {
  "id": "cotrimoxazole",
  "n": [
   "trimethoprim-sulfamethoxazole",
   "trimethoprim sulfamethoxazole",
   "cotrimoxazole",
   "septran",
   "bactrim",
   "tmp-smx"
  ],
  "c": "Sulfonamide antibiotic"
 },
 {
  "id": "nitrofurantoin",
  "n": [
   "nitrofurantoin"
  ],
  "c": "UTI antibiotic"
 },
 {
  "id": "rifampin",
  "n": [
   "rifampin",
   "rifampicin"
  ],
  "c": "Anti-TB (enzyme inducer)"
 },
 {
  "id": "isoniazid",
  "n": [
   "isoniazid",
   "inh"
  ],
  "c": "Anti-TB"
 },
 {
  "id": "linezolid",
  "n": [
   "linezolid",
   "zyvox"
  ],
  "c": "Oxazolidinone antibiotic (MAOI activity)"
 },
 {
  "id": "fluconazole",
  "n": [
   "fluconazole"
  ],
  "c": "Azole antifungal"
 },
 {
  "id": "ibuprofen",
  "n": [
   "ibuprofen",
   "brufen"
  ],
  "c": "NSAID"
 },
 {
  "id": "diclofenac",
  "n": [
   "diclofenac",
   "voltarol",
   "voren"
  ],
  "c": "NSAID"
 },
 {
  "id": "naproxen",
  "n": [
   "naproxen"
  ],
  "c": "NSAID"
 },
 {
  "id": "celecoxib",
  "n": [
   "celecoxib"
  ],
  "c": "COX-2 inhibitor (NSAID)"
 },
 {
  "id": "paracetamol",
  "n": [
   "paracetamol",
   "acetaminophen",
   "panadol"
  ],
  "c": "Analgesic/antipyretic"
 },
 {
  "id": "tramadol",
  "n": [
   "tramadol",
   "tramal"
  ],
  "c": "Opioid analgesic"
 },
 {
  "id": "morphine",
  "n": [
   "morphine"
  ],
  "c": "Opioid analgesic"
 },
 {
  "id": "codeine",
  "n": [
   "codeine"
  ],
  "c": "Opioid (prodrug)"
 },
 {
  "id": "fluoxetine",
  "n": [
   "fluoxetine",
   "prozac"
  ],
  "c": "SSRI"
 },
 {
  "id": "sertraline",
  "n": [
   "sertraline",
   "zoloft"
  ],
  "c": "SSRI"
 },
 {
  "id": "escitalopram",
  "n": [
   "escitalopram"
  ],
  "c": "SSRI"
 },
 {
  "id": "amitriptyline",
  "n": [
   "amitriptyline"
  ],
  "c": "Tricyclic antidepressant"
 },
 {
  "id": "phenelzine",
  "n": [
   "phenelzine",
   "maoi",
   "mao inhibitor"
  ],
  "c": "MAOI antidepressant"
 },
 {
  "id": "lithium",
  "n": [
   "lithium"
  ],
  "c": "Mood stabilizer"
 },
 {
  "id": "carbamazepine",
  "n": [
   "carbamazepine",
   "tegral",
   "tegretol"
  ],
  "c": "Antiepileptic (enzyme inducer)"
 },
 {
  "id": "phenytoin",
  "n": [
   "phenytoin",
   "epanutin"
  ],
  "c": "Antiepileptic"
 },
 {
  "id": "valproate",
  "n": [
   "valproate",
   "valproic acid",
   "depakine",
   "divalproex"
  ],
  "c": "Antiepileptic"
 },
 {
  "id": "levetiracetam",
  "n": [
   "levetiracetam",
   "keppra"
  ],
  "c": "Antiepileptic"
 },
 {
  "id": "diazepam",
  "n": [
   "diazepam",
   "valium"
  ],
  "c": "Benzodiazepine"
 },
 {
  "id": "alprazolam",
  "n": [
   "alprazolam",
   "xanax"
  ],
  "c": "Benzodiazepine"
 },
 {
  "id": "haloperidol",
  "n": [
   "haloperidol"
  ],
  "c": "Antipsychotic"
 },
 {
  "id": "olanzapine",
  "n": [
   "olanzapine"
  ],
  "c": "Antipsychotic"
 },
 {
  "id": "omeprazole",
  "n": [
   "omeprazole",
   "risek"
  ],
  "c": "Proton-pump inhibitor"
 },
 {
  "id": "salbutamol",
  "n": [
   "salbutamol",
   "albuterol",
   "ventolin"
  ],
  "c": "SABA bronchodilator"
 },
 {
  "id": "prednisolone",
  "n": [
   "prednisolone",
   "prednisone"
  ],
  "c": "Corticosteroid"
 },
 {
  "id": "dexamethasone",
  "n": [
   "dexamethasone"
  ],
  "c": "Corticosteroid"
 },
 {
  "id": "levothyroxine",
  "n": [
   "levothyroxine",
   "thyroxine"
  ],
  "c": "Thyroid hormone"
 },
 {
  "id": "allopurinol",
  "n": [
   "allopurinol",
   "zyloric"
  ],
  "c": "Xanthine oxidase inhibitor"
 },
 {
  "id": "colchicine",
  "n": [
   "colchicine"
  ],
  "c": "Anti-gout"
 },
 {
  "id": "methotrexate",
  "n": [
   "methotrexate",
   "mtx"
  ],
  "c": "Immunosuppressant/chemo"
 },
 {
  "id": "azathioprine",
  "n": [
   "azathioprine",
   "imuran"
  ],
  "c": "Immunosuppressant"
 },
 {
  "id": "theophylline",
  "n": [
   "theophylline"
  ],
  "c": "Methylxanthine bronchodilator"
 },
 {
  "id": "potassium",
  "n": [
   "potassium",
   "potassium chloride",
   "kcl"
  ],
  "c": "Potassium supplement"
 },
 {
  "id": "ocp",
  "n": [
   "oral contraceptive",
   "contraceptive pill",
   "birth control pill",
   "estrogen pill"
  ],
  "c": "Combined oral contraceptive"
 }
]

GROUPS = {
 "acei": [
  "lisinopril",
  "enalapril"
 ],
 "arb": [
  "losartan",
  "valsartan"
 ],
 "nsaid": [
  "ibuprofen",
  "diclofenac",
  "naproxen",
  "celecoxib"
 ],
 "ssri": [
  "fluoxetine",
  "sertraline",
  "escitalopram"
 ],
 "macrolide": [
  "azithromycin",
  "clarithromycin",
  "erythromycin"
 ],
 "quinolone": [
  "ciprofloxacin",
  "levofloxacin"
 ],
 "statin": [
  "atorvastatin",
  "simvastatin",
  "rosuvastatin"
 ],
 "benzo": [
  "diazepam",
  "alprazolam"
 ],
 "opioid": [
  "tramadol",
  "morphine",
  "codeine"
 ],
 "penicillin": [
  "amoxicillin",
  "amoxclav"
 ],
 "ceph": [
  "ceftriaxone",
  "cefixime"
 ],
 "sulfa": [
  "cotrimoxazole"
 ],
 "bb": [
  "atenolol",
  "propranolol",
  "metoprolol"
 ],
 "nondhp": [
  "verapamil",
  "diltiazem"
 ],
 "steroid": [
  "prednisolone",
  "dexamethasone"
 ],
 "anticoag": [
  "warfarin",
  "heparin",
  "enoxaparin",
  "apixaban",
  "rivaroxaban"
 ]
}

INTERACTIONS = [
 [
  "warfarin",
  "nsaid",
  "red",
  "Bleeding risk greatly increased — avoid NSAIDs; paracetamol is the safer analgesic."
 ],
 [
  "warfarin",
  "aspirin",
  "red",
  "Dual anticoagulant effect — major bleeding risk. Only combined under specialist supervision."
 ],
 [
  "warfarin",
  "metronidazole",
  "red",
  "INR increased — bleeding risk. Monitor INR closely."
 ],
 [
  "warfarin",
  "fluconazole",
  "red",
  "INR increased — bleeding risk. Monitor INR closely."
 ],
 [
  "warfarin",
  "macrolide",
  "amber",
  "INR may rise — watch for bleeding, check INR."
 ],
 [
  "warfarin",
  "cotrimoxazole",
  "red",
  "INR increased — bleeding risk."
 ],
 [
  "warfarin",
  "amiodarone",
  "red",
  "INR increased — reduce warfarin dose, monitor INR."
 ],
 [
  "warfarin",
  "rifampin",
  "red",
  "Warfarin effect reduced — clotting risk. Monitor INR, dose usually needs increase."
 ],
 [
  "acei",
  "spironolactone",
  "red",
  "Hyperkalemia (high potassium) risk — monitor K+ and kidney function."
 ],
 [
  "acei",
  "potassium",
  "red",
  "Hyperkalemia risk — avoid potassium supplements."
 ],
 [
  "arb",
  "spironolactone",
  "red",
  "Hyperkalemia risk — monitor K+."
 ],
 [
  "acei",
  "nsaid",
  "amber",
  "Kidney injury risk + blood-pressure control reduced."
 ],
 [
  "arb",
  "nsaid",
  "amber",
  "Kidney injury risk + blood-pressure control reduced."
 ],
 [
  "ssri",
  "phenelzine",
  "red",
  "Serotonin syndrome — CONTRAINDICATED. Needs 14-day washout between them."
 ],
 [
  "ssri",
  "tramadol",
  "red",
  "Serotonin syndrome + seizure risk — avoid combination."
 ],
 [
  "ssri",
  "linezolid",
  "red",
  "Serotonin syndrome (linezolid has MAOI activity) — avoid."
 ],
 [
  "tramadol",
  "linezolid",
  "red",
  "Serotonin syndrome risk — avoid."
 ],
 [
  "gentamicin",
  "furosemide",
  "red",
  "Ototoxicity (hearing damage) risk increased."
 ],
 [
  "gentamicin",
  "vancomycin",
  "red",
  "Nephrotoxicity increased — monitor kidney function and drug levels."
 ],
 [
  "statin",
  "clarithromycin",
  "red",
  "Rhabdomyolysis (muscle breakdown) risk — hold statin or switch antibiotic."
 ],
 [
  "statin",
  "erythromycin",
  "red",
  "Rhabdomyolysis risk — hold statin or switch antibiotic."
 ],
 [
  "statin",
  "fluconazole",
  "amber",
  "Statin levels rise — muscle-pain risk; monitor, consider dose reduction."
 ],
 [
  "digoxin",
  "verapamil",
  "red",
  "Digoxin toxicity — reduce digoxin dose, monitor levels."
 ],
 [
  "digoxin",
  "diltiazem",
  "red",
  "Digoxin levels rise — monitor for toxicity."
 ],
 [
  "digoxin",
  "amiodarone",
  "red",
  "Digoxin levels rise — halve digoxin dose, monitor."
 ],
 [
  "digoxin",
  "clarithromycin",
  "red",
  "Digoxin levels rise — monitor for toxicity."
 ],
 [
  "digoxin",
  "furosemide",
  "amber",
  "Low potassium raises digoxin toxicity risk — monitor K+."
 ],
 [
  "lithium",
  "nsaid",
  "red",
  "Lithium toxicity — monitor lithium levels closely."
 ],
 [
  "lithium",
  "hctz",
  "red",
  "Lithium levels rise — toxicity risk; monitor levels."
 ],
 [
  "lithium",
  "acei",
  "amber",
  "Lithium levels may rise — monitor."
 ],
 [
  "methotrexate",
  "nsaid",
  "red",
  "Methotrexate toxicity (kidney + bone marrow) — avoid NSAIDs."
 ],
 [
  "methotrexate",
  "cotrimoxazole",
  "red",
  "Severe bone-marrow suppression — avoid combination."
 ],
 [
  "allopurinol",
  "azathioprine",
  "red",
  "Severe myelosuppression — cut azathioprine to ~25% dose under specialist care."
 ],
 [
  "carbamazepine",
  "clarithromycin",
  "red",
  "Carbamazepine toxicity — monitor levels, consider alternative antibiotic."
 ],
 [
  "carbamazepine",
  "erythromycin",
  "red",
  "Carbamazepine toxicity — monitor levels."
 ],
 [
  "carbamazepine",
  "fluconazole",
  "amber",
  "Carbamazepine levels rise — monitor."
 ],
 [
  "carbamazepine",
  "ocp",
  "amber",
  "Contraceptive failure (enzyme induction) — use non-hormonal method."
 ],
 [
  "rifampin",
  "ocp",
  "red",
  "Contraceptive failure — use alternative contraception."
 ],
 [
  "opioid",
  "benzo",
  "red",
  "Respiratory depression — FDA black-box warning. Avoid combined use."
 ],
 [
  "clopidogrel",
  "omeprazole",
  "amber",
  "Clopidogrel activation reduced — pantoprazole preferred if PPI needed."
 ],
 [
  "aspirin",
  "ibuprofen",
  "amber",
  "Ibuprofen blocks aspirin's heart protection — take aspirin ≥30 min before ibuprofen."
 ],
 [
  "glibenclamide",
  "fluconazole",
  "red",
  "Severe hypoglycemia risk — monitor blood sugar closely."
 ],
 [
  "insulin",
  "propranolol",
  "amber",
  "Masks warning signs of low blood sugar (tremor, palpitations)."
 ],
 [
  "theophylline",
  "ciprofloxacin",
  "red",
  "Theophylline toxicity — reduce theophylline dose, monitor levels."
 ],
 [
  "theophylline",
  "clarithromycin",
  "red",
  "Theophylline toxicity — monitor levels."
 ],
 [
  "colchicine",
  "clarithromycin",
  "red",
  "Colchicine toxicity (fatal cases reported) — avoid; dose-adjust only under specialist care."
 ],
 [
  "sildenafil",
  "nitroglycerin",
  "red",
  "Severe hypotension — ABSOLUTE contraindication. Never combine."
 ],
 [
  "quinolone",
  "steroid",
  "amber",
  "Tendon-rupture risk increased (especially age >60)."
 ],
 [
  "fluconazole",
  "phenytoin",
  "amber",
  "Phenytoin toxicity — monitor levels."
 ],
 [
  "levothyroxine",
  "omeprazole",
  "amber",
  "Thyroxine absorption reduced — take thyroxine alone on empty stomach."
 ],
 [
  "spironolactone",
  "cotrimoxazole",
  "red",
  "Hyperkalemia — trimethoprim blocks potassium excretion."
 ],
 [
  "ssri",
  "nsaid",
  "amber",
  "Bleeding risk increased — watch for GI bleeding."
 ],
 [
  "nondhp",
  "propranolol",
  "red",
  "Severe bradycardia / heart block — avoid combination."
 ],
 [
  "isoniazid",
  "rifampin",
  "amber",
  "Liver-injury risk increased — monitor liver function tests."
 ],
 [
  "phenytoin",
  "valproate",
  "amber",
  "Protein-binding displacement — monitor free phenytoin levels."
 ],
 [
  "carbamazepine",
  "valproate",
  "amber",
  "Levels of both affected — monitor drug levels."
 ]
]

CONTRA = [
 [
  "acei",
  "pregnancy",
  "red",
  "Teratogenic (fetal kidney damage) — STOP immediately, switch therapy."
 ],
 [
  "arb",
  "pregnancy",
  "red",
  "Teratogenic — STOP immediately."
 ],
 [
  "statin",
  "pregnancy",
  "red",
  "Contraindicated in pregnancy — stop."
 ],
 [
  "warfarin",
  "pregnancy",
  "red",
  "Teratogenic — switch to heparin/enoxaparin under specialist care."
 ],
 [
  "doxycycline",
  "pregnancy",
  "red",
  "Affects fetal teeth and bones — avoid."
 ],
 [
  "doxycycline",
  "child",
  "red",
  "Avoid under 8 years — permanent teeth staining."
 ],
 [
  "valproate",
  "pregnancy",
  "red",
  "Neural-tube defects — avoid in pregnancy."
 ],
 [
  "valproate",
  "liver",
  "red",
  "Hepatotoxic — avoid in liver disease."
 ],
 [
  "methotrexate",
  "pregnancy",
  "red",
  "Abortifacient/teratogenic — absolute contraindication."
 ],
 [
  "methotrexate",
  "liver",
  "red",
  "Hepatotoxic — avoid in liver disease."
 ],
 [
  "nsaid",
  "ulcer",
  "red",
  "GI-bleeding risk — avoid NSAIDs; consider paracetamol."
 ],
 [
  "nsaid",
  "ckd",
  "red",
  "Worsens kidney function — avoid."
 ],
 [
  "nsaid",
  "pregnancy",
  "amber",
  "Avoid in 3rd trimester (ductus arteriosus risk)."
 ],
 [
  "nsaid",
  "hf",
  "amber",
  "Fluid retention worsens heart failure."
 ],
 [
  "propranolol",
  "asthma",
  "red",
  "Bronchospasm risk (non-selective) — use cardioselective beta-blocker if essential."
 ],
 [
  "metformin",
  "ckd",
  "red",
  "Lactic-acidosis risk — avoid if eGFR <30."
 ],
 [
  "gentamicin",
  "myasthenia",
  "red",
  "Worsens muscle weakness — avoid."
 ],
 [
  "gentamicin",
  "ckd",
  "amber",
  "Nephrotoxic — dose adjustment and monitoring needed."
 ],
 [
  "ciprofloxacin",
  "myasthenia",
  "red",
  "Worsens myasthenia — FDA warning; avoid."
 ],
 [
  "ciprofloxacin",
  "child",
  "amber",
  "Reserve use in children (joint/cartilage effects)."
 ],
 [
  "codeine",
  "child",
  "red",
  "Contraindicated under 12 — serious breathing risk."
 ],
 [
  "aspirin",
  "child",
  "amber",
  "Reye-syndrome risk in viral illness — avoid in children with fever."
 ],
 [
  "hctz",
  "gout",
  "amber",
  "Raises uric acid — may trigger gout flare."
 ],
 [
  "furosemide",
  "gout",
  "amber",
  "Raises uric acid — may trigger gout flare."
 ],
 [
  "tramadol",
  "epilepsy",
  "amber",
  "Lowers seizure threshold — use with caution."
 ],
 [
  "spironolactone",
  "ckd",
  "red",
  "Hyperkalemia risk in kidney disease."
 ],
 [
  "potassium",
  "ckd",
  "red",
  "Hyperkalemia risk — avoid supplements."
 ],
 [
  "nitrofurantoin",
  "ckd",
  "amber",
  "Ineffective if CrCl <60 + neuropathy risk."
 ],
 [
  "lithium",
  "ckd",
  "amber",
  "Accumulates — monitor levels, dose-adjust."
 ],
 [
  "lithium",
  "pregnancy",
  "amber",
  "Heart-defect risk (1st trimester) — specialist decision only."
 ],
 [
  "glibenclamide",
  "liver",
  "amber",
  "Hypoglycemia risk in liver disease."
 ],
 [
  "glibenclamide",
  "elderly",
  "amber",
  "Hypoglycemia risk in elderly — safer alternatives preferred."
 ],
 [
  "paracetamol",
  "liver",
  "amber",
  "Keep ≤2–3 g/day in liver disease."
 ],
 [
  "statin",
  "liver",
  "red",
  "Contraindicated in active liver disease."
 ],
 [
  "carbamazepine",
  "liver",
  "amber",
  "Monitor liver function tests."
 ],
 [
  "rifampin",
  "liver",
  "amber",
  "Hepatotoxic — monitor LFTs."
 ],
 [
  "isoniazid",
  "liver",
  "amber",
  "Hepatotoxic — monitor LFTs."
 ],
 [
  "allopurinol",
  "ckd",
  "amber",
  "Reduce dose in kidney disease."
 ],
 [
  "colchicine",
  "ckd",
  "amber",
  "Reduce dose in kidney disease."
 ],
 [
  "colchicine",
  "liver",
  "amber",
  "Reduce dose in liver disease."
 ],
 [
  "digoxin",
  "ckd",
  "amber",
  "Accumulates — monitor levels and kidney function."
 ],
 [
  "enoxaparin",
  "pregnancy",
  "info",
  "Preferred anticoagulant in pregnancy (does not cross placenta)."
 ],
 [
  "heparin",
  "pregnancy",
  "info",
  "Preferred anticoagulant in pregnancy."
 ],
 [
  "insulin",
  "pregnancy",
  "info",
  "Preferred option for diabetes in pregnancy."
 ]
]

ALLERGY_RULES = [
 [
  "penicillin",
  "penicillin",
  "red",
  "Penicillin allergy — AVOID all penicillins (anaphylaxis risk)."
 ],
 [
  "penicillin",
  "ceph",
  "amber",
  "Penicillin allergy — cephalosporin cross-reactivity ~2%; use with caution."
 ],
 [
  "sulfa",
  "sulfa",
  "red",
  "Sulfa allergy — avoid sulfonamides (incl. cotrimoxazole)."
 ],
 [
  "nsaid",
  "nsaid",
  "red",
  "NSAID allergy — avoid all NSAIDs."
 ],
 [
  "nsaid",
  "aspirin",
  "red",
  "NSAID allergy — avoid aspirin too."
 ]
]

CONDITIONS = [
 [
  "pregnancy",
  "Pregnancy"
 ],
 [
  "breastfeeding",
  "Breastfeeding"
 ],
 [
  "diabetes",
  "Diabetes"
 ],
 [
  "hypertension",
  "Hypertension"
 ],
 [
  "asthma",
  "Asthma"
 ],
 [
  "ckd",
  "Chronic kidney disease"
 ],
 [
  "liver",
  "Liver disease"
 ],
 [
  "ulcer",
  "Peptic ulcer"
 ],
 [
  "gout",
  "Gout"
 ],
 [
  "hf",
  "Heart failure"
 ],
 [
  "epilepsy",
  "Epilepsy"
 ],
 [
  "myasthenia",
  "Myasthenia gravis"
 ],
 [
  "child",
  "Child < 12 yrs"
 ],
 [
  "elderly",
  "Elderly > 65 yrs"
 ]
]

COND_LABEL = dict(CONDITIONS)

COUNSEL = {
 "metronidazole": "No alcohol during treatment and for 48h after (disulfiram-like reaction).",
 "doxycycline": "Take with a full glass of water; separate dairy/antacids/iron by 2–3h; sun sensitivity — use sunscreen.",
 "levothyroxine": "Take on an empty stomach, 30–60 min before breakfast.",
 "alendronate": "",
 "sildenafil": "Never combine with nitrate heart medicines.",
 "warfarin": "Keep vitamin-K foods (leafy greens) consistent; report any bleeding/bruising."
}
