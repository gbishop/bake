"""
Bake.py - bread recipes using relationships rather than spreadsheets.

Gary Bishop July 2024
"""

import textx
import re
import sys
import numpy as np
import scipy

# The textx grammar for my recipes
grammar = r"""
Recipe: statements *= Statement[/\n+/] /\s*/;

Statement: ( Part | Text ) ;

Text: /^.*$/ ;

Part: name=ID ':' '\n' ingredients*=Ingredient['\n'];

Ingredient: ('hydration' '=' hydration=Number '%' ) |
            ('scale' '=' scale=Number 'g') | 
            (name=ID ('=' expr=Sum)? );

Sum: term=Product sums*=Sums;

Sums: op=/[+-]/ term=Product;

Product: scalar=Number unit=/[%g]/ ('*' var=Var)? |
         var=Var;

Number: str=/[0-9.]+/;

Var: a=ID ('.' b=ID)?;

Comment: /\/\/.*?$|(?ms:\/\*.*?\*\/\n+)|\|.*?\n+/;
"""

# These ingredients are counted in the total flour. I count grains and such
# that absorb water regardless of where they occur.

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
    "bran",
    "bulgar",
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


# Keep track of the mapping from variable names to indicies
Vars = {}


class Constraint:
    """One relation for constraining the solution"""

    def __init__(self, part, ingredient):
        # the key for the ingredient
        name = (part, ingredient)
        # Add it with its index into the matrix we'll construct
        if name not in Vars:
            Vars[name] = len(Vars)
        # weighted sum of ingredients
        self.terms = {name: 1.0}
        # any constant term
        self.constant = 0
        # bakers percentage that must be multipled by total_flour
        self.bp = 0

    def addTerm(self, part, ingredient, scale):
        name = (part, ingredient)
        if name not in Vars:
            Vars[name] = len(Vars)
        self.terms[name] = self.terms.get(name, 0.0) + scale

    def addConstant(self, value):
        self.constant += value

    def addBp(self, value):
        self.bp += value

    def __repr__(self):
        """Print the constraints in a readable format"""
        chunks = []
        for term, scale in self.terms.items():
            op = " + " if scale > 0 else " - "
            coeff = "" if abs(scale) == 1.0 else str(abs(scale)) + "*"
            name = ".".join(term)
            chunk = f"{op}{coeff}{name}"
            chunks.append(chunk)
        s = "".join(chunks)
        if self.constant != 0:
            op = " + " if self.constant > 0 else " - "
            s = s + op + str(abs(self.constant))
        if self.bp != 0:
            op = " + " if self.bp > 0 else " - "
            s = s + op + "BP * " + str(abs(self.bp))
        return s.strip()


class TotalConstraint(Constraint):
    """A constraint that only counts an ingredient once"""

    def addTerm(self, part, ingredient, scale):
        name = (part, ingredient)
        if name not in Vars:
            Vars[name] = len(Vars)
        self.terms[name] = scale


