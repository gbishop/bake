# Convert .bake files to the new .html format

from tree import *
from pandas import DataFrame
from typing import List, TypedDict
import re


# the new format
class RecipeRow(TypedDict):
    part: str
    name: str
    formula: str
    mass: float
    bp: float
    flour: float
    water: float
    _inconsistent: bool
    _invalid: str


def row(
    part: str = "",
    name: str = "",
    formula: str = "",
    mass: float = 0,
    bp: float = 0,
    flour: float = 0,
    water: float = 0,
    _inconsistent: bool = False,
    _invalid: str = "",
):
    return RecipeRow(
        part=part,
        name=name,
        formula=formula,
        mass=mass,
        bp=bp,
        flour=flour,
        water=water,
        _inconsistent=_inconsistent,
        _invalid=_invalid,
    )


class NRecipe(TypedDict):
    table: List[RecipeRow]
    notes: str


@dataclass
class State:
    currentPart = ""


state = State()


def name(v: Var):
    if v.part == state.currentPart:
        return v.name
    elif v.name == "total":
        return v.part
    else:
        return f"{v.part}.{v.name}"


def formula(value):
    match value:
        case Sum(lhs, rhs):
            return f"{formula(lhs)} + {formula(rhs)}"
        case Difference(0, rhs):
            return f"-{formula(rhs)}"
        case Difference(lhs, rhs):
            return f"{formula(lhs)} - {formula(rhs)}"
        case Product(float(lhs), Var("dough", "total_flour")):
            return f"{lhs*100:.1f}%"
        case Product(lhs, rhs):
            return f"{formula(lhs)} * {formula(rhs)}"
        case Var(part, name):
            if part == state.currentPart:
                return name
            return f"{part}.{name}"
        case float(v):
            return f"{v:.3g}"
        case _:
            return str(value)


def convert(text: str, recipe: Recipe, solution: DataFrame) -> List[RecipeRow]:
    result: List[RecipeRow] = []
    parts = set([part.name for part in recipe.parts])
    for part in recipe.parts:
        state.currentPart = part.name
        result.append(row(part=part.name))
        allVars = [v.t for v in part.vars[3:]]
        presult: List[RecipeRow] = []
        for relation in part.relations[:-3]:
            rv = relation.var.t
            if rv in allVars and rv[1] not in parts:
                allVars.remove(rv)
            match relation:
                case Relation(
                    Var(part1, "total_water"),
                    Product(float(v), Var(part2, "total_flour")),
                ) if (
                    part1 == part2 == state.currentPart
                ):
                    presult.append(row(name="hydration", formula=f"{100 * v}%"))

                case Relation(Var(part1, "_loss"), 0):
                    continue
                case Relation(
                    Var(part1, "_loss"),
                    Product(float(v), Var(part2, "total")),
                ) if (
                    part1 == part2 == state.currentPart
                ):
                    presult.append(row(name="extra", formula=f"{-100 * v}pm"))

                case Relation(Var(part1, "_loss"), float(v)) if (
                    part1 == state.currentPart
                ):
                    presult.append(row(name="extra", formula=f"{v}g"))

                case Relation(Var(part1, name1), Var(part2, "total")) if name1 == part2:
                    continue

                case _:
                    presult.append(
                        row(
                            name=name(relation.var),
                            formula=formula(relation.value),
                        )
                    )
        for var in allVars:
            result.append(row(name=var[1]))
        result.extend(presult)

    # collect the notes
    commentRE = re.compile(r"^\s*#\s*(.*?)$|/\*(.*?)\*/", re.M | re.S)
    comments = commentRE.findall(text)
    print(comments)

    return result
