"""
┌───────────────┬───────┬────────┬───────────────┬────────┬─────────┐
│               │   %   │    g   │               │   sum  │   +bowl │
├───────────────┼───────┼────────┼───────────────┼────────┼─────────┤
│   total flour │ 100.0 │  500.0 │ total flour   │        │         │
│   total water │  70.0 │  350.0 │ total water   │        │         │
│               │       │        │               │        │         │
│ ─────Wet───── │       │        │               │        │         │
│               │       │        │               │        │         │
│        leaven │  20.0 │  100.0 │ leaven        │  100.0 │   825.1 │
│  water/leaven │  10.0 │   50.0 │ water/leaven  │        │         │
│    warm water │  60.0 │  300.0 │ warm water    │  400.0 │  1125.1 │
│           oil │   5.0 │   25.0 │ oil           │  425.0 │  1150.1 │
│         honey │   5.0 │   25.0 │ honey         │  450.0 │  1175.1 │
│               │       │        │               │        │         │
│ ───Flours──── │       │        │               │        │         │
│               │       │        │               │        │         │
│  prairie gold │  30.0 │  150.0 │ prairie gold  │  600.0 │  1325.1 │
│  bronze chief │  30.0 │  150.0 │ bronze chief  │  750.0 │  1475.1 │
│         spelt │  10.0 │   50.0 │ spelt         │  800.0 │  1525.1 │
│     ww/leaven │  10.0 │   50.0 │ ww/leaven     │        │         │
│          oats │  10.0 │   50.0 │ oats          │  850.0 │  1575.1 │
│ flaxseed meal │   5.0 │   25.0 │ flaxseed meal │  875.0 │  1600.1 │
│ potato flakes │   3.0 │   15.0 │ potato flakes │  890.0 │  1615.1 │
│           vwg │   2.0 │   10.0 │ vwg           │  900.0 │  1625.1 │
│               │       │        │               │        │         │
│ ─────Add───── │       │        │               │        │         │
│               │       │        │               │        │         │
│      improver │   1.0 │    5.0 │ improver      │  905.0 │  1630.1 │
│          salt │   2.0 │   10.0 │ salt          │  915.0 │  1640.1 │
│         yeast │   0.4 │    2.0 │ yeast         │  917.0 │  1642.1 │
│               │       │        │               │        │         │
│ ─Inclusions── │       │        │               │        │         │
│               │       │        │               │        │         │
│          nuts │  15.0 │   75.0 │ nuts          │  992.0 │  1717.1 │
│         glaze │  20.0 │  100.0 │ glaze         │ 1092.0 │  1817.1 │
│ ───────────── │       │        │               │        │         │
│         total │ 218.4 │ 1092.0 │ total         │        │         │
└───────────────┴───────┴────────┴───────────────┴────────┴─────────┘

# My usual loaf with glazed nuts

Back to simple leaven setup with 5g of seed + 50g water + 50g ww at 21:00.

The only commercial flour is the WW in the leaven. The is 98% whole grain and
88% home milled.

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

This loaf has glazed nuts added. I started with 75g of 50/50 pecan/walnuts and
glazed them with 100g of brown sugar, 30g water and 1.5g salt in a non-stick
pan. https://www.fifteenspatulas.com/quick-stovetop-candied-pecans/
I failed to weigh the result but it must have been about 175g.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 30 minutes, kneaded 8, added glazed nuts, kneaded 3 more. S&F in
the bowl every 45 minutes for 3 cycles.

Shaped and into pan. Proof took about 60 minutes. Baked at 350F starting cold
with lid on for 30 off for 20.

Really good loaf. Delicious. Very soft and tall. Not at much flavor pop from
the glazed nuts as I had hoped but it is really good. 

29 April 2024
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
    prairie_gold=TBD,
    bronze_chief=30,
    spelt=10,
    ww__leaven=flour(R.leaven, 100),
    oats=10,
    flaxseed_meal=5,
    potato_flakes=3,
    vwg=2,
)

R += "Add"

dry = R.sum(
    improver=1,
    salt=2,
    yeast=0.4,
)

R += "Inclusions"

inclusions = R.sum(nuts=15, glaze=20)

R += ""

R += R.total == 100 + R.total_water + wet + dry + inclusions
