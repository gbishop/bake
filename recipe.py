import pulp
from itertools import accumulate
from operator import add


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

    def table(self, vars: dict):
        headings = ["", "%", "g", "sum", "+bowl"]
        names = [name.replace("_", " ") for name in vars]
        pvalues = list(vars.values())
        gvalues = [value * self.scale / 100 for value in pvalues]
        cvalues = []
        csum = 0
        for i, name in enumerate(names):
            if "total" in name:
                cvalues.append(0)
            else:
                csum += gvalues[i]
                cvalues.append(csum)
        bvalues = [cvalue + self.bowl if cvalue else 0 for cvalue in cvalues]
        width = max(*(len(name) for name in names))
        cols = [names, pvalues, gvalues, cvalues, bvalues]
        rows = [
            "| {0:^{width}} | {1:^5} | {2:^6} | {0:^{width}} | {3:^7} | {4:^7} |".format(
                *headings, width=width
            ),
        ]
        lwidth = len(rows[0])
        rows.append("|" + "-" * (lwidth - 2) + "|")
        for i, r in enumerate(zip(*cols)):
            if i in self.divider:
                rows.append("|" + (lwidth - 2) * " " + "|")
                rows.append(f"| {self.divider[i]:-<{lwidth-3}}|")
            rows.append(
                "| {0:>{width}} | {1:5.1f} | {2:6.1f} | {0:<{width}} | {3:>7.1f} | {4:>7.1f} |".format(
                    *r, width=width
                )
            )
        return "\n".join(rows)


R = Recipe()
TBD = None


def water(total, hydration):
    return total * hydration / (100 + hydration)


def flour(total, hydration):
    return total * 100 / (100 + hydration)


bowl = 725.2
