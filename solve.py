from tree import *
import numpy as np
import pandas as pd
import os
from typing import cast
import pprint

dir = os.path.dirname(os.path.abspath(__file__))
map_path = os.path.join(dir, "ingredients.csv")
ingredients = pd.read_csv(map_path, index_col="index")


def getIngredient(name: str) -> pd.Series:
    """Return the components for an ingredient"""
    name = name.lower()
    if name not in ingredients.index:
        if "water_" in name or "_water" in name:
            name = "water"

        elif name.endswith("_oil"):
            name = "oil"

        elif name.endswith("_flour"):
            name = "flour"

        else:
            name = "unknown"
    result = ingredients.loc[name]
    result["total"] = 1
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

    columns = list(ingredients.columns)
    flour_water = ["flour", "water"]
    # nutrients such as protein, fiber, fat, carbs
    nutrients = [column for column in columns if column not in flour_water]

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
        for column in flour_water:
            part.addVar(total_(column))
        part.addVar("total")

    # construct our result matrix
    varList = [var.t for part in tree.parts for var in part.vars]
    index = pd.MultiIndex.from_tuples(varList, names=["part", "name"])
    solution = pd.DataFrame(
        index=index,
        columns=pd.Index(["value", *flour_water, *nutrients]),
        dtype=np.float64,
    )
    # add total relations
    for part in tree.parts:
        totals = pd.Series({key: Sum() for key in flour_water})
        totals["total"] = Sum()
        totalComponents: list[str] = list(totals.index)
        localVars = [var for var in part.vars if not var.name.startswith("total")]
        for var in localVars:
            if var.name in parts:
                totals += [
                    Var(var.name, total_(component)) for component in totalComponents
                ]
                part.addRelation(Relation(var, Var(var.name, "total"), weight=1000.0))
            elif var.name.startswith("_"):
                continue
            else:
                info = getIngredient(var.name)
                totals += info * var
                solution.loc[var.t] = info
        for component in totalComponents:
            part.addRelation(
                Relation(
                    Var(part.name, total_(component)),
                    cast(Values, totals[component]),
                    weight=1000.0,
                )
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
            case Var():
                result = oneHot(value)
            case float(value) | int(value):
                result = float(value)

        return result

    # collect relations
    relations = [relation for part in tree.parts for relation in part.relations]

    # build the matrix
    rows = []
    for relation in relations:
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
    # np.abs(A) @ np.abs(X) gives the sum of magnitudes for each equation
    row_sums = np.abs(A) @ np.abs(X)
    # Avoid division by zero for empty rows
    row_sums[row_sums < 1e-9] = 1.0
    # Calculate how much the residual "matters" relative to the ingredients in that row
    relative_errors = np.abs(residual) / row_sums

    failed = False
    errors = []
    for i, re in enumerate(relative_errors):
        if re > 0.001:
            failed = True
            errors.append(
                f"{format(relations[i])} --> ({re*100:.1f}% {residual[i]:.2f})"
            )

    if failed:
        errors.append("Inconsistent equations")
        errors.append("")

    solution.value = X
    to_scale = ["flour", "water", *nutrients]
    solution[to_scale] = solution[to_scale].mul(solution["value"], axis=0)
    solution = solution.fillna(0.0)

    # Identify all unique stages
    all_parts = solution.index.get_level_values(0).unique().tolist()

    # Build a dependency map: { 'dough': ['starter'], 'starter': [] }
    deps = {
        part: [
            ing for ing in solution.loc[part].index if ing in all_parts and ing != part
        ]
        for part in all_parts
    }

    # Topological Sort (Kahn's Algorithm simplified)
    ordered_stages = []
    while deps:
        # Find stages with no dependencies left
        ready = [p for p, d in deps.items() if not d]
        if not ready:
            # If this happens, you have a circular dependency (e.g., A needs B, B needs A)
            raise ValueError("Circular dependency detected!")

        for p in ready:
            ordered_stages.append(p)
            del deps[p]
            # Remove p from the dependency lists of other stages
            for other in deps:
                if p in deps[other]:
                    deps[other].remove(p)

    # Define your target columns

    for stage in ordered_stages:
        # 1. Identify which rows are actual inputs for this stage
        # Exclude the summary rows to prevent double-counting
        exclude = ["total", "total_flour", "total_water", "_loss"]
        ingredient_rows = solution.loc[stage].index.difference(exclude)

        # 2. Sum the ingredients to get the 'Actual' nutrients for this part
        sums = solution.loc[(stage, ingredient_rows), columns].sum()

        # 3. Update the summary 'total' row for this stage
        solution.loc[(stage, "total"), columns] = sums

        # 4. PROPAGATE: Find where this stage is used as an ingredient in FUTURE stages
        # Example: If we just finished 'starter', update ('dough', 'starter')
        # We use a cross-section (xs) or a mask to find level 1 == stage
        idx = pd.IndexSlice
        # Find rows where the ingredient NAME matches the current stage
        # but the PART name is different (to avoid updating the definition itself)
        usage_mask = (solution.index.get_level_values(1) == stage) & (
            solution.index.get_level_values(0) != stage
        )

        if usage_mask.any():
            # Update the 'ingredient' row in the next stage with the 'total' from this stage
            # We use .values to avoid index alignment issues
            solution.loc[usage_mask, columns] = sums.values

    # scale the nutrients to grams / 100g based on 9% loss while baking
    # baked_weight = solution.loc[("dough", "total"), "value"] * 0.91
    # solution[nutrients] *= 100 / baked_weight

    solution["bp"] = (
        solution["value"] / solution.loc[("dough", "total_flour"), "value"] * 100.0
    )

    return solution, errors
