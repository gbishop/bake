import pandas as pd
import numpy as np
import sys
import traceback
import os


def lean_traceback(exc_type, exc_value, exc_traceback):
    print(f"{exc_type.__name__}: {exc_value}\n")

    # Get all frames in the traceback
    frames = traceback.extract_tb(exc_traceback)

    for frame in frames:
        if "site-packages" not in frame.filename and "lib/python" not in frame.filename:
            print(f"File: {os.path.basename(frame.filename)}, line {frame.lineno}")
            print(f"  Code: {frame.line}")
            print(f"  Function: {frame.name}\n")


# This overrides the default behavior
sys.excepthook = lean_traceback


# load the usda data
usda = pd.read_csv("usda.csv", index_col="name").fillna(0)
usda_index = [key.lower() for key in usda.index]
# remove units from the column names
usda.columns = [name.replace(" (g)", "") for name in usda.columns]
unknown = pd.Series(0, index=usda.columns)
usda.loc["unknown"] = unknown
usda = usda.rename(columns={"carbohydrate": "carbs"})

# Extract the specific columns from the USDA database
nutrients = usda[["protein", "fiber", "carbs", "fat"]] / 100

# load my old mapped data
mapped = pd.read_csv("mapped.csv", index_col="index")

# merge with nutrients
result = mapped.merge(nutrients, left_on="usda", right_index=True, how="left")


enhanced = pd.read_csv("enhanced-ingredients.csv", index_col="index")

result = result.join(enhanced["water"])

cc = [*nutrients]

old_common = result.loc[result.index.isin(enhanced.index)][cc]
new_common = enhanced.loc[enhanced.index.isin(result.index)][cc]

close = np.isclose(old_common, new_common, rtol=0.0, atol=0.01).all(axis=1)

old_diff = old_common.iloc[~close]
new_diff = new_common.iloc[~close]

diff = old_diff.join(new_diff, rsuffix="_")
