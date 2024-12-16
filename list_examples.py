import glob
import json

result = {}
for fname in glob.glob("*.bake"):
    with open(fname, "rt") as fp:
        top = fp.readline()
        if top.startswith("#"):
            result[fname] = top[1:].strip()
        else:
            result[fname] = fname

with open("examples.json", "wt") as fp:
    json.dump(result, fp, indent=2)
