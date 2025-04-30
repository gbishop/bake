"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July 2024 April 2025
"""

from lark import Lark, visitors, UnexpectedInput, Token
import lark
import numpy as np
from numpy.typing import NDArray
import argparse
import sys
from ingredients import getIngredient
from output import output
from typing import Any, cast, Iterator, TypeGuard, Optional
from math import isnan

NaN = float('nan')

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

FullName = tuple[str, str]
Vector= NDArray[np.float64]
Matrix = NDArray[np.float64]

# Collect the variables with their values
Variables: dict[FullName, float] = {}
Parts: dict[str, None] = {}


class Tree[C](lark.Tree):
    """A typing hack"""
    children: list[C]

    def __init__(self, data: str, *children: Any, meta=None):
        super().__init__(data, list(children), meta)
        propagate_position(list(children), self.meta)

    def find_data(self, data):
        return cast(Iterator[Tree[C]], super().find_data(data))

def isTree(value, data="") -> TypeGuard[Tree]:
    """Test if the value is a Tree"""
    return isinstance(value, lark.Tree) and (not data or value.data == data)

def Unknown(part: str, name:str | Token, scale:Optional[float] = None):
    """Add an unknown possibly scaled"""
    r = Tree("unknown", (part, name))
    if isinstance(name, Token) and name.line and name.column:
        r.meta.line = name.line
        r.meta.column = name.column

    if scale is not None:
        r = Tree("multiply", scale, r, meta=r.meta)
    return r

def isUnknown(value) -> TypeGuard[Tree[FullName]]:
    return isTree(value, "unknown")

def isFloat(value) -> TypeGuard[float]:
    """Test if the value is a float"""
    return isinstance(value, (float, int))

def isVector(value) -> TypeGuard[Vector]:
    return isinstance(value, np.ndarray)

def propagate_position(children: list[Tree], meta):
    if hasattr(meta, 'line'):
        return
    line = 0
    for child in children:
        if isTree(child) and hasattr(child.meta, 'line'):
            line = max(line, child.meta.line)
        elif isinstance(child, Token) and child.line:
            line = max(line, child.line)
    if line:
        meta.line = line


def meta_wrapper(obj, _, children, meta):
    raw = obj(*children)
    if isTree(raw):
        # make sure children has line and column
        propagate_position(raw.children, meta)
        raw = Tree(raw.data, *raw.children, meta=meta)
    return raw

def PP(tree, offset=0):
    if isTree(tree):
        P(f"{' ' * offset}{tree.data} {getattr(tree.meta, 'line', '')}")
        for child in tree.children:
            PP(child, offset + 2)
    elif isinstance(tree, Token):
        P(f"{' ' * offset}{tree} {getattr(tree, 'line', '')}")
    else:
        P(f"{' ' * offset}{tree}")


@visitors.v_args(wrapper=meta_wrapper)
class Prepare(visitors.Transformer):
    """First pass after parsing"""

    def variable(self, name: str):
        return Unknown("", name)

    def reference(self, partname: str, name: str):
        return Unknown(partname, name)

    def bp(self, value: float):
        return Unknown("dough", "total_flour", value / 100.0)

    def product(self, *args: (Tree | str)):
        terms = list(args)
        # if the last term is a percent convert it to bakkers percent
        if isTree(terms[-1], "percent"):
            terms[-1] = Tree(
                "multiply", terms[-1].children[0] / 100.0, Unknown("dough", "total_flour")
            )
        result = terms[0]
        for i in range(1, len(terms), 2):
            if terms[i] == "*":
                result = Tree("multiply", result, terms[i + 1])
            else:
                result = Tree("divide", result, terms[i + 1])
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
            Unknown("", "total_water"), Unknown("", "total_flour", value / 100.0),
        )

    def part(self, partname: str, loss: None | float | Tree, *rest: Tree[Any]):
        relations = [r for r in rest if isTree(r, "relation")]

        # qualify the variables with their partname
        tosum = set()
        for children in rest:
            unknowns: Iterator[Tree[FullName]] = children.find_data("unknown")
            for unknown in unknowns:
                if unknown.children[0][0]:
                    continue
                name = unknown.children[0][1]
                fullname = (partname, name)
                unknown.children[0] = fullname
                if not (name.startswith("total") or name.startswith("_")):
                    tosum.add(fullname)
                if fullname not in Variables:
                    Variables[fullname] = NaN
                if name in Parts:
                    relations.append(Tree("relation", Unknown(*fullname), Unknown(name, "total")))

        # establish the total relations
        for which in ["total", "total_water", "total_flour"]:
            fullname = (partname, which)
            Variables[fullname] = NaN
            sum: Any = 0.0
            for name in tosum:
                if name[1] in Parts:
                    addin = Unknown(name[1], which)
                elif which == "total":
                    addin = Unknown(*name)
                else:
                    kind = which.replace("total_", "")
                    info = getIngredient(name[1])
                    addin = Unknown(name[0], name[1], info[kind])
                sum = Tree("add", addin, sum)
            relations.append(Tree("relation", Unknown(*fullname), sum))
        # add a relation for the loss
        if isTree(loss, "scaled_loss"):
            loss_value = Unknown(partname, "total", loss.children[0] / 100.0)
        elif isFloat(loss):
            loss_value = loss
        else:
            loss_value = 0.0
        loss_name = (partname, "_loss")
        Variables[loss_name] = NaN
        relations.append(Tree("relation", Unknown(*loss_name), loss_value))
        return Tree("part", *relations)


class Propagate_manager:
    """Automagically track updates while propagating constants"""

    updates = 0
    first_time = True

    def wrapper(self, obj, data, children, meta):
        """Inline parameters, copy if method returns nothing, count updates"""
        raw = obj(*children)
        # the the method returns nothing, return the tree
        if raw is None:
            return Tree(data, *children, meta=meta)
        # It updated something, increment updates
        self.updates += 1
        # if it returns a Tree augment it with meta
        if isTree(raw):
            propagate_position(raw.children, meta)
            return Tree(raw.data, *raw.children, meta=meta)
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

    def unknown(self, name: FullName):
        value = Variables[name]
        if not isnan(value):
            return value

    def relation(self, lhs: float | Tree, rhs: float | Tree):
        if isFloat(rhs) and isUnknown(lhs):
            lname = lhs.children[0]
            lvalue = Variables[lname]
            if isnan(lvalue):
                Variables[lname] = rhs
                return visitors.Discard
        elif isFloat(lhs) and isUnknown(rhs):
            rname = rhs.children[0]
            rvalue = Variables[rname]
            if isnan(rvalue):
                Variables[rname] = lhs
                return visitors.Discard
        elif isFloat(lhs) and isFloat(rhs):
            return visitors.Discard

    def percent(self, value: float):
        return value / 100.0

    def multiply(self, lhs: float | Tree, rhs: float | Tree):
        if isFloat(lhs):
            if lhs == 0.0:
                return 0.0
            elif lhs == 1.0:
                return rhs
            if isFloat(rhs):
                if rhs == 0.0:
                    return 0.0
                elif rhs == 1.0:
                    return lhs
                return lhs * rhs
        if isFloat(rhs):
            if rhs == 0.0:
                return 0.0
            elif rhs == 1.0:
                return lhs

    def divide(self, lhs: float | Tree, rhs: float | Tree):
        if isFloat(lhs):
            if lhs == 0.0:
                return 0.0
            if isFloat(rhs):
                return lhs / rhs
        if isFloat(rhs):
            if rhs == 1.0:
                return lhs
            return Tree("multiply", 1.0 / rhs, lhs)

    def add(self, lhs: float | Tree, rhs: float | Tree):
        if isFloat(lhs):
            if lhs == 0.0:
                return rhs
            if isFloat(rhs):
                if rhs == 0.0:
                    return lhs
                return lhs + rhs
        if isFloat(rhs) and rhs == 0.0:
            return lhs

    def subtract(self, lhs: float | Tree, rhs: float | Tree):
        if isFloat(lhs):
            if isFloat(rhs):
                if rhs == 0.0:
                    return lhs
                return lhs - rhs
        if isFloat(rhs) and rhs == 0.0:
            return lhs

class BuildMatrix(visitors.Transformer[Any, tuple[Matrix, Vector]]):
    """Convert the remaining relations into matrix equations"""

    def __init__(self, columns):
        self.columns = columns

    def onehot(self, index: int, value=1.0) -> Vector:
        r = np.zeros(self.columns)
        r[index] = value
        return r

    def vector(self, value: float | int | Vector) -> Vector:
        if isinstance(value, (float, int)):
            return self.onehot(self.columns - 1, value)
        return value

    @visitors.v_args(inline=True)
    def unknown(self, name: FullName) -> Vector:
        return self.onehot(Index[name])

    @visitors.v_args(inline=True)
    def add(self, lhs: float | Vector, rhs: float | Vector) -> Vector:
        return self.vector(lhs) + self.vector(rhs)

    @visitors.v_args(inline=True)
    def subtract(self, lhs: float | Vector, rhs: float | Vector) -> Vector:
        return self.vector(lhs) - self.vector(rhs)

    @visitors.v_args(inline=True, meta=True)
    def multiply(self, meta, lhs: float | Vector, rhs: float | Vector) -> Vector:
        if isFloat(lhs) and isVector(rhs):
            return lhs * rhs
        if isVector(lhs) and isFloat(rhs):
            return lhs * rhs
        print(f"Multiplication of unknowns is not supported {meta.line}:{meta.column}")
        sys.exit(1)

    @visitors.v_args(inline=True)
    def relation(self, lhs: float | Vector, rhs: float | Vector) -> Vector:
        return self.vector(lhs) - self.vector(rhs)

    def part(self, relations: list[Vector]) -> list[Vector]:
        return relations  # all the relations

    def start(self, relations: list[Vector]) -> tuple[Matrix, Vector]:
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
    parsetree = parser.parse(text)
except UnexpectedInput as e:
    print(e, e.get_context(text))
    sys.exit(1)

# Ordered set of Part names
Parts = {str(node.children[0]): None for node in parsetree.find_data("part")}

# process the tree to collect variables and parts
tree: Tree = Prepare().transform(parsetree)

# apply my wrapper to the transformer
pm = Propagate_manager()
PT = visitors.v_args(wrapper=pm.wrapper)(Propagate)()
# propagate constants
while pm.updated:
    tree = PT.transform(tree)

# map unknowns to columns in the matrix
Index: dict[FullName, int] = {}
unknowns = 0
# add the unknowns to the Index
for name, value in Variables.items():
    if isnan(value) and name[1] not in Parts:
        Index[name] = unknowns
        unknowns += 1
# link the part references to the part total
for name, value in Variables.items():
    if isnan(value) and name[1] in Parts:
        Index[name] = Index[(name[1], "total")]

failed = False
if unknowns > 0:
    # setup the equations
    A, B = BuildMatrix(unknowns + 1).transform(tree)
    # solve
    r = np.linalg.lstsq(A, B, rcond=-1)
    X = r[0]
    residuals: Vector = A.dot(X) - B
    error: float = np.sqrt(np.max(residuals**2))
    failed = error > 1
    # copy solution back to the unknowns
    for name, index in Index.items():
        Variables[name] = X[index]
# print the table
output(text, Variables, Parts, failed, args.rewrite, args.html)
