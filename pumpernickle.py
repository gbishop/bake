"""
┌──────────────┬───────┬───────┬──────────────┬────────┬─────────┐
│              │   %   │   g   │              │   sum  │   +bowl │
├──────────────┼───────┼───────┼──────────────┼────────┼─────────┤
│  total flour │ 100.0 │ 300.0 │ total flour  │        │         │
│  total water │  66.3 │ 198.8 │ total water  │        │         │
│              │       │       │              │        │         │
│ ────Wet───── │       │       │              │        │         │
│              │       │       │              │        │         │
│       leaven │  25.6 │  76.8 │ leaven       │   76.8 │   801.9 │
│ water/leaven │  12.8 │  38.4 │ water/leaven │        │         │
│   warm water │  53.5 │ 160.4 │ warm water   │  237.1 │   962.2 │
│     molasses │  15.9 │  47.6 │ molasses     │  284.7 │  1009.8 │
│       butter │  12.7 │  38.1 │ butter       │  322.8 │  1047.9 │
│              │       │       │              │        │         │
│ ───Flours─── │       │       │              │        │         │
│              │       │       │              │        │         │
│           ap │  39.6 │ 118.9 │ ap           │  441.7 │  1166.8 │
│          rye │  30.6 │  91.7 │ rye          │  533.4 │  1258.5 │
│ prairie gold │  17.0 │  51.0 │ prairie gold │  584.4 │  1309.5 │
│    ww/leaven │  12.8 │  38.4 │ ww/leaven    │        │         │
│              │       │       │              │        │         │
│ ────Add───── │       │       │              │        │         │
│              │       │       │              │        │         │
│  brown sugar │   2.9 │   8.8 │ brown sugar  │  593.2 │  1318.3 │
│ cacao powder │   6.8 │  20.4 │ cacao powder │  613.6 │  1338.7 │
│         salt │   1.8 │   5.4 │ salt         │  619.0 │  1344.1 │
│        yeast │   0.4 │   1.2 │ yeast        │  620.2 │  1345.3 │
│        total │ 206.7 │ 620.2 │ total        │        │         │
└──────────────┴───────┴───────┴──────────────┴────────┴─────────┘

# Faux (American) Pumpernickle

https://www.farmhouseonboone.com/sourdough-pumpernickel-bread-recipe

I think her pan is 1.2L. My pan is 1L so I'm scaling her recipe down by 1.2 to
368g. But my typical 1L loaf is 250g of flour. I'm going for 300g. 300g turned
out to be way too tall. I must be wrong about her pan size. 250g would have
been right. 

I'm using the / in the table to indicate an ingredient that is already
accounted for. In the variable names I use __ (2 underscores) to indicate this.

I rearranged the order so I could be sure everything is well mixed.

This loaf has no inclusions.

93F water mixed with the 68F starter and flours produced DT = 78F. Mixed,
rested 30 minutes. Very sticky and my hook had the usual problem with small
loaves sticking to the bottom. I didn't get adequate gluten development. I did
a few S&F during the intial rise. It doubled.

Shaped and into pan. Proof took about 45 minutes. 300g was too big for
my 1L pan. Baked at 350F starting cold with lid on for 30 off for 20.

Smells chocolatey while baking. Maybe too much cacao?

Really good loaf. Delicious. Very soft and tall. The flavor is a bit too
chocolate forward for my taste. Next time I'll try reducing the cacao and
adding some red rye malt to take the flavor in that direction.

26 April 2024
"""

from recipe import R, TBD, water, flour

R.scale = 300

S = 100 / (113 / 2 + 175 + 135 + 75)

R += R.total_flour == 100
R += R.total_water == S * (236 + 113 / 2)

R += "Wet"

R += R.leaven == S * 113
R += R.total_water == R.sum(water__leaven=water(R.leaven, 100), warm_water=TBD)
wet = R.sum(molasses=S * 70, butter=S * 56)

R += "Flours"

R += 100 == R.sum(
    ap=S * 175,
    rye=S * 135,
    prairie_gold=S * 75,
    ww__leaven=flour(R.leaven, 100),
)

R += "Add"

dry = R.sum(
    brown_sugar=S * 13,
    cacao_powder=S * 30,
    salt=S * 8,
    yeast=0.4,
)

R += R.total == 100 + R.total_water + wet + dry
