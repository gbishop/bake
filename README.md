# Baking formulas with relations

This is a hack. I wrote it because I was sick of fooling with
spreadsheets. Programming is more fun than spreadsheets!

I'm currently using the `*.bake` files for my recipes. The `bake.py` script
uses [lark](https://github.com/lark-parser/lark) to construct a parser for
recipes. It uses
[least_squares](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html)
to solve the resulting system of linear equations.

In a bake file. The program generates a C-style comment at the bottom of the file.

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

You can specify values in grams (suffix g) or baker's percent (suffix %). You
can mix them in the same recipe.

See the recipes folder for examples.
