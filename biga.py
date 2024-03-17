"""
┌───────────────┬───────┬───────┬───────────────┬────────┬─────────┐
│               │   %   │   g   │               │   sum  │   +bowl │
├───────────────┼───────┼───────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │ 300.0 │ total flour   │        │         │
│   total water │  60.0 │ 180.0 │ total water   │        │         │
│               │       │       │               │        │         │
│ ────Biga───── │       │       │               │        │         │
│               │       │       │               │        │         │
│       starter │   6.0 │  18.0 │ starter       │   18.0 │   738.5 │
│         water │  27.0 │  81.0 │ water         │   99.0 │   819.5 │
│         spelt │  19.0 │  57.0 │ spelt         │  156.0 │   876.5 │
│  bronze chief │  19.0 │  57.0 │ bronze chief  │  213.0 │   933.5 │
│  prairie gold │  19.0 │  57.0 │ prairie gold  │  270.0 │   990.5 │
│          salt │   0.3 │   0.9 │ salt          │  270.9 │   991.4 │
│               │       │       │               │        │         │
│ ────Dough──── │       │       │               │        │         │
│               │       │       │               │        │         │
│         water │  30.0 │  90.0 │ water         │  360.9 │  1081.4 │
│   bread flour │  35.0 │ 105.0 │ bread flour   │  465.9 │  1186.4 │
│ potato flakes │   3.0 │   9.0 │ potato flakes │  474.9 │  1195.4 │
│           vwg │   2.0 │   6.0 │ vwg           │  480.9 │  1201.4 │
│           oil │   5.0 │  15.0 │ oil           │  495.9 │  1216.4 │
│         honey │   5.0 │  15.0 │ honey         │  510.9 │  1231.4 │
│      improver │   1.0 │   3.0 │ improver      │  513.9 │  1234.4 │
│          salt │   1.7 │   5.1 │ salt          │  519.0 │  1239.5 │
│         yeast │   0.5 │   1.5 │ yeast         │  520.5 │  1241.0 │
│ ───────────── │       │       │               │        │         │
│         total │ 173.2 │ 519.6 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# 60% Biga Multigrain

Inspired by: https://www.thefreshloaf.com/node/68024/biga-controversy

## Changes

* Multiple grains
* Biga is 60%
* Adding salt to slow down the biga
* Adding potato flakes, oil and honey for softness and browning.
* Adding a little yeast to help the final rise.
* Try not mixing the biga at all.

## Biga

Mix the starter and water thoroughly then sprinkle the grains over it and mix gently. Store for 24 hours.

**FAIL** after 24 hours the biga smelled strongly of acetone. I threw it away. Needs
* Lower temperature,
* Less starter, or
* Less time.

## Dough

Mix the liquids into the biga thoroughly, then add the remaining ingredients.

"""

from recipe import R, TBD, water, flour

R.scale = 300  # total flour

R += R.total_flour == 100
R += R.total_water == 60

R += "Biga"

biga_flour = 60
biga_hydration = 50 / 100

R += R.starter == 0.1 * biga_flour
R += R.water1 == biga_hydration * biga_flour - water(R.starter, 100)

grains = R.parts(prairie_gold=1, bronze_chief=1, spelt=1)

R += biga_flour == flour(R.starter, 100) + grains

R += R.salt1 == 0.005 * biga_flour

R += "Dough"

R += R.total_water == R.water1 + R.water2 + water(R.starter, 100)

R += 100 == R.sum(biga_flour, bread_flour=TBD, potato_flakes=3, vwg=2)

additions = R.sum(oil=5, honey=5, improver=1, salt2=TBD, yeast=0.5)
R += 2 == R.salt1 + R.salt2

R += ""

R += R.total == 100 + R.total_water + additions
