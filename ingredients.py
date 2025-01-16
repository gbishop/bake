# define the components of some ingredients
Ingredients = {
    # flours
    "ap_flour": {"flour": 1.0},
    "bran": {"flour": 1.0},
    "bread_flour": {"flour": 1.0},
    "bronze_chief": {"flour": 1.0},
    "bulgar": {"flour": 1.0},
    "cracked_rye": {"flour": 1.0},
    "flaxseed_meal": {"flour": 1.0},
    "grain_mix": {"flour": 1.0},
    "hard_red": {"flour": 1.0},
    "hard_white": {"flour": 1.0},
    "improver": {"flour": 1.0},
    "oats": {"flour": 1.0},
    "polenta": {"flour": 1.0},
    "potato_flakes": {"flour": 1.0},
    "prairie_gold": {"flour": 1.0},
    "red_rye_malt": {"flour": 1.0},
    "rye": {"flour": 1.0},
    "spelt": {"flour": 1.0},
    "steel_cut_oats": {"flour": 1.0},
    "vital_wheat_gluten": {"flour": 1.0},
    "vwg": {"flour": 1.0},
    "wgbi": {"flour": 1.0},
    "whole_wheat": {"flour": 1.0},
    "ww": {"flour": 1.0},
    # liquids and fats
    "water": {"water": 1.0},
    "whey": {"water": 1.0},
    "egg": {"water": 0.75, "fat": 0.09},
    "eggs": {"water": 0.75, "fat": 0.09},
    "egg_yolk": {"water": 0.5, "fat": 0.30},
    "egg_yolks": {"water": 0.5, "fat": 0.30},
    "egg_white": {"water": 0.90},
    "egg_whites": {"water": 0.90},
    "milk": {"water": 0.87, "fat": 0.035},
    "evap_milk": {"water": 0.74, "fat": 0.07},
    "buttermilk": {"water": 0.87, "fat": 0.035},
    "nido": {"fat": 0.3},
    "butter": {"water": 0.18, "fat": 0.80},
    "honey": {"water": 0.17},
    "malt_syrup": {"water": 0.2},
    "lemon_juice": {"water": 1.0},
    # oils
    "oil": {"fat": 1.0},
    "olive_oil": {"fat": 1.0},
}

Components = ["flour", "water", "fat"]


def getIngredient(name: str) -> dict[str, float]:
    """Return the components for an ingredient"""
    name = name.lower()
    zero = {"flour": 0, "water": 0, "fat": 0}
    result = zero
    if name in Ingredients:
        result = Ingredients[name]
    if "flour" in name:
        result = {"flour": 1.0}
    if "water" in name:
        result = {"water": 1.0}
    if name.endswith("_oil"):
        result = {"fat": 1.0}
    return {**zero, **result}
