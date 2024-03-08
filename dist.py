import pulp


class Lp:
    vars = {}

    def var(self, name, lb=0, ub=None):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, lb, ub)
        return self.vars[name]

    def array(self, name, length, lb=0, ub=None):
        return [self.var(f"{name}_{i}", lb, ub) for i in range(length)]

    def __getattr__(self, name):
        return self.var(name)

    def __setattr__(self, name, value):
        global problem
        v = self.var(name)
        problem += v == value

    def solve(self):
        global problem
        problem.solve(pulp.PULP_CBC_CMD(msg=False))
        values = {var.name: var.varValue for var in problem.variables()}
        result = {var: values[var] for var in self.vars}
        return result


V = Lp()

problem = pulp.LpProblem("dist", pulp.LpMaximize)

m = V.array("m", 2)
b = V.array("b", 2)

# objective
problem += pulp.lpSum([2**i * v for i, v in enumerate(m + b)])

V.total_flour = 100
hydration = 80

V.total_water = hydration

V.biga = 50
V.biga = m[0] + b[0]

V.total_flour = V.biga + m[1] + b[1]


V.m = pulp.lpSum(m)
V.b = pulp.lpSum(b)

V.m = 70

result = V.solve()
for var in result:
    print(var, result[var])
