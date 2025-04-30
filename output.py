import re
from ingredients import getIngredient
import sys

FullName = tuple[str, str]


def format_table(Variables: dict[FullName, float], Parts: dict[str, None]):
    """Build a table from the solution"""

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
            r = v.replace("_", " ")
        return r

    # fmt: off
    def tabulate(headings: list[str], formats: str, input: list[list[float | str]]):
        """Format a list of lists as a table"""
        widths = [len(h) for h in headings]
        rows = [
            [
                fmt_value(format, column)
                for column, format in zip(row, formats)
            ]
            for row in input
        ]
        for row in rows:
            if len(row) <= 1:
                continue
            widths = [
                max(len(column), width)
                for column, width in zip(row, widths)]
        aligns = ["<" if fmt == "t" else ">" for fmt in formats]
        rows = [
            [
                f"{column:{align}{width}}"
                for column, align, width in zip(row, aligns, widths)
            ]
            for row in rows
        ]
        # headings
        header = [
            " | ".join(heading.center(width)
            for width, heading in zip(widths, headings)) + " |",
            "-|-".join("-" * width for width in widths) + "-|",
        ] 
        body = [
            " | ".join(row) + " |" if len(row) > 1 else ""
            for row in rows
        ]
        return "\n".join(header + body) + "\n"
    # fmt: on

    # reshape the data into a list of lists
    rows = []
    dtf = Variables[("dough", "total_flour")]
    if dtf == 0:
        print("no flour")
        sys.exit(1)
    grams_to_bp = 100 / dtf
    nutrition = getIngredient("unknown")
    for partName in Parts:
        part_total = Variables[(partName, "total")]
        part_loss = Variables[(partName, "_loss")]
        loss_scale = (part_total + part_loss) / part_total
        bp = part_total * grams_to_bp
        # add the total
        rows.append(
            [
                partName,
                part_total * loss_scale,
                f"+ {part_loss:.1f}g" if part_loss > 0 else "",
                bp,
                Variables[(partName, "total_flour")],
                Variables[(partName, "total_water")],
            ]
        )
        # add the ingredients from the part
        for pn, var in Variables:
            if pn != partName:
                continue
            if not var.startswith("total") and not var.startswith("_"):
                vg = Variables[(partName, var)]
                unknown = ""
                if var in Parts:
                    extras = [
                        Variables[(var, "total_flour")],
                        Variables[(var, "total_water")],
                    ]
                else:
                    info = getIngredient(var)
                    extras = [
                        vg * info["flour"],
                        vg * info["water"],
                    ]
                    nutrition = nutrition + info * vg
                    if info.name == "unknown":
                        unknown = "!"
                rows.append(
                    [
                        "",
                        vg * loss_scale,
                        var + unknown,
                        vg * grams_to_bp,
                        *extras,
                    ]
                )
        # add hydration for the final dough
        if partName == "dough":
            rows.append(
                [
                    "",
                    0,
                    "hydration",
                    Variables[("dough", "total_water")] * grams_to_bp,
                    0,
                    0,
                ]
            )
        # add a blank line
        rows.append([""])

    heading = ["part", "grams", "name", "%", "flour", "water"]
    recipe = tabulate(heading, "tgt%ggg", rows)

    return recipe


def output(
    text: str,
    Variables: dict[FullName, float],
    Parts: dict[str, None],
    failed=False,
    tobp=False,
    html="",
):
    """Insert the table into the input"""
    recipe = format_table(Variables, Parts)
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text)
    if tobp:
        text = rewrite(text, 100 / Variables[("dough", "total_flour")])

    if failed:
        recipe = re.sub(r"^", "E ", recipe, 0, re.M)
    result = f"{text}/*+\n{recipe}+*/\n"
    print(result)

    if html:
        with open(html, "wt") as fp:
            print("<table><tbody>", file=fp)
            td = "th"
            for line in recipe.split("\n"):
                if "---" in line:
                    continue
                line = re.sub(r"\| *$", "", line)
                line = line.replace("|", f"</{td}><{td}>")
                line = f"<tr><{td}>" + line + f"</{td}></tr>"
                line = line.replace(" ", "&numsp;")
                print(line, file=fp)
                td = "td"
            print("</tbody></table>", file=fp)


def rewrite(text: str, scale: float):
    """Rewrite grams as baker's percent"""

    def gtobp(match):
        if match.group(1) not in [
            "total_flour",
            "total_water",
            "total",
        ]:
            f = float(match.group(3)[:-1]) * scale
            return f"{match.group(1)}{match.group(2)}{f:.2f}%"
        else:
            return match.group(0)

    return re.sub(r"(\w+)(\s*=\s*)([\d.]+\s*g)", gtobp, text)
