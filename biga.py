"""
┌───────────────┬───────┬───────┬───────────────┬────────┬─────────┐
│               │   %   │   g   │               │   sum  │   +bowl │
├───────────────┼───────┼───────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │ 500.0 │ total flour   │        │         │
│   total water │  65.0 │ 325.0 │ total water   │        │         │
│               │       │       │               │        │         │
│─────Biga──────┼───────┼───────┼───────────────┼────────┼─────────│
│               │       │       │               │        │         │
│         spelt │  50.0 │ 250.0 │ spelt         │  250.0 │   970.5 │
│       starter │   5.0 │  25.0 │ starter       │  275.0 │   995.5 │
│         water │  22.5 │ 112.5 │ water         │  387.5 │  1108.0 │
│               │       │       │               │        │         │
│─────Dough─────┼───────┼───────┼───────────────┼────────┼─────────│
│               │       │       │               │        │         │
│   added water │  40.0 │ 200.0 │ added water   │  587.5 │  1308.0 │
│   bread flour │  42.5 │ 212.5 │ bread flour   │  800.0 │  1520.5 │
│ potato flakes │   3.0 │  15.0 │ potato flakes │  815.0 │  1535.5 │
│ flaxseed meal │   2.0 │  10.0 │ flaxseed meal │  825.0 │  1545.5 │
│           oil │   5.0 │  25.0 │ oil           │  850.0 │  1570.5 │
│         honey │   5.0 │  25.0 │ honey         │  875.0 │  1595.5 │
│      improver │   2.0 │  10.0 │ improver      │  885.0 │  1605.5 │
│          salt │   2.0 │  10.0 │ salt          │  895.0 │  1615.5 │
│         yeast │   0.5 │   2.5 │ yeast         │  897.5 │  1618.0 │
│───────────────┼───────┼───────┼───────────────┼────────┼─────────│
│         total │ 179.5 │ 897.5 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# Rene R's 50% Spelt Biga

And an experiment with LP to replace spreadsheets.
"""

from recipe import R, TBD, water, flour

R.scale = 500  # total flour

R += R.total_flour == 100
R += R.total_water == 65

R += "Biga"

R += R.spelt == 50
R += R.starter == 0.1 * R.spelt
R += R.water == 0.5 * R.spelt - water(R.starter, 100)

R += "Dough"

R += R.total_water == R.added_water + R.water + water(R.starter, 100)

R += 100 == R.sum(
    R.spelt, flour(R.starter, 100), bread_flour=TBD, potato_flakes=3, flaxseed_meal=2
)

additions = R.sum(oil=5, honey=5, improver=2, salt=2, yeast=0.5)

R += ""

R += R.total == 100 + R.total_water + additions
