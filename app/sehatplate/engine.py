"""SehatPlate nutrition math: BMR (Mifflin-St Jeor), TDEE, targets, BMI.

Formulas (all standard, published):
- Mifflin-St Jeor (1990), validated against indirect calorimetry:
    male:   BMR = 10*w + 6.25*h - 5*a + 5
    female: BMR = 10*w + 6.25*h - 5*a - 161
  (w = kg, h = cm, a = years)
- TDEE = BMR x activity factor (FAO/WHO PAL bands):
    sedentary 1.20 | light 1.375 | moderate 1.55 | active 1.725 | athlete 1.90
- Goal adjustment: lose -500 kcal/d (~0.5 kg/week), maintain 0, gain +300.
- Protein: 1.6 g/kg body weight (ISSN position stand range 1.4-2.0 for active adults;
  we use 1.6 as the middle, shown to the user).
- Fat: 25% of target kcal / 9. Carbs: remainder / 4.
- BMI = kg / m^2 with WHO bands.
"""

ACTIVITY = {
    "sedentary": (1.20, "Sedentary (desk job, little exercise)"),
    "light": (1.375, "Light (1-3 days/week)"),
    "moderate": (1.55, "Moderate (3-5 days/week)"),
    "active": (1.725, "Active (6-7 days/week)"),
    "athlete": (1.90, "Athlete (2x/day training)"),
}

GOALS = {
    "lose": (-500, "Lose weight (~0.5 kg/week)"),
    "maintain": (0, "Maintain weight"),
    "gain": (300, "Gain weight (lean)"),
}


def bmr_mifflin(weight_kg, height_cm, age, sex):
    sex = (sex or "").lower()
    b = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return b + 5 if sex.startswith("m") else b - 161


def bmi(weight_kg, height_cm):
    m = height_cm / 100.0
    v = weight_kg / (m * m)
    if v < 18.5:
        band = "Underweight"
    elif v < 25:
        band = "Healthy"
    elif v < 30:
        band = "Overweight"
    else:
        band = "Obese"
    return round(v, 1), band


def targets(weight_kg, height_cm, age, sex, activity="moderate", goal="maintain"):
    bmr = bmr_mifflin(weight_kg, height_cm, age, sex)
    factor = ACTIVITY.get(activity, ACTIVITY["moderate"])[0]
    tdee = bmr * factor
    adj = GOALS.get(goal, GOALS["maintain"])[0]
    kcal = max(1200, round(tdee + adj))  # safety floor, shown honestly
    protein = round(1.6 * weight_kg)
    fat = round(0.25 * kcal / 9)
    carbs = round((kcal - protein * 4 - fat * 9) / 4)
    bmi_v, bmi_band = bmi(weight_kg, height_cm)
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "kcal": kcal,
        "protein_g": protein,
        "fat_g": fat,
        "carbs_g": carbs,
        "bmi": bmi_v,
        "bmi_band": bmi_band,
        "water_ml": round(weight_kg * 35),  # ~35 ml/kg, standard guidance
    }
