import textx
import pulp
import re
import sys

Flours = [
    "prairie_gold",
    "bronze_chief",
    "vwg",
    "ww",
    "rye",
    "polenta",
    "flaxseed_meal",
    "potato_flakes",
    "spelt",
    "whole_wheat",
    "ap_flour",
    "red_rye_malt",
    "oats",
]


def flourFraction(name):
    if name in Flours:
        return 1.0
    return 0.0


def waterFraction(name):
    if "water" in name:
        return 1.0
    if name == "egg":
        return 0.75
    if name == "milk":
        return 0.87
    return 0.0


class Part:
    def __init__(self, name):
        self.name = name
        self.constraints = []
        self.vars = {}
        self.values = {}

    def var(self, name):
        if name not in self.vars:
            lpname = f"{self.name}.{name}"
            self.vars[name] = pulp.LpVariable(lpname, 0, None)
        return self.vars[name]

    def add(self, constraint):
        self.constraints.append(constraint)

    def print(self, scale, last=False):
        result = []
        bp = self.values["total"]
        g = bp * scale
        result.append(f"{self.name:.<35}({g:.1f}g = {100*bp:.1f}%)")
        for var in self.vars:
            if last and var != "total" or not var.startswith("total"):
                bp = self.values[var]
                g = bp * scale
                result.append(f"   {g:6.1f} {var.replace('_', ' '):15} {100*bp:6.2f}%")
        result.append("")
        return "\n".join(result)


class Bake:
    def __init__(self):
        self.meta = textx.metamodel_from_file("bake.tx", ws=" ")
        self.meta.register_obj_processors(
            {
                "Value": self.handleValue,
                "BP": self.handleBP,
                "NamedValue": self.handleNamedValue,
                "PartName": self.handlePartName,
                "Sum": self.handleSum,
                "Product": self.handleProduct,
                "Ingredient": self.handleIngredient,
                "Part": self.handlePart,
                "Setting": self.handleSetting,
            }
        )
        self.parts = {}
        self.hydration = 1

    def compile(self):
        text = sys.stdin.read()
        try:
            self.model = self.meta.model_from_str(text)
        except textx.TextXSyntaxError as e:
            return self.output(f"Error {e.line}:{e.col} {e.message}", text)
        problem = pulp.LpProblem("bake")
        problem += 0  # objective goes here
        for part in self.parts.values():
            for constraint in part.constraints:
                problem += constraint

        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        if problem.status < 1:
            return self.output("solution failed", text)
        else:
            for var in problem.variables():
                if "." in var.name:
                    part, ingredient = var.name.split(".")
                    self.parts[part].values[ingredient] = var.varValue
            parts = self.parts.values()
            N = len(parts)
            result = "\n".join(
                part.print(self.scale, i == N - 1) for i, part in enumerate(parts)
            )
            return self.output(result, text)

    def output(self, table, text):
        match = re.match(
            r"(?ms)(?P<title>.*?\n)?\s*(?P<table>\/\*\+.*?\+\*\/)?(?P<rest>.*)",
            text,
        )
        if match:
            title = match.group("title") or "the title"
            title = title.strip()
            table = table.strip()
            rest = match.group("rest").strip()
            result = f"{title}\n/*+\n{table}\n+*/\n{rest}"
        else:
            result = f"title\n/*+\n{table}+*/\n{text}"
        print(result)

    def handleSum(self, v):
        result = v.term.pulp
        for sum in v.sums:
            if sum.op == "+":
                result = result + sum.term.pulp
            else:
                result = result - sum.term.pulp
        v.pulp = result

    def handleProduct(self, v):
        result = v.factor.pulp
        for factor in v.products:
            result = result * factor.factor.pulp
        v.pulp = result

    def handleValue(self, v):
        if v.named:
            v.pulp = v.named.pulp
        elif v.expr:
            v.pulp = v.expr.pulp
        else:
            v.pulp = v.value.value

    def handleBP(self, v):
        if not v.unit or v.unit == "%":
            v.value = v.value / 100

    def handleNamedValue(self, v):
        if v.ingredient:
            v.pulp = self.parts[v.part].var(v.ingredient)
        else:
            v.pulp = self.part.var(v.part)

    def handlePartName(self, v):
        self.part = self.parts[v.name] = Part(v.name)

    def handleIngredient(self, v):
        if not v.name:
            if v.hydration:
                self.part.add(
                    self.part.var("total_water")
                    == v.hydration.value * self.part.var("total_flour")
                )
            elif v.scale:
                self.scale = v.scale.value
            return

        name = v.name
        var = self.part.var(name)

        if name in self.parts:
            otherPart = self.parts[v.name]
            self.part.add(var == otherPart.var("total"))
            if v.parameter:
                othervar = otherPart.var(v.parameter.name)
                otherPart.add(othervar == v.parameter.value.pulp)

        if v.expr:
            self.part.add(var == v.expr.pulp)

    def handlePart(self, _):
        part = self.part
        total = pulp.lpSum(
            part.vars[var] for var in part.vars if not var.startswith("total")
        )
        var = part.var("total")
        part.add(var == total)
        flour = 0
        water = 0
        for var in part.vars:
            if var in self.parts:
                flour += self.parts[var].var("total_flour")
                water += self.parts[var].var("total_water")
            else:
                if "total" not in var:
                    f = flourFraction(var)
                    if f > 0:
                        flour += f * part.var(var)
                    w = waterFraction(var)
                    if w > 0:
                        water += w * part.var(var)
        part.add(self.part.var("total_flour") == flour)
        part.add(self.part.var("total_water") == water)

    def handleSetting(self, v):
        if v.setting == "flour":
            self.scale = float(v.value.value)
        elif v.setting == "hydration":
            self.hydration = float(v.value.value)


Baker = Bake()
Baker.compile()
