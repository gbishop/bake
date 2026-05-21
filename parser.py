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
    %import common.SIGNED_NUMBER
    %import common.NUMBER
    %import common.NEWLINE
    %ignore WS_INLINE
    %ignore SH_COMMENT
    %ignore C_COMMENT
    %declare _INDENT _DEDENT

    _NL: (NEWLINE /[\t ]*/ | SH_COMMENT | C_COMMENT )+

    start: _NL* recipe ERROR* TABLE?

    recipe: part+

    part: ID [ "^" NUMBER /[%g]/ ] ":" _NL _INDENT relation+ _DEDENT

    relation: "hydration" "=" NUMBER "%" _NL -> hydration
        | unknown "=" sum _NL -> relation
        | unknown _NL -> inclusion

    ?sum: sum "+" product -> add
        | sum "-" product -> subtract
        | product

    ?product: product "*" term -> product
        | product "/" number -> divide
        | term

    ?term: unknown
        | number
        | "(" sum ")"

    number: SIGNED_NUMBER [ UNIT ]

    UNIT: ("%" | "ppm" | "g" | "dt" | "df" | "dw" | "pt" | "pf" | "pw")

    unknown: [ ID "." ] ID

    ERROR: "⚠" /.*/ _NL

    TABLE: "┌" /.*?/s "┘" _NL
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
            return Product(v / 100, Var(*basis))
        case "dt":
            return Product(v / 100, Var("dough", "total"))
        case "df":
            return Product(v / 100, Var("dough", "total_flour"))
        case "dw":
            return Product(v / 100, Var("dough", "total_water"))
        case "pt":
            return Product(v / 100, Var("", "total"))
        case "pw":
            return Product(v / 100, Var("", "total_water"))
        case "pf":
            return Product(v / 100, Var("", "total_flour"))
        case _:
            raise NotImplementedError


# use a Lark visitor to convert to my rep
@lark.visitors.v_args(inline=True)
class Convert(lark.Transformer):
    def start(self, recipe, *rest):
        return recipe

    def recipe(self, *parts: Part):
        return Recipe(parts)

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
                    if not var.part or var.part == partName:
                        result.addVar(var.name)
                case Relation() as relation:
                    var = relation.var
                    if not var.part or var.part == partName:
                        result.addVar(var.name)
                    result.addRelation(relation)

        lvalue = convertNumber(loss, unit, (partName, "total"))
        lvar = result.addVar("_loss")
        result.addRelation(Relation(lvar, lvalue))
        return result

    def hydration(self, value: str):
        return Relation(
            Var("", "total_water"),
            Product(float(value) / 100, Var("", "total_flour")),
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

    def add(self, left, right):
        return Sum(left, right)

    def product(self, lhs, rhs):
        return Product(lhs, rhs)

    def divide(self, lhs, rhs):
        return Product(1 / rhs, lhs)

    def subtract(self, left, right):
        return Difference(left, right)

    def table(self, *_):
        return None


def parse(text: str):
    parser = Lark(
        grammar,
        parser="lalr",
        postlex=TreeIndenter(),
        propagate_positions=True,
        regex=True,
    )

    try:
        tree = parser.parse(text)
    except lark.UnexpectedInput as e:
        print(e, e.get_context(text), file=sys.stderr)
        sys.exit(1)

    r = Convert().transform(tree)

    return r
