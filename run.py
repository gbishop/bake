import sys
from runpy import run_path
from recipe import R
import pulp

name = sys.argv[1]
print("running", name)

run_path(f"{name}.py")

problem = pulp.LpProblem(name)

problem += R.objective

for constraint in R.constraints:
    problem += constraint

result = problem.solve(pulp.PULP_CBC_CMD(msg=False))
values = {
    var.name: var.varValue
    for var in problem.variables()
    if not var.name.startswith("_")
}
result = {var: values[var] for var in R.vars}

for var in result:
    print(var, "=", result[var])
