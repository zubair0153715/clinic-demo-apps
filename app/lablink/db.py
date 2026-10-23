"""LabLink (/lablink) — SQLite persistence.

University lab-connect app for SMBBMU Larkana (Pharm-D): teacher-student
announcements, experiments library, lab inventory, library catalog,
weekly timetable + in-app notifications.

DB path via LABLINK_DB_PATH env var (default: <app>/data/lablink.db).
Container SQLite can be wiped on deploy — demo seed re-runs on empty DB.
"""
import json
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "lablink.db")
    return os.environ.get("LABLINK_DB_PATH", default)


def now() -> int:
    return int(time.time())


def get_conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = db_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fresh = not os.path.exists(path) or os.path.getsize(path) == 0
            _conn = sqlite3.connect(path, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            init_schema(_conn)
            if fresh:
                seed_demo(_conn)
        return _conn


def q(sql, params=()):
    with _lock:
        c = get_conn()
        cur = c.execute(sql, params)
        c.commit()
        return cur


def qall(sql, params=()):
    with _lock:
        return get_conn().execute(sql, params).fetchall()


def qone(sql, params=()):
    rows = qall(sql, params)
    return rows[0] if rows else None


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT DEFAULT '',
    role TEXT DEFAULT 'student',      -- 'student' | 'teacher' | 'admin'
    batch TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    is_active INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    title TEXT DEFAULT '',
    body TEXT NOT NULL,
    target_batch TEXT DEFAULT '',     -- '' = all batches
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    announcement_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    objective TEXT DEFAULT '',
    chemicals TEXT DEFAULT '[]',      -- JSON [{name, qty, unit, grade}]
    apparatus TEXT DEFAULT '',        -- one per line
    procedure TEXT DEFAULT '',        -- one step per line
    precautions TEXT DEFAULT '',
    observation TEXT DEFAULT '',
    diagram TEXT DEFAULT '',          -- key into DIAGRAMS in pages.py
    created_by INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS inv_chemicals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    qty REAL DEFAULT 0,
    unit TEXT DEFAULT 'g',
    lab TEXT DEFAULT '',
    threshold REAL DEFAULT 0        -- low-stock when qty < threshold
);
CREATE TABLE IF NOT EXISTS inv_instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    lab TEXT DEFAULT '',
    status TEXT DEFAULT 'working'   -- 'working' | 'maintenance'
);
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    edition TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    total_copies INTEGER DEFAULT 1,
    available_copies INTEGER DEFAULT 1,
    shelf TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS book_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,              -- 'Monday' ... 'Saturday'
    start_time TEXT DEFAULT '',     -- '10:00 AM'
    end_time TEXT DEFAULT '',
    batch TEXT NOT NULL,
    subject TEXT DEFAULT '',
    lab_room TEXT DEFAULT '',
    teacher TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    dedupe TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    is_read INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);
