"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July 2024
"""

import textx
import re
import sys
import numpy as np
import scipy
import operator

# The textx grammar for my recipes
grammar = r"""
Recipe: statements *= Statement[/\n+/] /\s*/;

Statement: ( Part | Text ) ;

Text: /^.*$/ ;

Part: name=ID ':' '\n' relations*=Relation['\n'];

Relation: ('hydration' '=' hydration=Number '%' ) |
          ('scale' '=' scale=Number 'g') | 
          (lhs=Sum '=' rhs=Sum) |
          (mention=ID);

Sum: term=Product sums*=Sums;

Sums: op=/[+-]/ term=Product;

Product: factor=Factor factors*=Factors;

Factors: op=/[*\/]/ factor=Factor;

Factor: '-' negated=Factor |
        name=Var |
        number=Number unit=/[%g]/ |
        '(' sum=Sum ')';

Number: str=/[0-9.]+/;

Var: names += ID['.'];

Comment: /\/\/.*?$|(?ms:\/\*.*?\*\/\n+)/;
"""


def tis(node, name):
    return type(node).__name__ == name


# These ingredients are counted in the total flour. I count grains and such
# that absorb water regardless of where they occur.

Flours = [
    "ap_flour",
    "bran",
    "bread_flour",
    "bronze_chief",
    "bulgar",
    "flaxseed_meal",
    "hard_red",
    "hard_white",
    "improver",
    "oats",
    "polenta",
    "potato_flakes",
    "prairie_gold",
    "red_rye_malt",
    "rye",
    "spelt",
    "steel_cut_oats",
    "vital_wheat_gluten",
    "vwg",
    "wgbi",
    "whole_wheat",
    "ww",
]


def flourFraction(name):
    """Compute the amount of flour in the ingredient"""
    if name in Flours or "flour" in name:
        return 1.0
    return 0.0


# These ingredients are counted as water.
water = {
    "water": 1.0,
    "egg": 0.75,
    "egg_yolk": 0.5,
    "egg_white": 0.9,
    "milk": 0.87,
    "butter": 0.18,
    "honey": 0.17,
}


def waterFraction(name):
    """Compute the amount of water in the ingredient"""
    return water.get(name, 1.0 if "water" in name else 0.0)


def fmt_grams(g):
    """Format grams in the table"""
    if g >= 100:
        r = f"{g:.0f}   "
    elif g >= 10:
        r = f"{g:0.1f} "
    else:
        r = f"{g:0.2f}"

    if len(r) < 8:
        r = " " * (8 - len(r)) + r
    return r


operators = {
    "+": (operator.add, 2),
    "-": (operator.sub, 2),
    "*": (operator.mul, 2),
    "/": (operator.truediv, 2),
}


class Relations:
    def __init__(self):
        self.program = []
        self.vars = {}
        self.relations = 0

    def var(self, name):
        if name not in self.vars:
            self.vars[name] = len(self.vars)
        return self.vars[name]

    def relation(self, *atoms):
        if debug:
            print(atoms)
        self.relations += 1
        for atom in atoms:
            if isinstance(atom, tuple):
                self.program.append(self.var(atom))

            elif isinstance(atom, (int, float)):
                self.program.append(float(atom))

            elif isinstance(atom, str):
                self.program.append(operators[atom])

    def exec(self, params):
        """Interpret the cost function"""
        stack = []
        for step in self.program:
            if isinstance(step, int):
                stack.append(params[step])

            elif isinstance(step, float):
                stack.append(step)

            elif isinstance(step, tuple):
                op, arity = step
                args = stack[-arity:]
                stack = stack[0:-arity]
                stack.append(op(*args))

        return np.array(stack)

    def solve(self):
        x0 = np.ones(len(self.vars)) * 50
        opt = scipy.optimize.least_squares(program.exec, x0)
        if debug:
            print(opt)
        return opt


program = Relations()


class Bake:
    """The recipe"""

    def __init__(self):
        try:
            self.meta = textx.metamodel_from_str(grammar, ws=" ")
        except textx.TextXSyntaxError as e:
            print(f"Grammar Error {e.line}:{e.col} {e.message}")
            sys.exit(1)
        self.meta.register_obj_processors({"Number": lambda Number: float(Number.str)})
        self.parts = []

    def compile(self, stdin, rewrite=False):
        text = stdin.read()
        try:
            self.model = self.meta.model_from_str(text)
        except textx.TextXSyntaxError as e:
            return self.output(f"Error {e.line}:{e.col} {e.message}", text)

        # get all the part names
        for part in textx.get_children_of_type("Part", self.model):
            self.parts.append(part.name)

        # add each part to the program
        for part in textx.get_children_of_type("Part", self.model):
            total = {}
            flour = {}
            water = {}

            for relation in part.relations:
                if relation.hydration:
                    program.relation(
                        (part.name, "total_water"),
                        relation.hydration / 100.0,
                        (part.name, "total_flour"),
                        "*",
                        "-",
                    )

                elif relation.scale:
                    program.relation((part.name, "total_flour"), relation.scale, "-")

                elif relation.mention:
                    name = relation.mention
                    if name in self.parts:
                        program.relation((part.name, name), (name, "total"), "-")
                        total[(part.name, name)] = 1
                        flour[(name, "total_flour")] = 1
                        water[(name, "total_water")] = 1

                    else:
                        program.var((part.name, name))
                        total[(part.name, name)] = 1
                        f = flourFraction(name)
                        if f > 0:
                            flour[(part.name, name)] = f
                        w = waterFraction(name)
                        if w > 0:
                            water[(part.name, name)] = w

                elif relation.lhs:
                    lhs = self.expr(relation.lhs, part.name, total, flour, water)
                    rhs = self.expr(relation.rhs, part.name, total, flour, water)
                    program.relation(*lhs, *rhs, "-")

            self.doTotal((part.name, "total"), total)
            self.doTotal((part.name, "total_flour"), flour)
            self.doTotal((part.name, "total_water"), water)

        opt = program.solve()

        result = []
        scale = 100 / opt.x[program.vars[("dough", "total_flour")]]
        for i, partName in enumerate(self.parts):
            pvars = {
                name[1]: opt.x[program.vars[name]]
                for name in program.vars
                if name[0] == partName and not name[1].startswith("_")
            }
            g = pvars["total"]
            bp = g * scale
            result.append(f"{partName:.<35}({g:.1f}g = {bp:.1f}%)")
            for var in pvars:
                if not var.startswith("total"):
                    g = pvars[var]
                    fg = fmt_grams(g)
                    bp = g * scale
                    result.append(f"{fg} {var.replace('_', ' '):15} {bp:6.1f}%")
            if i == len(self.parts) - 1:
                for var in ["total_flour", "total_water"]:
                    g = pvars[var]
                    fg = fmt_grams(g)
                    bp = g * scale
                    result.append(f"{fg} {var.replace('_', ' '):15} {bp:6.1f}%")
            result.append("")

        table = "\n".join(result)
        self.output(
            table, text, not opt.success or opt.cost > 1, scale if rewrite else 0
        )

    def expr(self, node, part, total, flour, water):
        if tis(node, "Sum"):
            r = self.expr(node.term, part, total, flour, water)
            for sum in node.sums:
                s = self.expr(sum.term, part, total, flour, water)
                r += [*s, sum.op]
            return r

        elif tis(node, "Product"):
            if node.factor.unit == "%" and len(node.factors) == 0:
                return [node.factor.number / 100.0, ("dough", "total_flour"), "*"]
            r = self.expr(node.factor, part, total, flour, water)
            for factor in node.factors:
                s = self.expr(factor.factor, part, total, flour, water)
                r += [*s, factor.op]
            return r

        elif tis(node, "Factor"):
            if node.negated:
                r = self.expr(node.negated, part, total, flour, water)
                return [0.0, *r, "-"]

            elif node.name:
                name = node.name.names
                if len(name) == 1:
                    if name[0] in self.parts:
                        pname = name[0]
                        name = (part, pname)
                        total[name] = 1
                        program.relation(name, (pname, "total"), "-")
                        flour[(pname, "total_flour")] = 1
                        water[(pname, "total_water")] = 1
                        return [name]
                    else:
                        name = (part, name[0])

                else:
                    name = tuple(name)

                if (
                    name[0] == part
                    and not name[1].startswith("total")
                    and not name[1].startswith("_")
                ):
                    total[name] = 1
                    f = flourFraction(name[1])
                    if f > 0:
                        flour[name] = f
                    w = waterFraction(name[1])
                    if w > 0:
                        water[name] = w
                return [name]

            elif node.number:
                if node.unit == "%":
                    return [node.number / 100.0]
                return [node.number]

            elif node.sum:
                return self.expr(node.sum, part, total, flour, water)

        else:
            print("error", node)

        return []

    def doTotal(self, name, ingredients):
        relation = [name]
        for ingredient, scale in ingredients.items():
            if scale != 1:
                relation += [ingredient, scale, "*", "-"]
            else:
                relation += [ingredient, "-"]
        program.relation(*relation)

    def output(self, table, text, failed=False, scale=0):
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
            rest = rest.lstrip()
            if scale > 0:
                rest = self.rewrite(rest, scale)
            result = f"{title}\n/*+\n{table}\n+*/\n\n{rest}"
        else:
            result = f"title\n/*+\n{table}+*/{text}"
        print(result)

    def rewrite(self, rest, scale):
        def gtobp(match):
            if match.group(1) != "scale":
                f = float(match.group(3)[:-1]) * scale
                return f"{match.group(1)}{match.group(2)}{f:.2f}%"
            else:
                return match.group(0)

        return re.sub(r"(\w+)(\s*=\s*)([\d.]+\s*g)", gtobp, rest)


Baker = Bake()
rewrite = False
debug = False
filename = ""
for arg in sys.argv[1:]:
    if arg == "-R":
        rewrite = True
    elif arg == "-D":
        debug = True
    else:
        filename = arg
if filename:
    stdin = open(filename, "rt")
else:
    stdin = sys.stdin
Baker.compile(stdin, rewrite)
