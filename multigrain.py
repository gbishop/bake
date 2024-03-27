"""
┌───────────────┬───────┬────────┬───────────────┬────────┬─────────┐
│               │   %   │    g   │               │   sum  │   +bowl │
├───────────────┼───────┼────────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │  700.0 │ total flour   │        │         │
│   total water │  70.0 │  490.0 │ total water   │        │         │
│               │       │        │               │        │         │
│ ─────Wet───── │       │        │               │        │         │
│               │       │        │               │        │         │
│        leaven │  20.0 │  140.0 │ leaven        │  140.0 │   860.5 │
│  water/leaven │  10.0 │   70.0 │ water/leaven  │        │         │
│    warm water │  60.0 │  420.0 │ warm water    │  560.0 │  1280.5 │
│           oil │   5.0 │   35.0 │ oil           │  595.0 │  1315.5 │
│         honey │   5.0 │   35.0 │ honey         │  630.0 │  1350.5 │
│               │       │        │               │        │         │
│ ───Flours──── │       │        │               │        │         │
│               │       │        │               │        │         │
│  prairie gold │  25.0 │  175.0 │ prairie gold  │  805.0 │  1525.5 │
│  bronze chief │  20.0 │  140.0 │ bronze chief  │  945.0 │  1665.5 │
│         spelt │  15.0 │  105.0 │ spelt         │ 1050.0 │  1770.5 │
│    rye/leaven │  10.0 │   70.0 │ rye/leaven    │        │         │
│          oats │   5.0 │   35.0 │ oats          │ 1085.0 │  1805.5 │
│ potato flakes │   3.0 │   21.0 │ potato flakes │ 1106.0 │  1826.5 │
│ flaxseed meal │   2.0 │   14.0 │ flaxseed meal │ 1120.0 │  1840.5 │
│           vwg │   2.0 │   14.0 │ vwg           │ 1134.0 │  1854.5 │
│   bread flour │  18.0 │  126.0 │ bread flour   │ 1260.0 │  1980.5 │
│               │       │        │               │        │         │
│ ─────Add───── │       │        │               │        │         │
│               │       │        │               │        │         │
│      improver │   1.0 │    7.0 │ improver      │ 1267.0 │  1987.5 │
│          salt │   2.0 │   14.0 │ salt          │ 1281.0 │  2001.5 │
│         yeast │   0.4 │    2.8 │ yeast         │ 1283.8 │  2004.3 │
│               │       │        │               │        │         │
│ ─Inclusions── │       │        │               │        │         │
│               │       │        │               │        │         │
│          nuts │  15.0 │  105.0 │ nuts          │ 1388.8 │  2109.3 │
│ ───────────── │       │        │               │        │         │
│         total │ 198.4 │ 1388.8 │ total         │        │         │
└───────────────┴───────┴────────┴───────────────┴────────┴─────────┘

# My usual loaf

This is a double loaf 9 and 4 inches long. Both turned out OK but a bit sunken
on the sides. What causes that?

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

This loaf features pecans and walnuts. Really tastes great.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 40 minutes, kneaded 4, added roughly broken nuts, kneaded 3 more. S&F in
the bowl every 45 minutes

Shaped and into pan. Proof took about 1.5 hours. Baked at 350F starting cold
with lid on for 35 off for 15, removed from pan then 5 more.

Really good loaf. Could be a bit more sour.

26 March 2024
"""

from recipe import R, TBD, water, flour

R.scale = 700

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
