"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from ingredients import getIngredient
from lark import Lark, Visitor, visitors
import lark
import numpy as np
import argparse
import re
import sys
import traceback

# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID ( "^" NUMBER )? ":" (hydration | relation | mention)+

hydration: "hydration" "=" NUMBER

relation: sum "=" sum

sum: product "+" sum   -> add
   | product "-" sum   -> subtract
   | product

product: mention
       | scale "*" mention  -> multiply
       | mention "/" NUMBER -> divide
       | NUMBER -> constant

scale: NUMBER ("*" NUMBER)*

mention: ID
       | ID "." ID

ID: /[a-zA-Z_][a-zA-Z_0-9]*/
NUMBER: /[0-9]+([.][0-9]+)?[g%]?/

WHITESPACE: /[ \n]+/ 
%ignore WHITESPACE

COMMENT:  "/*" /(.|\n|\r)+/ "*/"     
       |  "#" /(.)+\n/ 
%ignore COMMENT
"""


class SymbolTable:
    """Collect information about our unknowns"""

    def __init__(self):
        self.symbol_count = 0
        self.name_to_index = {}
        self.index_to_name = {}
        self.parts = {}
        self.loss = {}

    def add(self, name, value=-1):
        """Add a name if it isn't already known"""
        if name not in self.name_to_index:
            if value >= 0:
                self.name_to_index[name] = value
            else:
                self.name_to_index[name] = self.symbol_count
                self.index_to_name[self.symbol_count] = name
                self.symbol_count += 1
        return self.name_to_index[name]

    def vector(self, name):
        """Create a matrix row representing this unknown"""
        r = np.zeros(self.symbol_count + 1)
        r[self.name_to_index[name]] = 1
        return r

    def dump(self, vector):
        """Make a vector readable"""
        s = ""
        for i in range(self.symbol_count):
            name = ".".join(self.index_to_name[i])
            if vector[i] == 1:
                s += f" + {name}"
            elif vector[i] < 0:
                s += f" - {-vector[i]} * {name}"
            elif vector[i] > 0:
                s += f" + {vector[i]} * {name}"
        if vector[-1] < 0:
            s += f" - {-vector[-1]}"
        elif vector[-1] > 0:
            s += f" + {-vector[-1]}"

        if s.startswith(" + "):
            s = s[3:]
        return s

    def constant(self, value):
        """Create a vector representing a numeric constant"""
        r = np.zeros(self.symbol_count + 1)
        r[-1] = value
        return r


ST = SymbolTable()


def isPercent(s):
    """Test if a string represents a percentage"""
    return s.endswith("%")


def number(s):
    """Get the value of a number based on its units"""
    if s.endswith("%"):
        return float(s[:-1]) / 100
    elif s.endswith("g"):
        return float(s[:-1])
    else:
        return float(s)


class GetParts(Visitor):
    """Scan the tree for part names"""

    def part(self, tree):
        name = tree.children[0] + ""
        ST.add((name, "total"))
        ST.add((name, "total_flour"))
        ST.add((name, "total_water"))
        ST.add((name, "total_fat"))

        ST.parts[name] = None


class GetUnknowns(Visitor):
    """Scan the tree for names of unknowns"""

    def mention(self, tree):
        if len(tree.children) == 1:
            name = tree.children[0] + ""
            fullname = (self.part_name, name)
            if name in ST.parts:
                ST.add(fullname, ST.add((name, "total")))
            else:
                ST.add(fullname)

    def part(self, tree):
        self.part_name = tree.children[0] + ""


