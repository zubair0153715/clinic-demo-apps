"""IQLab question generators — 13 test styles, all procedural.

Every generator: gen(level:int, rng) -> dict with:
  qtype, domain, prompt, visual (svg/html string or ""), options (list),
  answer (index into options), explain (short)
Levels 1..5. All original content (Raven/WAIS-style formats, own items).
"""
import random

DOMAINS = ["fluid", "verbal", "memory", "speed", "quant"]

# ---------- svg helpers ----------
COLORS = {"red": "#e74c3c", "blue": "#3498db", "green": "#2ecc71",
          "yellow": "#f1c40f", "purple": "#9b59b6", "orange": "#e67e22",
          "black": "#2c3e50", "pink": "#fd79a8"}

def _shape_svg(kind, color="#3498db", size=40, rot=0, cx=50, cy=50):
    c = COLORS.get(color, color)
    t = f' transform="rotate({rot} {cx} {cy})"' if rot else ""
    if kind == "circle":
        return f'<circle cx="{cx}" cy="{cy}" r="{size/2}" fill="{c}"{t}/>'
    if kind == "square":
        h = size / 2
        return f'<rect x="{cx-h}" y="{cy-h}" width="{size}" height="{size}" fill="{c}"{t}/>'
    if kind == "triangle":
        h = size / 2
        pts = f"{cx},{cy-h} {cx-h},{cy+h} {cx+h},{cy+h}"
        return f'<polygon points="{pts}" fill="{c}"{t}/>'
    if kind == "diamond":
        h = size / 2
        pts = f"{cx},{cy-h} {cx+h},{cy} {cx},{cy+h} {cx-h},{cy}"
        return f'<polygon points="{pts}" fill="{c}"{t}/>'
    if kind == "star":
        import math
        pts = []
        for i in range(10):
            r = size / 2 if i % 2 == 0 else size / 4
            a = math.pi / 5 * i - math.pi / 2
            pts.append(f"{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}")
        return f'<polygon points="{" ".join(pts)}" fill="{c}"{t}/>'
    if kind == "arrow":
        h = size / 2
        pts = f"{cx-h},{cy-h*0.4} {cx},{cy-h*0.4} {cx},{cy-h} {cx+h},{cy} {cx},{cy+h} {cx},{cy+h*0.4} {cx-h},{cy+h*0.4}"
        return f'<polygon points="{pts}" fill="{c}"{t}/>'
    return f'<circle cx="{cx}" cy="{cy}" r="{size/2}" fill="{c}"/>'

def _svg(shapes, w=300, h=110):
    return f'<svg viewBox="0 0 {w} {h}" style="max-width:100%;background:#f8f9fa;border-radius:8px;">{"".join(shapes)}</svg>'

def _opt_svgs(list_of_shape_lists):
    return [_svg(s) for s in list_of_shape_lists]

