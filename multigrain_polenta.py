"""
┌────────────────────┬───────┬───────┬────────────────────┬────────┬─────────┐
│                    │   %   │   g   │                    │   sum  │   +bowl │
├────────────────────┼───────┼───────┼────────────────────┼────────┼─────────┤
│        total flour │ 100.0 │ 500.0 │ total flour        │        │         │
│        total water │  70.0 │ 350.0 │ total water        │        │         │
│                    │       │       │                    │        │         │
│ ──────Soaker────── │       │       │                    │        │         │
│            polenta │  10.0 │  50.0 │ polenta            │   50.0 │   775.1 │
│              water │  25.0 │ 125.0 │ water              │  175.0 │   900.1 │
│     diastatic malt │   0.1 │   0.8 │ diastatic malt     │  175.8 │   900.9 │
│ ────────────────── │       │       │                    │        │         │
│       soaker total │  35.1 │ 175.8 │ soaker total       │        │         │
│                    │       │       │                    │        │         │
│ ──────Sponge────── │       │       │                    │        │         │
│        rye starter │   1.0 │   5.0 │ rye starter        │  180.8 │   905.9 │
│              water │  14.5 │  72.5 │ water              │  253.2 │   978.4 │
│          rye flour │  14.5 │  72.5 │ rye flour          │  325.8 │  1050.8 │
│ ────────────────── │       │       │                    │        │         │
│       sponge total │  30.0 │ 150.0 │ sponge total       │        │         │
│                    │       │       │                    │        │         │
│ ──────Flours────── │       │       │                    │        │         │
│     polenta/soaker │  10.0 │  50.0 │ polenta/soaker     │        │         │
│ rye starter/sponge │   0.5 │   2.5 │ rye starter/sponge │        │         │
│   rye flour/sponge │  14.5 │  72.5 │ rye flour/sponge   │        │         │
│       prairie gold │  45.0 │ 225.0 │ prairie gold       │  550.8 │  1275.8 │
│       bronze chief │  20.0 │ 100.0 │ bronze chief       │  650.8 │  1375.8 │
│      flaxseed meal │   5.0 │  25.0 │ flaxseed meal      │  675.8 │  1400.8 │
│      potato flakes │   2.0 │  10.0 │ potato flakes      │  685.8 │  1410.8 │
│                vwg │   3.0 │  15.0 │ vwg                │  700.8 │  1425.8 │
│ ────────────────── │       │       │                    │        │         │
│       flours total │ 100.0 │ 500.0 │ flours total       │        │         │
│                    │       │       │                    │        │         │
│ ───────Add──────── │       │       │                    │        │         │
│           improver │   1.0 │   5.0 │ improver           │  705.8 │  1430.8 │
│               salt │   2.0 │  10.0 │ salt               │  715.8 │  1440.8 │
│              yeast │   0.4 │   2.0 │ yeast              │  717.8 │  1442.8 │
│                    │       │       │                    │        │         │
│ ──────Final─────── │       │       │                    │        │         │
│              water │  30.0 │ 150.0 │ water              │  867.8 │  1592.8 │
│                oil │   5.0 │  25.0 │ oil                │  892.8 │  1617.8 │
│              honey │   5.0 │  25.0 │ honey              │  917.8 │  1642.8 │
│                    │       │       │                    │        │         │
│ ────Inclusions──── │       │       │                    │        │         │
│               nuts │  15.0 │  75.0 │ nuts               │  992.8 │  1717.8 │
│ ────────────────── │       │       │                    │        │         │
│              total │ 198.6 │ 992.8 │ total              │        │         │
└────────────────────┴───────┴───────┴────────────────────┴────────┴─────────┘

# My usual loaf with polenta

I'm riffing on a recipe by [Michael
Sinclair](https://www.thefreshloaf.com/node/74229/mark-sinclair-walnut-bread)
and trying saccharification like
[Benni](https://www.thefreshloaf.com/node/70656/saccarified-polenta-sourdough)
but I took a lazier approach by simply pouring boiling water over the polenta,
waiting for a few minutes for it to cool to about 150F, then adding the
diastatic malt.

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

Very nice texture and flavor on first taste. This is a keeper.

13 May 2024
"""

from recipe import R, TBD, water, flour

R.scale = 500

R += R.total_flour == 100
R += R.total_water == 70

R += "Soaker"

soaker = R.sum(polenta=10, water_1=25, diastatic_malt=0.15)

R += ""
R += R.soaker_total == soaker

R += "Sponge"

sponge = R.sum(rye_starter=1, water_2=14.5, rye_flour=14.5)
R += ""
R += R.sponge_total == sponge

R += "Flours"

flours = R.sum(
    polenta__soaker=R.polenta,
    rye_starter__sponge=R.rye_starter * 0.5,
    rye_flour__sponge=R.rye_flour,
    prairie_gold=TBD,
    bronze_chief=20,
    flaxseed_meal=5,
    potato_flakes=2,
    vwg=3,
)
R += 100 == flours

R += ""
R += R.flours_total == 100

R += "Add"

dry = R.sum(
    improver=1,
    salt=2,
    yeast=0.4,
)

R += "Final"

R += R.total_water == R.sum(R.water_1 + R.water_2 + R.rye_starter * 0.5, water=TBD)

wet = R.sum(oil=5, honey=5)

R += "Inclusions"

inclusions = R.sum(nuts=15)

R += ""

R += R.total == 100 + R.total_water + wet + dry + inclusions + R.diastatic_malt
