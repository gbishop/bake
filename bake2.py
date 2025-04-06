"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July-December 2024
"""

from lark import Lark, Visitor, Tree, Token, visitors
from formula import Formula
import lark
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Dict, List
import argparse
import re
import sys

formula = Formula()


def P(*args):
    print(*args, file=sys.stderr)


# Lark grammar for my formulas
grammar = r"""
start: part+

part: ID [ "^" margin ] ":" (hydration | relation | unknown)+

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

?term: unknown
     | NUMBER -> constant
     | NUMBER "%" -> percent
     | "(" sum ")"

unknown: ID
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


def TF():
    return Tree("unknown", [("dough", "total_flour")])


class TransformNumbers(visitors.Transformer):
    def bp(self, args):
        return Tree(
            "multiply",
            [args[0] / 100.0, TF()],
        )

    def NUMBER(self, value):
        if value.endswith("g"):
            return float(value[:-1])
        else:
            return float(value)

    def ID(self, value):
        return str(value)

    def unknown(self, args):
        if len(args) == 1:
            return Tree("unknown", [args[0]])
        else:
            return Tree("unknown", [tuple(args)])

    def part(self, args):
        partname, loss, *rest = args
        if loss is None:
            loss = 0

        class T(visitors.Transformer):
            def unknown(self, args):
                if len(args) == 1:
                    unknown = formula.addUnknown(partname, args[0])
                else:
                    unknown = formula.addUnknown(*args)
                return Tree("unknown", unknown)

        t = T()
        rest = [t.transform(arg) for arg in rest]
        part = formula.addPart(partname, loss)
        return Tree("part", [partname, part, *rest])


P(TransformNumbers().transform(tree).pretty())
