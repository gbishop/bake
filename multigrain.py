"""
┌───────────────┬───────┬───────┬───────────────┬────────┬─────────┐
│               │   %   │   g   │               │   sum  │   +bowl │
├───────────────┼───────┼───────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │ 500.0 │ total flour   │        │         │
│   total water │  70.0 │ 350.0 │ total water   │        │         │
│               │       │       │               │        │         │
│ ─────Wet───── │       │       │               │        │         │
│               │       │       │               │        │         │
│        leaven │  20.0 │ 100.0 │ leaven        │  100.0 │   825.1 │
│  water/leaven │  10.0 │  50.0 │ water/leaven  │        │         │
│    warm water │  60.0 │ 300.0 │ warm water    │  400.0 │  1125.1 │
│           oil │   5.0 │  25.0 │ oil           │  425.0 │  1150.1 │
│         honey │   5.0 │  25.0 │ honey         │  450.0 │  1175.1 │
│               │       │       │               │        │         │
│ ───Flours──── │       │       │               │        │         │
│               │       │       │               │        │         │
│  prairie gold │  32.0 │ 160.0 │ prairie gold  │  610.0 │  1335.1 │
│  bronze chief │  25.0 │ 125.0 │ bronze chief  │  735.0 │  1460.1 │
│         spelt │  15.0 │  75.0 │ spelt         │  810.0 │  1535.1 │
│     ww/leaven │  10.0 │  50.0 │ ww/leaven     │        │         │
│           rye │   5.0 │  25.0 │ rye           │  835.0 │  1560.1 │
│          oats │   5.0 │  25.0 │ oats          │  860.0 │  1585.1 │
│ potato flakes │   3.0 │  15.0 │ potato flakes │  875.0 │  1600.1 │
│ flaxseed meal │   3.0 │  15.0 │ flaxseed meal │  890.0 │  1615.1 │
│           vwg │   2.0 │  10.0 │ vwg           │  900.0 │  1625.1 │
│            ww │       │       │ ww            │  900.0 │  1625.1 │
│               │       │       │               │        │         │
│ ─────Add───── │       │       │               │        │         │
│               │       │       │               │        │         │
│      improver │   1.0 │   5.0 │ improver      │  905.0 │  1630.1 │
│          salt │   2.0 │  10.0 │ salt          │  915.0 │  1640.1 │
│         yeast │   0.4 │   2.0 │ yeast         │  917.0 │  1642.1 │
│ ───────────── │       │       │               │        │         │
│         total │ 183.4 │ 917.0 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# My usual loaf

Back to simple leaven setup with 5g of seed + 50g water + 50g ww at 21:00.

The only commercial flour is the WW in the leaven. The is 98% whole grain and
88% home milled.

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

This loaf has no inclusions.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 30 minutes, kneaded 8, added roughly broken nuts, kneaded 3 more. S&F in
the bowl every 45 minutes for 3 cycles.

Shaped and into pan. Proof took about 60 minutes. Baked at 350F starting cold
with lid on for 30 off for 20.

Really good loaf. Delicious. Very soft and tall.

23 April 2024
"""

from recipe import R, TBD, water, flour

R.scale = 500

R += R.total_flour == 100
R += R.total_water == 70

R += "Wet"

R += R.leaven == 20
R += R.total_water == R.sum(water__leaven=water(R.leaven, 100), warm_water=TBD)
wet = R.sum(oil=5, honey=5)

R += "Flours"

R += 100 == R.sum(
    prairie_gold=32,
    bronze_chief=25,
    spelt=15,
    ww__leaven=flour(R.leaven, 100),
    rye=5,
    oats=5,
    potato_flakes=3,
    flaxseed_meal=3,
    vwg=2,
    ww=TBD,
)

R += "Add"

dry = R.sum(
    improver=1,
    salt=2,
    yeast=0.4,
)

R += "Inclusions"

inclusions = R.sum(0)

R += ""

R += R.total == 100 + R.total_water + wet + dry + inclusions
