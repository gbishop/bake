"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July 2024
"""

import textx
import re
import sys
import numpy as np
from numpy.typing import NDArray
import scipy
import operator
from typing import Callable, TextIO

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

# define the components of some ingredients
Ingredients = {
    # flours
    "ap_flour": {"flour": 1.0},
    "bran": {"flour": 1.0},
    "bread_flour": {"flour": 1.0},
    "bronze_chief": {"flour": 1.0},
    "bulgar": {"flour": 1.0},
    "cracked_rye": {"flour": 1.0},
    "flaxseed_meal": {"flour": 1.0},
    "hard_red": {"flour": 1.0},
    "hard_white": {"flour": 1.0},
    "improver": {"flour": 1.0},
    "oats": {"flour": 1.0},
    "polenta": {"flour": 1.0},
    "potato_flakes": {"flour": 1.0},
    "prairie_gold": {"flour": 1.0},
    "red_rye_malt": {"flour": 1.0},
    "rye": {"flour": 1.0},
    "spelt": {"flour": 1.0},
    "steel_cut_oats": {"flour": 1.0},
    "vital_wheat_gluten": {"flour": 1.0},
    "vwg": {"flour": 1.0},
    "wgbi": {"flour": 1.0},
    "whole_wheat": {"flour": 1.0},
    "ww": {"flour": 1.0},
    # liquids and fats
    "water": {"water": 1.0},
    "egg": {"water": 0.75, "fat": 0.09},
    "egg_yolk": {"water": 0.5, "fat": 0.30},
    "egg_white": {"water": 0.90},
    "milk": {"water": 0.87, "fat": 0.035},
    "nido": {"fat": 0.3},
    "butter": {"water": 0.18, "fat": 0.80},
    "honey": {"water": 0.17},
    # oils
    "oil": {"fat": 1.0},
    "olive_oil": {"fat": 1.0},
}

Components = ["flour", "water", "fat"]


def getIngredient(name: str) -> dict[str, float]:
    """Return the components for an ingredient"""
    name = name.lower()
    if name in Ingredients:
        return Ingredients[name]
    if "flour" in name:
        return {"flour": 1.0}
    if "water" in name:
        return {"water": 1.0}
    if name.endswith("_oil"):
        return {"fat": 1.0}
    return {}


# mapping from character to function and arity
operators: dict[str, tuple[Callable, int]] = {
    "+": (operator.add, 2),
    "-": (operator.sub, 2),
    "*": (operator.mul, 2),
    "/": (operator.truediv, 2),
}


class Relations:
    """Build and evaluate the residuals for the relations"""

    def __init__(self):
        self.program: list[tuple[Callable, int] | int | float] = []
        self.vars: dict[tuple[str, str], int] = {}
        self.relations = 0

    def var(self, name):
        """Get the index for a variable"""
        if name not in self.vars:
            self.vars[name] = len(self.vars)
        return self.vars[name]

    def relation(self, *atoms: tuple[str, str] | int | float | str):
        """Add a relation"""
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

    def exec(self, params: NDArray):
        """Interpret the residuals by running the program"""
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
        """Run the optimizer on the program"""
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
        self.total = {}

    def compile(self, stdin: TextIO, rewrite=False):
        """Compile the recipe into a program for the solver"""
        text = stdin.read()
        try:
            self.model = self.meta.model_from_str(text)
        except textx.TextXSyntaxError as e:
            print(f"Syntax Error {e.line}:{e.col} {e.message}")
            sys.exit(1)

        # get all the part names
        for part in textx.get_children_of_type("Part", self.model):
            self.parts.append(part.name)

        # add each part to the program
        for part in textx.get_children_of_type("Part", self.model):
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
                        self.total[(part.name, name)] = name

                    else:
                        program.var((part.name, name))
                        self.total[(part.name, name)] = getIngredient(name)

                elif relation.lhs:
                    lhs = self.expr(relation.lhs, part.name)
                    rhs = self.expr(relation.rhs, part.name)
                    program.relation(*lhs, *rhs, "-")

            self.doTotal(part.name)

        opt = program.solve()

        scale = 100 / opt.x[program.vars[("dough", "total_flour")]]

        table = self.format_table(opt, scale)
        self.output(
            table, text, not opt.success or opt.cost > 1, scale if rewrite else 0
        )

    def format_table(self, opt, scale):
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

        result = []
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
                result.append("")
                for component in Components:
                    var = "total_" + component
                    g = pvars[var]
                    if g < 1:
                        continue
                    fg = fmt_grams(g)
                    bp = g * scale
                    result.append(f"{fg} {var.replace('_', ' '):15} {bp:6.1f}%")
            result.append("")

        return "\n".join(result)

    def expr(self, node, part):
        """Return code for an expression"""
        return getattr(self, node.__class__.__name__)(node, part)

    def Sum(self, node, part):
        """Return code for addition/subtraction"""
        r = self.expr(node.term, part)
        for sum in node.sums:
            s = self.expr(sum.term, part)
            r += [*s, sum.op]
        return r

    def Product(self, node, part):
        """Return code for multiplication/division"""
        if node.factor.unit == "%" and len(node.factors) == 0:
            return [node.factor.number / 100.0, ("dough", "total_flour"), "*"]
        r = self.expr(node.factor, part)
        for factor in node.factors:
            s = self.expr(factor.factor, part)
            r += [*s, factor.op]
        return r

    def Factor(self, node, part):
        """Return code for variables, numbers, parenthesized expressions, negation"""
        if node.negated:
            r = self.expr(node.negated, part)
            return [0.0, *r, "-"]

        elif node.name:
            name = node.name.names
            if len(name) == 1:
                if name[0] in self.parts:
                    pname = name[0]
                    name = (part, pname)
                    self.total[name] = pname
                    program.relation(name, (pname, "total"), "-")
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
                self.total[name] = getIngredient(name[1])
            return [name]

        elif node.number:
            if node.unit == "%":
                return [node.number / 100.0]
            return [node.number]

        elif node.sum:
            return self.expr(node.sum, part)

    def doTotal(self, part):
        """Generate code for the totals for a part"""
        relation = [(part, "total")]
        crelations = {}
        for component in Components:
            crelations[component] = [(part, "total_" + component)]
        for ingredient, components in self.total.items():
            if ingredient[0] != part:
                continue
            relation += [ingredient, "-"]
            if isinstance(components, str):
                for cname in Components:
                    crelation = crelations[cname]
                    crelation += [(components, "total_" + cname), "-"]
            else:
                for component, value in components.items():
                    crelation = crelations[component]
                    if isinstance(value, tuple):
                        crelation += [value, "-"]
                    else:
                        crelation += [ingredient, value, "*", "-"]

        program.relation(*relation)
        for crelation in crelations.values():
            program.relation(*crelation)

    def output(self, table, text, failed=False, scale=0):
        """Insert the table into the input"""
        text = re.sub(r"(?ms)\/\*\+.*?\+\*\/\n", "", text)
        if scale > 0:
            text = self.rewrite(text, scale)

        if failed:
            table = re.sub(r"^", "E ", table, 0, re.M)
        result = f"{text}/*+\n{table}+*/\n"
        print(result)

    def rewrite(self, rest, scale):
        """Rewrite grams as baker's percent"""

        def gtobp(match):
            if match.group(1) not in [
                "scale",
                "total_flour",
                "total_water",
                "total_fat",
                "total",
            ]:
                f = float(match.group(3)[:-1]) * scale
                return f"{match.group(1)}{match.group(2)}{f:.2f}%"
            else:
                return match.group(0)

        return re.sub(r"(\w+)(\s*=\s*)([\d.]+\s*g)", gtobp, rest)


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

Baker = Bake()
Baker.compile(stdin, rewrite)
