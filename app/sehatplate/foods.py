"""SehatPlate food database — curated South Asian foods, per 100 g.

Provenance rule: every row carries a `src` tag.
- "usda": USDA FoodData Central / SR Legacy per-100g values (standard published values).
- "recipe": documented recipe decomposition (ingredients x typical proportions),
  computed in DATA_NOTES.md in the repo — an honest estimate, labeled as such in the UI.

No row is invented: if a value isn't USDA-published or decomposable from one,
it doesn't ship.
"""

# (name, kcal, protein_g, carbs_g, fat_g, src, note)
FOODS = [
    # ---- staples: breads & rice ----
    ("White rice (cooked)", 130, 2.7, 28.2, 0.3, "usda", "ubla chawal"),
    ("Brown rice (cooked)", 111, 2.6, 23.0, 0.9, "usda", ""),
    ("Whole wheat flour (atta)", 340, 13.2, 72.0, 2.5, "usda", ""),
    ("Roti / chapati (no oil)", 297, 8.0, 50.0, 7.4, "recipe", "1 roti ~40g ~120 kcal"),
    ("Paratha (with oil)", 350, 8.5, 45.0, 15.0, "recipe", ""),
    ("Naan", 310, 9.0, 56.0, 5.1, "recipe", ""),
    ("Puri (fried)", 340, 8.0, 48.0, 13.0, "recipe", ""),
    ("Kulcha / bun", 290, 8.0, 55.0, 4.0, "recipe", ""),
    ("White bread", 265, 9.0, 49.0, 3.2, "usda", ""),
    ("Rusk", 380, 9.0, 70.0, 8.0, "recipe", ""),
    # ---- pulses & legumes (cooked) ----
    ("Masoor dal (red lentils, cooked)", 116, 9.0, 20.1, 0.4, "usda", ""),
    ("Moong dal (cooked)", 105, 7.0, 19.2, 0.4, "usda", ""),
    ("Safed chana / chickpeas (cooked)", 164, 9.0, 27.4, 2.6, "usda", ""),
    ("Kala chana (cooked)", 160, 9.5, 27.0, 2.5, "recipe", ""),
    ("Rajma / kidney beans (cooked)", 127, 8.9, 22.8, 0.5, "usda", ""),
    ("Lobiya / black-eyed peas (cooked)", 116, 7.7, 20.3, 0.5, "usda", ""),
    ("Mash dal / urad (cooked)", 115, 8.0, 20.0, 0.5, "recipe", ""),
    # ---- desi dishes (recipe decomposition) ----
    ("Chicken biryani", 150, 9.0, 20.0, 5.0, "recipe", ""),
    ("Beef biryani", 170, 10.0, 20.0, 6.0, "recipe", ""),
    ("Chicken pulao", 145, 8.0, 21.0, 4.0, "recipe", ""),
    ("Chicken karahi", 180, 14.0, 4.0, 12.0, "recipe", "oil-heavy; ask for kam tel"),
    ("Chicken curry / salan", 140, 12.0, 5.0, 8.0, "recipe", ""),
    ("Daal fry / tarka", 120, 7.0, 15.0, 4.0, "recipe", ""),
    ("Daal (plain boiled)", 105, 8.0, 18.0, 1.0, "recipe", ""),
    ("Nihari (beef)", 200, 14.0, 6.0, 13.0, "recipe", "slow-cooked shank, rich gravy"),
    ("Haleem", 150, 10.0, 16.0, 5.5, "recipe", ""),
    ("Paye (trotters)", 220, 15.0, 3.0, 16.0, "recipe", "very fatty"),
    ("Keema (beef mince curry)", 190, 14.0, 5.0, 13.0, "recipe", ""),
    ("Aloo gosht", 150, 9.0, 10.0, 8.0, "recipe", ""),
    ("Palak gosht", 130, 10.0, 6.0, 7.0, "recipe", ""),
    ("Palak paneer", 120, 6.0, 5.0, 9.0, "recipe", ""),
    ("Aloo palak", 90, 3.0, 12.0, 4.0, "recipe", ""),
    ("Bhindi (okra) sabzi", 80, 2.5, 10.0, 4.0, "recipe", ""),
    ("Baingan sabzi", 85, 2.0, 11.0, 4.5, "recipe", ""),
    ("Aloo ki tarkari", 95, 2.5, 14.0, 3.5, "recipe", ""),
    ("Mix sabzi", 75, 2.5, 10.0, 3.0, "recipe", ""),
    ("Daal chawal (mixed)", 135, 6.5, 23.0, 2.0, "recipe", ""),
    ("Khichdi", 120, 5.0, 22.0, 2.0, "recipe", ""),
    ("Chana chaat", 130, 6.0, 22.0, 2.5, "recipe", ""),
    ("Dahi bhalla", 110, 5.0, 16.0, 3.0, "recipe", ""),
    # ---- fried snacks & kebabs ----
    ("Samosa", 260, 5.0, 30.0, 13.0, "recipe", "deep-fried"),
    ("Pakora", 280, 7.0, 22.0, 18.0, "recipe", "deep-fried"),
    ("Kachori", 300, 6.0, 35.0, 15.0, "recipe", "deep-fried"),
    ("Shami kebab", 220, 14.0, 12.0, 12.0, "recipe", "shallow-fried patty"),
    ("Seekh kebab", 210, 16.0, 3.0, 15.0, "recipe", ""),
    ("Chicken tikka", 165, 22.0, 2.0, 8.0, "recipe", "grilled — lean pick"),
    ("Chicken malai boti", 190, 18.0, 3.0, 12.0, "recipe", "cream"),
    ("Fish fry", 200, 18.0, 8.0, 10.0, "recipe", ""),
    ("Omelette (2 eggs + oil)", 200, 12.0, 2.0, 15.0, "recipe", ""),
    # ---- sweets ----
    ("Suji halwa", 350, 5.0, 55.0, 12.0, "recipe", "ghee + sugar"),
    ("Kheer", 140, 4.0, 22.0, 4.0, "recipe", ""),
    ("Gulab jamun", 300, 4.0, 55.0, 8.0, "recipe", "syrup-soaked"),
    ("Jalebi", 350, 2.0, 75.0, 5.0, "recipe", ""),
    ("Rasmalai", 180, 6.0, 25.0, 6.0, "recipe", ""),
    ("Barfi (milk)", 400, 8.0, 60.0, 14.0, "recipe", ""),
    ("Besan ladoo", 420, 8.0, 55.0, 20.0, "recipe", "ghee-heavy"),
    ("Gur / jaggery", 380, 0.5, 98.0, 0.2, "usda", ""),
    ("Honey", 304, 0.3, 82.0, 0.0, "usda", ""),
    ("Sugar", 387, 0.0, 100.0, 0.0, "usda", ""),
    # ---- dairy, fats, drinks ----
    ("Milk (whole)", 62, 3.2, 4.8, 3.3, "usda", "per 100 ml"),
    ("Milk (skim)", 34, 3.4, 5.0, 0.1, "usda", "per 100 ml"),
    ("Dahi / yogurt (whole)", 62, 3.5, 4.7, 3.3, "usda", ""),
    ("Lassi (sweet)", 90, 3.0, 15.0, 2.0, "recipe", "per 100 ml"),
    ("Lassi (salty)", 55, 3.2, 5.5, 2.0, "recipe", "per 100 ml"),
    ("Chai (doodh patti + sugar)", 60, 2.5, 9.0, 1.5, "recipe", "per 100 ml; 1 cup ~150 ml"),
    ("Ghee", 900, 0.0, 0.0, 100.0, "usda", "1 tsp ~5 g ~45 kcal"),
    ("Butter", 717, 0.9, 0.1, 81.0, "usda", ""),
    ("Cooking oil", 884, 0.0, 0.0, 100.0, "usda", ""),
    ("Paneer", 265, 18.0, 3.5, 20.0, "recipe", ""),
    # ---- proteins ----
    ("Chicken breast (roasted)", 165, 31.0, 0.0, 3.6, "usda", "leanest pick"),
    ("Chicken leg / thigh (cooked)", 200, 26.0, 0.0, 10.0, "usda", ""),
    ("Beef (lean, cooked)", 182, 29.0, 0.0, 8.4, "usda", ""),
    ("Mutton / lamb (cooked)", 294, 25.0, 0.0, 21.0, "usda", "fatty"),
    ("Fish — rohu (cooked)", 130, 20.0, 0.0, 5.0, "recipe", ""),
    ("Egg (boiled)", 155, 12.6, 1.1, 10.6, "usda", "1 egg ~50 g ~78 kcal"),
    ("Egg (fried)", 200, 13.0, 1.5, 16.0, "recipe", ""),
    # ---- fruits ----
    ("Banana", 89, 1.1, 22.8, 0.3, "usda", "1 medium ~120 g"),
    ("Apple", 52, 0.3, 13.8, 0.2, "usda", ""),
    ("Orange", 47, 0.9, 11.8, 0.1, "usda", ""),
    ("Mango", 60, 0.8, 15.0, 0.4, "usda", ""),
    ("Grapes", 69, 0.7, 18.1, 0.2, "usda", ""),
    ("Watermelon", 30, 0.6, 7.6, 0.2, "usda", ""),
    ("Papaya", 43, 0.5, 10.8, 0.3, "usda", ""),
    ("Guava", 68, 2.6, 14.3, 1.0, "usda", ""),
    ("Dates (khajoor)", 282, 2.5, 75.0, 0.4, "usda", "1 date ~8 g ~23 kcal"),
    ("Lemon", 29, 1.1, 9.3, 0.3, "usda", ""),
    # ---- vegetables ----
    ("Potato (boiled)", 78, 2.9, 17.2, 0.1, "usda", ""),
    ("Onion", 40, 1.1, 9.3, 0.1, "usda", ""),
    ("Tomato", 18, 0.9, 3.9, 0.2, "usda", ""),
    ("Spinach (cooked)", 23, 2.9, 3.6, 0.4, "usda", ""),
    ("Cauliflower", 25, 1.9, 5.0, 0.3, "usda", ""),
    ("Cabbage", 25, 1.3, 5.8, 0.1, "usda", ""),
    ("Carrot", 41, 0.9, 9.6, 0.2, "usda", ""),
    ("Peas (matar)", 81, 5.4, 14.5, 0.4, "usda", ""),
    ("Cucumber", 15, 0.7, 3.6, 0.1, "usda", ""),
]


def to_dicts():
    return [
        {"id": i, "name": n, "kcal": k, "protein": p, "carbs": c, "fat": f,
         "src": s, "note": note}
        for i, (n, k, p, c, f, s, note) in enumerate(FOODS)
    ]


def search(q, limit=20):
    q = (q or "").strip().lower()
    if not q:
        return to_dicts()[:limit]
    scored = []
    for d in to_dicts():
        name = d["name"].lower()
        note = d["note"].lower()
        if name.startswith(q):
            scored.append((0, d))
        elif q in name:
            scored.append((1, d))
        elif q in note:
            scored.append((2, d))
    scored.sort(key=lambda t: t[0])
    return [d for _, d in scored[:limit]]


def scale(food, grams):
    """Scale a food dict to `grams`; returns rounded macro dict."""
    f = grams / 100.0
    return {
        "name": food["name"],
        "grams": round(grams, 1),
        "kcal": round(food["kcal"] * f, 1),
        "protein": round(food["protein"] * f, 1),
        "carbs": round(food["carbs"] * f, 1),
        "fat": round(food["fat"] * f, 1),
        "src": food["src"],
    }
