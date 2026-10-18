"""Hotel PMS (/hotelpms) — SQLite persistence.

Single-hotel v1: one deployment = one hotel. Multi-tenant = v2.
DB path via HOTELPMS_DB_PATH env var (default: <app>/data/hotelpms.db).
Container SQLite can be wiped on deploy — demo seed re-runs on empty DB.
"""
import os
import sqlite3
import threading
import time

_lock = threading.RLock()
_conn = None


def db_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(os.path.dirname(here), "data", "hotelpms.db")
    return os.environ.get("HOTELPMS_DB_PATH", default)


def now() -> int:
    return int(time.time())


def get_conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            path = db_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            fresh = not os.path.exists(path)
            _conn = sqlite3.connect(path, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            init_schema(_conn)
            if fresh:
                seed_demo(_conn)
        return _conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT DEFAULT '',
    email TEXT UNIQUE,
    password_hash TEXT DEFAULT '',
    pin TEXT DEFAULT '',
    role TEXT DEFAULT 'staff',       -- 'owner' | 'staff'
    is_active INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    hotel_name TEXT DEFAULT '',
    hotel_address TEXT DEFAULT '',
    hotel_phone TEXT DEFAULT '',
    ntn TEXT DEFAULT '',
    strn TEXT DEFAULT '',
    srb_rate_card REAL DEFAULT 8.0,
    srb_rate_cash REAL DEFAULT 15.0,
    fbr_mode TEXT DEFAULT 'test',    -- 'test' | 'live'
    fbr_iris_user TEXT DEFAULT '',
    fbr_iris_pass TEXT DEFAULT '',
    fbr_api_url TEXT DEFAULT '',
    invoice_prefix TEXT DEFAULT 'INV',
    invoice_seq INTEGER DEFAULT 1000,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS room_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rate REAL NOT NULL,
    description TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL UNIQUE,
    room_type_id INTEGER NOT NULL,
    floor TEXT DEFAULT '',
    status TEXT DEFAULT 'ready',     -- ready|occupied|dirty|cleaning|maintenance
    notes TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS guests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cnic TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    nationality TEXT DEFAULT 'Pakistani',
    preferences TEXT DEFAULT '',
    repeat_count INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guest_id INTEGER NOT NULL,
    room_type_id INTEGER NOT NULL,
    room_id INTEGER,
    check_in_date TEXT NOT NULL,      -- YYYY-MM-DD
    check_out_date TEXT NOT NULL,
    nights INTEGER DEFAULT 1,
    rate REAL NOT NULL,
    advance REAL DEFAULT 0,
    status TEXT DEFAULT 'confirmed', -- confirmed|checked_in|checked_out|cancelled
    source TEXT DEFAULT 'walk-in',   -- walk-in|phone|online
    created_at INTEGER NOT NULL,
    created_by TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS stays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER,
    guest_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    check_in_at INTEGER NOT NULL,
    check_out_at INTEGER,
    status TEXT DEFAULT 'active',    -- active|closed
    folio_no TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS folio_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stay_id INTEGER NOT NULL,
    kind TEXT DEFAULT 'room',        -- room|restaurant|extra|discount
    description TEXT NOT NULL,
    qty REAL DEFAULT 1,
    unit_price REAL DEFAULT 0,
    amount REAL NOT NULL,
    created_at INTEGER NOT NULL,
    created_by TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS restaurant_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'Food',
    price REAL NOT NULL,
    active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS restaurant_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stay_id INTEGER,                 -- NULL = direct cash counter bill
    table_no TEXT DEFAULT '',
    status TEXT DEFAULT 'open',      -- open|billed|cancelled
    created_at INTEGER NOT NULL,
    created_by TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS order_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    qty REAL DEFAULT 1,
    price REAL NOT NULL,
    amount REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL UNIQUE,
    stay_id INTEGER,
    event_id INTEGER,
    guest_id INTEGER,
    lines_json TEXT DEFAULT '[]',
    subtotal REAL NOT NULL,
    tax_rate REAL NOT NULL,
    tax_amount REAL NOT NULL,
    total REAL NOT NULL,
    payment_method TEXT DEFAULT 'cash',  -- cash|card
    fbr_invoice_no TEXT DEFAULT '',
    fbr_qr_payload TEXT DEFAULT '',
    fbr_status TEXT DEFAULT 'test',  -- test|pending|submitted|failed
    fbr_response TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    created_by TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_phone TEXT DEFAULT '',
    event_date TEXT NOT NULL,
    hall TEXT DEFAULT 'Main Hall',
    guests_count INTEGER DEFAULT 0,
    package_name TEXT DEFAULT '',
    per_head_rate REAL DEFAULT 0,
    total REAL NOT NULL,
    advance REAL DEFAULT 0,
    balance REAL DEFAULT 0,
    status TEXT DEFAULT 'booked',    -- booked|confirmed|completed|cancelled
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS housekeeping_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id INTEGER NOT NULL,
    task_type TEXT DEFAULT 'cleaning',  -- cleaning|maintenance
    description TEXT DEFAULT '',
    status TEXT DEFAULT 'open',       -- open|in_progress|done
    assigned_to TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    done_at INTEGER
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT DEFAULT 'cash',
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_stays_status ON stays(status);
CREATE INDEX IF NOT EXISTS idx_folio_stay ON folio_items(stay_id);
CREATE INDEX IF NOT EXISTS idx_invoices_created ON invoices(created_at);
-- v2: inventory / payroll / fbr log -------------------------------------
CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'General',   -- Kitchen|Linen|Toiletries|Housekeeping|General
    unit TEXT DEFAULT 'pcs',           -- pcs|kg|litre|pack
    qty_on_hand REAL DEFAULT 0,
    reorder_level REAL DEFAULT 0,
    cost_price REAL DEFAULT 0,
    active INTEGER DEFAULT 1,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    kind TEXT DEFAULT 'purchase',      -- purchase|use|adjust|waste
    qty REAL NOT NULL,                 -- +in / -out
    note TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    created_by TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS menu_recipe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_item_id INTEGER NOT NULL,     -- restaurant_items.id
    inv_item_id INTEGER NOT NULL,      -- inventory_items.id
    qty REAL NOT NULL                  -- qty of stock used per 1 serving
);
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    att_date TEXT NOT NULL,            -- YYYY-MM-DD
    status TEXT DEFAULT 'present',     -- present|absent|leave|half
    created_at INTEGER NOT NULL,
    UNIQUE(user_id, att_date)
);
CREATE TABLE IF NOT EXISTS staff_pay (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT NOT NULL,               -- YYYY-MM
    base_salary REAL DEFAULT 0,
    present_days REAL DEFAULT 0,
    deductions REAL DEFAULT 0,
    bonus REAL DEFAULT 0,
    net_pay REAL DEFAULT 0,
    paid INTEGER DEFAULT 0,            -- 0|1
    created_at INTEGER NOT NULL,
    UNIQUE(user_id, month)
);
CREATE TABLE IF NOT EXISTS fbr_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    attempt_no INTEGER DEFAULT 1,
    request_json TEXT DEFAULT '',
    http_code INTEGER DEFAULT 0,
    response_text TEXT DEFAULT '',
    ok INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_att_user_date ON attendance(user_id, att_date);
