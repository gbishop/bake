from ingredients import getIngredient
from lark import Lark, Visitor, visitors
import lark
import numpy as np

# Lark grammar for my formulas
grammar = r"""
start: part*

part: ID [ "^" NUMBER ] ":" (hydration | relation | mention)+

hydration: "hydration" "=" NUMBER

relation: sum "=" sum

sum: product "+" sum   -> add
   | product "-" sum   -> subtract
   | product

product: mention
       | scale "*" mention  -> multiply
       | mention "/" NUMBER -> divide
       | NUMBER -> constant

scale: NUMBER ("*" NUMBER)*

mention: ID
       | ID "." ID

ID: /[a-zA-Z_][a-zA-Z_0-9]*/
NUMBER: /[0-9]+([.][0-9]+)?[g%]?/

WHITESPACE: /[ \n]+/ 
%ignore WHITESPACE

COMMENT:  "/*" /(.|\n|\r)*?/ "*/"     
       |  "#" /(.)+\n/ 
%ignore COMMENT
"""


class SymbolTable:
    """Collect information about our unknowns"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.symbol_count = 0
        self.name_to_index = {}
        self.index_to_name = {}
        self.parts = {}
        self.loss = {}

    def add(self, name, value=-1):
        """Add a name if it isn't already known"""
        if name not in self.name_to_index:
            if value >= 0:
                self.name_to_index[name] = value
            else:
                self.name_to_index[name] = self.symbol_count
                self.index_to_name[self.symbol_count] = name
                self.symbol_count += 1
        return self.name_to_index[name]

    def vector(self, name):
        """Create a matrix row representing this unknown"""
        r = np.zeros(self.symbol_count + 1)
        r[self.name_to_index[name]] = 1
        return r

    def dump(self, vector):
        """Make a vector readable"""
        s = ""
        for i in range(self.symbol_count):
            name = ".".join(self.index_to_name[i])
            if vector[i] == 1:
                s += f" + {name}"
            elif vector[i] < 0:
                s += f" - {-vector[i]} * {name}"
            elif vector[i] > 0:
                s += f" + {vector[i]} * {name}"
        if vector[-1] < 0:
            s += f" - {-vector[-1]}"
        elif vector[-1] > 0:
            s += f" + {-vector[-1]}"

        if s.startswith(" + "):
            s = s[3:]
        return s

    def constant(self, value):
        """Create a vector representing a numeric constant"""
        r = np.zeros(self.symbol_count + 1)
        r[-1] = value
        return r


ST = SymbolTable()


def isPercent(s):
    """Test if a string represents a percentage"""
    return s.endswith("%")


def number(s):
    """Get the value of a number based on its units"""
    if s.endswith("%"):
        return float(s[:-1]) / 100
    elif s.endswith("g"):
        return float(s[:-1])
    else:
        return float(s)


class GetParts(Visitor):
    """Scan the tree for part names"""

    def part(self, tree):
        name = tree.children[0] + ""
        ST.add((name, "total"))
        ST.add((name, "total_flour"))
        ST.add((name, "total_water"))
        ST.add((name, "total_fat"))

        ST.parts[name] = None


class GetUnknowns(Visitor):
    """Scan the tree for names of unknowns"""

    def mention(self, tree):
        if len(tree.children) == 1:
            name = tree.children[0] + ""
            fullname = (self.part_name, name)
            if name in ST.parts:
                ST.add(fullname, ST.add((name, "total")))
            else:
                ST.add(fullname)

    def part(self, tree):
        self.part_name = tree.children[0] + ""


