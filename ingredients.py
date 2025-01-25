import pandas as pd

pd.options.mode.copy_on_write = True
import os
from thefuzz import process, fuzz
import re
import sys
import readline


dir = os.path.dirname(os.path.abspath(__file__))
usda_path = os.path.join(dir, "usda.csv")
map_path = os.path.join(dir, "ingredients.csv")

# map my short names to their long names and a flour indicator
map = pd.read_csv(map_path, index_col="index")

# load the usda database
usda = pd.read_csv(usda_path, index_col="name").fillna(0)
usda_index = [key.lower() for key in usda.index]
# remove units from the column names
usda.columns = [name.replace(" (g)", "") for name in usda.columns]
# trim unneeded columns
usda = usda.loc[:, usda.columns[1:-1]]
# ann a row for unknown ingredients
unknown = pd.Series(0, index=usda.columns)
usda.loc["unknown"] = unknown


def searchUSDA(query, prompt):
    readline.add_history(query)
    while True:
        query = str(query)
        query = query.replace("_", " ")
        terms = query.split()
        negative = [term for term in terms if term.startswith("-")]
        positive = [term for term in terms if term not in negative]
        search = " ".join(positive)
        choices = process.extract(
            search,
            usda_index,
            scorer=fuzz.partial_token_sort_ratio,
            limit=40,
        )
        if negative:
            pruned = []
            for choice, score in choices:
                words = re.findall(r"\w+", choice.lower())
                for neg in negative:
                    if neg[1:] in words:
                        break
                else:
                    pruned.append((choice, score))
            choices = pruned
        for i, choice in enumerate(choices):
            print(i, choice)
        resp = input(f"{prompt}? ")
        try:
            n = int(resp)
            if n == -1:
                return ""
            elif n == -2:
                return None
            elif n >= 0 and n < len(choices) - 1:
                return choices[n][0]
        except ValueError:
            pass
        query = resp


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        r = searchUSDA(query, query)
        print(r)

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


def getIngredient(name: str):
    """Return the components for an ingredient"""
    name = name.lower()
    if name not in map.index:
        if "water" in name:
            name = "water"

        elif name.endswith("_oil"):
            name = "oil"

        else:
            if name != "unknown":
                print("unknown", name)
            name = "unknown"
    m = map.loc[name]
    u = usda.loc[m.usda]
    u.loc["flour"] = m.loc["flour"]
    result = u
    # pretend flour has no water because hydration calculations assume
    # it doesn't
    result.loc["true_water"] = result.loc["water"]
    if result.loc["flour"]:
        result.loc["water"] = 0
    return result
