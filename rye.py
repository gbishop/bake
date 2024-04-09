"""
┌─────────────────────┬───────┬───────┬─────────────────────┬────────┬─────────┐
│                     │   %   │   g   │                     │   sum  │   +bowl │
├─────────────────────┼───────┼───────┼─────────────────────┼────────┼─────────┤
│         total flour │ 100.0 │ 500.0 │ total flour         │        │         │
│         total water │  70.0 │ 350.0 │ total water         │        │         │
│                     │       │       │                     │        │         │
│ ──────Leaven─────── │       │       │                     │        │         │
│                     │       │       │                     │        │         │
│         seed/leaven │   0.7 │   3.5 │ seed/leaven         │        │         │
│                 rye │   7.0 │  35.0 │ rye                 │   35.0 │   760.1 │
│        red rye malt │   3.0 │  15.0 │ red rye malt        │   50.0 │   775.1 │
│               water │  10.0 │  50.0 │ water               │  100.0 │   825.1 │
│                     │       │       │                     │        │         │
│ ────────Wet──────── │       │       │                     │        │         │
│                     │       │       │                     │        │         │
│          warm water │  60.0 │ 300.0 │ warm water          │  400.0 │  1125.1 │
│                 oil │   5.0 │  25.0 │ oil                 │  425.0 │  1150.1 │
│               honey │   5.0 │  25.0 │ honey               │  450.0 │  1175.1 │
│                     │       │       │                     │        │         │
│ ──────Flours─────── │       │       │                     │        │         │
│                     │       │       │                     │        │         │
│          rye/leaven │   7.0 │  35.0 │ rye/leaven          │        │         │
│ red rye malt/leaven │   3.0 │  15.0 │ red rye malt/leaven │        │         │
│                 rye │  23.0 │ 115.0 │ rye                 │  565.0 │  1290.1 │
│        prairie gold │  31.0 │ 155.0 │ prairie gold        │  720.0 │  1445.1 │
│       potato flakes │   3.0 │  15.0 │ potato flakes       │  735.0 │  1460.1 │
│       flaxseed meal │   2.0 │  10.0 │ flaxseed meal       │  745.0 │  1470.1 │
│                 vwg │   2.0 │  10.0 │ vwg                 │  755.0 │  1480.1 │
│         bread flour │  29.0 │ 145.0 │ bread flour         │  900.0 │  1625.1 │
│                     │       │       │                     │        │         │
│ ────────Add──────── │       │       │                     │        │         │
│                     │       │       │                     │        │         │
│            improver │   1.0 │   5.0 │ improver            │  905.0 │  1630.1 │
│                salt │   2.0 │  10.0 │ salt                │  915.0 │  1640.1 │
│               yeast │   0.4 │   2.0 │ yeast               │  917.0 │  1642.1 │
│       caraway seeds │   2.0 │  10.0 │ caraway seeds       │  927.0 │  1652.1 │
│ ─────────────────── │       │       │                     │        │         │
│               total │ 185.4 │ 927.0 │ total               │        │         │
└─────────────────────┴───────┴───────┴─────────────────────┴────────┴─────────┘

# 30% rye variant of my usual

I made the leaven from a newly created batch of NMNF starter. I used 3.5g of the
starter with 50g of water, 15g of red rye malt and 35g of rye. I mixed it about 20:00.

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 30 minutes, kneaded 8, added roughly broken nuts, kneaded 3 more. S&F in
the bowl every 45 minutes for 3 cycles.

Shaped and into pan. Proof took about 60 minutes. Baked at 350F starting cold
with lid on for 35 off for 15.

This is a really good rye loaf. I like the flavor, aroma and texture. 

07 April 2024
"""

from recipe import R, TBD, water, flour

R.scale = 500

R += R.total_flour == 100
R += R.total_water == 70

R += "Leaven"
R += R.seed__leaven == 3.5 / 500 * 100
leaven = R.sum(rye_1=7, red_rye_malt=3, water=10)

R += "Wet"

R += R.total_water == R.sum(water(leaven, 100), warm_water=TBD)
wet = R.sum(oil=5, honey=5)

R += "Flours"

R += 100 == R.sum(
    rye__leaven=R.rye_1,
    red_rye_malt__leaven=R.red_rye_malt,
    rye_2=23,
    prairie_gold=31,
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

inclusions = R.sum(
    caraway_seeds=2,
)

R += ""

R += R.total == 100 + R.total_water + wet + dry + inclusions