class Bake:
    """The recipe"""

    def __init__(self):
        self.meta = textx.metamodel_from_str(grammar, ws=" ")
        self.meta.register_obj_processors({"Number": lambda Number: float(Number.str)})
        self.vars = Vars
        self.parts = []
        self.constraints = []

    def compile(self, stdin, rewrite=False):
        text = stdin.read()
        try:
            self.model = self.meta.model_from_str(text)
        except textx.TextXSyntaxError as e:
            return self.output(f"Error {e.line}:{e.col} {e.message}", text)

        # build a list of constraints
        for part in textx.get_children_of_type("Part", self.model):
            self.parts.append(part.name)
            total = TotalConstraint(part.name, "total")
            total_flour = TotalConstraint(part.name, "total_flour")
            total_water = TotalConstraint(part.name, "total_water")
            for ingredient in part.ingredients:
                if ingredient.name:
                    if ingredient.name in self.parts:
                        # reference to another part
                        opart = ingredient.name
                        total.addTerm(opart, "total", -1)
                        total_flour.addTerm(opart, "total_flour", -1)
                        total_water.addTerm(opart, "total_water", -1)
                        c = Constraint(part.name, ingredient.name)
                        c.addTerm(opart, "total", -1.0)
                        self.constraints.append(c)
                        if ingredient.expr:
                            c = self.handleExpr(ingredient, part)
                            self.constraints.append(c)
                    elif ingredient.name.startswith("_"):
                        # variables that are not ingredients
                        if ingredient.expr:
                            c = self.handleExpr(ingredient, part)
                            self.constraints.append(c)
                    elif "total" in ingredient.name:
                        if ingredient.expr:
                            c = self.handleExpr(ingredient, part)
                            self.constraints.append(c)
                    else:
                        # an ordinary ingredient
                        total.addTerm(part.name, ingredient.name, -1.0)
                        f = flourFraction(ingredient.name)
                        if f > 0:
                            total_flour.addTerm(part.name, ingredient.name, -f)
                        w = waterFraction(ingredient.name)
                        if w > 0:
                            total_water.addTerm(part.name, ingredient.name, -w)
                        if ingredient.expr:
                            c = self.handleExpr(ingredient, part)
                            self.constraints.append(c)

                elif ingredient.hydration:
                    c = Constraint(part.name, "total_water")
                    c.addTerm(part.name, "total_flour", -ingredient.hydration / 100)
                    self.constraints.append(c)
                elif ingredient.scale:
                    c = Constraint(part.name, "total_flour")
                    c.addConstant(-ingredient.scale)
                    self.constraints.append(c)
                else:
                    continue

            self.constraints.append(total)
            self.constraints.append(total_flour)
            self.constraints.append(total_water)

        if debug:
            print(self.vars)
            for constraint in self.constraints:
                print(constraint)

        opt = self.solve()

        result = []
        scale = 100 / opt.x[self.vars[(self.parts[-1], "total_flour")]]
        for i, partName in enumerate(self.parts):
            pvars = {
                name[1]: opt.x[self.vars[name]]
                for name in self.vars
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

    def handleExpr(self, ingredient, part):
        expr = ingredient.expr

        c = Constraint(part.name, ingredient.name)

        terms = [[1, expr.term]] + [
            [1 if sum.op == "+" else -1, sum.term] for sum in expr.sums
        ]

        for sign, term in terms:
            if term.var:
                if term.var.b:
                    pname = term.var.a
                    iname = term.var.b
                elif term.var.a in self.parts:
                    pname = term.var.a
                    iname = "total"
                else:
                    pname = part.name
                    iname = term.var.a
                if term.scalar:
                    scalar = sign * term.scalar
                    if term.unit == "%":
                        scalar /= 100
                else:
                    scalar = sign
                c.addTerm(pname, iname, -1 * scalar)
            else:
                if term.unit == "%":
                    c.addBp(-sign * term.scalar)
                else:
                    c.addConstant(-sign * term.scalar)

        return c

    def solve(self):
        coeff = np.zeros([len(self.constraints), len(self.vars)])
        const = np.zeros(len(self.constraints))
        bp = np.zeros(len(self.constraints))
        x0 = np.ones(len(self.vars)) * 50

        for row, c in enumerate(self.constraints):
            for name, scale in c.terms.items():
                col = self.vars[name]
                coeff[row, col] = scale
            const[row] = c.constant
            bp[row] = c.bp

        def cost(
            x,  # current solution estimate
            m,  # linear terms
            n,  # terms scaled by total flour
            c,  # constant terms
            ti,  # index of the total flour
        ):
            lv = np.dot(m, x)
            nv = n * x[ti] / 100
            return lv + nv + c

        ti = self.vars[(self.parts[-1], "total_flour")]
        opt = scipy.optimize.least_squares(cost, x0, args=(coeff, bp, const, ti))

        return opt

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
