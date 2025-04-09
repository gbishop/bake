import re
from ingredients import getIngredient
import sys
from math import log10


def format_table(Variables, Parts):
    """Build a table from the solution"""

    def fmt_grams(g, threshold=0.1):
        """Format grams in the table"""
        if abs(g) < threshold:
            return ""
        w = max(0, int(log10(round(abs(g), 2)))) + 1
        p = max(0, 3 - w)
        s = max(0, 2 - p) + (p == 0)
        return f"{g:.{p}f}" + s * " "

    fmt = {
        "g": fmt_grams,
        "%": lambda p: f"{p:5.1f}",
        "t": lambda s: s.replace("_", " "),
    }

    def tabulate(headings, fmts, rows):
        """Format a list of lists as a table"""
        widths = [len(h) for h in headings]
        rows = [[fmt[fmts[i]](col) for i, col in enumerate(row)] for row in rows]
        for row in rows:
            for i, col in enumerate(row):
                widths[i] = max(widths[i], len(col))
        # headings
        result = [
            " | ".join([h.center(widths[i]) for i, h in enumerate(headings)]) + " |",
            "-|-".join(["-" * widths[i] for i in range(len(headings))]) + "-|",
        ]
        for row in rows:
            cols = []
            for i, col in enumerate(row):
                if fmts[i] == "t":
                    cols.append(f"{col:<{widths[i]}}")
                else:
                    cols.append(f"{col:>{widths[i]}}")
            line = " | ".join(cols)
            if len(row) > 1:
                line += " |"
            result.append(line)
        return "\n".join(result) + "\n"

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

    nrows = []
    # account for 9% loss during baking
    fdw = Variables[("dough", "total")] * 0.91
    serving = Variables.get(("dough", "_serving"), 100)
    if serving > 1:
        nscale = serving / fdw
        for key in sorted(nutrition.index):
            if key == "water" or key == "flour":
                continue
            v = nutrition.loc[key] * nscale
            if key == "true_water":
                key = "water"
                v *= 0.91
            if v > 0.01:
                nrows.append((key, v))
        nut = tabulate(["name", f"per {serving:.0f}g"], "tg", nrows)
        nut = "Nutrition\n" + nut
    else:
        nut = ""

    return recipe, nut


def output(text, Variables, Parts, failed=False, tobp=False, html=""):
    """Insert the table into the input"""
    recipe, nut = format_table(Variables, Parts)
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text)
    if tobp:
        text = rewrite(text, 100 / Variables[("dough", "total_flour")])

    if failed:
        recipe = re.sub(r"^", "E ", recipe, 0, re.M)
    result = f"{text}/*+\n{nut}\n\n{recipe}+*/\n"
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


def rewrite(rest, scale):
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

    return re.sub(r"(\w+)(\s*=\s*)([\d.]+\s*g)", gtobp, rest)
