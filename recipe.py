import pulp
from tabulate import tabulate, SEPARATING_LINE
import re

""""""


class Recipe:
    vars = {}
    constraints = []
    objective = 0
    divider = {}
    bowl = 720.5
    scale = 500

    def __getattr__(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __getitem__(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __iadd__(self, constraint):
        if isinstance(constraint, str):
            self.divider[len(self.vars)] = constraint
        elif isinstance(constraint, (float, int)):
            pass
        elif isinstance(constraint, (tuple, list)):
            for c, v in constraint:
                self.constraints.append(c)
        else:
            self.constraints.append(constraint)
        return self

    def sum(self, *terms, **constants):
        result = 0.0
        for term in terms:
            result = result + term
        for name, value in constants.items():
            if value is None:
                result = result + self[name]
            else:
                self.constraints.append(self[name] == value)
                result = result + value

        return result

    def parts(self, **weighted):
        names = [name for name in weighted]
        zero = [name for name, value in weighted.items() if value == 0]
        nonzero = list(set(names) - set(zero))
        for name1, name2 in zip(nonzero[:-1], nonzero[1:]):
            self.constraints.append(
                weighted[name2] * self[name1] == weighted[name1] * self[name2]
            )
        for name in zero:
            self.constraints.append(self[name] == 0)
        return sum(self[name] for name in nonzero)

    def table(self, vars: dict):
        names = [
            re.sub(r"_?\d+$", "", name.replace("__", "/").replace("_", " "))
            for name in vars
        ]
        nwidth = max(len(name) for name in names)
        pvalues = list(vars.values())
        gvalues = [value * self.scale / 100 for value in pvalues]
        cvalues = []
        csum = 0
        for i, name in enumerate(names):
            if "total" in name or "/" in name:
                cvalues.append(0)
            else:
                csum += gvalues[i]
                cvalues.append(csum)
        bvalues = [cvalue + self.bowl if cvalue else 0 for cvalue in cvalues]
        headings = ["", "%  ", "g  ", "", "sum ", "+bowl"]

        cols = [names, pvalues, gvalues, names, cvalues, bvalues]
        rows = []
        for i, row in enumerate(zip(*cols)):
            if i in self.divider:
                d = self.divider[i]
                if d:
                    rows.append([])
                ld = nwidth - len(d)
                l = ld // 2
                r = ld - l
                rows.append(["─" * l + d + "─" * r])
                if d:
                    rows.append([])
            rows.append(row)

        table = tabulate(
            rows,
            headers=headings,
            floatfmt=".1f",
            colalign=("right",),
            tablefmt="simple_outline",
        )
        table = table.replace(" 0.0", "    ").replace(" ", "\u2002")
        table = "\n".join(
            [
                (
                    line.replace(" ", "─").replace("─│─", "─┼─")
                    if line.startswith("│ ─")
                    else line
                )
                for line in table.split("\n")
            ]
        )

        return table


R = Recipe()
TBD = None


def water(total, hydration):
    return total * hydration / (100 + hydration)


def flour(total, hydration):
    return total * 100 / (100 + hydration)


bowl = 725.2
