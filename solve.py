from tree import *
import numpy as np
import pandas as pd
import os
from rich.pretty import pprint

# silence obnoxious warning
# pd.set_option("future.no_silent_downcasting", True)

dir = os.path.dirname(os.path.abspath(__file__))
map_path = os.path.join(dir, "ingredients.csv")
ingredients = pd.read_csv(map_path, index_col="index")


def getIngredient(name: str):
    """Return the components for an ingredient"""
    name = name.lower()
    if name not in ingredients.index:
        if "water" in name:
            name = "water"

        elif name.endswith("_oil"):
            name = "oil"

        elif name.endswith("_flour"):
            name = "flour"

        else:
            name = "unknown"
    result = ingredients.loc[name]
    return result


def total_(name: str):
    if name == "total":
        r = name
    else:
        r = f"total_{name}"

    return r


def solve(tree: Start):
    """Solve the system of equations"""

    # gather the parts
    parts = {part.name for part in tree.parts}

    # qualify the variables
    currentPart = ""
    for node in tree.walk():
        match node:
            case Part() as part:
                currentPart = part.name
            case Var() as var:
                if not var.part:
                    var.part = currentPart

    # add totals
    for part in tree.parts:
        for column in ingredients.columns:
            part.addVar(part.name, total_(column))
        part.addVar(part.name, "total")

    # construct our result matrix
    varList = [var.t for part in tree.parts for var in part.vars]
    index = pd.MultiIndex.from_tuples(varList, names=["part", "name"])
    solution = pd.DataFrame(
        index=index,
        columns=pd.Index(["value", *list(ingredients.columns)]),
        dtype=np.float64,
    )

    # add total relations
    for part in tree.parts:
        totals: dict[str, list[Values]] = {key: [] for key in ingredients.columns}
        totals["total"] = []
        localVars = [var for var in part.vars if not var.name.startswith("total")]
        for var in localVars:
            if var.name in parts:
                for key in totals:
                    totals[key].append(Var(var.name, total_(key)))
                part.addRelation(Relation(var, Var(var.name, "total"), weight=1000.0))
            elif var.name.startswith("_"):
                continue
            else:
                info = getIngredient(var.name)
                for key in info.index.tolist():
                    if info[key] == 1:
                        totals[key].append(var)
                    elif info[key] != 0:
                        totals[key].append(Product([info[key], var]))
                totals["total"].append(var)
                solution.loc[var.t] = info
        for key in totals:
            part.addRelation(
                Relation(Var(part.name, total_(key)), Sum(totals[key]), weight=1000.0)
            )

    # additional column for the constant terms
    Ncolumns = len(solution) + 1

    def constant(value) -> Vector:
        """Create a vector representing a constant"""
        r = np.zeros(Ncolumns)
        r[Ncolumns - 1] = value
        return r

    def oneHot(var: Var, value: float = 1.0):
        """Create a vector representing a variable"""
        index = solution.index.get_loc(var.t)
        r = np.zeros(Ncolumns)
        r[index] = value
        return r

    def eval(value: Values) -> Vector | float:
        """Recursively evaluate an equation"""
        result: float | Vector
        match value:
            case Sum():
                terms = [eval(term) for term in value.terms]
                f = sum(term for term in terms if isinstance(term, (float, int)))
                c = constant(f)
                result = c + np.sum([term for term in terms if isVector(term)], axis=0)
            case Product(factors):
                result = eval(factors[0])
                for factor in factors[1:]:
                    f = eval(factor)
                    if isVector(result) and isVector(f):
                        raise NotImplementedError("Product")
                    result = result * f
                if not isVector(result):
                    result = constant(result)
            case Divide(lhs, rhs):
                l = eval(lhs)
                r = eval(rhs)
                match (l, r):
                    case (float(l), float(r)):
                        return l / r
                    case (l, float(r)) if isVector(l):
                        return l * (1 / r)
                    case _:
                        raise NotImplementedError("Division")
            case Var():
                result = oneHot(value)
            case float(value) | int(value):
                result = float(value)

        return result

    # collect rows
    rows = []
    for part in tree.parts:
        for relation in part.relations:
            lhs = eval(relation.var)
            rhs = eval(relation.value)
            if not isVector(rhs):
                rhs = constant(rhs)
            rows.append(relation.weight * (lhs - rhs))

    # build and slice up the matrix
    M = np.array(rows)
    A = M[:, :-1]
    B = -M[:, -1]
    r = np.linalg.lstsq(A, B, rcond=-1)
    X = r[0]
    residual = A @ X - B

    # Attempt to detect failure to meet the constraints
    # Calculate the "mass" involved in each constraint
    # np.abs(A) @ np.abs(X) gives the sum of magnitudes for each equation
    row_sums = np.abs(A) @ np.abs(X)
    # Avoid division by zero for empty rows
    row_sums[row_sums < 1e-9] = 1.0
    # Calculate how much the residual "matters" relative to the ingredients in that row
    relative_errors = np.abs(residual) / row_sums

    # Failed if any equation is off by more than, say, 0.1%
    failed = np.any(
        relative_errors > 0.001
    )  # Calculate the 'size' of each equation's coefficients
    errors = []
    if failed:
        errors = ["Inconsistent equations"]

    solution.value = X

    solution = solution.fillna(0.0)
    for part in tree.parts:
        for var in part.vars:
            if var.name.startswith("total_"):
                component = var.name.replace("total_", "")
                solution.at[var.t, component] = solution.loc[var.t, "value"]
            elif var.name in parts:
                for component in ingredients.columns:
                    solution.at[var.t, component] = solution.loc[
                        (var.name, total_(component)), "value"
                    ]
            else:
                solution.loc[var.t, "flour":] *= solution.loc[var.t, "value"]
    solution["bp"] = (
        solution["value"] / solution.loc[("dough", "total_flour"), "value"] * 100.0
    )

    return solution, errors
