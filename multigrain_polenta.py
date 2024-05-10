"""
┌────────────────────┬───────┬───────┬────────────────────┬────────┬─────────┐
│                    │   %   │   g   │                    │   sum  │   +bowl │
├────────────────────┼───────┼───────┼────────────────────┼────────┼─────────┤
│        total flour │ 100.0 │ 250.0 │ total flour        │        │         │
│        total water │  70.0 │ 175.0 │ total water        │        │         │
│                    │       │       │                    │        │         │
│ ──────Soaker────── │       │       │                    │        │         │
│            polenta │  10.0 │  25.0 │ polenta            │   25.0 │   750.1 │
│              water │  25.0 │  62.5 │ water              │   87.5 │   812.6 │
│     diastatic malt │   0.1 │   0.4 │ diastatic malt     │   87.9 │   813.0 │
│ ────────────────── │       │       │                    │        │         │
│       soaker total │  35.1 │  87.9 │ soaker total       │        │         │
│                    │       │       │                    │        │         │
│ ──────Sponge────── │       │       │                    │        │         │
│        rye starter │   1.0 │   2.5 │ rye starter        │   90.4 │   815.5 │
│              water │  14.5 │  36.2 │ water              │  126.6 │   851.7 │
│          rye flour │  14.5 │  36.2 │ rye flour          │  162.9 │   888.0 │
│ ────────────────── │       │       │                    │        │         │
│       sponge total │  30.0 │  75.0 │ sponge total       │        │         │
│                    │       │       │                    │        │         │
│ ──────Flours────── │       │       │                    │        │         │
│     polenta/soaker │  10.0 │  25.0 │ polenta/soaker     │        │         │
│ rye starter/sponge │   0.5 │   1.2 │ rye starter/sponge │        │         │
│   rye flour/sponge │  14.5 │  36.2 │ rye flour/sponge   │        │         │
│       prairie gold │  45.0 │ 112.5 │ prairie gold       │  275.4 │  1000.5 │
│       bronze chief │  20.0 │  50.0 │ bronze chief       │  325.4 │  1050.5 │
│      flaxseed meal │   5.0 │  12.5 │ flaxseed meal      │  337.9 │  1063.0 │
│      potato flakes │   2.0 │   5.0 │ potato flakes      │  342.9 │  1068.0 │
│                vwg │   3.0 │   7.5 │ vwg                │  350.4 │  1075.5 │
│ ────────────────── │       │       │                    │        │         │
│       flours total │ 100.0 │ 250.0 │ flours total       │        │         │
│                    │       │       │                    │        │         │
│ ───────Add──────── │       │       │                    │        │         │
│           improver │   1.0 │   2.5 │ improver           │  352.9 │  1078.0 │
│               salt │   2.0 │   5.0 │ salt               │  357.9 │  1083.0 │
│              yeast │   0.4 │   1.0 │ yeast              │  358.9 │  1084.0 │
│                    │       │       │                    │        │         │
│ ──────Final─────── │       │       │                    │        │         │
│              water │  30.0 │  75.0 │ water              │  433.9 │  1159.0 │
│                oil │   5.0 │  12.5 │ oil                │  446.4 │  1171.5 │
│              honey │   5.0 │  12.5 │ honey              │  458.9 │  1184.0 │
│                    │       │       │                    │        │         │
│ ────Inclusions──── │       │       │                    │        │         │
│               nuts │  15.0 │  37.5 │ nuts               │  496.4 │  1221.5 │
│ ────────────────── │       │       │                    │        │         │
│              total │ 198.6 │ 496.4 │ total              │        │         │
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

10 May 2024
"""

from recipe import R, TBD, water, flour

R.scale = 250

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
