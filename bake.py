"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July 2024 April 2025
"""

from lark import Lark, Tree, visitors, UnexpectedInput
import numpy as np
import argparse
import sys
from ingredients import getIngredient
from output import output
from typing import Any


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

?sum: sum "+" product -> add
    | sum "-" product -> subtract
    | product

product: term (/[*\/]/ term)*

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

# Collect the variables with their values
Variables = {}
Parts = {}


def U(part, name, scale=None):
    """Add an unknown possibly scaled"""
    r = Tree("unknown", [(part, name)])
    if scale is not None:
        r = Tree("multiply", [scale, r])
    return r


def isF(value):
    """Test if the value is a float"""
    return isinstance(value, (float, int))


def isT(value, data=""):
    """Test if the value is a Tree"""
    return isinstance(value, Tree) and (not data or value.data == data)


@visitors.v_args(inline=True)
class Prepare(visitors.Transformer):
    """First pass after parsing"""

    def variable(self, name):
        return U("", name)

    def reference(self, partname, name):
        return U(partname, name)

    def bp(self, value):
        return U("dough", "total_flour", value / 100.0)

    def product(self, *args):
        args = list(args)
        # if the last term is a percent convert it to bakkers percent
        if isT(args[-1], "percent"):
            args[-1] = Tree(
                "multiply", [args[-1].children[0] / 100.0, U("dough", "total_flour")]
            )
        result = args[0]
        for i in range(1, len(args), 2):
            if args[i] == "*":
                result = Tree("multiply", [result, args[i + 1]])
            else:
                result = Tree("divide", [result, args[i + 1]])
        return result

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
            [U("", "total_water"), U("", "total_flour", value / 100.0)],
        )

    def part(self, partname, loss: Any, *rest):
        relations = [r for r in rest if isT(r, "relation")]

        # qualify the variables with their partname
        tosum = set()
        for children in rest:
            unknowns = children.find_data("unknown")
            for unknown in unknowns:
                if unknown.children[0][0]:
                    continue
                name = unknown.children[0][1]
                fullname = (partname, name)
                unknown.children[0] = fullname
                if not (name.startswith("total") or name.startswith("_")):
                    tosum.add(fullname)
                if fullname not in Variables:
                    Variables[fullname] = None
                if name in Parts:
                    relations.append(Tree("relation", [U(*fullname), U(name, "total")]))

        # establish the total relations
        for which in ["total", "total_water", "total_flour"]:
            fullname = (partname, which)
            Variables[fullname] = None
            sum: Any = 0.0
            for name in tosum:
                if name[1] in Parts:
                    addin = U(name[1], which)
                elif which == "total":
                    addin = U(*name)
                else:
                    kind = which.replace("total_", "")
                    nutrition = getIngredient(name[1])
                    addin = U(name[0], name[1], nutrition[kind])
                sum = Tree("add", [addin, sum])
            relations.append(Tree("relation", [U(*fullname), sum]))
        # add a relation for the loss
        if isT(loss):
            loss = U(partname, "total", loss.children[0] / 100.0)
        elif loss is None:
            loss = 0.0
        loss_name = (partname, "_loss")
        Variables[loss_name] = None
        relations.append(Tree("relation", [U(*loss_name), loss]))
        return Tree("part", [*relations])


class Propagate_manager:
    """Automagically track updates while propagating constants"""

    updates = 0
    first_time = True

    def wrapper(self, obj, data, children, meta):
        """Inline parameters, copy if method returns nothing, count updates"""
        raw = obj(*children)
        # the the method returns nothing, return the tree
        if raw is None:
            return Tree(data, children, meta)
        # It updated something, increment updates
        self.updates += 1
        # if it returns a Tree augment it with meta
        if isT(raw):
            return Tree(raw.data, raw.children, meta)
        # otherwise return the raw result
        return raw

    @property
    def updated(self):
        """Allow testing if the propagation has converged"""
        result = self.first_time or self.updates != 0
        self.updates = 0
        self.first_time = False
        return result


# this will be wrapped by the Propagate_manager
class Propagate(visitors.Transformer):

    def unknown(self, name):
        value = Variables[name]
        if value is not None:
            return value

    def relation(self, lhs, rhs):
        if isF(rhs) and isT(lhs, "unknown"):
            lname = lhs.children[0]
            lvalue = Variables[lname]
            if lvalue is None:
                Variables[lname] = rhs
                return visitors.Discard
        elif isF(lhs) and isT(rhs, "unknown"):
            rname = rhs.children[0]
            rvalue = Variables[rname]
            if rvalue is None:
                Variables[rname] = lhs
                return visitors.Discard
        elif isF(lhs) and isF(rhs):
            return visitors.Discard

    def percent(self, value):
        return value / 100.0

    def multiply(self, lhs, rhs):
        if isF(lhs):
            if lhs == 0.0:
                return 0.0
            elif lhs == 1.0:
                return rhs
            if isF(rhs):
                if rhs == 0.0:
                    return 0.0
                elif rhs == 1.0:
                    return lhs
                return lhs * rhs
        if isF(rhs):
            if rhs == 0.0:
                return 0.0
            elif rhs == 1.0:
                return lhs

    def divide(self, lhs, rhs):
        if isF(lhs):
            if lhs == 0.0:
                return 0.0
            if isF(rhs):
                return lhs / rhs
        if isF(rhs):
            if rhs == 1.0:
                return lhs
            return Tree("multiply", [1.0 / rhs, lhs])

    def add(self, lhs, rhs):
        if isF(lhs):
            if lhs == 0.0:
                return rhs
            if isF(rhs):
                if rhs == 0.0:
                    return lhs
                return lhs + rhs
        if isF(rhs) and rhs == 0.0:
            return lhs

    def subtract(self, lhs, rhs):
        if isF(lhs):
            if isF(rhs):
                if rhs == 0.0:
                    return lhs
                return lhs - rhs
        if isF(rhs) and rhs == 0.0:
            return lhs


@visitors.v_args(inline=True)
class BuildMatrix(visitors.Transformer):
    """Convert the remaining relations into matrix equations"""

    def __init__(self, columns):
        self.columns = columns

    def vector(self, value):
        def onehot(index, value=1.0):
            r = np.zeros(self.columns)
            r[index] = value
            return r

        if isF(value):
            return onehot(self.columns - 1, value)
        elif isinstance(value, tuple):
            return onehot(Index[value])
        else:
            return value

    def unknown(self, name):
        return self.vector(name)

    def add(self, lhs, rhs):
        return self.vector(lhs) + self.vector(rhs)

    def subtract(self, lhs, rhs):
        return self.vector(lhs) - self.vector(rhs)

    @visitors.v_args(inline=True, meta=True)
    def multiply(self, meta, lhs, rhs):
        if isF(lhs):
            return lhs * rhs
        elif isF(rhs):
            return lhs * rhs
        print(f"Multiplication of unknowns is not supported {meta.line}:{meta.column}")
        sys.exit(1)

    @visitors.v_args(inline=True, meta=True)
    def divide(self, meta, _):
        print(f"Division of unknowns is not supported {meta.line}:{meta.column}")
        sys.exit(1)

    def relation(self, lhs, rhs):
        return self.vector(lhs) - self.vector(rhs)

    def part(self, *relations):
        return relations  # all the relations

    def start(self, *relations):
        # join the lists of relations then convert to array
        M = np.array([vector for part in relations for vector in part])
        return M[:, :-1], -M[:, -1]


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

# Ordered set of Part names
Parts = {str(node.children[0]): None for node in tree.find_data("part")}

# process the tree to collect variables and parts
tree = Prepare().transform(tree)

# apply my wrapper to the transformer
pm = Propagate_manager()
PT = visitors.v_args(wrapper=pm.wrapper)(Propagate)()
# propagate constants
while pm.updated:
    tree = PT.transform(tree)

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
# link the part references to the part total
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
