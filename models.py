from typing import List
import re
from dataclasses import dataclass


@dataclass
class Relation:
    part: str = ""
    name: str = ""
    formula: str = ""
    mass: float = 0.0
    bp: float = 0.0
    flour: float = 0.0
    water: float = 0.0
    _inconsistent: bool = False
    _invalid: str = ""


type Relations = List[Relation]


@dataclass
class SymbolTableEntry:
    partName: str
    ingredient: str
    index: int
    value: float = 0.0


def getRelations(text: str) -> Relations:
    # remove all the comments from the text
    cleanText: List[str] = []
    notesRE = re.compile(r"^#\s*(.*?)$|/\*(.*?)\*/", re.M | re.S)
    lastEnd = 0
    for match in notesRE.finditer(text):
        cleanText.append(text[lastEnd : match.start()])
        lastEnd = match.end()
    cleanText.append(text[lastEnd:])
    text = "".join(cleanText)

    # extract the relations
    relations = []
    part = ""
    for line in text.split("\n"):
        if m := re.match(r"(\w+)(\s*\^\s*)?(\d+[g%])?:.*", line):
            # a new part
            part, _, extra = m.groups()
            relations.append(Relation(part=part))
            if extra:
                relations.append(Relation(name="extra", formula=f"-{extra}"))

        elif m := re.match(r"\s+(\w+)(\s*=\s*([a-zA-Z_0-9.\+\-\*\/()% ]+))?", line):
            # an ingredient
            ingredient, _, formula = m.groups()
            if ingredient == "_part":
                continue
            ingredient = re.sub(r"\btotal\b", "total_mass", ingredient)
            if formula:
                formula = re.sub(r"(\w+)\.total\b", "\\1", formula)
                formula = re.sub(r"\btotal\b", "total_mass", formula)
            relations.append(Relation(name=ingredient, formula=formula))

    return relations


def fmt_value(fmt: str, v: float | str):
    """Format values in the table"""
    r = ""
    if fmt == "g":
        assert isinstance(v, (float, int))
        g = v
        ga = abs(g)
        if round(ga, 0) >= 100:
            r = f"{g:.0f}   "
        elif round(ga, 1) >= 5:
            r = f"{g:0.1f} "
        elif ga < 0.01:
            r = ""
        else:
            r = f"{g:0.2f}"
    elif fmt == "%":
        assert isinstance(v, (float, int))
        r = f"{v:5.1f}"
    elif fmt == "t":
        assert isinstance(v, str)
        r = v
    return r


layout = {
    "part": {"heading": "Part", "format": "t"},
    "mass": {"heading": "Mass", "format": "g"},
    "name": {"heading": "Ingredient", "format": "t"},
    "bp": {"heading": "%", "format": "%"},
    "flour": {"heading": "Flour", "format": "g"},
    "water": {"heading": "Water", "format": "g"},
}


def formatRelations(relations: Relations):
    """Build a table from the relations"""
    headings = [layout[prop]["heading"] for prop in layout]
    widths = [len(heading) for heading in headings]
    aligns = ["<" if layout[prop]["format"] == "t" else ">" for prop in layout]
    rows = [
        [fmt_value(layout[prop]["format"], getattr(relation, prop)) for prop in layout]
        for relation in relations
    ]
    errors = [
        "⚠️" if relation._inconsistent else "❗" if relation._invalid else ""
        for relation in relations
    ]
    for row in rows:
        if len(row) <= 1:
            continue
        widths = [max(len(column), width) for column, width in zip(row, widths)]
    rows = [
        [
            f"{column:{align}{width}}"
            for column, align, width in zip(row, aligns, widths)
        ]
        for row in rows
    ]

    top = "┌─" + "─┬─".join("─" * width for width in widths) + "─┐"
    bar = "├─" + "─┼─".join("─" * width for width in widths) + "─┤"
    end = "└─" + "─┴─".join("─" * width for width in widths) + "─┘"

    headings = [heading.center(width) for width, heading in zip(widths, headings)]
    header = [
        top,
        "│ " + " │ ".join(headings) + " │",
    ]
    body = []
    for i, row in enumerate(rows):
        if row[0].strip():
            body.append(bar)
        body.append("│ " + " │ ".join(row) + " │" + errors[i])
    footer = [end]
    return "\n".join(header + body + footer) + "\n"
