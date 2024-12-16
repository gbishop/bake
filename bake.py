"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from solver import solve
import argparse
import re
import sys


def format_table(rows, heading):
    """Build a table from the solution"""

    def fmt_grams(g):
        """Format grams in the table"""
        if round(g, 0) >= 100:
            r = f"{g:.0f}   "
        elif round(g, 1) >= 10:
            r = f"{g:0.1f} "
        elif abs(g) < 0.1:
            r = ""
        else:
            r = f"{g:0.2f}"

        return r

    def fmt_value(value, format):
        """Format a value based on the format code"""
        if format == "%":
            return f"{value:6.1f}"
        elif format == "g":
            return fmt_grams(value)
        else:
            return str(value)

    def tabulate(headings, fmts, rows):
        """Format a list of lists as a table"""
        widths = [len(h) for h in headings]
        rows = [[fmt_value(col, fmts[i]) for i, col in enumerate(row)] for row in rows]
        for row in rows:
            for i, col in enumerate(row):
                widths[i] = max(widths[i], len(col))
        result = [
            " | ".join([h.center(widths[i]) for i, h in enumerate(headings)]) + " |"
        ]
        for row in rows:
            cols = []
            for i, col in enumerate(row):
                if fmts[i] == "t":
                    cols.append(f"{col:<{widths[i]}}")
                else:
                    cols.append(f"{col:>{widths[i]}}")
            line = " | ".join(cols)
            if len(row) > 1:
                line += " |"
            result.append(line)
        return "\n".join(result) + "\n"

    return tabulate(heading, "tgt%ggg", rows)


def output(table, text, message="", grams_to_bp=0):
    """Insert the table into the input"""
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text).strip()
    if grams_to_bp and not message:
        text = rewrite(text, grams_to_bp)

    if message:
        table = re.sub(r"^", "E ", table, 0, re.M) + f"\n***** {message} *****\n"
    result = f"{text}\n\n/*+\n{table}+*/\n"
    print(result)


def rewrite(rest, scale):
    """Rewrite grams as baker's percent"""

    def gtobp(match):
        if match.group(1) not in [
            "total_flour",
            "total_water",
            "total_fat",
            "total",
        ]:
            f = float(match.group(3)[:-1]) * scale
            return f"{match.group(1)}{match.group(2)}{f:.2f}%"
        else:
            return match.group(0)

    return re.sub(r"(\w+)(\s*=\s*)([\d.]+\s*g)", gtobp, rest)


argparser = argparse.ArgumentParser(
    prog="bake.py",
    description="From formulas to recipes",
)
argparser.add_argument("filename", nargs="?", default="")
argparser.add_argument("-R", "--rewrite", action="store_true")
args = argparser.parse_args()
if args.filename:
    fp = open(args.filename, "rt")
else:
    fp = sys.stdin

text = fp.read()

result = solve(text)
if result["error"] == "Syntax Error":
    print(result["message"])
    sys.exit(1)

heading = ["part", "grams", "name", "%", "flour", "water", "fat"]

table = format_table(result["rows"], heading)

output(table, text, result["message"], args.rewrite)
