import numpy as np
from symbolTable import SymbolTable
from formula import formulaV, formulaN, FormulaError
from models import Relation
import re
from dataclasses import replace


def solveRelations(relations: list[Relation], convertToBP=False) -> list[Relation]:
    if len(relations) == 0:
        return []

    ST = SymbolTable()

    # collect the part names and add their total variables
    for row in relations:
        if row.part:
            part = row.part
            ST.part = part
            for total in ST.totals:
                ST.add(total)

    # collect the unknowns
    for row in relations:
        if row.part:
            ST.part = row.part
        elif row.name and row.name != "hydration" and row.name not in ST.parts:
            ST.add(row.name)

    invalidFormulas = {}
    M = []

    # Add the total rows first so I can block partition
    for row in relations:
        if row.part:
            ST.part = row.part
            for total in ST.totals:
                M.append(ST.vector(total, -1))

    # Add rows for relations
    partTotals = {}
    for rowIndex, row in enumerate(relations):
        formula_text = row.formula or ""
        value = None
        if formula_text:
            try:
                value = formulaV(ST, formula_text, row.name == "hydration")
            except FormulaError as err:
                invalidFormulas[rowIndex] = err.msg
            except:
                invalidFormulas[rowIndex] = "Internal Error"
        if row.part:
            ST.part = row.part
            for total in ST.totals:
                partTotals[total] = M[ST.index(total)]
            if value is not None:
                M.append(value - ST.vector("total_mass"))
        elif row.name:
            name = row.name
            if name == "hydration":
                if value is not None:
                    M.append(value - ST.vector("total_water"))
            else:
                profile = ST.profileVectors(name)
                if not name.startswith("total"):
                    for total in ST.totals:
                        partTotals[total] += profile[total.replace("total_", "")]
                if value is not None:
                    M.append(value - profile["mass"])

    if len(invalidFormulas) > 0:
        updatedRelations = []
        for rowIndex, row in enumerate(relations):
            updatedRelations.append(
                replace(row, _invalid=invalidFormulas.get(rowIndex, ""))
            )
        return updatedRelations

    M = np.array(M)
    A = M[:, :-1]
    b = -M[:, -1]
    K = 3 * len(ST.parts)

    # partition into totals and ingredients so any least-squares
    # tension doesn't get pushed into the totals

    A_tt = A[:K, :K]  # totals related to other totals
    A_ti = A[:K, K:]  # totals related to ingredients
    A_it = A[K:, :K]  # ingredients related to totals
    A_ii = A[K:, K:]  # ingredients related to ingredients
    b_i = b[K:]  # constants for ingredients

    # map from ingredients to totals
    C = -np.linalg.solve(A_tt, A_ti)

    # reduced equations for ingredients only
    A_red = A_ii + A_it @ C
    b_red = b_i

    # solve for the ingredients using least squares
    x_i = np.linalg.lstsq(A_red, b_red)[0]

    x_i = np.round(x_i, decimals=1)

    # compute the totals
    x_t = C @ x_i

    x_t = np.round(x_t, decimals=1)

    # join them to form the solution vector
    x = np.concatenate((x_t, x_i))

    ST.setValues(x)

    try:
        TF = ST.value("total_flour", "dough")
    except KeyError:
        return relations

    updatedRelations = []
    for i, row in enumerate(relations):
        name = ""
        if row.part:
            ST.part = row.part
            name = row.part
        elif row.name:
            name = row.name
        name = name.strip()
        if name == "hydration":
            pw = ST.value("total_water")
            pf = ST.value("total_flour")

            urow = replace(
                row, bp=round((100 * pw) / pf, 1), _invalid=invalidFormulas.get(i, "")
            )
            updatedRelations.append(urow)
        elif name:
            profile = ST.profileValues(name)
            urow = replace(
                row,
                mass=profile["mass"],
                flour=profile["flour"],
                water=profile["water"],
                bp=round(profile["mass"] * 100 / TF, 1),
                _invalid=invalidFormulas.get(i, ""),
            )
            updatedRelations.append(urow)
        else:
            updatedRelations.append(replace(row))

    if convertToBP:
        part = ""
        for row in updatedRelations:
            if row.part:
                part = row.part
            if part == "dough" and row.name == "total_flour":
                row.formula = f"{TF}g"
                continue
            if row.formula:
                if re.match(r"[-0-9.eg]+$", row.formula):
                    row.formula = f"{round(row.bp, 1)}%"

    # Validate the updated relations
    for i, row in enumerate(updatedRelations):
        if row.part:
            ST.part = row.part
        if row.formula:
            fv = formulaN(ST, row.formula, row.name == "hydration")
            if row.name == "hydration":
                row._inconsistent = not np.isclose(
                    fv, ST.value("total_water"), 1e-3, 0.1
                )
            else:
                row._inconsistent = not np.isclose(fv, row.mass, 1e-3, 0.1)
        else:
            row._inconsistent = False

    return updatedRelations
