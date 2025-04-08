"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from lark import Lark, Tree, visitors, UnexpectedInput
import numpy as np
import argparse
import sys
from ingredients import getIngredient
from output import output


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


@visitors.v_args(inline=True)
class Prepare(visitors.Transformer):
    @staticmethod
    def U(part, name):
        return Tree("unknown", [(part, name)])

    def variable(self, name: str):
        return self.U("", name)

    def reference(self, partname, name):
        return self.U(partname, name)

    def bp(self, value):
        return Tree("multiply", [value / 100.0, self.U("dough", "total_flour")])

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
                self.U("", "total_water"),
                Tree("multiply", [value / 100.0, self.U("", "total_flour")]),
            ],
        )

    def part(self, partname, loss, *rest):
        if loss is None:
            loss = 0.0

        relations = [r for r in rest if isinstance(r, Tree) and r.data == "relation"]

        # qualify the variables with their partname
        vnames = set()
        for r in rest:
            vars = r.find_data("unknown")
            for var in vars:
                if var.children[0][0]:
                    continue
                name = var.children[0][1]
                fullname = (partname, name)
                vnames.add(fullname)
                var.children[0] = fullname
                if fullname not in Variables:
                    Variables[fullname] = None
                if name in Parts:
                    relations.append(
                        Tree("relation", [self.U(*fullname), self.U(name, "total")])
                    )
        # variables contributing to the totals
        tosum = [
            name
            for name in vnames
            if not name[1].startswith("total") and not name[1].startswith("_")
        ]

        def summand(name: tuple, which: str):
            """Access the total, flour, water for an unknown"""
            n = name[1]
            if n in Parts:
                return self.U(n, which)
            elif which == "total":
                return self.U(*name)
            else:
                kind = which.replace("total_", "")
                nutrition = getIngredient(n)
                return Tree("multiply", [nutrition[kind] / 100, self.U(*name)])

        # establish the total relations
        for which in ["total", "total_water", "total_flour"]:
            fullname = (partname, which)
            Variables[fullname] = None
            sum = summand(tosum[0], which)
            for var in tosum[1:]:
                sum = Tree("add", [summand(var, which), sum])
            relations.append(Tree("relation", [self.U(*fullname), sum]))
        # add a relation for the loss
        if isinstance(loss, Tree):
            assert isinstance(loss.children[0], float)
            loss = Tree("multiply", [loss.children[0] / 100, self.U(partname, "total")])
        Variables[(partname, "_loss")] = None
        relations.append(Tree("relation", [self.U(partname, "_loss"), loss]))
        return Tree("part", [partname, loss, *relations])


class Propagate:
    updates = 0

    def wrapper(self, obj, data, children, meta):
        """Inline parameters, copy if method returns nothing, count updates"""
        raw = obj(*children)
        # the the method returns nothing, return the tree
        if raw is None:
            return Tree(data, children, meta)
        # It updated something, increment updates
        self.updates += 1
        # if it returns a Tree augment it with meta
        if isinstance(raw, Tree):
            return Tree(raw.data, raw.children, meta)
        # otherwise return the raw result
        return raw

    def transform(self, tree):
        # apply my wrapper to the transformer
        @visitors.v_args(wrapper=self.wrapper)
        class PropagateTransformer(visitors.Transformer):
            def unknown(self, name):
                value = Variables[name]
                if value is not None:
                    return value

            def relation(self, lhs, rhs):
                if isinstance(lhs, Tree) and lhs.data == "unknown":
                    lname = lhs.children[0]
                    assert isinstance(lname, tuple)
                    lvalue = Variables[lname]
                    if lvalue is None:
                        if isinstance(rhs, float):
                            Variables[lname] = rhs
                            return visitors.Discard
                elif isinstance(rhs, Tree) and rhs.data == "unknown":
                    rname = rhs.children[0]
                    assert isinstance(rname, tuple)
                    rvalue = Variables[rname]
                    if rvalue is None:
                        if isinstance(lhs, float):
                            Variables[rname] = lhs
                            return visitors.Discard
                elif isinstance(lhs, float) and isinstance(rhs, float):
                    return visitors.Discard

            def multiply(self, lhs, rhs):
                if isinstance(lhs, float):
                    if lhs == 0:
                        return 0.0
                    elif lhs == 1:
                        return rhs
                    if isinstance(rhs, float):
                        if rhs == 0:
                            return 0.0
                        elif rhs == 1:
                            return lhs
                        return lhs * rhs
                if isinstance(rhs, float):
                    if rhs == 0:
                        return 0
                    elif rhs == 1:
                        return lhs

            def divide(self, lhs, rhs):
                if isinstance(lhs, float):
                    if lhs == 0:
                        return 0.0
                    if isinstance(rhs, float):
                        return lhs / rhs
                if isinstance(rhs, float):
                    if rhs == 1:
                        return lhs
                    return Tree("multiply", [1.0 / rhs, lhs])

            def add(self, lhs, rhs):
                if isinstance(lhs, float):
                    if lhs == 0:
                        return rhs
                    if isinstance(rhs, float):
                        if rhs == 0:
                            return lhs
                        return lhs + rhs
                if isinstance(rhs, float) and rhs == 0:
                    return lhs

            def subtract(self, lhs, rhs):
                if isinstance(lhs, float):
                    if isinstance(rhs, float):
                        if rhs == 0:
                            return lhs
                        return lhs - rhs
                if isinstance(rhs, float) and rhs == 0:
                    return lhs

        PT = PropagateTransformer()
        while True:
            self.updates = 0
            tree = PT.transform(tree)
            if self.updates == 0:
                break
        return tree


