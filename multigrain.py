"""
┌───────────────┬───────┬───────┬───────────────┬────────┬─────────┐
│               │   %   │   g   │               │   sum  │   +bowl │
├───────────────┼───────┼───────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │ 500.0 │ total flour   │        │         │
│   total water │  70.0 │ 350.0 │ total water   │        │         │
│               │       │       │               │        │         │
│ ─────Wet───── │       │       │               │        │         │
│               │       │       │               │        │         │
│        leaven │  20.0 │ 100.0 │ leaven        │  100.0 │   820.5 │
│    warm water │  60.0 │ 300.0 │ warm water    │  400.0 │  1120.5 │
│           oil │   5.0 │  25.0 │ oil           │  425.0 │  1145.5 │
│         honey │   5.0 │  25.0 │ honey         │  450.0 │  1170.5 │
│               │       │       │               │        │         │
│ ───Flours──── │       │       │               │        │         │
│               │       │       │               │        │         │
│  prairie gold │  15.0 │  75.0 │ prairie gold  │  525.0 │  1245.5 │
│  bronze chief │  15.0 │  75.0 │ bronze chief  │  600.0 │  1320.5 │
│         spelt │  15.0 │  75.0 │ spelt         │  675.0 │  1395.5 │
│          oats │   5.0 │  25.0 │ oats          │  700.0 │  1420.5 │
│ potato flakes │   3.0 │  15.0 │ potato flakes │  715.0 │  1435.5 │
│ flaxseed meal │   2.0 │  10.0 │ flaxseed meal │  725.0 │  1445.5 │
│           vwg │   2.0 │  10.0 │ vwg           │  735.0 │  1455.5 │
│   bread flour │  33.0 │ 165.0 │ bread flour   │  900.0 │  1620.5 │
│               │       │       │               │        │         │
│ ─────Dry───── │       │       │               │        │         │
│               │       │       │               │        │         │
│      improver │   1.0 │   5.0 │ improver      │  905.0 │  1625.5 │
│          salt │   2.0 │  10.0 │ salt          │  915.0 │  1635.5 │
│         yeast │   0.4 │   2.0 │ yeast         │  917.0 │  1637.5 │
│          nuts │  15.0 │  75.0 │ nuts          │  992.0 │  1712.5 │
│ ───────────── │       │       │               │        │         │
│         total │ 198.4 │ 992.0 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# My usual loaf

I'm hoping to improve on the previous loaf with some vital wheat gluten. The last one
tasted great but was weak.

I also refreshed the starter with rye this time rather than whole wheat.

I rearranged the order so I could be sure everything is well mixed.

This loaf features pecans and walnuts. Really tastes great.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 30 minutes, kneaded 8, added roughly broken nuts, kneaded 3 more. S&F in
the bowl every 30 minutes for 1 hour. pH was down to 5.0 so I quit early.
Shaped and into pan. Proof took about 1.25 hours. Baked at 350F starting cold
with lid on for 40 off for 15.

Only 4 hours from start to finish today! Not including the leaven, of course,
which had 12 hours. Loaf looks great. 6 inches tall. Baked weight is 947.6
before cooling.

Good flavor. Much better strength

19 March 2024
"""

from recipe import R, TBD, water, flour

R += R.total_flour == 100
R += R.total_water == 70

R += "Wet"

R += R.leaven == 20
R += R.total_water == water(R.leaven, 100) + R.warm_water
wet = R.sum(oil=5, honey=5)

R += "Flours"

R += 100 == R.sum(
    flour(R.leaven, 100),
    prairie_gold=15,
    bronze_chief=15,
    spelt=15,
    oats=5,
    potato_flakes=3,
    flaxseed_meal=2,
    vwg=2,
    bread_flour=TBD,
)

R += "Dry"

dry = R.sum(
    improver=1,
    salt=2,
    yeast=0.4,
    nuts=15,
)

R += ""

R += R.total == 100 + R.total_water + wet + dry
