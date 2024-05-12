test = """
# A Loaf

A description of this loaf.

```
total_flour == 100
hydration == 80bp

biga_flour == 50bp
biga_flour == starter_flour + milled_grains
biga_water == 0.5 * biga_flour - starter_water

starter_water == starter_flour
starter_total == starter_water + starter_flour
starter_total == 0.05 * biga_flour

added_water == hydration - biga_water - starter_water

total_flour == biga_flour + starter_flour + 
              potato_flakes + flaxseed_meal + bread_flour

potato_flakes == 3bp
flaxseed_meal == 2bp

add_ins == oil + honey + improver + salt + yeast + seeds

oil == 5bp
honey == 5bp
improver == 2bp
salt == 2bp
yeast == 0.3bp

seeds == 10bp

milled_grains == hard_white + hard_red + spelt + rye

hard_white == 4 * part
hard_red == 3 * part
spelt == 2 * part
rye == 1 * part

tdw == total_flour + hydration + add_ins

```

Some more text at the end.

"""

from arpeggio import Optional, ZeroOrMore, OneOrMore, Not, EOF
from arpeggio import RegExMatch as _
from arpeggio import ParserPython, PTNodeVisitor, visit_parse_tree
import pulp


def number():
    return _(r"\d*\.\d*|\d+")


def bp():
    return number, "bp"


def name():
    return _(r"[a-zA-Z_][a-zA-Z0-9_]*")


def atom():
    return [number, name]


def factor():
    return Optional(["+", "-"]), [atom, ("(", expression, ")")]


def term():
    return [(number, "*", name), bp, number, name]


def expression():
    return term, ZeroOrMore(["+", "-"], term)


def text():
    return ZeroOrMore(_(r"(?!```).*"))


def equation():
    return expression, "==", expression


def comparison():
    return expression, ["<=", ">="], Optional("-"), number


def equations():
    return _(r"^```"), OneOrMore([equation, comparison]), _(r"^```")


def chunk():
    return [equations, text]


def chunks():
    return OneOrMore(chunk), EOF


class Visitor(PTNodeVisitor):
    def __init__(self):
        super().__init__()
        self.P = pulp.LpProblem("bread", pulp.LpMinimize)
        self.vars = {}

    def var(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def visit_number(self, node, children):
        return float(node.value)

    def visit_bp(self, node, children):
        return children[0] * 0.01 * self.var("total_flour")

    def visit_name(self, node, children):
        name = node.value
        return self.var(name)

    def visit_factor(self, node, children):
        """
        Applies a sign to the expression or number.
        """
        if len(children) == 1:
            return children[0]
        sign = -1 if children[0] == "-" else 1
        return sign * children[-1]

    def visit_term(self, node, children):
        """
        Multiplies factors.
        Factor nodes will be already evaluated.
        """
        term = children[0]
        if len(children) == 2:
            term *= children[1]
        return term

    def visit_expression(self, node, children):
        """
        Adds or subtracts terms.
        Term nodes will be already evaluated.
        """
        expr = children[0]
        for i in range(2, len(children), 2):
            if i and children[i - 1] == "-":
                expr -= children[i]
            else:
                expr += children[i]
        return expr

    def visit_equation(self, node, children):
        """
        Adds an equation to the problem
        """
        self.P += children[0] == children[1]

    def visit_comparison(self, node, children):
        if children[1] == "<=":
            self.P += children[0] <= children[2]
        else:
            self.P += children[0] >= children[2]

    def values(self):
        # print(self.P)
        self.P.solve(pulp.PULP_CBC_CMD(msg=False))
        print(self.P.status)
        values = {
            var.name: var.varValue
            for var in self.P.variables()
            if not var.name.startswith("_")
        }
        result = {var: values[var] for var in self.vars}
        return result


parser = ParserPython(chunks, reduce_tree=True, debug=False)


tree = parser.parse(test)
visitor = Visitor()
result = visit_parse_tree(tree, visitor)
values = visitor.values()
for var in values:
    print(var, values[var])
