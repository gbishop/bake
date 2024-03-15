"""
┌───────────────┬───────┬───────┬───────────────┬────────┬─────────┐
│               │   %   │   g   │               │   sum  │   +bowl │
├───────────────┼───────┼───────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │ 500.0 │ total flour   │        │         │
│   total water │  70.0 │ 350.0 │ total water   │        │         │
│               │       │       │               │        │         │
│────Liquid─────┼───────┼───────┼───────────────┼────────┼─────────│
│               │       │       │               │        │         │
│       starter │  20.0 │ 100.0 │ starter       │  100.0 │   820.5 │
│    warm water │  60.0 │ 300.0 │ warm water    │  400.0 │  1120.5 │
│               │       │       │               │        │         │
│────Grains─────┼───────┼───────┼───────────────┼────────┼─────────│
│               │       │       │               │        │         │
│  prairie gold │  20.0 │ 100.0 │ prairie gold  │  500.0 │  1220.5 │
│  bronze chief │  20.0 │ 100.0 │ bronze chief  │  600.0 │  1320.5 │
│         spelt │  15.0 │  75.0 │ spelt         │  675.0 │  1395.5 │
│           rye │   5.0 │  25.0 │ rye           │  700.0 │  1420.5 │
│          oats │   5.0 │  25.0 │ oats          │  725.0 │  1445.5 │
│ potato flakes │   3.0 │  15.0 │ potato flakes │  740.0 │  1460.5 │
│ flaxseed meal │   2.0 │  10.0 │ flaxseed meal │  750.0 │  1470.5 │
│   bread flour │  20.0 │ 100.0 │ bread flour   │  850.0 │  1570.5 │
│               │       │       │               │        │         │
│───Additions───┼───────┼───────┼───────────────┼────────┼─────────│
│               │       │       │               │        │         │
│           oil │   5.0 │  25.0 │ oil           │  875.0 │  1595.5 │
│         honey │   5.0 │  25.0 │ honey         │  900.0 │  1620.5 │
│      improver │   2.0 │  10.0 │ improver      │  910.0 │  1630.5 │
│          salt │   2.0 │  10.0 │ salt          │  920.0 │  1640.5 │
│         yeast │   0.4 │   2.0 │ yeast         │  922.0 │  1642.5 │
│          nuts │  15.0 │  75.0 │ nuts          │  997.0 │  1717.5 │
│───────────────┼───────┼───────┼───────────────┼────────┼─────────│
│         total │ 199.4 │ 997.0 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# My usual loaf

This version was first using my new recipe format. It worked fine.
This loaf features pecans and walnuts. Really tastes great.

93F water mixed with the 68F starter and flours produced DT = 78F.
Mixed, rested 30 minutes, kneaded 8, added roughly broken nuts, kneaded 2 more.
S&F in the bowl every 30 minutes for 1.5 hours. 
Shaped and into pan. Proof took about 1.5 hours. 
Baked at 350F starting cold with lid on for 25.
Beautiful and flavorful loaf. Top a big cracked. A few larger holes.

This is a great result.

Rating=5

14 March 2024
"""

from recipe import R, TBD, water, flour

R += R.total_flour == 100
R += R.total_water == 70

R += "Liquid"

R += R.starter == 20
R += R.total_water == water(R.starter, 100) + R.warm_water

R += "Grains"

R += 100 == R.sum(
    flour(R.starter, 100),
    prairie_gold=20,
    bronze_chief=20,
    spelt=15,
    rye=5,
    oats=5,
    potato_flakes=3,
    flaxseed_meal=2,
    bread_flour=TBD,
)

R += "Additions"

additions = R.sum(
    oil=5,
    honey=5,
    improver=2,
    salt=2,
    yeast=0.4,
    nuts=15,
)

R += ""

R += R.total == 100 + R.total_water + additions
