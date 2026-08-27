import argparse
import os
import sys
import traceback

from output import output
from parser import parse
from solve import solve
from tree import *
from convert import convert


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
argparser.add_argument("-R", "--rewrite", action="store_true")
argparser.add_argument("--html")
argparser.add_argument("-q", "--quiet", action="store_true")
argparser.add_argument("-a", "--allcolumns", action="store_true")
argparser.add_argument("-d", "--debug", action="store_true")
argparser.add_argument("-c", "--convert", action="store_true")
args = argparser.parse_args()

with open(args.filename, "rt", encoding="utf-8") if args.filename else sys.stdin as fp:
    text = fp.read()
    tree = parse(text)
    solution, failed = solve(tree, args.debug)

    if args.convert and not failed:
        try:
            convert(args.filename, text, tree, solution)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)

    elif not args.quiet:
        output(
            text,
            solution,
            filename=args.filename,
            inplace=args.inplace,
            errors=failed,
            tobp=args.rewrite,
            html=args.html,
            allcolumns=args.allcolumns,
        )