CREATE INDEX IF NOT EXISTS idx_fbrlog_inv ON fbr_log(invoice_id);
"""


def init_schema(conn):
    conn.executescript(SCHEMA)
    # ---- v2 column migrations (safe on existing v1 DBs) ----
    for ddl in (
        "ALTER TABLE users ADD COLUMN salary_monthly REAL DEFAULT 0",
        "ALTER TABLE settings ADD COLUMN lang TEXT DEFAULT 'en'",
    ):
        try:
            conn.execute(ddl)
        except Exception:
            pass  # column already exists
    conn.commit()


# ---------------------------------------------------------------- helpers ---
def q(sql, args=()):
    conn = get_conn()
    with _lock:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur


def qone(sql, args=()):
    conn = get_conn()
    with _lock:
        return conn.execute(sql, args).fetchone()


def qall(sql, args=()):
    conn = get_conn()
    with _lock:
        return conn.execute(sql, args).fetchall()


def get_settings() -> dict:
    row = qone("SELECT * FROM settings WHERE id=1")
    if not row:
        q("INSERT INTO settings (id, hotel_name, updated_at) VALUES (1,'',?)", (now(),))
        row = qone("SELECT * FROM settings WHERE id=1")
    return dict(row)


def tax_rate_for(method: str) -> float:
    s = get_settings()
    return float(s["srb_rate_card"] if method == "card" else s["srb_rate_cash"])


# ------------------------------------------------------------------ seed ---
def seed_demo(conn):
    import hashlib
    import hmac as _hmac
    import secrets as _secrets

    def h(pw):
        salt = _secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
        return salt.hex() + "$" + dk.hex()

    t = int(time.time())
    # Owner + staff
    conn.execute(
        "INSERT INTO users (name,email,password_hash,role,created_at) VALUES (?,?,?,?,?)",
        ("Hotel Owner", "owner@demo.pk", h("demo1234"), "owner", t))
    conn.execute(
        "INSERT INTO users (name,pin,role,created_at) VALUES (?,?,?,?)",
        ("Ahmed (Receptionist)", "1234", "staff", t))
    # Settings
    conn.execute(
        """INSERT INTO settings (id, hotel_name, hotel_address, hotel_phone, ntn, strn,
           srb_rate_card, srb_rate_cash, fbr_mode, invoice_prefix, invoice_seq, updated_at)
           VALUES (1,?,?,?,?,?,?,?,'test',?,1000,?)""",
        ("Hotel Mehran Larkana", "Station Road, Larkana, Sindh", "074-1234567",
         "1234567-8", "1234567-8-001", 8.0, 15.0, "INV", t))
    # Room types
    rt = {}
    for name, rate, desc in [
            ("Standard", 3500, "Double bed, AC, attached bath"),
            ("Deluxe", 5000, "King bed, AC, LED, mini fridge"),
            ("Suite", 9000, "2 rooms, lounge, premium bath")]:
        cur = conn.execute("INSERT INTO room_types (name, rate, description) VALUES (?,?,?)",
                           (name, rate, desc))
        rt[name] = cur.lastrowid
    # 12 rooms
    rooms = [("101", "Standard"), ("102", "Standard"), ("103", "Standard"),
             ("104", "Standard"), ("105", "Standard"),
             ("201", "Deluxe"), ("202", "Deluxe"), ("203", "Deluxe"),
             ("204", "Deluxe"), ("205", "Deluxe"),
             ("301", "Suite"), ("302", "Suite")]
    room_ids = {}
    for num, rtype in rooms:
        cur = conn.execute(
            "INSERT INTO rooms (number, room_type_id, floor, status) VALUES (?,?,?, 'ready')",
            (num, rt[rtype], num[0]))
        room_ids[num] = cur.lastrowid
    # Guests
    guests = {}
    for name, cnic, phone in [
            ("Ahmed Khan", "43201-1234567-1", "0300-1234567"),
            ("Fatima Sheikh", "43201-7654321-2", "0333-7654321"),
            ("Bilal Raza", "43201-1111111-3", "0345-1111111"),
            ("Sara Malik", "43201-2222222-4", "0321-2222222"),
            ("Usman Tariq", "43201-3333333-5", "0301-3333333")]:
        cur = conn.execute(
            "INSERT INTO guests (name, cnic, phone, created_at) VALUES (?,?,?,?)",
            (name, cnic, phone, t))
        guests[name] = cur.lastrowid
    # Restaurant menu
    menu = [("Chicken Biryani", "Food", 350), ("Beef Karahi (Half)", "Food", 1200),
            ("Daal Fry", "Food", 280), ("Mix Sabzi", "Food", 300),
            ("Chicken Tikka", "BBQ", 450), ("Seekh Kabab (4pc)", "BBQ", 550),
            ("Roghni Naan", "Bread", 60), ("Tandoori Roti", "Bread", 30),
            ("Fresh Lime Soda", "Drinks", 200), ("Doodh Patti", "Drinks", 120),
            ("Mineral Water (1.5L)", "Drinks", 150), ("Gulab Jamun (4pc)", "Dessert", 250)]
    menu_ids = {}
    for name, cat, price in menu:
        cur = conn.execute(
            "INSERT INTO restaurant_items (name, category, price) VALUES (?,?,?)",
            (name, cat, price))
        menu_ids[name] = cur.lastrowid

    from datetime import date, timedelta
    today = date.today()
    d = lambda n: (today + timedelta(days=n)).isoformat()

    # 5 sample bookings: 2 future confirmed, 1 past checked-out, 1 cancelled, 1 future
    bdata = [
        ("Fatima Sheikh", "Deluxe", d(2), d(4), 2, 5000, 3000, "confirmed", "phone"),
        ("Bilal Raza", "Standard", d(5), d(6), 1, 3500, 1000, "confirmed", "walk-in"),
        ("Sara Malik", "Suite", d(-6), d(-4), 2, 9000, 9000, "checked_out", "online"),
        ("Usman Tariq", "Standard", d(3), d(5), 2, 3500, 0, "cancelled", "phone"),
        ("Fatima Sheikh", "Standard", d(9), d(11), 2, 3500, 2000, "confirmed", "online"),
    ]
    for gname, rtype, ci, co, nights, rate, adv, status, src in bdata:
        conn.execute(
            """INSERT INTO bookings (guest_id, room_type_id, check_in_date, check_out_date,
               nights, rate, advance, status, source, created_at, created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (guests[gname], rt[rtype], ci, co, nights, rate, adv, status, src, t, "seed"))

    # 1 ACTIVE STAY: Ahmed Khan in 201 (Deluxe), checked in yesterday, 2 nights
    conn.execute(
        """INSERT INTO bookings (guest_id, room_type_id, room_id, check_in_date, check_out_date,
           nights, rate, advance, status, source, created_at, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (guests["Ahmed Khan"], rt["Deluxe"], room_ids["201"], d(-1), d(1), 2, 5000,
         2000, "checked_in", "walk-in", t, "seed"))
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        """INSERT INTO stays (booking_id, guest_id, room_id, check_in_at, status, folio_no)
           VALUES (?,?,?,?,?,?)""",
        (bid, guests["Ahmed Khan"], room_ids["201"], t - 86400, "active", "F-1001"))
    sid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # Room charges on folio (2 nights x 5000)
    conn.execute(
        """INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (sid, "room", "Deluxe Room 201 — 2 nights", 2, 5000, 10000, t))
    # Restaurant order posted to room folio
    conn.execute(
        "INSERT INTO restaurant_orders (stay_id, table_no, status, created_at) VALUES (?,?,?,?)",
        (sid, "T-5", "billed", t))
    oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    price_map = {m[0]: m[2] for m in menu}
    for item, qty in [("Chicken Biryani", 2), ("Doodh Patti", 2), ("Roghni Naan", 4)]:
        price = price_map[item]
        conn.execute(
            "INSERT INTO order_lines (order_id, item_id, qty, price, amount) VALUES (?,?,?,?,?)",
            (oid, menu_ids[item], qty, price, qty * price))
    rtotal = 2 * 350 + 2 * 120 + 4 * 60  # 1180
    conn.execute(
        """INSERT INTO folio_items (stay_id, kind, description, qty, unit_price, amount, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (sid, "restaurant", "Restaurant — Order #1 (T-5)", 1, rtotal, rtotal, t))
    conn.execute("UPDATE rooms SET status='occupied' WHERE id=?", (room_ids["201"],))
    conn.execute("UPDATE guests SET repeat_count=2 WHERE id=?", (guests["Ahmed Khan"],))

    # One room dirty (housekeeping demo)
    conn.execute("UPDATE rooms SET status='dirty' WHERE id=?", (room_ids["203"],))
    conn.execute(
        """INSERT INTO housekeeping_tasks (room_id, task_type, description, status, assigned_to, created_at)
           VALUES (?,?,?,?,?,?)""",
        (room_ids["203"], "cleaning", "Checkout cleaning — full service", "open", "Cleaner team", t))

    # 1 marriage-hall event
    conn.execute(
        """INSERT INTO events (event_name, client_name, client_phone, event_date, hall,
           guests_count, package_name, per_head_rate, total, advance, balance, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("Walima — Ahmed family", "Imran Ahmed", "0300-9998888", d(14), "Main Hall",
         400, "Deluxe Dinner", 1800, 720000, 200000, 520000, "booked", t))

    # ---- v2 seed: inventory, recipes, salaries ----
    inv_ids = {}
    for name, cat, unit, qty, reorder, cost in [
            ("Basmati Rice", "Kitchen", "kg", 120, 25, 380),
            ("Chicken (whole)", "Kitchen", "kg", 60, 15, 620),
            ("Cooking Oil", "Kitchen", "litre", 80, 20, 540),
            ("Wheat Flour (Atta)", "Kitchen", "kg", 100, 20, 160),
            ("Sugar", "Kitchen", "kg", 50, 10, 150),
            ("Tea Leaves", "Kitchen", "kg", 12, 3, 2200),
            ("Milk", "Kitchen", "litre", 40, 10, 190),
            ("Mineral Water Bottles", "Kitchen", "pcs", 200, 48, 120),
            ("Bedsheets (white)", "Linen", "pcs", 60, 15, 900),
            ("Towels", "Linen", "pcs", 80, 20, 450),
            ("Pillow Covers", "Linen", "pcs", 70, 15, 250),
            ("Soap (small)", "Toiletries", "pcs", 300, 60, 45),
            ("Shampoo Sachets", "Toiletries", "pcs", 250, 60, 30),
            ("Toilet Roll", "Housekeeping", "pcs", 120, 30, 90),
            ("Floor Cleaner", "Housekeeping", "litre", 25, 6, 650)]:
        cur = conn.execute(
            """INSERT INTO inventory_items (name, category, unit, qty_on_hand, reorder_level,
               cost_price, created_at) VALUES (?,?,?,?,?,?,?)""",
            (name, cat, unit, qty, reorder, cost, t))
        inv_ids[name] = cur.lastrowid
    # Recipes: menu item -> stock used per serving
    for menu_name, uses in [
            ("Chicken Biryani", [("Basmati Rice", 0.25), ("Chicken (whole)", 0.25),
                                 ("Cooking Oil", 0.05)]),
            ("Beef Karahi (Half)", [("Cooking Oil", 0.08)]),
            ("Daal Fry", [("Cooking Oil", 0.04)]),
            ("Roghni Naan", [("Wheat Flour (Atta)", 0.12)]),
            ("Tandoori Roti", [("Wheat Flour (Atta)", 0.10)]),
            ("Doodh Patti", [("Milk", 0.25), ("Tea Leaves", 0.01), ("Sugar", 0.03)]),
            ("Fresh Lime Soda", [("Sugar", 0.04)]),
            ("Mineral Water (1.5L)", [("Mineral Water Bottles", 1)])]:
        mid = menu_ids.get(menu_name)
        if not mid:
            continue
        for iname, q in uses:
            conn.execute(
                "INSERT INTO menu_recipe (menu_item_id, inv_item_id, qty) VALUES (?,?,?)",
                (mid, inv_ids[iname], q))
    # Staff monthly salaries (demo)
    conn.execute("UPDATE users SET salary_monthly=60000 WHERE email='owner@demo.pk'")
    conn.execute("UPDATE users SET salary_monthly=35000 WHERE pin='1234'")
    conn.execute(
        "INSERT INTO users (name, pin, role, salary_monthly, created_at) VALUES (?,?, 'staff', ?, ?)",
        ("Sana (Housekeeping)", "5678", 28000, t))
    conn.commit()