class BuildMatrix(visitors.Interpreter):
    """Setup the matrix representing the relations"""

    def start(self, tree):
        r = self.visit_children(tree)
        residuals = []
        for relations in r:
            for lhs, rhs in relations:
                residuals.append(lhs - rhs)
        if len(residuals):
            # add a weak bias toward 1kg of flour
            residuals.append(
                1e-4 * (ST.vector(("dough", "total_flour")) - ST.constant(1000))
            )
            R = np.array(residuals)
            A = R[:, :-1]
            B = -R[:, -1]
        else:
            A = []
            B = []
        return A, B

    def part(self, tree):
        total_names = ["total", "total_flour", "total_water", "total_fat"]
        part = self.part_name = tree.children[0]
        r = self.visit_children(tree)
        _, theloss, *relations = r
        if theloss:
            ST.loss[part] = (number(theloss), isPercent(theloss))
        # we only want the relations which are lists
        relations = [row for row in relations if type(row) == list]
        totals = {}
        for total_name in total_names:
            totals[total_name] = np.zeros(ST.symbol_count + 1)
        for fullname in ST.name_to_index:
            if fullname[0] != part:
                continue
            if fullname[1].startswith("total"):
                continue
            if fullname[1] in ST.parts:
                for total_name in total_names:
                    totals[total_name] += ST.vector((fullname[1], total_name))
            else:
                vect = ST.vector(fullname)
                totals["total"] += vect
                info = getIngredient(fullname[1])
                for total_name in total_names[1:]:
                    field_name = total_name.replace("total_", "")
                    w = info[field_name]
                    totals[total_name] += w * vect
        for total_name in total_names:
            relations.append([ST.vector((part, total_name)), totals[total_name]])

        return relations

    def hydration(self, tree):
        r = self.visit_children(tree)
        v = number(r[0])
        return [
            ST.vector((self.part_name, "total_water")),
            v * ST.vector((self.part_name, "total_flour")),
        ]

    def add(self, tree):
        r = self.visit_children(tree)
        return r[0] + r[1]

    def subtract(self, tree):
        r = self.visit_children(tree)
        return r[0] - r[1]

    def multiply(self, tree):
        r = self.visit_children(tree)
        return r[0] * r[1]

    def divide(self, tree):
        r = self.visit_children(tree)
        return r[0] / r[1]

    def constant(self, tree):
        r = self.visit_children(tree)
        value = number(r[0])
        if isPercent(r[0]):
            return ST.vector(("dough", "total_flour")) * value
        else:
            return ST.constant(value)

    def scale(self, tree):
        r = self.visit_children(tree)
        result = number(r[0])
        for n in r[1:]:
            result *= number(n)
        return result

    def mention(self, tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            fullname = (self.part_name, r[0])
        else:
            fullname = tuple(r)
        return ST.vector(fullname)

    def __default__(self, tree):
        r = self.visit_children(tree)
        if len(r) == 1:
            return r[0]
        else:
            return r


def solve(text):
    def result(error="", message="", rows=[], residual=0, grams_to_bp=0):
        return dict(
            error=error,
            message=message,
            rows=rows,
            residual=residual,
            grams_to_bp=grams_to_bp,
        )

    ST.reset()

    parser = Lark(grammar)

    try:
        tree = parser.parse(text)
    except lark.exceptions.UnexpectedToken as error:
        return result(
            error="Syntax Error",
            message=f"Unexpected token {error.line}:{error.column}\n${ error.get_context(text) }",
        )

    except lark.exceptions.UnexpectedCharacters as error:
        return result(
            error="Syntax Error",
            message=f"Unexpected characters {error.line}:{error.column}\n${ error.get_context(text) }",
        )
    except lark.exceptions.UnexpectedEOF as error:
        return result(
            error="Syntax Error",
            message=f"Unexpected end of file {error.line}:{error.column}\n${error.get_context(text)}",
        )

    GetParts().visit(tree)

    GetUnknowns().visit_topdown(tree)

    A, B = BuildMatrix().visit(tree)

    if len(A) == 0:
        return result()

    r = np.linalg.lstsq(A, B, rcond=-1)

    X = r[0]

    residuals = A.dot(X) - B

    error = np.sqrt(np.mean(residuals**2))

    solution = {name: X[index] for name, index in ST.name_to_index.items()}

    # reshape the data into a list of parts
    rows = []
    dtf = solution[("dough", "total_flour")]
    if dtf == 0:
        return result(error="Value error", message="No flour")
    grams_to_bp = 100 / solution[("dough", "total_flour")]
    for partName in ST.parts:
        loss_value, isPercent = ST.loss.get(partName, (0, False))
        gt = g = solution[(partName, "total")]
        if isPercent:
            loss_value = loss_value * gt
        loss_scale = (gt + loss_value) / gt
        bp = g * grams_to_bp
        # add the total
        rows.append(
            [
                partName.replace("_", " "),
                g * loss_scale,
                f"+ {loss_value:.1f}g" if loss_value > 0 else "",
                bp,
                solution[(partName, "total_flour")],
                solution[(partName, "total_water")],
                solution[(partName, "total_fat")],
            ]
        )
        # add the ingredients from the part
        for pn, var in solution:
            if pn != partName:
                continue
            if not var.startswith("total") and not var.startswith("_"):
                pg = solution[(partName, var)]
                if var in ST.parts:
                    extras = [
                        solution[(var, "total_flour")],
                        solution[(var, "total_water")],
                        solution[(var, "total_fat")],
                    ]
                else:
                    info = getIngredient(var)
                    extras = [
                        pg * info["flour"],
                        pg * info["water"],
                        pg * info["fat"],
                    ]
                rows.append(
                    [
                        "",
                        pg * loss_scale,
                        var.replace("_", " "),
                        pg * grams_to_bp,
                        *extras,
                    ]
                )
        if partName == "dough":
            # add the hydration because I miss it
            rows.append(
                [
                    "",
                    0,
                    "hydration",
                    solution[("dough", "total_water")] * grams_to_bp,
                    0,
                    0,
                    0,
                ]
            )
        # add a blank line
        rows.append([""])

    if error > 1:
        return result(
            error="Value error",
            message=f"Residual = {error:.2f}",
            rows=rows,
            residual=error,
            grams_to_bp=grams_to_bp,
        )

    return result(rows=rows, grams_to_bp=grams_to_bp, residual=error)
