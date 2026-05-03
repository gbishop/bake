import re
import pandas as pd


def format_table(solution: pd.DataFrame):
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
    for partName, pdf in solution.groupby(level=0, sort=False):
        part_total = pdf.loc[(partName, "total"), "value"]
        part_loss = pdf.loc[(partName, "_loss"), "value"]
        loss_scale = (part_total + part_loss) / part_total
        # add the total
        rows.append(
            [
                partName,
                part_total * loss_scale,
                f"+ {part_loss:.1f}g" if abs(part_loss) > 0.1 else "",
                pdf.loc[(partName, "total"), "bp"],
                pdf.loc[(partName, "total_flour"), "value"],
                pdf.loc[(partName, "total_water"), "value"],
            ]
        )

        # add the ingredients from the part
        for var in pdf.index:
            name = var[1]
            if not name.startswith("total") and not name.startswith("_"):
                vg = pdf.loc[var, "value"]
                unknown = ""
                extras = pdf.loc[var, "flour":].tolist()
                rows.append(
                    [
                        "",
                        vg * loss_scale,
                        name + unknown,
                        pdf.loc[var, "bp"],
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
                    pdf.loc[("dough", "total_water"), "bp"],
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
    solution: pd.DataFrame,
    errors=[],
    tobp=False,
    html="",
):
    """Insert the table into the input"""
    recipe = format_table(solution)
    text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text).rstrip()
    if tobp:
        text = rewrite(text, 100 / solution.loc[("dough", "total_flour"), "value"])

    if errors:
        recipe = re.sub(r"^", "E ", recipe, 0, re.M)
        recipe = f"{'\n'.join(errors)}\n{recipe}"
    result = f"{text}\n\n/*+\n{recipe}+*/\n"
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
