import pandas as pd
import os

dir = os.path.dirname(os.path.abspath(__file__))
csv = os.path.join(dir, "ingredients.csv")

Ingredients = pd.read_csv(csv, index_col="index").fillna(0) / 100


def getIngredient(name: str):
    """Return the components for an ingredient"""
    name = name.lower()
    if name in Ingredients.index:
        result = Ingredients.loc[name]
    elif "flour" in name:
        result = Ingredients.loc["ap_flour"]
    elif "water" in name:
        result = Ingredients.loc["water"]
    elif name.endswith("_oil"):
        result = Ingredients.loc["oil"]
    else:
        result = Ingredients.loc["other"]

    return result
