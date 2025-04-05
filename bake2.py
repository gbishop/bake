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


def P(*args):
    print(*args, file=sys.stderr)


# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID [ "^" margin ] ":" (hydration | relation | ingredient)+

margin: NUMBER -> fixed_loss
      | NUMBER "%" -> scaled_loss

hydration: "hydration" "=" NUMBER

relation: sum "=" sum

?sum: product "+" sum   -> add
   | product "-" sum   -> subtract
   | product

bp: NUMBER "%"

?product: bp
       | term
       | term "*" product -> multiply
       | term "/" product -> divide

?term: ingredient
    | NUMBER -> constant
    | NUMBER "%" -> percent
    | "(" sum ")"

ingredient: ID
       | ID "." ID

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


class CollectPartNames(visitors.Visitor):
    def part(self, args):
        ST.addPart(args[0])


class AddPartName(visitors.Transformer):
    def __init__(self, partname):
        super()
        self.partname = partname

    def ingredient(self, args):
        name = args[0]
        if name.startswith("."):
            name = self.partname + name
        return Tree("ingredient", [name])


class TransformNumbers(visitors.Transformer):
    def bp(self, args):
        return Tree(
            "multiply",
            [args[0] / 100.0, "dough.total_flour"],
        )

    def NUMBER(self, value):
        if value.endswith("g"):
            return float(value[:-1])
        else:
            return float(value)

    def ID(self, value):
        return str(value)

    def ingredient(self, args):
        if len(args) == 1:
            return Tree("ingredient", ["." + args[0]])
        else:
            return Tree("ingredient", [".".join(args)])

    def part(self, args):
        P("part", args)
        if args[1] is None:
            args[1] = 0
        t = Tree("part", args)
        return AddPartName(args[0]).transform(t)


P(TransformNumbers().transform(tree).pretty())
