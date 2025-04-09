import pandas as pd
import numpy as np
import os
import re
import sys
import readline

pd.options.mode.copy_on_write = True

dir = os.path.dirname(os.path.abspath(__file__))
usda_path = os.path.join(dir, "usda.csv")
map_path = os.path.join(dir, "ingredients.csv")

# map my short names to their long names and a flour indicator
map = pd.read_csv(map_path, index_col="index")

# load the usda database
usda = pd.read_csv(usda_path, index_col="name").fillna(0)

# remove units from the column names
usda.columns = [name.replace(" (g)", "") for name in usda.columns]
# trim unneeded columns
usda = usda.loc[:, usda.columns[1:-1]] / 100.0

# add a row for unknown ingredients
unknown = pd.Series(0, index=usda.columns)
usda.loc["unknown"] = unknown


def score(name, positive, negative):
    words = set(re.split(r"\W+", name.lower()))
    return len(words & positive) - len(words & negative)


def searchUSDA(query, prompt):
    readline.add_history(query)
    while True:
        query = str(query)
        query = query.replace("_", " ")
        terms = set(query.split())
        negative = set(term[1:] for term in terms if term.startswith("-"))
        positive = terms - negative
        scores = np.array([score(name, positive, negative) for name in usda.index])
        best = scores.argsort()[-1:-30:-1]
        best = best[scores[best] > 0]
        choices = usda.index[best]
        for i, choice in enumerate(choices):
            print(i, choice)
        try:
            resp = input(f"{prompt}? ")
        except EOFError:
            return None
        try:
            n = int(resp)
            if n == -1:
                return ""
            elif n == -2:
                return None
            elif n >= 0 and n < len(choices):
                return choices[n]
        except ValueError:
            pass
        query = resp


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        r = searchUSDA(query, query)
        print(r)
        print(usda.loc[r])

    else:
        # update the ingredients.csv file
        for index, row in map[map.usda.isna()].iterrows():
            name = str(index)
            r = searchUSDA(name, name)
            if name:
                map.loc[index, "usda"] = r
                map.to_csv(map_path)
            elif name is None:
                break


def getIngredient(name: str) -> pd.Series:
    """Return the components for an ingredient"""
    name = name.lower()
    if name not in map.index:
        if "water" in name:
            name = "water"

        elif name.endswith("_oil"):
            name = "oil"

        else:
            name = "unknown"
    m = map.loc[name]
    u = usda.loc[m.usda]
    if name == "water":
        u.loc["water"] = 1.0
    u.loc["flour"] = m.loc["flour"]
    result = u
    # pretend flour has no water because hydration calculations assume it doesn't
    result.loc["true_water"] = result.loc["water"]
    if result.loc["flour"]:
        result.loc["water"] = 0
    return result
