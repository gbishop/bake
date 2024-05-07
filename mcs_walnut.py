"""
┌─────────────────┬───────┬───────┬─────────────────┬────────┬─────────┐
│                 │   %   │   g   │                 │   sum  │   +bowl │
├─────────────────┼───────┼───────┼─────────────────┼────────┼─────────┤
│     total flour │ 100.0 │ 250.0 │ total flour     │        │         │
│     total water │  79.2 │ 198.1 │ total water     │        │         │
│                 │       │       │                 │        │         │
│ ────Sponge───── │       │       │                 │        │         │
│                 │       │       │                 │        │         │
│             rye │  16.8 │  41.9 │ rye             │   41.9 │   767.0 │
│           water │  16.8 │  41.9 │ water           │   83.8 │   808.9 │
│         starter │   2.2 │   5.6 │ starter         │   89.4 │   814.5 │
│                 │       │       │                 │        │         │
│ ────Soaker───── │       │       │                 │        │         │
│                 │       │       │                 │        │         │
│   water boiling │  24.5 │  61.2 │ water boiling   │  150.6 │   875.7 │
│     oats rolled │   5.1 │  12.8 │ oats rolled     │  163.4 │   888.5 │
│ cornmeal medium │   5.1 │  12.8 │ cornmeal medium │  176.2 │   901.4 │
│           honey │   1.8 │   4.4 │ honey           │  180.6 │   905.7 │
│                 │       │       │                 │        │         │
│ ──Final dough── │       │       │                 │        │         │
│                 │       │       │                 │        │         │
│        ap flour │  46.1 │ 115.3 │ ap flour        │  295.9 │  1021.0 │
│           water │  36.9 │  92.2 │ water           │  388.1 │  1113.2 │
│        ww flour │  25.8 │  64.4 │ ww flour        │  452.5 │  1177.6 │
│         walnuts │  18.0 │  45.0 │ walnuts         │  497.5 │  1222.6 │
│            salt │   1.8 │   4.4 │ salt            │  501.9 │  1227.0 │
│           yeast │   0.4 │   0.9 │ yeast           │  502.8 │  1227.9 │
│                 │       │       │                 │        │         │
│ ─────Total───── │       │       │                 │        │         │
│                 │       │       │                 │        │         │
│           total │ 201.1 │ 502.8 │ total           │        │         │
└─────────────────┴───────┴───────┴─────────────────┴────────┴─────────┘

# Mark Sinclair Walnut Loaf

https://www.facebook.com/photo?fbid=859627496209368&set=pcb.859628569542594

Very sticky. I add 25g more ww flour. 

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

Good loaf. More sour than I expected. Good flavor and texture.

5 May 2024
"""

from recipe import R, TBD, water, flour

tf = 134 + 9 + 41 + 41 + 369 + 206
tw = 134 + 9 + 196 + 295

R.scale = 250

g = 100 / tf

R += R.total_flour == 100
R += R.total_water == tw * g

R += "Sponge"

sponge = R.sum(rye=134 * g, water_1=134 * g, starter=18 * g)

R += "Soaker"

soaker = R.sum(
    water_boiling=196 * g, oats_rolled=41 * g, cornmeal_medium=41 * g, honey=14 * g
)

R += "Final dough"

final = R.sum(
    ap_flour=369 * g,
    water_2=295 * g,
    ww_flour=206 * g,
    walnuts=144 * g,
    salt=14 * g,
    yeast=3 * g,
)

R += "Total"

R += R.total == sponge + soaker + final