# ---------- 1. number series ----------
def gen_number_series(level, rng):
    t = rng.random()
    if level == 1:
        step = rng.randint(2, 9) * rng.choice([1, -1])
        start = rng.randint(1, 20)
        seq = [start + i * step for i in range(5)]
        rule = f"{'+' if step > 0 else ''}{step}"
    elif level == 2:
        if t < 0.5:
            step = rng.randint(2, 9) * rng.choice([1, -1])
            start = rng.randint(5, 30)
            seq = [start + i * step for i in range(5)]
            rule = f"{'+' if step > 0 else ''}{step}"
        else:
            mult = rng.choice([2, 3])
            start = rng.randint(1, 6)
            seq = [start * mult ** i for i in range(5)]
            rule = f"×{mult}"
    elif level == 3:
        if t < 0.4:
            a, b = rng.randint(1, 9), rng.randint(1, 9)
            s1, s2 = rng.randint(2, 5), rng.randint(2, 5)
            seq = [a + i * s1 if i % 2 == 0 else b + (i // 2) * s2 for i in range(6)]
            seq = [a, b] + [0]*4
            for i in range(2, 6):
                seq[i] = seq[i-2] + (s1 if i % 2 == 0 else s2)
            rule = "alternate"
        else:
            seq = [1, 1]
            for _ in range(4):
                seq.append(seq[-1] + seq[-2])
            if rng.random() < 0.5:
                k = rng.randint(2, 5)
                seq = [x * k for x in seq]
            rule = "fibonacci"
    elif level == 4:
        if t < 0.5:
            n0 = rng.randint(2, 6)
            seq = [(n0 + i) ** 2 for i in range(5)]
            rule = "squares"
        else:
            mult, add = rng.choice([2, 3]), rng.randint(1, 5) * rng.choice([1, -1])
            seq = [rng.randint(2, 8)]
            for _ in range(4):
                seq.append(seq[-1] * mult + add)
            rule = f"×{mult}{'+' if add > 0 else ''}{add}"
    else:
        if t < 0.5:
            n0 = rng.randint(2, 5)
            op = rng.choice([1, -1])
            seq = [(n0 + i) ** 2 + op * (i + 1) for i in range(5)]
            rule = "n²±n"
        else:
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
            s = rng.randint(0, 4)
            seq = primes[s:s+5]
            rule = "primes"
    ans = seq[-1]
    shown = seq[:-1]
    distract = {ans + rng.choice([1, 2, -1, -2, 10, -10]),
                ans + rng.randint(3, 9), ans - rng.randint(3, 9)}
    distract.discard(ans)
    opts = [ans] + list(distract)[:3]
    rng.shuffle(opts)
    return {"qtype": "number_series", "domain": "fluid",
            "prompt": "Agla number kya aayega? " + ", ".join(map(str, shown)) + ", ?",
            "visual": "", "options": [str(o) for o in opts],
            "answer": opts.index(ans), "explain": f"Rule: {rule}"}

# ---------- 2. matrix reasoning ----------
def gen_matrix(level, rng):
    kinds = ["circle", "square", "triangle", "diamond", "star"]
    color = rng.choice(list(COLORS)[:6])
    rule = rng.choice(["count", "rotate", "size"])
    n = 3
    cells = []
    if rule == "count":
        base = rng.randint(1, 3)
        step = rng.randint(1, 2)
        for r in range(n):
            for c_ in range(n):
                cnt = base + (r * n + c_) * step if level > 2 else base + c_ * step + r
                cnt = base + (r + c_) * step
                shapes = []
                for i in range(min(cnt, 6)):
                    x = 30 + (i % 3) * 32
                    y = 30 + (i // 3) * 32
                    shapes.append(_shape_svg(rng.choice(kinds), color, 22, 0, x, y))
                cells.append(_svg(shapes, 110, 70))
        # missing = last cell; correct count:
        correct_cnt = min(base + (2 + 2) * step, 6)
        shapes = []
        for i in range(correct_cnt):
            x = 30 + (i % 3) * 32
            y = 30 + (i // 3) * 32
            shapes.append(_shape_svg(kinds[0], color, 22, 0, x, y))
        correct = _svg(shapes, 110, 70)
        # distractors: wrong counts
        opts_svg = [correct]
        for d in [1, -1, 2]:
            cc = max(1, min(6, correct_cnt + d))
            shapes = [_shape_svg(kinds[0], color, 22, 0, 30 + (i % 3) * 32, 30 + (i // 3) * 32) for i in range(cc)]
            s = _svg(shapes, 110, 70)
            if s not in opts_svg:
                opts_svg.append(s)
        while len(opts_svg) < 4:
            cc = rng.randint(1, 6)
            shapes = [_shape_svg(kinds[0], color, 22, 0, 30 + (i % 3) * 32, 30 + (i // 3) * 32) for i in range(cc)]
            s = _svg(shapes, 110, 70)
            if s not in opts_svg:
                opts_svg.append(s)
        rng.shuffle(opts_svg)
        grid_cells = cells[:-1]
    elif rule == "rotate":
        kind = "arrow"
        for r in range(n):
            for c_ in range(n):
                rot = ((r * n + c_) * 90) % 360
                grid_cells_extra = _svg([_shape_svg(kind, color, 44, rot, 55, 35)], 110, 70)
                cells.append(grid_cells_extra)
        correct_rot = ((8) * 90) % 360
        correct = _svg([_shape_svg(kind, color, 44, correct_rot, 55, 35)], 110, 70)
        opts_svg = [correct]
        for d in [90, 180, 270]:
            s = _svg([_shape_svg(kind, color, 44, (correct_rot + d) % 360, 55, 35)], 110, 70)
            if s not in opts_svg:
                opts_svg.append(s)
        rng.shuffle(opts_svg)
        grid_cells = cells[:-1]
    else:  # size progression across row
        for r in range(n):
            for c_ in range(n):
                sz = 18 + (r + c_) * 8
                cells.append(_svg([_shape_svg(rng.choice(kinds), color, sz, 0, 55, 35)], 110, 70))
        correct = _svg([_shape_svg(kinds[0], color, 18 + 4 * 8, 0, 55, 35)], 110, 70)
        opts_svg = [correct]
        for d in [-12, 12, -24]:
            s = _svg([_shape_svg(kinds[0], color, 18 + 4 * 8 + d, 0, 55, 35)], 110, 70)
            if s not in opts_svg:
                opts_svg.append(s)
        rng.shuffle(opts_svg)
        grid_cells = cells[:-1]
    grid = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px;max-width:360px;">'
    for i, c_ in enumerate(grid_cells):
        grid += f"<div>{c_}</div>"
    grid += '<div style="display:flex;align-items:center;justify-content:center;background:#e9ecef;border-radius:8px;font-size:32px;min-height:70px;">?</div></div>'
    return {"qtype": "matrix", "domain": "fluid",
            "prompt": "Khaali khana ( ? ) me kaunsi shape aayegi? Pattern dekho.",
            "visual": grid, "options": opts_svg,
            "answer": opts_svg.index(correct),
            "explain": f"Rule: {rule} progression across rows"}

# ---------- 3. spatial rotation ----------
def gen_spatial(level, rng):
    import math
    # asymmetric L-shape polygon
    pts = "30,20 55,20 55,45 80,45 80,70 30,70"
    color = rng.choice(["blue", "purple", "orange"])
    base_rot = rng.choice([0, 90, 180, 270])
    target_rot = (base_rot + rng.choice([90, 180, 270])) % 360
    def poly(rot, mirror=False):
        c = COLORS[color]
        pts2 = pts if not mirror else "80,20 55,20 55,45 30,45 30,70 80,70"
        return (f'<svg viewBox="0 0 110 90" style="max-width:100%;background:#f8f9fa;border-radius:8px;">'
                f'<polygon points="{pts2}" fill="{c}" transform="rotate({rot} 55 45)"/></svg>')
    correct = poly(target_rot)
    opts = [correct, poly((target_rot + 90) % 360), poly(target_rot, mirror=True)]
    if level >= 3:
        opts.append(poly((target_rot + 180) % 360, mirror=True))
    else:
        opts.append(poly((target_rot + 180) % 360))
    # dedupe
    uniq = []
    for o in opts:
        if o not in uniq:
            uniq.append(o)
    rng.shuffle(uniq)
    return {"qtype": "spatial", "domain": "fluid",
            "prompt": "Neeche wali shape ko ghumane pe kaunsi option banegi? (Mirror nahi, sirf rotation)",
            "visual": poly(base_rot),
            "options": uniq, "answer": uniq.index(correct),
            "explain": f"{target_rot}° rotation (mirror galat hai)"}

# ---------- 4. odd one out (numbers) ----------
def gen_odd_one_out(level, rng):
    if level <= 2:
        prop = rng.choice(["even", "odd"])
        if prop == "even":
            good = [rng.randrange(2, 50, 2) for _ in range(4)]
            bad = rng.randrange(1, 50, 2)
            why = "baqi sab even hain"
        else:
            good = [rng.randrange(1, 50, 2) for _ in range(4)]
            bad = rng.randrange(2, 50, 2)
            why = "baqi sab odd hain"
    elif level == 3:
        mult = rng.choice([3, 4, 5])
        good = [mult * rng.randint(2, 12) for _ in range(4)]
        bad = rng.randint(10, 60)
        while bad % mult == 0:
            bad = rng.randint(10, 60)
        why = f"baqi sab {mult} ke multiples hain"
    else:
        primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
        good = rng.sample(primes, 4)
        bad = rng.choice([4, 6, 8, 9, 10, 12, 15, 21, 25, 27])
        why = "baqi sab prime numbers hain"
    opts = [str(x) for x in good] + [str(bad)]
    rng.shuffle(opts)
    return {"qtype": "odd_one_out", "domain": "fluid",
            "prompt": "Kaunsa number sab se alag hai?",
            "visual": "", "options": opts, "answer": opts.index(str(bad)),
            "explain": why}

# ---------- 5. pattern completion (shapes) ----------
def gen_pattern(level, rng):
    kinds = ["circle", "square", "triangle"]
    cols = ["red", "blue", "green"]
    if level <= 2:
        pat = [rng.choice(kinds), rng.choice(kinds)]
        while pat[0] == pat[1]:
            pat[1] = rng.choice(kinds)
        seq = [pat[i % 2] for i in range(5)]
        why = "ABAB pattern"
    elif level == 3:
        pat = rng.sample(kinds, 3)
        seq = [pat[i % 3] for i in range(6)]
        why = "ABCABC pattern"
    else:
        k = rng.choice(kinds)
        seq = [k] * 2 + [rng.choice([x for x in kinds if x != k])] * 1
        # AAB AAB
        p1, p2 = rng.sample(kinds, 2)
        seq = [p1, p1, p2, p1, p1, p2][:5]
        why = "AABAAB pattern"
    shown = seq[:-1]
    ans_kind = seq[-1]
    shapes = []
    for i, k in enumerate(shown):
        shapes.append(_shape_svg(k, rng.choice(cols), 34, 0, 34 + i * 52, 55))
    visual = _svg(shapes, 320, 110)
    opt_kinds = list(dict.fromkeys([ans_kind] + kinds))[:4]
    rng.shuffle(opt_kinds)
    opts = [_svg([_shape_svg(k, "blue", 40, 0, 55, 55)], 110, 110) for k in opt_kinds]
    correct_svg = _svg([_shape_svg(ans_kind, "blue", 40, 0, 55, 55)], 110, 110)
    # rebuild to match exactly
    opts = []
    for k in opt_kinds:
        s = _svg([_shape_svg(k, "blue", 40, 0, 55, 55)], 110, 110)
        opts.append(s)
    correct = _svg([_shape_svg(ans_kind, "blue", 40, 0, 55, 55)], 110, 110)
    return {"qtype": "pattern", "domain": "fluid",
            "prompt": "Sequence me agla shape kaunsa? " + why.split()[0] + " pattern dekho.",
            "visual": visual, "options": opts, "answer": opts.index(correct),
            "explain": why}

# ---------- 6/7/8. verbal ----------
_ANALOGIES = [
    ("king", "queen", "man", "woman"), ("hot", "cold", "light", "dark"),
    ("book", "read", "pen", "write"), ("bird", "nest", "bee", "hive"),
    ("doctor", "hospital", "teacher", "school"), ("wheel", "car", "wing", "plane"),
    ("hammer", "nail", "key", "lock"), ("fish", "water", "bird", "sky"),
    ("happy", "sad", "up", "down"), ("begin", "end", "morning", "night"),
    ("chef", "kitchen", "pilot", "cockpit"), ("seed", "tree", "egg", "chicken"),
    ("loud", "quiet", "fast", "slow"), ("paint", "brush", "write", "pen"),
    ("cow", "milk", "hen", "egg"), ("sword", "warrior", "pen", "writer"),
]
_SYNONYMS = [
    ("khush", "maghmoom", ["udaas", "khush-haal", "thaka", "bhoka"], 1),
    ("tez", "sust", ["tez-raftar", "gehra", "narm", "thanda"], 0),
    ("aman", "jang", ["sukoon", "shor", "bheer", "andhera"], 0),
    ("ilm", "jahalat", ["danish", "dolat", "taqat", "waqt"], 0),
    ("himmat", "buzdili", ["jurat", "kamzori", "gussa", "neend"], 0),
    ("sach", "jhoot", ["haq", "khwab", "dhoka", "saaya"], 0),
    ("dost", "dushman", ["yaar", "ajnabi", "mehman", "shor"], 0),
    ("roshni", "andhera", ["noor", "saaya", "dhund", "raat"], 0),
    ("mehnat", "susti", ["koshish", "neend", "khel", "baat"], 0),
    ("wafa", "bewafai", ["ehd", "dhoka", "gussa", "nafrat"], 0),
    ("abundant", "scarce", ["plentiful", "empty", "loud", "tiny"], 0),
    ("frugal", "wasteful", ["thrifty", "rich", "tall", "fast"], 0),
    ("candid", "deceptive", ["frank", "shy", "rude", "slow"], 0),
    ("diligent", "lazy", ["hardworking", "sleepy", "rich", "tall"], 0),
    ("vivid", "dull", ["bright", "dark", "soft", "cold"], 0),
]
_WORD_GROUPS = [
    (["apple", "mango", "banana", "grapes"], "car", "car phal nahi"),
    (["red", "blue", "green", "yellow"], "circle", "circle rang nahi"),
    (["dog", "cat", "horse", "cow"], "table", "table janwar nahi"),
    (["pen", "pencil", "eraser", "sharpener"], "book", "book likhne ka aala nahi"),
    (["cricket", "football", "hockey", "tennis"], "chess", "chess outdoor/physical khel nahi"),
    (["january", "march", "july", "october"], "monday", "monday mahina nahi"),
]

def gen_analogy(level, rng):
    a, b, c, d = rng.choice(_ANALOGIES)
    distract = rng.sample(["table", "cloud", "stone", "river", "fire", "moon",
                           "drum", "rope", "leaf", "star"], 3)
    opts = [d] + distract
    rng.shuffle(opts)
    return {"qtype": "analogy", "domain": "verbal",
            "prompt": f"{a} : {b} :: {c} : ?",
            "visual": "", "options": opts, "answer": opts.index(d),
            "explain": f"{a} ka {b} se wahi rishta jo {c} ka {d} se"}

def gen_synonym(level, rng):
    w, _, opts4, ci = rng.choice(_SYNONYMS)
    opts = list(opts4)
    rng.shuffle(opts)
    return {"qtype": "synonym", "domain": "verbal",
            "prompt": f"'{w}' ka hum-mani (synonym) kaunsa hai?",
            "visual": "", "options": opts, "answer": opts.index(opts4[ci]),
            "explain": f"{w} = {opts4[ci]}"}

def gen_odd_word(level, rng):
    good, bad, why = rng.choice(_WORD_GROUPS)
    opts = good + [bad]
    rng.shuffle(opts)
    return {"qtype": "odd_word", "domain": "verbal",
            "prompt": "Kaunsa lafz alag category ka hai?",
            "visual": "", "options": opts, "answer": opts.index(bad),
            "explain": why}

# ---------- 9/10. memory ----------
def gen_digit_span(level, rng):
    length = {1: 4, 2: 5, 3: 6, 4: 7, 5: 8}[level]
    digits = "".join(str(rng.randint(0, 9)) for _ in range(length))
    backward = level >= 3 and rng.random() < 0.5
    return {"qtype": "digit_span", "domain": "memory",
            "prompt": ("Digits ko **ulti tartib** me likho (jaise 582 → 285)."
                       if backward else "Digits ko **usi tartib** me likho."),
            "visual": "", "options": [],
            "answer": digits[::-1] if backward else digits,
            "explain": f"Digits: {digits}", "_digits": digits,
            "_backward": backward, "_input": True}

def gen_nback(level, rng):
    n = 1 if level <= 2 else 2
    length = 8 + level * 2
    letters = [rng.choice("ABCDEFGH") for _ in range(length)]
    # force some matches
    for i in range(n, length):
        if rng.random() < 0.35:
            letters[i] = letters[i - n]
    return {"qtype": "nback", "domain": "memory",
            "prompt": f"Har letter pe batao: kya ye **{n} peeche** wale letter jaisa hai? (haan/naa)",
            "visual": "", "options": [],
            "answer": [letters[i] == letters[i - n] for i in range(length)],
            "_letters": letters, "_n": n, "_input": "nback"}

# ---------- 11/12. speed ----------
_STROOP_COLORS = [("LAAL", "#e74c3c"), ("NEELA", "#3498db"), ("HARA", "#2ecc71"), ("PEELA", "#f1c40f")]

def gen_stroop(level, rng):
    trials = 6 + level * 2
    items = []
    for _ in range(trials):
        word, _ = rng.choice(_STROOP_COLORS)
        _, ink = rng.choice(_STROOP_COLORS)
        while ink == dict(_STROOP_COLORS)[word]:
            _, ink = rng.choice(_STROOP_COLORS)
        items.append({"word": word, "ink": ink,
                      "ink_name": [k for k, v in _STROOP_COLORS if v == ink][0]})
    return {"qtype": "stroop", "domain": "speed",
            "prompt": "Lafz ko NAHI — **ink ka rang** batao (jis rang me likha hai)!",
            "visual": "", "options": ["LAAL", "NEELA", "HARA", "PEELA"],
            "answer": [t["ink_name"] for t in items],
            "_trials": items, "_input": "stroop"}

def gen_symbol_coding(level, rng):
    syms = ["★", "●", "▲", "■", "◆", "✚", "⬟", "⬢"][:4 + level]
    digits = rng.sample(range(1, 10), len(syms))
    key = dict(zip(syms, digits))
    n = 5 + level * 2
    items = [rng.choice(syms) for _ in range(n)]
    return {"qtype": "symbol_coding", "domain": "speed",
            "prompt": "Upar di gayi key se har symbol ka number likho (tartib me, comma se).",
            "visual": "", "options": [],
            "answer": ",".join(str(key[s]) for s in items),
            "_key": {s: key[s] for s in syms}, "_items": items, "_input": True,
            "explain": "Key: " + " ".join(f"{s}={key[s]}" for s in syms)}

# ---------- 13. quant ----------
def gen_arithmetic(level, rng):
    if level == 1:
        a, b = rng.randint(5, 30), rng.randint(5, 30)
        op = rng.choice(["+", "-"])
        ans = a + b if op == "+" else a - b
        if op == "-" and b > a:
            a, b = b, a
            ans = a - b
        q = f"Ahmed ke paas {a} marbles hain, usay {b} aur milte hain. Total kitne?" if op == "+" else \
            f"Dukaan me {a} seb the, {b} bik gaye. Kitne bache?"
    elif level == 2:
        a, b = rng.randint(3, 12), rng.randint(3, 12)
        ans = a * b
        q = f"Ek dabbe me {a} ande hain. Aise {b} dabbon me total kitne ande?"
    elif level == 3:
        price, n = rng.randint(20, 90), rng.randint(2, 6)
        ans = price * n
        q = f"Ek kitab Rs. {price} ki hai. {n} kitabein kitne ki?"
    elif level == 4:
        a = rng.randint(100, 500)
        pct = rng.choice([10, 20, 25, 50])
        ans = a * pct // 100
        q = f"Rs. {a} ka {pct}% kitna hoga?"
    else:
        a, b = rng.randint(8, 20), rng.randint(8, 20)
        ans = (a + b) * 3 - 10
        q = f"Usman ne {a} + {b} ka jama kiya, phir teen guna kiya, phir 10 minus kiye. Jawab?"
    opts = [ans, ans + rng.randint(1, 5), ans - rng.randint(1, 5), ans + rng.randint(6, 15)]
    opts = list(dict.fromkeys(opts))[:4]
    while len(opts) < 4:
        opts.append(ans + rng.randint(16, 30))
    rng.shuffle(opts)
    return {"qtype": "arithmetic", "domain": "quant",
            "prompt": q, "visual": "", "options": [str(o) for o in opts],
            "answer": opts.index(ans), "explain": f"Jawab: {ans}"}

GENERATORS = {
    "number_series": gen_number_series, "matrix": gen_matrix,
    "spatial": gen_spatial, "odd_one_out": gen_odd_one_out,
    "pattern": gen_pattern, "analogy": gen_analogy,
    "synonym": gen_synonym, "odd_word": gen_odd_word,
    "digit_span": gen_digit_span, "nback": gen_nback,
    "stroop": gen_stroop, "symbol_coding": gen_symbol_coding,
    "arithmetic": gen_arithmetic,
}

QTYPE_DOMAIN = {k: v("domain", None) if False else None for k, v in []}
DOMAIN_QTYPES = {
    "fluid": ["number_series", "matrix", "spatial", "odd_one_out", "pattern"],
    "verbal": ["analogy", "synonym", "odd_word"],
    "memory": ["digit_span", "nback"],
    "speed": ["stroop", "symbol_coding"],
    "quant": ["arithmetic", "number_series"],
}

QTYPES_UR = {
    "number_series": "Number Series", "matrix": "Matrix Reasoning",
    "spatial": "Spatial Rotation", "odd_one_out": "Odd One Out",
    "pattern": "Pattern Completion", "analogy": "Verbal Analogy",
    "synonym": "Synonyms", "odd_word": "Odd Word Out",
    "digit_span": "Digit Span", "nback": "N-Back Memory",
    "stroop": "Stroop Test", "symbol_coding": "Symbol Coding",
    "arithmetic": "Arithmetic",
}

def generate(qtype, level, seed=None):
    rng = random.Random(seed if seed is not None else random.randint(0, 10**9))
    q = GENERATORS[qtype](level, rng)
    q["seed"] = seed
    q["level"] = level
    q["qtype_ur"] = QTYPES_UR[qtype]
    return q
