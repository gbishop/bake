"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from ingredients import getIngredient
from lark import Lark, Visitor, Tree, Token, visitors
import lark
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Dict, List
import argparse
import re
import sys

# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID [ "^" NUMBER ] ":" (hydration | relation | mention)+

hydration: "hydration" "=" NUMBER

relation: sum "=" sum

sum: product "+" sum   -> add
   | product "-" sum   -> subtract
   | product

product: term -> constant
       | term "*" product -> multiply
       | product "/" NUMBER -> divide

term: mention
    | NUMBER
    | "(" sum ")"

mention: ID
       | ID "." ID

ID: /[a-zA-Z_][a-zA-Z_0-9]*/
NUMBER: /-?[0-9]+([.][0-9]+)?[g%]?/

WHITESPACE: /[ \n]+/ 
%ignore WHITESPACE

COMMENT:  "/*" /(.|\n|\r)*?/ "*/"     
       |  "#" /(.)+\n/ 
%ignore COMMENT
"""

Fullname = tuple[str, str]
Array = NDArray[np.float64]


class SymbolTableEntry:
    """Information about each symbol"""

    def __init__(self, name=("", ""), index=-1, part=False):
        self.name: Fullname = name
        self.index: int = index
        self.part: bool = part
        self.nutrition = getIngredient(name[1])
        self.unknown = not part and self.nutrition.name == "unknown"


class SymbolTable:
    """Collect information about our unknowns"""

    def __init__(self):
        self.symbol_count: int = 0
        self.entries: dict[Fullname, SymbolTableEntry] = {}
        self.byIndex: dict[int, SymbolTableEntry] = {}
        # don't use a set because I need this ordered
        self.parts: dict[str, None] = {}
        self.loss: dict[str, tuple[float, bool]] = {}

    def __getitem__(self, key: int | Fullname):
        if isinstance(key, int):
            return self.byIndex[key]

        elif isinstance(key, tuple):
            return self.entries[key]

    def __iter__(self):
        return iter(self.entries)

    def items(self):
        return self.entries.items()

    def add(self, name: Fullname):
        """Add a name if it isn't already known"""
        if name not in self.entries:
            if name[1] in self.parts:
                self.entries[name] = SymbolTableEntry(
                    name, index=self.entries[(name[1], "total")].index, part=True
                )
            else:
                self.entries[name] = SymbolTableEntry(name, self.symbol_count)
                self.byIndex[self.symbol_count] = self.entries[name]
                self.symbol_count += 1

    def vector(self, name: Fullname):
        """Create a matrix row representing this unknown"""
        r = np.zeros(self.symbol_count + 1)
        r[self.entries[name].index] = 1
        return r

    def dump(self, vector: Array):
        """Make a vector readable"""
        s = ""
        for i in range(self.symbol_count):
            name = ".".join(self.byIndex[i].name)
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

    def constant(self, value: float):
        """Create a vector representing a numeric constant"""
        r = np.zeros(self.symbol_count + 1)
        r[-1] = value
        return r


ST = SymbolTable()


def isPercent(s: str):
    """Test if a string represents a percentage"""
    return s.endswith("%")


def number(s: str):
    """Get the value of a number based on its units"""
    if s.endswith("%"):
        return float(s[:-1]) / 100
    elif s.endswith("g"):
        return float(s[:-1])
    else:
        return float(s)


def token(t):
    """Verify argument is a token and return it as a string"""
    assert isinstance(t, Token)
    return str(t)


class GetParts(Visitor):
    """Scan the tree for part names"""

    def part(self, tree: Tree):
        name = token(tree.children[0])
        ST.add((name, "total"))
        ST.add((name, "total_flour"))
        ST.add((name, "total_water"))

        ST.parts[name] = None


class GetUnknowns(Visitor):
    """Scan the tree for names of unknowns"""

    def mention(self, tree: Tree):
        if len(tree.children) == 1:
            name = token(tree.children[0])
            fullname = (self.part_name, name)
            ST.add(fullname)

    def part(self, tree: Tree):
        self.part_name = token(tree.children[0])


