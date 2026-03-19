"""
personalization.py
------------------
Generates personalised health warnings based on:
  - Diabetic status
  - User-declared allergies
  - Detected harmful ingredients
"""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data.json")
with open(_DATA_PATH, "r") as f:
    _DATA = json.load(f)

DIABETIC_TRIGGERS = [i.lower() for i in _DATA["diabetic_warnings"]]
ALLERGEN_MAP      = {k: [i.lower() for i in v]
                     for k, v in _DATA["common_allergens"].items()}


def _ingredient_names(classified: list[dict]) -> list[str]:
    return [item["name"].lower() for item in classified]


def _matches_any(ingredient: str, trigger_list: list[str]) -> bool:
    """Check if ingredient string contains or closely matches any trigger."""
    for trigger in trigger_list:
        if trigger in ingredient or ingredient in trigger:
            return True
    return False


def check_diabetic_warnings(classified: list[dict]) -> list[str]:
    """
    Returns a list of warning strings for ingredients that affect blood sugar.
    """
    warnings = []
    for item in _ingredient_names(classified):
        if _matches_any(item, DIABETIC_TRIGGERS):
            warnings.append(
                f"⚠️ '{item.title()}' may raise blood sugar levels — "
                "diabetic individuals should consume with caution."
            )
    return warnings


def check_allergy_warnings(classified: list[dict], user_allergies: list[str]) -> list[str]:
    """
    Cross-references user's declared allergies with ingredient list.

    user_allergies: list of allergy names, e.g. ["gluten", "nuts", "dairy"]
    """
    warnings = []
    ingredient_names = _ingredient_names(classified)
    user_allergies_lower = [a.lower().strip() for a in user_allergies]

    for allergy in user_allergies_lower:
        triggers = ALLERGEN_MAP.get(allergy, [allergy])  # fallback: treat allergy name as trigger
        found = []
        for ing in ingredient_names:
            if _matches_any(ing, triggers):
                found.append(ing.title())
        if found:
            warnings.append(
                f"🚨 ALLERGY ALERT ({allergy.upper()}): "
                f"Contains {', '.join(found)} — avoid if allergic!"
            )

    return warnings


def check_harmful_ingredients(classified: list[dict]) -> list[str]:
    """Return warnings for every ingredient flagged as harmful."""
    warnings = []
    for item in classified:
        if item["category"] == "harmful":
            warnings.append(
                f"☠️ '{item['name'].title()}' is classified as harmful "
                "and is linked to health risks."
            )
    return warnings


def get_general_advice(health_score: dict) -> str:
    """Return a general advice string based on the normalised score."""
    score = health_score.get("normalised", 50)
    if score >= 80:
        return "✅ This product looks generally safe. Enjoy in moderation."
    elif score >= 60:
        return "🟡 This product is acceptable but has some ingredients to watch. Check warnings above."
    elif score >= 40:
        return "🟠 Consume this product cautiously. Several moderate-risk ingredients present."
    else:
        return "🔴 This product contains multiple harmful ingredients. Consider healthier alternatives."


def personalise(
    classified: list[dict],
    health_score: dict,
    is_diabetic: bool,
    user_allergies: list[str],
) -> dict:
    """
    Master personalisation function.

    Returns:
        dict with:
            diabetic_warnings  (list[str])
            allergy_warnings   (list[str])
            harmful_warnings   (list[str])
            general_advice     (str)
            total_warnings     (int)
    """
    diabetic_warnings = check_diabetic_warnings(classified) if is_diabetic else []
    allergy_warnings  = check_allergy_warnings(classified, user_allergies)
    harmful_warnings  = check_harmful_ingredients(classified)
    general_advice    = get_general_advice(health_score)

    return {
        "diabetic_warnings": diabetic_warnings,
        "allergy_warnings":  allergy_warnings,
        "harmful_warnings":  harmful_warnings,
        "general_advice":    general_advice,
        "total_warnings":    len(diabetic_warnings) + len(allergy_warnings) + len(harmful_warnings),
    }
