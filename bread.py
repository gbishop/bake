text = """
# A Loaf

A description of this loaf.

```
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
```

Some more text at the end.

"""

from lark import Lark, Transformer, v_args

parser = Lark(
    """
    ?start: (TEXT "```" relation* "```" TEXT)*

    TEXT: /.+/s

    ?relation: NAME relationship sum    -> relate

    ?relationship: "=" | "<" | "<=" | ">" | ">="

    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub

    ?product: atom
        | product "*" atom  -> mul
        | product "/" atom  -> div

    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | NAME             -> var
         | "(" sum ")"

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
"""
)

print(parser.parse(text).pretty())