class BuildMatrix(visitors.Interpreter):
    """Setup the matrix representing the relations"""

    def start(self, tree: Tree) -> Tuple[Array, Array]:
        r = self.visit_children(tree)
        residuals = []
        for relations in r:
            for lhs, rhs in relations:
                residuals.append(lhs - rhs)
        R = np.array(residuals)
        A = R[:, :-1]
        B = -R[:, -1]
        return A, B

    def part(self, tree: Tree):
        total_names = ["total", "total_flour", "total_water"]
        part = self.part_name = token(tree.children[0])
        r = self.visit_children(tree)
        theloss = r[1]
        if theloss:
            ST.loss[part] = (number(theloss), isPercent(theloss))
        # we only want the children that are lists
        relations: List[List[Array]] = [
            row for row in r[2:] if isinstance(row, list) and len(row) == 2
        ]
        totals: Dict[str, Array] = {}
        for total_name in total_names:
            totals[total_name] = np.zeros(ST.symbol_count + 1)
        for fullname, entry in ST.items():
            if fullname[0] != part:
                continue
            if fullname[1].startswith("total"):
                continue
            if fullname[1].startswith("_"):
                continue
            if entry.part:
                for total_name in total_names:
                    totals[total_name] += ST.vector((fullname[1], total_name))
            else:
                vect = ST.vector(fullname)
                totals["total"] += vect
                info = entry.nutrition
                for total_name in total_names[1:]:
                    field_name = total_name.replace("total_", "")
                    w = info[field_name] / 100
                    totals[total_name] += w * vect
        for total_name in total_names:
            relations.append([ST.vector((part, total_name)), totals[total_name]])

        return relations

    def hydration(self, tree: Tree):
        r = self.visit_children(tree)
        v = number(r[0])
        return [
            ST.vector((self.part_name, "total_water")),
            v * ST.vector((self.part_name, "total_flour")),
        ]

    def add(self, tree: Tree):
        r = self.visit_children(tree)
        return r[0] + r[1]

    def subtract(self, tree: Tree):
        r = self.visit_children(tree)
        return r[0] - r[1]

    def multiply(self, tree: Tree):
        r = self.visit_children(tree)
        if isinstance(r[0], Token):
            return number(r[0]) * r[1]
        elif isinstance(r[1], Token):
            value = number(r[1])
            if isPercent(r[1]):
                raise Exception(f"Cannot multiply unknowns on line {tree.meta.line}")
            return r[0] * value
        else:
            raise Exception(f"Cannot multiply unknowns on line {tree.meta.line}")

    def divide(self, tree: Tree):
        r = self.visit_children(tree)
        if isinstance(r[1], Token):
            return r[0] / number(r[1])
        else:
            raise Exception(f"Only divide by numbers on line {tree.meta.line}")

    def constant(self, tree: Tree):
        r = self.visit_children(tree)
        if isinstance(r[0], Token):
            value = number(r[0])
            if isPercent(r[0]):
                return ST.vector(("dough", "total_flour")) * value
            else:
                return ST.constant(value)
        else:
            return r[0]

    def mention(self, tree: Tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            fullname = (self.part_name, r[0])
        else:
            fullname = tuple(r)
        return ST.vector(fullname)

    def __default__(self, tree: Tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            return r[0]
        else:
            return r


def format_table(solution):
    """Build a table from the solution"""

    def fmt_grams(g, threshold=0.1):
        """Format grams in the table"""
        if round(g, 0) >= 100:
            r = f"{g:.0f}   "
        elif round(g, 1) >= 1:
            r = f"{g:0.1f} "
        elif abs(g) < threshold:
            r = ""
        else:
            r = f"{g:0.2f}"

        return r

    def fmt_value(value, format, threshold=0.1):
        """Format a value based on the format code"""
        if format == "%":
            return f"{value:5.1f}"
        elif format == "g":
            return fmt_grams(value, threshold)
        else:
            return str(value)

    def tabulate(headings, fmts, rows, threshold=0.1):
        """Format a list of lists as a table"""
        widths = [len(h) for h in headings]
        rows = [
            [fmt_value(col, fmts[i], threshold) for i, col in enumerate(row)]
            for row in rows
        ]
        for row in rows:
            for i, col in enumerate(row):
                widths[i] = max(widths[i], len(col))
        # headings
        result = [
            " | ".join([h.center(widths[i]) for i, h in enumerate(headings)]) + " |",
            "-|-".join(["-" * widths[i] for i in range(len(headings))]) + "-|",
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
    dtf = solution[("dough", "total_flour")]
    if dtf == 0:
        raise Exception("No flour")
    grams_to_bp = 100 / solution[("dough", "total_flour")]
    nutrition = getIngredient("unknown")
    for partName in ST.parts:
        loss_value, isPercent = ST.loss.get(partName, (0, False))
        gt = g = solution[(partName, "total")]
        if isPercent:
            loss_value = loss_value * gt
        loss_scale = (gt + loss_value) / gt
        bp = g * grams_to_bp
        # add the total
        rows.append(
            [
                partName.replace("_", " "),
                g * loss_scale,
                f"+ {loss_value:.1f}g" if loss_value > 0 else "",
                bp,
                solution[(partName, "total_flour")],
                solution[(partName, "total_water")],
            ]
        )
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
                    ]
                else:
                    info = getIngredient(var)
                    extras = [
                        pg * info["flour"] / 100,
                        pg * info["water"] / 100,
                    ]
                    nutrition = nutrition + info * pg / 100
                unknown = "!" if ST[(partName, var)].unknown else ""
                rows.append(
                    [
                        "",
                        pg * loss_scale,
                        var.replace("_", " ") + unknown,
                        pg * grams_to_bp,
                        *extras,
                    ]
                )
        # add hydration for the final dough
        if partName == "dough":
            rows.append(
                [
                    "",
                    0,
                    "hydration",
                    solution[("dough", "total_water")] * grams_to_bp,
                    0,
                    0,
                ]
            )
        # add a blank line
        rows.append([""])

    nrows = []
    # account for 9% loss during baking
    fdw = solution[("dough", "total")] * 0.91
    serving = solution.get(("dough", "_serving"), 100)
    if serving > 1:
        nscale = serving / fdw
        for key in sorted(nutrition.index):
            if key == "water" or key == "flour":
                continue
            v = nutrition.loc[key] * nscale
            if key == "true_water":
                key = "water"
                v *= 0.91
            if v > 0.01:
                nrows.append((key, v))
        nut = tabulate(["name", f"per {serving:.0f}g"], "tg", nrows, threshold=0.01)
        nut = "Nutrition\n" + nut + 2 * "\n"
    else:
        nut = ""

    heading = ["part", "grams", "name", "%", "flour", "water"]
    recipe = tabulate(heading, "tgt%ggg", rows)
    return recipe, nut


def output(table, text, failed=False, tobp=False):
    """Insert the table into the input"""
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text)
    if tobp:
        text = rewrite(text, 100 / solution[("dough", "total_flour")])

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
argparser.add_argument("--html")
args = argparser.parse_args()
if args.filename:
    fp = open(args.filename, "rt")
else:
    fp = sys.stdin

text = fp.read()

parser = Lark(grammar, propagate_positions=True)

try:
    tree = parser.parse(text)
except lark.exceptions.UnexpectedToken as e:
    print(f"Unexpected token {e.line}:{e.column}\n", e.get_context(text))
    sys.exit(1)
except lark.exceptions.UnexpectedCharacters as e:
    print(f"Unexpected character {e.line}:{e.column}\n", e.get_context(text))
    sys.exit(1)
except lark.exceptions.UnexpectedEOF as e:
    print(f"Unexpected end of file {e.line}:{e.column}\n", e.get_context(text))
    sys.exit(1)
except AssertionError as e:
    raise (e)

GetParts().visit(tree)

GetUnknowns().visit_topdown(tree)

try:
    A, B = BuildMatrix().start(tree)
except AssertionError as e:
    raise e
except Exception as e:
    print("exception", e)
    sys.exit(1)

r = np.linalg.lstsq(A, B, rcond=-1)

X = r[0]

residuals: Array = A.dot(X) - B

error: float = np.sqrt(np.max(residuals**2))

failed = error > 1

solution: Dict[Fullname, float] = {name: X[entry.index] for name, entry in ST.items()}

table, nutrition = format_table(solution)

output(nutrition + table, text, failed, args.rewrite)

if args.html:
    with open(args.html, "wt") as fp:
        print("<table><tbody>", file=fp)
        td = "th"
        for line in table.split("\n"):
            if "---" in line:
                continue
            line = re.sub(r"\| *$", "", line)
            line = line.replace("|", f"</{td}><{td}>")
            line = f"<tr><{td}>" + line + f"</{td}></tr>"
            line = line.replace(" ", "&numsp;")
            print(line, file=fp)
            td = "td"
        print("</tbody></table>", file=fp)