"""


def init_schema(conn):
    conn.executescript(SCHEMA)
    conn.commit()


BATCH_A = "Pharm-D 3rd Year Batch A"
BATCH_B = "Pharm-D 3rd Year Batch B"
BATCH_2A = "Pharm-D 2nd Year Batch A"


def _pw(password: str) -> str:
    # local import to avoid a cycle (auth imports db)
    from app.lablink.auth import hash_password
    return hash_password(password)


def seed_demo(conn):
    t = now()
    users = [
        ("Demo Student", "student@demo.pk", "student", BATCH_A, "0300-0000001"),
        ("Demo Teacher", "teacher@demo.pk", "teacher", "", "0300-0000002"),
        ("Demo Admin", "admin@demo.pk", "admin", "", "0300-0000003"),
        ("Ayesha Khan", "ayesha@demo.pk", "student", BATCH_A, ""),
        ("Bilal Ahmed", "bilal@demo.pk", "student", BATCH_A, ""),
        ("Fatima Zahra", "fatima@demo.pk", "student", BATCH_B, ""),
        ("Dr. Sana Baloch", "sana@demo.pk", "teacher", "", ""),
        ("Dr. Imran Sheikh", "imran@demo.pk", "teacher", "", ""),
    ]
    uid = {}
    for name, email, role, batch, phone in users:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash, role, batch, phone, created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (name, email, _pw("demo1234"), role, batch, phone, t))
        uid[email] = cur.lastrowid

    anns = [
        (uid["teacher@demo.pk"], "Pharmaceutics practical this week",
         "Batch A: Simple Syrup IP ki preparation hogi. Lab coat aur practical notebook lazmi layein.",
         BATCH_A),
        (uid["sana@demo.pk"], "Pharmacognosy viva schedule",
         "Clove aur cinnamon ke microscopy slides revise kar lein — viva Friday ko hai.",
         ""),
        (uid["admin@demo.pk"], "Library new arrivals",
         "Katzung Basic & Clinical Pharmacology (16th ed.) ki 6 nayi copies library me aa gayi hain.",
         ""),
    ]
    for author, title, body, target in anns:
        conn.execute(
            "INSERT INTO announcements (author_id, title, body, target_batch, created_at)"
            " VALUES (?,?,?,?,?)", (author, title, body, target, t))

    for exp in EXPERIMENTS:
        conn.execute(
            "INSERT INTO experiments (title, subject, objective, chemicals, apparatus,"
            " procedure, precautions, observation, diagram, created_by, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (exp["title"], exp["subject"], exp["objective"],
             json.dumps(exp["chemicals"]), "\n".join(exp["apparatus"]),
             "\n".join(exp["procedure"]), exp["precautions"], exp["observation"],
             exp.get("diagram", ""), uid["teacher@demo.pk"], t))

    for name, qty, unit, lab, thr in CHEMICALS:
        conn.execute(
            "INSERT INTO inv_chemicals (name, qty, unit, lab, threshold) VALUES (?,?,?,?,?)",
            (name, qty, unit, lab, thr))
    for name, lab, status in INSTRUMENTS:
        conn.execute(
            "INSERT INTO inv_instruments (name, lab, status) VALUES (?,?,?)",
            (name, lab, status))
    for title, author, ed, subj, total, avail, shelf in BOOKS:
        conn.execute(
            "INSERT INTO books (title, author, edition, subject, total_copies,"
            " available_copies, shelf) VALUES (?,?,?,?,?,?,?)",
            (title, author, ed, subj, total, avail, shelf))
    for day, st, en, batch, subj, room, teacher in TIMETABLE:
        conn.execute(
            "INSERT INTO timetable (day, start_time, end_time, batch, subject, lab_room, teacher)"
            " VALUES (?,?,?,?,?,?,?)", (day, st, en, batch, subj, room, teacher))
    conn.commit()


# ---------------------------------------------------------------- seed data

EXPERIMENTS = [
    {
        "title": "Preparation of Simple Syrup IP",
        "subject": "Pharmaceutics",
        "objective": "To prepare and submit 100 mL of Simple Syrup IP (66.7% w/w sucrose) "
                    "used as a sweetening vehicle for liquid oral preparations.",
        "chemicals": [
            {"name": "Sucrose (refined sugar)", "qty": "66.7", "unit": "g", "grade": "IP"},
            {"name": "Purified water", "qty": "q.s. to 100", "unit": "mL", "grade": "IP"},
        ],
        "apparatus": ["Analytical balance", "Beaker (250 mL)", "Measuring cylinder (100 mL)",
                      "Glass rod", "Water bath", "Funnel", "Amber glass bottle (100 mL)"],
        "procedure": [
            "Weigh accurately 66.7 g of sucrose and transfer to a clean dry beaker.",
            "Add about 40–50 mL of purified water and stir.",
            "Heat gently on a water bath (not above 60 °C) with continuous stirring until the sucrose dissolves completely. Do not boil.",
            "Cool the solution to room temperature.",
            "Transfer to a 100 mL measuring cylinder and add purified water to make the final volume 100 mL.",
            "Mix well, filter if any particle is visible, and transfer to an amber glass bottle.",
            "Label: name, category (sweetening vehicle), date of preparation, batch number, storage (cool place).",
        ],
        "precautions": "Do not heat above 60 °C — sucrose hydrolyses and caramelises, giving a yellow colour. "
                       "Avoid boiling. Use purified water only. Store in a cool place in a well-closed amber bottle.",
        "observation": "A clear, colourless, viscous syrupy liquid is obtained. "
                       "Submit 100 mL in an amber bottle with a proper label.",
        "diagram": "beaker",
    },
    {
        "title": "Preparation of Calamine Lotion IP",
        "subject": "Pharmaceutics",
        "objective": "To prepare and submit 100 mL of Calamine Lotion IP, a shake lotion used as a "
                    "soothing protectant for mild skin irritation and sunburn.",
        "chemicals": [
            {"name": "Calamine", "qty": "15", "unit": "g", "grade": "IP"},
            {"name": "Zinc oxide", "qty": "5", "unit": "g", "grade": "IP"},
            {"name": "Bentonite", "qty": "3", "unit": "g", "grade": "IP"},
            {"name": "Sodium citrate", "qty": "0.5", "unit": "g", "grade": "IP"},
            {"name": "Liquefied phenol", "qty": "0.5", "unit": "mL", "grade": "IP"},
            {"name": "Glycerin", "qty": "5", "unit": "mL", "grade": "IP"},
            {"name": "Rose water", "qty": "q.s. to 100", "unit": "mL", "grade": "IP"},
        ],
        "apparatus": ["Analytical balance", "Mortar and pestle", "Measuring cylinder (100 mL)",
                      "Beaker", "Glass rod", "Bottle (100 mL)"],
        "procedure": [
            "Weigh calamine, zinc oxide and bentonite; triturate together in a mortar to a fine uniform powder.",
            "Dissolve sodium citrate in about 60 mL of rose water in a beaker.",
            "Add the citrate solution gradually to the powder in the mortar, triturating to a smooth cream.",
            "Add liquefied phenol and glycerin; mix well.",
            "Transfer to a measuring cylinder and make up the volume to 100 mL with rose water.",
            "Shake well and transfer to a bottle. Label with 'SHAKE WELL BEFORE USE' and 'For external use only'.",
        ],
        "precautions": "Liquefied phenol is corrosive — handle with care and avoid skin contact. "
                       "The lotion separates on standing (suspending system), so the shake label is compulsory. "
                       "External use only.",
        "observation": "A pink-coloured lotion of uniform consistency is obtained, which re-disperses on shaking.",
        "diagram": "bottle",
    },
    {
        "title": "Synthesis of Aspirin (Acetylsalicylic Acid)",
        "subject": "Pharmaceutical Chemistry",
        "objective": "To synthesise aspirin by acetylation of salicylic acid with acetic anhydride "
                    "and to verify the product by melting point and ferric chloride test.",
        "chemicals": [
            {"name": "Salicylic acid", "qty": "2", "unit": "g", "grade": "LR"},
            {"name": "Acetic anhydride", "qty": "5", "unit": "mL", "grade": "LR"},
            {"name": "Concentrated sulphuric acid", "qty": "2–3", "unit": "drops", "grade": "AR"},
            {"name": "Distilled water (ice-cold)", "qty": "50", "unit": "mL", "grade": "—"},
            {"name": "Ethanol (for recrystallisation)", "qty": "10", "unit": "mL", "grade": "LR"},
            {"name": "Ferric chloride solution (1%)", "qty": "2", "unit": "mL", "grade": "LR"},
        ],
        "apparatus": ["Conical flask (100 mL)", "Water bath", "Thermometer", "Buchner funnel and flask",
                      "Filter paper", "Glass rod", "Melting point apparatus", "Test tubes"],
        "procedure": [
            "Place 2 g of salicylic acid in a dry conical flask and add 5 mL of acetic anhydride.",
            "Add 2–3 drops of concentrated sulphuric acid as catalyst and swirl to mix.",
            "Warm the flask on a water bath at 50–60 °C for about 15 minutes, stirring occasionally, until the solid dissolves.",
            "Remove from heat and add about 2 mL of water dropwise (this decomposes excess anhydride — the mixture warms up).",
            "Cool the flask, then pour the contents into about 50 mL of ice-cold water with stirring. Crystals of aspirin separate.",
            "Filter the crystals under suction (Buchner funnel), wash with a little cold water and dry.",
            "Recrystallise a small portion from hot water or aqueous ethanol for purity.",
            "Determine the melting point (pure aspirin: 135 °C) and record the yield.",
            "Purity check: aqueous solution of the product gives NO violet colour with ferric chloride (free salicylic acid gives a violet colour).",
        ],
        "precautions": "Acetic anhydride is lachrymatory and corrosive — work in a fume cupboard and avoid inhaling vapours. "
                       "Concentrated H2SO4 is highly corrosive; add dropwise only. All glassware must be dry at the start "
                       "(water hydrolyses the anhydride). Wear gloves and goggles.",
        "observation": "White needle-like crystals of aspirin are obtained (typical student yield 1.8–2.2 g). "
                       "Melting point ≈ 135 °C; no violet colour with FeCl3 confirms absence of unreacted salicylic acid.",
        "diagram": "flask",
    },
    {
        "title": "Preparation and Evaluation of Paracetamol Tablets (500 mg)",
        "subject": "Pharmaceutics",
        "objective": "To prepare paracetamol tablets by wet granulation (lab-scale batch of 10 tablets) "
                    "and evaluate them for hardness, friability, weight variation and disintegration.",
        "chemicals": [
            {"name": "Paracetamol", "qty": "500", "unit": "mg per tablet", "grade": "IP"},
            {"name": "Lactose (diluent)", "qty": "40", "unit": "mg per tablet", "grade": "IP"},
            {"name": "Starch (binder + disintegrant)", "qty": "30", "unit": "mg per tablet", "grade": "IP"},
            {"name": "Starch paste 10% (binder)", "qty": "q.s.", "unit": "—", "grade": "—"},
            {"name": "Talc (glidant)", "qty": "10", "unit": "mg per tablet", "grade": "IP"},
            {"name": "Magnesium stearate (lubricant)", "qty": "5", "unit": "mg per tablet", "grade": "IP"},
        ],
        "apparatus": ["Mortar and pestle", "Sieve no. 16 and no. 22", "Hot air oven", "Single-punch tablet machine",
                      "Monsanto hardness tester", "Roche friabilator", "Disintegration test apparatus",
                      "Analytical balance"],
        "procedure": [
            "Weigh all ingredients for a batch of 10 tablets (paracetamol 5 g total).",
            "Mix paracetamol, lactose and half the starch uniformly in a mortar (geometric dilution).",
            "Add 10% starch paste a little at a time and knead to a damp coherent mass (wet granulation).",
            "Pass the mass through sieve no. 16 to form granules; dry at 50–60 °C in a hot air oven.",
            "Pass dried granules through sieve no. 22; add remaining starch, talc and magnesium stearate; mix gently.",
            "Compress on a single-punch tablet machine to the target tablet weight (585 mg per tablet).",
            "Evaluation — Weight variation: weigh 20 tablets (or batch), each within ±5% of average.",
            "Evaluation — Hardness: Monsanto tester; acceptable range roughly 4–6 kg/cm² for this teaching batch.",
            "Evaluation — Friability: friabilator at 25 rpm for 4 minutes; weight loss should be less than 1%.",
            "Evaluation — Disintegration: in water at 37 ± 2 °C; uncoated tablets should disintegrate within 15 minutes (IP limit).",
        ],
        "precautions": "Over-wetting the mass gives hard granules and slow disintegration; under-wetting gives soft tablets. "
                       "Do not over-mix after adding magnesium stearate (it coats granules and slows dissolution). "
                       "Keep hands clear of the punch during compression.",
        "observation": "White, round tablets are obtained. Record hardness, friability % loss and disintegration time "
                       "in the observation table and compare with IP limits.",
        "diagram": "tablet",
    },
    {
        "title": "Extraction of Caffeine from Tea Leaves",
        "subject": "Pharmaceutical Chemistry",
        "objective": "To extract crude caffeine from tea leaves by aqueous extraction followed by "
                    "liquid–liquid extraction with dichloromethane, and confirm by melting point (236 °C).",
        "chemicals": [
            {"name": "Tea leaves (or tea dust)", "qty": "20", "unit": "g", "grade": "—"},
            {"name": "Distilled water", "qty": "150", "unit": "mL", "grade": "—"},
            {"name": "Sodium carbonate (anhydrous)", "qty": "10", "unit": "g", "grade": "LR"},
            {"name": "Dichloromethane", "qty": "3 × 20", "unit": "mL", "grade": "LR"},
            {"name": "Anhydrous sodium sulphate", "qty": "2", "unit": "g", "grade": "LR"},
        ],
        "apparatus": ["Beaker (500 mL)", "Separating funnel (250 mL)", "Funnel and filter paper",
                      "Water bath", "Evaporating dish", "Melting point apparatus", "Analytical balance"],
        "procedure": [
            "Boil 20 g of tea leaves with 150 mL of distilled water for about 10 minutes.",
            "Filter the hot decoction and press the leaves to recover maximum liquid.",
            "To the filtrate add 10 g of sodium carbonate (this frees caffeine base and precipitates tannins as salts), stir and cool to room temperature.",
            "Transfer to a separating funnel and extract with dichloromethane in three portions of 20 mL each. Shake gently (vigorous shaking forms emulsions); the DCM layer is the LOWER layer.",
            "Combine the DCM extracts and dry over anhydrous sodium sulphate for 10 minutes; filter.",
            "Evaporate the DCM on a water bath (fume cupboard — no naked flame) to obtain crude caffeine.",
            "Weigh the product and determine its melting point (pure caffeine sublimes/melts at 236 °C). Recrystallise from hot water if required.",
        ],
        "precautions": "Dichloromethane is volatile and harmful by inhalation — use the fume cupboard and never heat it over a flame. "
                       "Vent the separating funnel frequently to release pressure. Shake gently to avoid emulsion formation.",
        "observation": "White needle-like crystals of crude caffeine are obtained (typical crude yield 0.1–0.3 g from 20 g tea). "
                       "Melting point ≈ 236 °C confirms caffeine.",
        "diagram": "funnel",
    },
    {
        "title": "Determination of Partition Coefficient of Benzoic Acid",
        "subject": "Pharmaceutics",
        "objective": "To determine the partition (distribution) coefficient of benzoic acid between "
                    "n-butanol and water by the shake-flask method.",
        "chemicals": [
            {"name": "Benzoic acid", "qty": "0.5", "unit": "g", "grade": "LR"},
            {"name": "n-Butanol", "qty": "50", "unit": "mL", "grade": "LR"},
            {"name": "Distilled water", "qty": "50", "unit": "mL", "grade": "—"},
            {"name": "Sodium hydroxide solution 0.1 N", "qty": "as required", "unit": "mL", "grade": "standardised"},
            {"name": "Phenolphthalein indicator", "qty": "2–3", "unit": "drops", "grade": "—"},
        ],
        "apparatus": ["Separating funnel or stoppered bottle (250 mL)", "Mechanical shaker (or manual shaking)",
                      "Burette (50 mL)", "Pipettes (10 mL)", "Conical flasks", "Analytical balance"],
        "procedure": [
            "Dissolve 0.5 g of benzoic acid in 50 mL of n-butanol (gentle warming if needed) in a stoppered bottle.",
            "Add 50 mL of distilled water, stopper firmly and shake vigorously for about 30 minutes to reach equilibrium.",
            "Allow the two layers to separate completely; carefully separate the aqueous (lower) layer from the butanol (upper) layer.",
            "Pipette 10 mL of the aqueous layer into a conical flask, add phenolphthalein and titrate against 0.1 N NaOH to a pale pink end point.",
            "Similarly titrate a 10 mL aliquot of the butanol layer (add a little water/ethanol to mix) against 0.1 N NaOH.",
            "Calculate the concentration of benzoic acid in each phase from the titres.",
            "Partition coefficient K = concentration in n-butanol / concentration in water. Repeat and report the mean.",
        ],
        "precautions": "Shake long enough for true equilibrium, and let layers separate fully before sampling — "
                       "cross-contamination of layers is the biggest error source. Titrate promptly after separation.",
        "observation": "More benzoic acid is found in the butanol layer than in water (K > 1, commonly around 5–10 under these conditions), "
                       "showing the drug prefers the lipid-like phase — the basis of its absorption behaviour.",
        "diagram": "funnel",
    },
    {
        "title": "Effect of Drugs on the Isolated Frog Heart",
        "subject": "Pharmacology",
        "objective": "To study the effects of adrenaline, acetylcholine, atropine, calcium chloride and potassium "
                    "chloride on the isolated perfused frog heart (heart rate and force of contraction). "
                    "Overview practical — performed only under teacher supervision and institutional animal-ethics approval.",
        "chemicals": [
            {"name": "Frog Ringer solution", "qty": "as required", "unit": "mL", "grade": "freshly prepared"},
            {"name": "Adrenaline solution (1:10,000)", "qty": "0.1–0.2", "unit": "mL", "grade": "—"},
            {"name": "Acetylcholine solution (1:100,000)", "qty": "0.1–0.2", "unit": "mL", "grade": "—"},
            {"name": "Atropine sulphate solution (1:10,000)", "qty": "0.1–0.2", "unit": "mL", "grade": "—"},
            {"name": "Calcium chloride solution (1%)", "qty": "0.1–0.2", "unit": "mL", "grade": "—"},
            {"name": "Potassium chloride solution (1%)", "qty": "0.1–0.2", "unit": "mL", "grade": "—"},
        ],
        "apparatus": ["Frog board and dissection instruments", "Syme's cannula", "Perfusion reservoir and tubing",
                      "Starling heart lever", "Kymograph (or digital recorder)", "Thread and hooks", "Stopwatch"],
        "procedure": [
            "The frog is pithed (CNS destroyed) by the demonstrator as per ethics-approved protocol, and placed on the frog board.",
            "Open the thorax, remove the pericardium and expose the beating heart.",
            "Insert a Syme's cannula into the inferior vena cava / sinus venosus and perfuse the heart with frog Ringer solution at constant pressure.",
            "Connect the apex of the ventricle to a Starling heart lever and record normal contractions on the kymograph.",
            "Add each drug (0.1–0.2 mL) one at a time into the perfusion fluid; record the change in rate and amplitude.",
            "Wash out with fresh Ringer solution after each drug and wait for the normal rhythm to return before the next drug.",
            "Sequence: adrenaline → wash → acetylcholine → wash → atropine then acetylcholine again (blocks ACh) → CaCl2 → wash → KCl (excess stops heart in diastole).",
            "Tabulate rate (beats/min) and amplitude for normal and each drug condition.",
        ],
        "precautions": "This practical involves a live vertebrate preparation — it is demonstrated/approved only under the "
                       "institution's animal ethics committee rules; students follow the demonstrator's instructions exactly. "
                       "Keep the heart moist with Ringer at all times; avoid air bubbles in the cannula.",
        "observation": "Adrenaline increases rate and force (β1 stimulation). Acetylcholine decreases rate and force, and its effect "
                       "is blocked after atropine (muscarinic antagonism). CaCl2 increases force; excess KCl arrests the heart in diastole.",
        "diagram": "heart",
    },
    {
        "title": "Identification of Crude Drug Clove by Microscopy",
        "subject": "Pharmacognosy",
        "objective": "To identify clove (Syzygium aromaticum flower buds) from its transverse section and powder "
                    "characters: oil glands, aerenchyma, calcium oxalate cluster crystals, pollen grains and fibres.",
        "chemicals": [
            {"name": "Chloral hydrate solution", "qty": "2–3", "unit": "drops", "grade": "LR"},
            {"name": "Phloroglucinol solution + conc. HCl (1:1)", "qty": "2–3", "unit": "drops", "grade": "LR"},
            {"name": "Sudan Red III solution", "qty": "2–3", "unit": "drops", "grade": "LR"},
            {"name": "Glycerin (mounting)", "qty": "1–2", "unit": "drops", "grade": "IP"},
            {"name": "Distilled water", "qty": "as required", "unit": "mL", "grade": "—"},
        ],
        "apparatus": ["Compound microscope", "Razor / microtome", "Watch glass", "Glass slides and cover slips",
                      "Needles and forceps", "Filter paper"],
        "procedure": [
            "Soak dried clove buds in water (or use the pre-soaked sample) until soft.",
            "Cut a thin transverse section through the hypanthium (lower cylindrical part) with a sharp razor.",
            "Clear the section with chloral hydrate solution on a slide (gentle warming), then mount in glycerin and observe — note the two zones of the section and large oval oil glands.",
            "Stain a second section with phloroglucinol + conc. HCl: lignified fibres and vessels turn pink/red.",
            "Stain a third section with Sudan Red III: oil glands/volatile oil stain orange-red.",
            "Prepare a powder mount: place powdered clove in chloral hydrate, warm, mount and observe — cluster crystals of calcium oxalate, pollen grains, fibres and oil globules.",
            "Draw and label: epidermis, oil glands, aerenchyma (loosely arranged parenchyma with air spaces), vascular tissue, cluster crystals, pollen grains.",
        ],
        "precautions": "Concentrated HCl is corrosive — handle the staining reagent with care. Sections must be thin and uniform, "
                       "otherwise structures overlap. Do not overheat chloral hydrate (it bubbles and ruins the section).",
        "observation": "TS shows an outer zone with numerous large oil glands and an inner zone of aerenchyma with a ring of "
                       "vascular bundles; powder shows calcium oxalate cluster crystals, characteristic pollen grains and fibres — "
                       "confirming the drug is clove.",
        "diagram": "microscope",
    },
]

CHEMICALS = [
    # name, qty, unit, lab, low-stock threshold
    ("Sucrose (IP)", 8.5, "kg", "Pharmaceutics Lab", 10),
    ("Salicylic acid", 450, "g", "Pharmaceutical Chemistry Lab", 500),
    ("Acetic anhydride", 1.25, "L", "Pharmaceutical Chemistry Lab", 0.5),
    ("Ethanol 96%", 4.5, "L", "Pharmaceutical Chemistry Lab", 2),
    ("Hydrochloric acid (conc.)", 2.5, "L", "Pharmaceutical Chemistry Lab", 1),
    ("Sodium hydroxide pellets", 1.8, "kg", "Pharmaceutical Chemistry Lab", 1),
    ("Starch (maize)", 6.0, "kg", "Pharmaceutics Lab", 2),
    ("Lactose", 3.2, "kg", "Pharmaceutics Lab", 1),
    ("Calamine powder", 800, "g", "Pharmaceutics Lab", 500),
    ("Zinc oxide", 600, "g", "Pharmaceutics Lab", 250),
    ("Bentonite", 350, "g", "Pharmaceutics Lab", 500),
    ("Glycerin", 2.0, "L", "Pharmaceutics Lab", 1),
    ("Benzoic acid", 320, "g", "Pharmaceutics Lab", 250),
    ("Dichloromethane", 750, "mL", "Pharmaceutical Chemistry Lab", 500),
    ("Phenolphthalein indicator", 90, "mL", "Pharmaceutical Chemistry Lab", 50),
    ("Talc (purified)", 1.5, "kg", "Pharmaceutics Lab", 0.5),
    ("Magnesium stearate", 300, "g", "Pharmaceutics Lab", 250),
    ("Chloral hydrate", 200, "g", "Pharmacognosy Lab", 100),
]

INSTRUMENTS = [
    # name, lab, status
    ("UV–Visible Spectrophotometer", "Pharmaceutical Chemistry Lab", "working"),
    ("HPLC System", "Pharmaceutical Chemistry Lab", "maintenance"),
    ("Dissolution Apparatus (USP)", "Pharmaceutics Lab", "working"),
    ("Disintegration Test Apparatus", "Pharmaceutics Lab", "working"),
    ("Friability Tester (Roche)", "Pharmaceutics Lab", "working"),
    ("Tablet Hardness Tester (Monsanto)", "Pharmaceutics Lab", "working"),
    ("Single-Punch Tablet Machine", "Pharmaceutics Lab", "working"),
    ("Analytical Balance", "Pharmaceutics Lab", "working"),
    ("Analytical Balance", "Pharmaceutical Chemistry Lab", "working"),
    ("Compound Microscopes (set of 12)", "Pharmacognosy Lab", "working"),
    ("pH Meter", "Pharmaceutical Chemistry Lab", "working"),
    ("Melting Point Apparatus", "Pharmaceutical Chemistry Lab", "working"),
    ("Kymograph with Perfusion Setup", "Pharmacology Lab", "working"),
    ("Centrifuge Machine", "Pharmacology Lab", "maintenance"),
    ("Hot Air Oven", "Pharmaceutics Lab", "working"),
    ("Digital Water Bath", "Pharmacognosy Lab", "working"),
]

BOOKS = [
    # title, author, edition, subject, total, available, shelf
    ("The Theory and Practice of Industrial Pharmacy", "Lachman, Lieberman & Kanig", "4th ed.", "Pharmaceutics", 12, 7, "Rack A-1"),
    ("Ansel's Pharmaceutical Dosage Forms and Drug Delivery Systems", "Loyd V. Allen Jr.", "11th ed.", "Pharmaceutics", 10, 4, "Rack A-2"),
    ("Aulton's Pharmaceutics: The Design and Manufacture of Medicines", "Michael E. Aulton", "6th ed.", "Pharmaceutics", 8, 5, "Rack A-3"),
    ("Remington: The Science and Practice of Pharmacy", "Adeboye Adejare (ed.)", "23rd ed.", "Pharmaceutics", 6, 2, "Rack A-4"),
    ("Basic & Clinical Pharmacology (Katzung)", "Todd W. Vanderah (ed.)", "16th ed.", "Pharmacology", 14, 6, "Rack B-1"),
    ("Essentials of Medical Pharmacology", "K. D. Tripathi", "9th ed.", "Pharmacology", 20, 11, "Rack B-2"),
    ("Rang & Dale's Pharmacology", "James M. Ritter et al.", "10th ed.", "Pharmacology", 10, 3, "Rack B-3"),
    ("Goodman & Gilman's The Pharmacological Basis of Therapeutics", "Laurence Brunton (ed.)", "14th ed.", "Pharmacology", 5, 1, "Rack B-4"),
    ("Pharmacology and Pharmacotherapeutics", "R. S. Satoskar", "26th ed.", "Pharmacology", 9, 5, "Rack B-4"),
    ("Pharmacognosy", "C. K. Kokate", "55th ed.", "Pharmacognosy", 15, 9, "Rack C-1"),
    ("Textbook of Pharmacognosy", "T. E. Wallis", "5th ed.", "Pharmacognosy", 6, 4, "Rack C-2"),
    ("Review of Medical Physiology (Ganong)", "Kim E. Barrett et al.", "26th ed.", "Physiology", 10, 6, "Rack D-1"),
    ("Textbook of Medical Physiology (Guyton & Hall)", "John E. Hall", "14th ed.", "Physiology", 10, 0, "Rack D-2"),
    ("Martin's Physical Pharmacy and Pharmaceutical Sciences", "Patrick J. Sinko", "6th ed.", "Pharmaceutical Chemistry", 7, 4, "Rack E-1"),
    ("Indian Pharmacopoeia 2018 (Set of 4 Volumes)", "Indian Pharmacopoeia Commission", "8th ed. (2018)", "Reference", 3, 3, "Reference Shelf R-1"),
]

TIMETABLE = [
    # day, start, end, batch, subject, lab room, teacher
    ("Monday", "10:00 AM", "12:00 PM", BATCH_A, "Pharmaceutics", "Pharmaceutics Lab (Room 2)", "Dr. Imran Sheikh"),
    ("Monday", "12:30 PM", "02:30 PM", BATCH_B, "Pharmaceutics", "Pharmaceutics Lab (Room 2)", "Dr. Imran Sheikh"),
    ("Tuesday", "09:00 AM", "11:00 AM", BATCH_A, "Pharmacology", "Pharmacology Lab (Room 4)", "Dr. Sana Baloch"),
    ("Tuesday", "11:30 AM", "01:30 PM", BATCH_2A, "Physiology", "Physiology Lab (Room 5)", "Demo Teacher"),
    ("Wednesday", "10:00 AM", "12:00 PM", BATCH_A, "Pharmaceutical Chemistry", "Pharmaceutical Chemistry Lab (Room 3)", "Demo Teacher"),
    ("Wednesday", "12:30 PM", "02:30 PM", BATCH_B, "Pharmacognosy", "Pharmacognosy Lab (Room 6)", "Dr. Sana Baloch"),
    ("Thursday", "09:00 AM", "11:00 AM", BATCH_A, "Pharmacognosy", "Pharmacognosy Lab (Room 6)", "Dr. Sana Baloch"),
    ("Thursday", "11:30 AM", "01:30 PM", BATCH_B, "Pharmaceutical Chemistry", "Pharmaceutical Chemistry Lab (Room 3)", "Demo Teacher"),
    ("Friday", "09:00 AM", "11:00 AM", BATCH_A, "Pharmaceutics", "Pharmaceutics Lab (Room 2)", "Dr. Imran Sheikh"),
    ("Friday", "11:30 AM", "01:00 PM", BATCH_2A, "Pharmacology", "Pharmacology Lab (Room 4)", "Dr. Sana Baloch"),
    ("Saturday", "10:00 AM", "12:00 PM", BATCH_B, "Pharmacology", "Pharmacology Lab (Room 4)", "Dr. Sana Baloch"),
    ("Saturday", "12:30 PM", "02:30 PM", BATCH_2A, "Pharmaceutics", "Pharmaceutics Lab (Room 2)", "Dr. Imran Sheikh"),
]
