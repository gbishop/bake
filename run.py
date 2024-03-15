import sys
from runpy import run_path
from recipe import R
import pulp
import re

name = sys.argv[1]
text = ""
if 0:
    run_path(f"{name}")
else:
    text = sys.stdin.read()
    code = compile(text, name, "exec")
    exec(code)

problem = pulp.LpProblem(name.replace(".py", ""))

problem += R.objective

for constraint in R.constraints:
    problem += constraint

problem.solve(pulp.PULP_CBC_CMD(msg=False))
if problem.status < 1:
    table = pulp.LpStatus[problem.status]
else:
    values = {
        var.name: var.varValue
        for var in problem.variables()
        if not var.name.startswith("_")
    }
    result = {var: values[var] for var in R.vars if var in values}

    table = R.table(result)

start = re.search(r'^"""', text, re.M)
if start:
    end = re.search(r'^# |^"""', text[start.end() :], re.M)
    if end:
        text = text[: start.end()] + "\n" + table + "\n" + text[end.end() :]

print(text)
