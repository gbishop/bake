test = """
# A Loaf

A description of this loaf.

```
total_flour = 100
hydration = 80bp

biga_flour = 50bp
biga_flour = starter_flour + milled_grains
biga_water = 0.5 * biga_flour - starter_water

starter_water = starter_flour
starter_total = starter_water + starter_flour
starter_total = 0.05 * biga_flour

added_water = hydration - biga_water - starter_water

total_flour = biga_flour + starter_flour + 
              potato_flakes + flaxseed_meal + bread_flour

potato_flakes = 3bp
flaxseed_meal = 2bp

add_ins = oil + honey + improver + salt + yeast + seeds

oil = 5bp
honey = 5bp
improver = 2bp
salt = 2bp
yeast = 0.3bp

seeds = 10bp

milled_grains = hard_white + hard_red + spelt + rye

hard_white = 4 * part
hard_red = 3 * part
spelt = 2 * part
rye = 1 * part

tdw = total_flour + hydration + add_ins

```

Some more text at the end.

"""

import pulp

problem = pulp.LpProblem("bread", pulp.LpMinimize)
problem += 0


class Lp:
    vars = {}

    def __getattr__(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __setattr__(self, name, value):
        global problem
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        problem += self.vars[name] == value

    def solve(self):
        global problem
        problem.solve()
        values = {var.name: var.varValue for var in problem.variables()}
        result = {var: values[var] for var in self.vars}
        return result


V = Lp()

V.total_flour = 100
hydration = 80
V.bp = 0.01 * V.total_flour

V.total_water = hydration * V.bp

starter_hydration = 1.00

V.biga_flour = 50 * V.bp
V.biga_flour = V.starter_flour + V.milled_grains
V.biga_water = 0.5 * V.biga_flour - V.starter_water

V.starter = 0.10 * V.biga_flour
V.starter_flour = 1.0 / (1 + starter_hydration) * V.starter
V.starter_water = starter_hydration * V.starter_flour

V.added_water = V.total_water - V.biga_water - V.starter_water

V.total_flour = (
    V.biga_flour + V.starter_flour + V.potato_flakes + V.flaxseed_meal + V.bread_flour
)

V.potato_flakes = 3 * V.bp
V.flaxseed_meal = 2 * V.bp

V.add_ins = V.oil + V.honey + V.improver + V.salt + V.yeast + V.seeds

V.oil = 5 * V.bp
V.honey = 5 * V.bp
V.improver = 2 * V.bp
V.salt = 2 * V.bp
V.yeast = 0.3 * V.bp

V.seeds = 10 * V.bp

V.milled_grains = V.hard_white + V.hard_red + V.spelt + V.rye

V.hard_white = 4 * V.part
V.hard_red = 3 * V.part
V.spelt = 2 * V.part
V.rye = 1 * V.part

V.tdw = V.total_flour + V.total_water + V.add_ins

result = V.solve()
for var in result:
    print(var, result[var])
