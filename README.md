# Baking formulas with linear programming

This is a hack. I wrote it because I was sick of fooling with
spreadsheets.

I'm currently using the `*.bake` files for my recipes. The `bake.py` script
uses [textx](https://textx.github.io/textX/) to construct a simple grammar
for recipes. It uses [pulp](https://coin-or.github.io/pulp/) to solve the
equations. I'm not using its optimization capabilities though I'd like to
try that in the future.

In a bake file, the first line is the title. The program generates a C-style comment next with the baking formula. I'm depending on a fixed width font to
get the layout to work. After the block comment the recipe consists of blocks of free text followed by blocks like:

```
starter:
  rye
  water
  hydration = 60%

sponge:
  starter = 1%
  rye
  water = 10%
  hydration = 100%
```

These two blocks result in a sponge that has 10% of the total flour. The total
mass of the starter will be 1% of the total flour and the water and flour in
the sponge will be adjusted give it 100% hydration.

I'm confident there is a better syntax but this is how far I got with it so
far.

The previous incarnation uses the `recipe.py` module to enable writing the
recipes directly in Python.