class BuildMatrix(visitors.Transformer):

    def __init__(self, columns):
        self.columns = columns

    def vector(self, value):
        def onehot(index, value=1.0):
            r = np.zeros(self.columns)
            r[index] = value
            return r

        if isinstance(value, (float, int)):
            return onehot(self.columns - 1, value)
        elif isinstance(value, tuple):
            return onehot(Index[value])
        else:
            return value

    def unknown(self, args):
        return self.vector(args[0])

    def add(self, args):
        lhs, rhs = [self.vector(arg) for arg in args]
        return lhs + rhs

    def subtract(self, args):
        lhs, rhs = [self.vector(arg) for arg in args]
        return lhs - rhs

    def multiply(self, args):
        lhs, rhs = args
        if isinstance(lhs, (float, int)):
            return lhs * rhs
        elif isinstance(rhs, (float, int)):
            return lhs * rhs
        assert False

    @visitors.v_args(meta=True)
    def divide(self, meta, _):
        print(
            f"Division of unknowns is not supported on line {meta.line} column {meta.column}"
        )
        sys.exit(1)

    def relation(self, args):
        lhs, rhs = [self.vector(arg) for arg in args]
        return rhs - lhs

    def part(self, args):
        return args[2:]  # all the relations

    def start(self, args):
        # join the lists of relations then convert to array
        M = np.array([vector for part in args for vector in part])
        return M[:, :-1], -M[:, -1]

    def __default__(self, *args):
        return args[2][0]


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
except UnexpectedInput as e:
    print(e, e.get_context(text))
    sys.exit(1)

# Collect the variables with their values
Variables = {}
# Ordered set of Part names
Parts = {str(node.children[0]): None for node in tree.find_data("part")}

# process the tree to collect variables and parts
tree = Prepare().transform(tree)
# propagate constants
tree = Propagate().transform(tree)

# map unknowns to columns in the matrix
Index = {}
unknowns = 0
# add the unknowns to the Index
for name, value in Variables.items():
    if value is not None:
        continue
    if name[1] not in Parts:
        Index[name] = unknowns
        unknowns += 1
# link the part references to the total
for name, value in Variables.items():
    if value is not None:
        continue
    if name[1] in Parts:
        Index[name] = Index[(name[1], "total")]

# P("unknowns", unknowns, "variables", len(Variables))
# P(Index.keys())

failed = False
if unknowns > 0:
    # setup the equations
    A, B = BuildMatrix(unknowns + 1).transform(tree)
    # solve
    r = np.linalg.lstsq(A, B, rcond=-1)
    X = r[0]
    residuals = A.dot(X) - B
    error = np.sqrt(np.max(residuals**2))
    failed = error > 1
    # copy solution back to the unknowns
    for name, index in Index.items():
        Variables[name] = X[index]
# print the table
output(text, Variables, Parts, failed, args.rewrite, args.html)
