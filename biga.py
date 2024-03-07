# Thinking about equations for bread formulas

# An alternative to spreadsheets.

"""
bp = total_flour * 0.01

biga_flour = 50 * bp
biga_flour = starter_flour + milled_grains
biga_water = 0.5 * biga_flour - starter_water

starter_water = starter_flour
starter_total = starter_water + starter_flour
starter_total = 0.05 * biga_flour

dough_water = 80 * bp
added_water = dough_water - biga_water - starter_water

total_flour = biga_flour + starter_flour + potato_flakes + flaxseed_meal + bread_flour

potato_flakes = 3 * bp
flaxseed_meal = 2 * bp

add_ins = oil + honey + improver + salt + yeast + seeds

oil = 5 * bp
honey = 5 * bp
improver = 2 * bp
salt = 2 * bp
yeast = 0.3 * bp

seeds = 10 * bp

milled_grains = hard_white + hard_red + spelt + rye

hard_white = 4 * part
hard_red = 3 * part
spelt = 2 * part
rye = 1 * part

tdw = total_flour + dough_water + add_ins

total_flour = 100

"""

import pulp
import re
import types

V = types.SimpleNamespace(
    **{
        var: pulp.LpVariable(var, 0, None)
        for var in re.split(
            r"\s+",
            """
       biga_flour
       biga_water
       starter_water
       starter_flour
       starter_total
       dough_water
       added_water
       total_flour
       potato_flakes
       flaxseed_meal
       bread_flour
       add_ins
       oil
       honey
       improver
       salt
       yeast
       milled_grains
       hard_white
       hard_red
       spelt
       rye
       tdw
       total_flour
       seeds
       part
       """,
        )
    }
)

bp = V.total_flour * 0.01

P = pulp.LpProblem("Biga", pulp.LpMinimize)

P += V.tdw - 2 * V.total_flour

P += V.biga_flour == 50 * bp
P += V.biga_flour == V.starter_flour + V.milled_grains
P += V.biga_water == 0.5 * V.biga_flour - V.starter_water

P += V.starter_water == V.starter_flour
P += V.starter_total == V.starter_water + V.starter_flour
P += V.starter_total == 0.05 * V.biga_flour

P += V.dough_water == 80 * bp
P += V.added_water == V.dough_water - V.biga_water - V.starter_water

P += (
    V.total_flour
    == V.biga_flour
    + V.starter_flour
    + V.potato_flakes
    + V.flaxseed_meal
    + V.bread_flour
)

P += V.potato_flakes == 3 * bp
P += V.flaxseed_meal == 2 * bp

P += V.add_ins == V.oil + V.honey + V.improver + V.salt + V.yeast + V.seeds

P += V.oil == 5 * bp
P += V.honey == 5 * bp
P += V.improver == 2 * bp
P += V.salt == 2 * bp
P += V.yeast == 0.3 * bp

P += V.seeds == 10 * bp

P += V.milled_grains == V.hard_white + V.hard_red + V.spelt + V.rye

P += V.hard_white == 4 * V.part
P += V.hard_red == 3 * V.part
P += V.spelt == 2 * V.part
P += V.rye == 1 * V.part

P += V.tdw == V.total_flour + V.dough_water + V.add_ins

P += V.total_flour == 500

P.solve()

for var in P.variables():
    print(var.name, "=", var.varValue)
