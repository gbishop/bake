"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from lark import Lark, Visitor, Tree, Token, visitors
import lark
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Dict, List
import argparse
import re
import sys
from ingredients import getIngredient


def P(*args):
    print(*args, file=sys.stderr)


# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID [ "^" margin ] ":" (hydration | relation | variable)+

margin: NUMBER -> fixed_loss
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


def TF():
    return Tree("reference", [("dough", "total_flour")])


Variables: Dict[tuple, None | float] = {}
Parts: Dict[str, None] = {}


@visitors.v_args(inline=True)
class Pass1(visitors.Transformer):

    def variable(self, name: str):
        return Tree("unknown", [("", name)])

    def reference(self, partname, name):
        return Tree("reference", [(partname, name)])

    def bp(self, value):
        return Tree(
            "multiply",
            [value / 100.0, TF()],
        )

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
                Tree("unknown", [("", "total_water")]),
                Tree(
                    "multiply", [value / 100.0, Tree("unknown", [("", "total_flour")])]
                ),
            ],
        )

    def part(self, partname, loss, *rest):
        Parts[partname] = None
        if loss is None:
            loss = 0

        # qualify the variables with their partname
        vnames = set()
        for r in rest:
            vars = r.find_data("unknown")
            for var in vars:
                name = (partname, var.children[0][1])
                vnames.add(name)
                var.children[0] = name
                if name not in Variables:
                    Variables[name] = None

        vnames = [
            name
            for name in vnames
            if not name[1].startswith("total") and not name[1].startswith("_")
        ]
        relations = [r for r in rest if isinstance(r, Tree) and r.data == "relation"]
        for name, func in [
            ("total", total),
            ("total_water", water),
            ("total_flour", flour),
        ]:
            tname = (partname, name)
            Variables[tname] = None
            sum = func(vnames[0])
            for var in vnames[1:]:
                sum = Tree("add", [func(var), sum])
            relations.append(Tree("relation", [Tree("unknown", [tname]), sum]))

        return Tree("part", [partname, loss, *relations])


def flour(name):
    n = name[1]
    if n in Parts:
        return Tree("unknown", [(n, "total_flour")])
    else:
        info = getIngredient(n)
        return Tree("multiply", [info["flour"] / 100, name])


def water(name):
    n = name[1]
    if n in Parts:
        return Tree("unknown", [(n, "total_water")])
    else:
        info = getIngredient(n)
        return Tree("multiply", [info["water"] / 100, name])


def total(name):
    n = name[1]
    if n in Parts:
        return Tree("unknown", [(n, "total")])
    else:
        return name


@visitors.v_args(tree=True)
class Eval(visitors.Transformer):
    updates = 0

    def unknown(self, tree):
        name = tree.children[0]
        if name[1] in Parts:
            return Tree("unknown", [(name[1], "total")])
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


t = Pass1().transform(tree)

# P(t.pretty())

for i in range(10):
    P(i)
    e = Eval()
    t = e.transform(t)
    P(e.updates)
    if e.updates == 0:
        break

P(t.pretty())

P(Variables)