class BuildMatrix(visitors.Interpreter):
    """Setup the matrix representing the relations"""

    def start(self, tree):
        r = self.visit_children(tree)
        residuals = []
        for relations in r:
            for lhs, rhs in relations:
                residuals.append(lhs - rhs)
        R = np.array(residuals)
        A = R[:, :-1]
        B = -R[:, -1]
        return A, B

    def part(self, tree):
        total_names = ["total", "total_flour", "total_water", "total_fat"]
        part = self.part_name = tree.children[0]
        r = self.visit_children(tree)
        _, theloss, *relations = r
        if len(theloss) == 1:
            ST.loss[part] = (number(theloss[0]), isPercent(theloss[0]))
        # we only want the relations which are lists
        relations = [row for row in relations if type(row) == list]
        totals = {}
        for total_name in total_names:
            totals[total_name] = np.zeros(ST.symbol_count + 1)
        for fullname in ST.name_to_index:
            if fullname[0] != part:
                continue
            if fullname[1].startswith("total"):
                continue
            if fullname[1] in ST.parts:
                for total_name in total_names:
                    totals[total_name] += ST.vector((fullname[1], total_name))
            else:
                vect = ST.vector(fullname)
                totals["total"] += vect
                info = getIngredient(fullname[1])
                for total_name in total_names[1:]:
                    field_name = total_name.replace("total_", "")
                    w = info[field_name]
                    totals[total_name] += w * vect
        for total_name in total_names:
            relations.append([ST.vector((part, total_name)), totals[total_name]])

        return relations

    def hydration(self, tree):
        r = self.visit_children(tree)
        v = number(r[0])
        return [
            ST.vector((self.part_name, "total_water")),
            v * ST.vector((self.part_name, "total_flour")),
        ]

    def add(self, tree):
        r = self.visit_children(tree)
        return r[0] + r[1]

    def subtract(self, tree):
        r = self.visit_children(tree)
        return r[0] - r[1]

    def multiply(self, tree):
        r = self.visit_children(tree)
        return r[0] * r[1]

    def divide(self, tree):
        r = self.visit_children(tree)
        return r[0] / r[1]

    def constant(self, tree):
        r = self.visit_children(tree)
        value = number(r[0])
        if isPercent(r[0]):
            return ST.vector(("dough", "total_flour")) * value
        else:
            return ST.constant(value)

    def scale(self, tree):
        r = self.visit_children(tree)
        result = number(r[0])
        for n in r[1:]:
            result *= number(n)
        return result

    def mention(self, tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            fullname = (self.part_name, r[0])
        else:
            fullname = tuple(r)
        return ST.vector(fullname)

    def __default__(self, tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            return r[0]
        else:
            return r


def format_table(solution):
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

    # reshape the data into a list of lists
    rows = []
    grame_to_bp = 100 / solution[("dough", "total_flour")]
    for partName in ST.parts:
        loss_value, isPercent = ST.loss.get(partName, (0, False))
        gt = g = solution[(partName, "total")]
        if isPercent:
            loss_value = loss_value * gt
        loss_scale = (gt + loss_value) / gt
        bp = g * grame_to_bp
        # add the ingredients from the part
        for pn, var in solution:
            if pn != partName:
                continue
            if not var.startswith("total") and not var.startswith("_"):
                pg = solution[(partName, var)]
                if var in ST.parts:
                    extras = [
                        solution[(var, "total_flour")],
                        solution[(var, "total_water")],
                        solution[(var, "total_fat")],
                    ]
                else:
                    info = getIngredient(var)
                    extras = [
                        pg * info["flour"],
                        pg * info["water"],
                        pg * info["fat"],
                    ]
                rows.append(
                    [
                        "",
                        pg * loss_scale,
                        var.replace("_", " "),
                        pg * grame_to_bp,
                        *extras,
                    ]
                )
        # add the total
        rows.append(
            [
                partName,
                g * loss_scale,
                f"+ {loss_value:.1f}g" if loss_value > 0 else "",
                bp,
                solution[(partName, "total_flour")],
                solution[(partName, "total_water")],
                solution[(partName, "total_fat")],
            ]
        )
        # add a blank line
        rows.append([""])

    heading = ["part", "grams", "name", "%", "flour", "water", "fat"]
    return tabulate(heading, "tgt%ggg", rows)


def output(table, text, failed=False, tobp=False):
    """Insert the table into the input"""
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text)
    if tobp:
        text = rewrite(text, solution[("dough", "total_flour")])

    if failed:
        table = re.sub(r"^", "E ", table, 0, re.M)
    result = f"{text}/*+\n{table}+*/\n"
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

parser = Lark(grammar)

try:
    tree = parser.parse(text)
except lark.exceptions.UnexpectedToken as error:
    print(f"Unexpected token {error.line}:{error.column}\n", error.get_context(text))
    sys.exit(1)
except lark.exceptions.UnexpectedCharacters as error:
    print(
        f"Unexpected character {error.line}:{error.column}\n", error.get_context(text)
    )
    sys.exit(1)
except lark.exceptions.UnexpectedEOF as error:
    print(
        f"Unexpected end of file {error.line}:{error.column}\n", error.get_context(text)
    )
    sys.exit(1)

GetParts().visit(tree)

GetUnknowns().visit_topdown(tree)

try:
    A, B = BuildMatrix().visit(tree)
except Exception:
    traceback.print_exc(limit=-2)
    sys.exit(1)

r = np.linalg.lstsq(A, B, rcond=-1)

X = r[0]

residuals = A.dot(X) - B
error = np.sqrt(np.max(residuals**2))

failed = error > 1

solution = {name: X[index] for name, index in ST.name_to_index.items()}

table = format_table(solution)

output(table, text, failed, args.rewrite)
