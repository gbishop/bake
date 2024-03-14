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

problem.solve(pulp.PULP_CBC_CMD(msg=False))
if problem.status < 1:
    print(pulp.LpStatus[problem.status])
else:
    values = {
        var.name: var.varValue
        for var in problem.variables()
        if not var.name.startswith("_")
    }
    result = {var: values[var] for var in R.vars if var in values}

    print(R.table(result))
