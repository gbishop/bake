import argparse
import os
import sys
import traceback
from pathlib import Path
import re

from models import getRelations, formatRelations
from solve import solveRelations


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

argparser = argparse.ArgumentParser(
    prog="bake.py",
    description="From formulas to recipes",
)
argparser.add_argument("filename", nargs="?", default="")
argparser.add_argument("-i", "--inplace", action="store_true")
argparser.add_argument("-q", "--quiet", action="store_true")
argparser.add_argument("-R", "--rewrite", action="store_true")
args = argparser.parse_args()

if args.filename:
    text = Path(args.filename).resolve().read_text()
else:
    text = sys.stdin.read()
    if not isinstance(text, str):
        exit(1)

text = text.strip()

# remove the grid at the bottom
match = re.search(r"/\*\+|┌", text)
if match:
    text = text[0 : match.start()]

# remove any old error messages
text = re.sub("⚠.*\n", "", text)

relations = getRelations(text)
relations = solveRelations(relations, args.rewrite)
table = formatRelations(relations)

text = text.strip() + "\n\n" + table

if args.inplace and args.filename:
    Path(args.filename).resolve().write_text(text)

elif not args.quiet:
    print(text)
