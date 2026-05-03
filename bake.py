from tree import *
from parser import parse
import sys
import argparse
from output import output
from solve import solve
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

argparser = argparse.ArgumentParser(
    prog="bake.py",
    description="From formulas to recipes",
)
argparser.add_argument("filename", nargs="?", default="")
argparser.add_argument("-R", "--rewrite", action="store_true")
argparser.add_argument("--html")
args = argparser.parse_args()
if args.filename:
    fp = open(args.filename, "rt")
else:
    fp = sys.stdin

text = fp.read()

result = parse(text)

# pprint(result)
solution, failed = solve(result)

output(text, solution, errors=failed, tobp=args.rewrite, html=args.html)
