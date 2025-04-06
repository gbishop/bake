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
        for r in rest:
            vars = r.find_data("unknown")
            for var in vars:
                var.children[0] = (partname, var.children[0][1])
                if var.children[0] not in Variables:
                    Variables[var.children[0]] = None

        for name in ["total", "total_water", "total_flour"]:
            Variables[(partname, name)] = None

        return Tree("part", [partname, loss, *rest])


@visitors.v_args(tree=True)
class Eval(visitors.Transformer):
    def variable(self, tree):
        value = Variables[tree.children[0]]
        if value is None:
            return tree
        else:
            return value

    def reference(self, tree):
        value = Variables[tree.children[0]]
        if value is None:
            return tree
        else:
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
                    return visitors.Discard
        return tree

    def multiply(self, tree):
        lhs, rhs = tree.children
        if isinstance(lhs, float) and isinstance(rhs, float):
            return lhs * rhs
        return tree


P(Variables)

t1 = Pass1().transform(tree)

P(t1.pretty())

t2 = Eval().transform(t1)
t3 = Eval().transform(t2)

P(t3.pretty())

P(Variables)
