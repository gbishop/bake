# Thinking about equations for bread formulas

An alternative to spreadsheets.

```
biga_flour = 50
biga_flour = starter_flour + milled_grains
biga_water = 50% * biga_flour - starter_water

starter_water = 100% * starter_flour
starter_total = starter_water + starter_flour
starter_total = 5% * biga_flour

dough_hydration = 80
added_water = dough_hydration - biga_water - starter_water

total_flour = biga_flour + starter_flour + potato_flakes + flaxseed_meal + bread_flour

potato_flakes = 3
flaxseed_meal = 2

add_ins = oil + honey + improver + salt + yeast + seeds

oil = 5
honey = 5
improver = 2
salt = 2
yeast = 0.3

seeds = 10

milled_grains = hard_white + hard_red + spelt + rye

hard_white = hard_red
hard_white > spelt
hard_white > rye

tdw = total_flour + dough_hydration + add_ins

total_flour = 100

```
