from __future__ import annotations
import lark
from lark import Lark
from lark.indenter import Indenter
from tree import *
import sys

grammar = r"""
    %import common.CNAME -> ID
    %import common.WS_INLINE
    %import common.SH_COMMENT
    %import common.C_COMMENT
    %import common.NUMBER
    %import common.NEWLINE
    %ignore WS_INLINE
    %ignore SH_COMMENT
    %ignore C_COMMENT
    %declare _INDENT _DEDENT

    _NL: (NEWLINE /[\t ]*/ | SH_COMMENT | C_COMMENT )+

    start: _NL* part+
    part: ID [ "^" NUMBER /[%g]/ ] ":" _NL _INDENT relation+ _DEDENT

    relation: "hydration" "=" NUMBER "%" _NL -> hydration
        | unknown "=" sum _NL -> relation
        | unknown _NL -> inclusion

    ?sum: product ("+" product)+ -> add
        | product ("-" product)+ -> subtract
        | product

    ?product: term ("*" term)*

    ?term: unknown
        | number "/" number -> divide
        | number
        | "(" sum ")"

    number: NUMBER [ UNIT ]

    UNIT: ("%" | "ppm" | "g" | "dt" | "df" | "dw" | "pt" | "pf" | "pw")

    unknown: [ ID "." ] ID
"""


class TreeIndenter(Indenter):
    NL_type = "_NL"  # pyright: ignore
    OPEN_PAREN_types = ["LPAR"]  # pyright: ignore
    CLOSE_PAREN_types = ["RPAR"]  # pyright: ignore
    INDENT_type = "_INDENT"  # pyright: ignore
    DEDENT_type = "_DEDENT"  # pyright: ignore
    tab_len = 8  # pyright: ignore


def convertNumber(value: str | None, unit: str | None, basis=("dough", "total_flour")):
    if value is None:
        return 0
    v = float(value)
    match unit:
        case None | "g":
            return v
        case "ppm":
            return v / 1e6
        case "%":
            return Product([v / 100, Var(*basis)])
        case "dt":
            return Product([v / 100, Var("dough", "total")])
        case "df":
            return Product([v / 100, Var("dough", "total_flour")])
        case "dw":
            return Product([v / 100, Var("dough", "total_water")])
        case "pt":
            return Product([v / 100, Var("", "total")])
        case "pw":
            return Product([v / 100, Var("", "total_water")])
        case "pf":
            return Product([v / 100, Var("", "total_flour")])
        case _:
            raise NotImplementedError


# use a Lark visitor to convert to my rep
@lark.visitors.v_args(inline=True)
class Convert(lark.Transformer):
    def start(self, *parts: Part):
        return Start(parts)

    def part(
        self,
        partName: str,
        loss: str | None,
        unit: str | None,
        *items: Relation | Var,
    ):

        partName = str(partName)
        result = Part(partName)

        for item in items:
            match item:
                case Var() as var:
                    if not var.part:
                        var.part = partName
                    result.addVar(var.part, var.name)
                case Relation() as relation:
                    var = relation.var
                    if not var.part:
                        var.part = partName
                    result.addVar(var.part, var.name)
                    result.addRelation(relation)

        lvalue = convertNumber(loss, unit, ("", "total"))
        result.addVar(partName, "_loss")
        result.addRelation(partName, "_loss", lvalue)
        return result

    def hydration(self, value: str):
        return Relation(
            Var("", "total_water"),
            Product([float(value) / 100, Var("", "total_flour")]),
        )

    def number(self, value: str, unit: str):
        return convertNumber(value, unit)

    def unknown(self, part, name):
        name = str(name)
        return Var(part and str(part) or "", name)

    def inclusion(self, var):
        return var

    def relation(self, var, value):
        return Relation(var, value)

    def add(self, product, *rest):
        return Sum([product, *rest])

    def product(self, term, *rest):
        return Product([term, *rest])

    def divide(self, lhs, rhs):
        return Divide(lhs, rhs)

    def subtract(self, first, *rest):
        return Sum([first, Product([-1, *rest])])


def parse(text: str):
    parser = Lark(
        grammar, parser="lalr", postlex=TreeIndenter(), propagate_positions=True
    )

    try:
        tree = parser.parse(text)
    except lark.UnexpectedInput as e:
        print(e, e.get_context(text), file=sys.stderr)
        sys.exit(1)

    r = Convert().transform(tree)

    return r
