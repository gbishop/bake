import textx
import pulp
import re
import sys

Flours = [
    "prairie_gold",
    "hard_white",
    "bronze_chief",
    "hard_red",
    "vwg",
    "vital_wheat_gluten",
    "ww",
    "whole_wheat",
    "rye",
    "polenta",
    "flaxseed_meal",
    "potato_flakes",
    "spelt",
    "ap_flour",
    "red_rye_malt",
    "oats",
    "steel_cut_oats",
    "bread_flour",
]


def flourFraction(name):
    if name in Flours or "flour" in name:
        return 1.0
    return 0.0


water = {
    "water": 1.0,
    "egg": 0.75,
    "egg_yolk": 0.5,
    "egg_white": 0.9,
    "milk": 0.87,
}


def waterFraction(name):
    return water.get(name, 1.0 if "water" in name else 0.0)


class Part:
    def __init__(self, name):
        self.name = name
        self.constraints = []
        self.vars = {}
        self.values = {}
        self.limit = 0
        self.limitScale = 1
        self.units = "%"

    def var(self, name):
        if name not in self.vars:
            lpname = f"{self.name}.{name}"
            self.vars[name] = pulp.LpVariable(lpname, 0, None)
        return self.vars[name]

    def add(self, var, op, value):
        if op == "=":
            self.constraints.append([var, op, value])

    def print(self, scale, last=False, total=1):
        result = []
        bp = self.values["total"] / total
        g = bp * scale
        result.append(f"{self.name:.<35}({g:.1f}g = {100*bp:.1f}%)")
        for var in self.vars:
            if last and var != "total" or not var.startswith("total"):
                bp = self.values[var] / total
                g = bp * scale
                result.append(f"   {g:6.1f} {var.replace('_', ' '):15} {100*bp:6.2f}%")
        result.append("")
        return "\n".join(result)

    def applyLimit(self):
        total = self.values["total"]
        if total > self.limit and self.limitScale == 1:
            self.limitScale = self.limit / total
            return True


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
                "Units": self.handleUnits,
            }
        )
        self.parts = {}
        self.limits = []
        self.units = "%"

    def compile(self):
        text = sys.stdin.read()
        try:
            self.model = self.meta.model_from_str(text)
        except textx.TextXSyntaxError as e:
            return self.output(f"Error {e.line}:{e.col} {e.message}", text)
        parts = list(self.parts.values())
        if self.units == "%":
            parts[-1].add(parts[-1].var("total_flour"), "=", 1)
        failed = self.solve()
        N = len(parts)
        if self.units == "%":
            total = 1
        else:
            total = parts[-1].values["total_flour"]
        result = "\n".join(
            part.print(self.scale, last=i == N - 1, total=total)
            for i, part in enumerate(parts)
        )
        return self.output(result, text, failed)

    def solve(self):
        parts = self.parts
        for _ in range(10):
            problem = pulp.LpProblem("bake")
            problem += 0  # objective goes here
            for part in parts.values():
                total = 0
                flour = 0
                water = 0
                for var in part.vars:
                    if "total" in var:
                        continue
                    if var in self.parts:
                        otherPart = self.parts[var]
                        ls = otherPart.limitScale
                        total += ls * otherPart.var("total")
                        water += ls * otherPart.var("total_water")
                        flour += ls * otherPart.var("total_flour")
                        problem += part.var(var) == ls * otherPart.var("total")
                    else:
                        f = flourFraction(var)
                        if f > 0:
                            flour += f * part.var(var)
                        w = waterFraction(var)
                        if w > 0:
                            water += w * part.var(var)
                        total += part.var(var)

                for var, op, value in part.constraints:
                    if op == "=":
                        problem += var == value

                problem += part.var("total") == total
                problem += part.var("total_water") == water
                problem += part.var("total_flour") == flour

            problem.solve(pulp.PULP_CBC_CMD(msg=False))
            failed = problem.status < 1
            for var in problem.variables():
                if "." in var.name:
                    part, ingredient = var.name.split(".")
                    self.parts[part].values[ingredient] = var.varValue
            if failed:
                return failed
            for part in self.limits:
                if part.applyLimit():
                    break
            else:
                break

        return False

    def output(self, table, text, failed=False):
        match = re.match(
            r"(?ms)(?P<title>.*?\n)?\s*(?P<table>\/\*\+.*?\+\*\/)?(?P<rest>.*)",
            text,
        )
        if match:
            title = match.group("title") or "the title"
            title = title.strip()
            table = table.strip()
            if failed:
                table = re.sub(r"^", "E ", table, 0, re.M)
            rest = match.group("rest")
            result = f"{title}\n/*+\n{table}\n+*/{rest}"
        else:
            result = f"title\n/*+\n{table}+*/{text}"
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
        part = self.part
        if not v.name:
            if v.hydration:
                part.add(
                    part.var("total_water"),
                    "=",
                    v.hydration.value * part.var("total_flour"),
                )
            elif v.scale:
                self.scale = v.scale.value
            return

        name = v.name
        var = part.var(name)

        if name in self.parts:
            otherPart = self.parts[v.name]
            if v.limit:
                otherPart.limit = v.limit.value
                self.limits.append(otherPart)
            elif v.parameter:
                othervar = otherPart.var(v.parameter.name)
                otherPart.add(othervar, "=", v.parameter.value.pulp)

        if v.expr:
            part.add(var, "=", v.expr.pulp)

    def handleUnits(self, v):
        self.units = v.units

    def handleSetting(self, v):
        print("setting", v)
        if v.setting == "units":
            self.units = v.value
            print(self.units)
        elif v.setting == "flour":
            self.scale = float(v.value.value)
        elif v.setting == "hydration":
            self.hydration = float(v.value.value)


Baker = Bake()
Baker.compile()
