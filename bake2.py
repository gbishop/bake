"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from lark import Lark, Tree, visitors
import lark
import numpy as np
import argparse
import sys
from ingredients import getIngredient
import re


def P(*args):
    """Print on stderr for debugging"""
    print(*args, file=sys.stderr)


# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID [ "^" loss ] ":" (hydration | relation | variable)+

?loss: NUMBER
     | NUMBER "%" -> scaled_loss

hydration: "hydration" "=" NUMBER "%"

relation: sum "=" sum

?sum: product "+" sum   -> add
    | product "-" sum   -> subtract
    | product

bp: NUMBER "%"

?product: bp
        | term
        | term "*" product -> multiply
        | term "/" product -> divide

?term: variable
     | reference
     | NUMBER
     | NUMBER "%" -> percent
     | "(" sum ")"

variable: ID
reference: ID "." ID

ID: /[a-zA-Z_][a-zA-Z_0-9]*/
NUMBER: /-?[0-9]+([.][0-9]+)?g?/

WHITESPACE: /[ \n]+/ 
%ignore WHITESPACE

COMMENT:  "/*" /(.|\n|\r)*?/ "*/"     
       |  "#" /(.)+\n/ 
%ignore COMMENT
"""

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
except Exception as e:
    P("failed")
    raise (e)


Variables = {}
Parts = {str(node.children[0]): 0.0 for node in tree.find_data("part")}


@visitors.v_args(inline=True)
class Prepare(visitors.Transformer):

    def variable(self, name: str):
        return U("", name)

    def reference(self, partname, name):
        return Tree("reference", [(partname, name)])

    def bp(self, value):
        return Tree("multiply", [value / 100.0, self.reference("dough", "total_flour")])

    def percent(self, value):
        return value / 100.0

    def NUMBER(self, value):
        if value.endswith("g"):
            return float(value[:-1])
        else:
            return float(value)

    def ID(self, value):
        return str(value)

    def hydration(self, value):
        return Tree(
            "relation",
            [
                U("", "total_water"),
                Tree("multiply", [value / 100.0, U("", "total_flour")]),
            ],
        )

    def part(self, partname, loss, *rest):
        if loss is None:
            loss = 0

        relations = [r for r in rest if isinstance(r, Tree) and r.data == "relation"]

        # qualify the variables with their partname
        vnames = set()
        for r in rest:
            vars = r.find_data("unknown")
            for var in vars:
                name = var.children[0][1]
                fullname = (partname, name)
                vnames.add(fullname)
                var.children[0] = fullname
                if fullname not in Variables:
                    Variables[fullname] = None
                if name in Parts:
                    relations.append(Tree("relation", [U(*fullname), U(name, "total")]))

        tosum = [
            name
            for name in vnames
            if not name[1].startswith("total") and not name[1].startswith("_")
        ]
        for fullname, func in [
            ("total", total),
            ("total_water", water),
            ("total_flour", flour),
        ]:
            tname = (partname, fullname)
            Variables[tname] = None
            sum = func(tosum[0])
            for var in tosum[1:]:
                sum = Tree("add", [func(var), sum])
            relations.append(Tree("relation", [Tree("unknown", [tname]), sum]))
        Parts[partname] = loss
        return Tree("part", [partname, loss, *relations])


def flour(name):
    n = name[1]
    if n in Parts:
        return U(n, "total_flour")
    else:
        info = getIngredient(n)
        return Tree("multiply", [info["flour"] / 100, U(*name)])


def water(name):
    n = name[1]
    if n in Parts:
        return U(n, "total_water")
    else:
        info = getIngredient(n)
        return Tree("multiply", [info["water"] / 100, U(*name)])


def total(name):
    n = name[1]
    if n in Parts:
        return U(n, "total")
    else:
        return U(*name)


def U(part, name):
    return Tree("unknown", [(part, name)])


@visitors.v_args(tree=True)
class Propagate(visitors.Transformer):
    updates = 0

    def unknown(self, tree):
        value = Variables[tree.children[0]]
        if value is None:
            return tree
        else:
            self.updates += 1
            return value

    def reference(self, tree):
        value = Variables[tree.children[0]]
        if value is None:
            return tree
        else:
            self.updates += 1
            return value

    def relation(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, Tree) and lhs.data == "unknown":
            lname = lhs.children[0]
            assert isinstance(lname, tuple)
            lvalue = Variables[lname]
            if lvalue is None:
                if isinstance(rhs, float):
                    Variables[lname] = rhs
                    self.updates += 1
                    return visitors.Discard
        elif isinstance(rhs, Tree) and rhs.data == "unknown":
            rname = rhs.children[0]
            assert isinstance(rname, tuple)
            rvalue = Variables[rname]
            if rvalue is None:
                if isinstance(lhs, float):
                    Variables[rname] = lhs
                    self.updates += 1
                    return visitors.Discard
        elif isinstance(lhs, float) and isinstance(rhs, float):
            return visitors.Discard
        return tree

    def multiply(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, float):
            if lhs == 0:
                self.updates += 1
                return 0.0
            elif lhs == 1:
                self.updates += 1
                return rhs
            if isinstance(rhs, float):
                if rhs == 0:
                    self.updates += 1
                    return 0.0
                elif rhs == 1:
                    self.updates += 1
                    return lhs
                self.updates += 1
                return lhs * rhs
        if isinstance(rhs, float):
            if rhs == 0:
                self.updates += 1
                return 0
            elif rhs == 1:
                return lhs

        return tree

    def divide(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, float):
            if lhs == 0:
                self.updates += 1
                return 0.0
            if isinstance(rhs, float):
                self.updates += 1
                return lhs / rhs
        if isinstance(rhs, float):
            if rhs == 1:
                return lhs

        return tree

    def add(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, float):
            if lhs == 0:
                self.updates += 1
                return rhs
            if isinstance(rhs, float):
                if rhs == 0:
                    self.updates += 1
                    return lhs
                self.updates += 1
                return lhs + rhs
        if isinstance(rhs, float) and rhs == 0:
            return lhs
        return tree

    def subtract(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, float):
            if isinstance(rhs, float):
                if rhs == 0:
                    self.updates += 1
                    return lhs
                self.updates += 1
                return lhs - rhs
        if isinstance(rhs, float) and rhs == 0:
            return lhs
        return tree


t = Prepare().transform(tree)

for i in range(10):
    e = Propagate()
    t = e.transform(t)
    if e.updates == 0:
        break

Index = {}
count = 0
# add the unknowns to the Index
for name, value in Variables.items():
    if value is not None:
        continue
    if name[1] not in Parts:
        Index[name] = count
        count += 1
# link the part references to the total
for name, value in Variables.items():
    if value is not None:
        continue
    if name[1] in Parts:
        Index[name] = Index[(name[1], "total")]

relations = list(t.find_data("relation"))

columns = len(Index) + 1


def onehot(index, value=1.0):
    r = np.zeros(columns)
    r[index] = value
    return r


def Vector(value):
    if isinstance(value, (float, int)):
        return onehot(columns - 1, value)
    elif isinstance(value, tuple):
        return onehot(Index[value])
    else:
        return value


class Vectorize(visitors.Transformer):

    def unknown(self, args):
        return Vector(args[0])

    def add(self, args):
        lhs, rhs = [Vector(arg) for arg in args]
        return lhs + rhs

    def multiply(self, args):
        lhs, rhs = args
        if isinstance(lhs, (float, int)):
            return lhs * rhs
        elif isinstance(rhs, (float, int)):
            return lhs * rhs
        assert False

    def relation(self, args):
        lhs, rhs = [Vector(arg) for arg in args]
        return rhs - lhs


M = np.array([Vectorize().transform(relation) for relation in relations])

A = M[:, :-1]
B = -M[:, -1]

r = np.linalg.lstsq(A, B, rcond=-1)
X = r[0]
residuals = A.dot(X) - B
error = np.sqrt(np.max(residuals**2))
failed = error > 1

for name, index in Index.items():
    Variables[name] = X[index]


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
    for partName in Parts:
        gt = g = solution[(partName, "total")]
        loss = Parts[partName]
        if isinstance(loss, Tree) and loss.data == "scaled_loss":
            assert isinstance(loss.children[0], float)
            loss = loss.children[0] / 100 * gt
        loss_scale = (gt + loss) / gt
        bp = g * grams_to_bp
        # add the total
        rows.append(
            [
                partName.replace("_", " "),
                g * loss_scale,
                f"+ {loss:.1f}g" if loss > 0 else "",
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
                unknown = ""
                if var in Parts:
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
                    if info.name == "unknown":
                        unknown = "!"
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
        text = rewrite(text, 100 / Variables[("dough", "total_flour")])

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


table, nutrition = format_table(Variables)

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
