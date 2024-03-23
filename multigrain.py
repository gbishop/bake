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
│  water/leaven │  10.0 │  50.0 │ water/leaven  │        │         │
│    warm water │  60.0 │ 300.0 │ warm water    │  400.0 │  1120.5 │
│           oil │   5.0 │  25.0 │ oil           │  425.0 │  1145.5 │
│         honey │   5.0 │  25.0 │ honey         │  450.0 │  1170.5 │
│               │       │       │               │        │         │
│ ───Flours──── │       │       │               │        │         │
│               │       │       │               │        │         │
│  prairie gold │  25.0 │ 125.0 │ prairie gold  │  575.0 │  1295.5 │
│  bronze chief │  20.0 │ 100.0 │ bronze chief  │  675.0 │  1395.5 │
│         spelt │  15.0 │  75.0 │ spelt         │  750.0 │  1470.5 │
│    rye/leaven │  10.0 │  50.0 │ rye/leaven    │        │         │
│          oats │   5.0 │  25.0 │ oats          │  775.0 │  1495.5 │
│ potato flakes │   3.0 │  15.0 │ potato flakes │  790.0 │  1510.5 │
│ flaxseed meal │   2.0 │  10.0 │ flaxseed meal │  800.0 │  1520.5 │
│           vwg │   2.0 │  10.0 │ vwg           │  810.0 │  1530.5 │
│   bread flour │  18.0 │  90.0 │ bread flour   │  900.0 │  1620.5 │
│               │       │       │               │        │         │
│ ─────Add───── │       │       │               │        │         │
│               │       │       │               │        │         │
│      improver │   1.0 │   5.0 │ improver      │  905.0 │  1625.5 │
│          salt │   2.0 │  10.0 │ salt          │  915.0 │  1635.5 │
│         yeast │   0.4 │   2.0 │ yeast         │  917.0 │  1637.5 │
│               │       │       │               │        │         │
│ ─Inclusions── │       │       │               │        │         │
│               │       │       │               │        │         │
│          nuts │  15.0 │  75.0 │ nuts          │  992.0 │  1712.5 │
│ ───────────── │       │       │               │        │         │
│         total │ 198.4 │ 992.0 │ total         │        │         │
└───────────────┴───────┴───────┴───────────────┴────────┴─────────┘

# My usual loaf

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

This loaf features pecans and walnuts. Really tastes great.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 40 minutes, kneaded 4, added roughly broken nuts, kneaded 3 more. S&F in
the bowl every 45 minutes

pH=5.18 at first S&F
pH=5.15 at second S&F

Shaped and into pan. Proof took about 1.5 hours. Baked at 350F starting cold
with lid on for 35 off for 15, removed from pan then 5 more.

Really good loaf. Could be a bit more sour.

23 March 2024
"""

from recipe import R, TBD, water, flour

R += R.total_flour == 100
R += R.total_water == 70

R += "Wet"

R += R.leaven == 20
R += R.total_water == R.sum(water__leaven=water(R.leaven, 100), warm_water=TBD)
wet = R.sum(oil=5, honey=5)

R += "Flours"

R += 100 == R.sum(
    prairie_gold=25,
    bronze_chief=20,
    spelt=15,
    rye__leaven=flour(R.leaven, 100),
    oats=5,
    potato_flakes=3,
    flaxseed_meal=2,
    vwg=2,
    bread_flour=TBD,
)

R += "Add"

dry = R.sum(
    improver=1,
    salt=2,
    yeast=0.4,
)

R += "Inclusions"

inclusions = R.sum(
    nuts=15,
)

R += ""

R += R.total == 100 + R.total_water + wet + dry + inclusions
