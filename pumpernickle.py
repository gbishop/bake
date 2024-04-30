"""
┌──────────────┬───────┬───────┬──────────────┬────────┬─────────┐
│              │   %   │   g   │              │   sum  │   +bowl │
├──────────────┼───────┼───────┼──────────────┼────────┼─────────┤
│  total flour │ 100.0 │ 200.0 │ total flour  │        │         │
│  total water │  66.0 │ 132.0 │ total water  │        │         │
│              │       │       │              │        │         │
│ ────Wet───── │       │       │              │        │         │
│              │       │       │              │        │         │
│       leaven │  25.0 │  50.0 │ leaven       │   50.0 │   775.1 │
│ water/leaven │  12.5 │  25.0 │ water/leaven │        │         │
│   warm water │  53.5 │ 107.0 │ warm water   │  157.0 │   882.1 │
│     molasses │  16.0 │  32.0 │ molasses     │  189.0 │   914.1 │
│       butter │  13.0 │  26.0 │ butter       │  215.0 │   940.1 │
│              │       │       │              │        │         │
│ ───Flours─── │       │       │              │        │         │
│              │       │       │              │        │         │
│          rye │  30.0 │  60.0 │ rye          │  275.0 │  1000.1 │
│ prairie gold │  17.0 │  34.0 │ prairie gold │  309.0 │  1034.1 │
│    ww/leaven │  12.5 │  25.0 │ ww/leaven    │        │         │
│ red rye malt │   3.0 │   6.0 │ red rye malt │  315.0 │  1040.1 │
│           ap │  37.5 │  75.0 │ ap           │  390.0 │  1115.1 │
│              │       │       │              │        │         │
│ ────Add───── │       │       │              │        │         │
│              │       │       │              │        │         │
│  brown sugar │   3.0 │   6.0 │ brown sugar  │  396.0 │  1121.1 │
│ cacao powder │   4.0 │   8.0 │ cacao powder │  404.0 │  1129.1 │
│         salt │   1.8 │   3.6 │ salt         │  407.6 │  1132.7 │
│        yeast │   0.4 │   0.8 │ yeast        │  408.4 │  1133.5 │
│        total │ 204.2 │ 408.4 │ total        │        │         │
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

27 April 2024
"""

from recipe import R, TBD, water, flour

R.scale = 200

R += R.total_flour == 100
R += R.total_water == 66

R += "Wet"

R += R.leaven == 25
R += R.total_water == R.sum(water__leaven=water(R.leaven, 100), warm_water=TBD)
wet = R.sum(molasses=16, butter=13)

R += "Flours"

R += 100 == R.sum(
    rye=30,
    prairie_gold=17,
    ww__leaven=flour(R.leaven, 100),
    red_rye_malt=3,
    ap=TBD,
)

R += "Add"

dry = R.sum(
    brown_sugar=3,
    cacao_powder=4,
    salt=1.8,
    yeast=0.4,
)

R += R.total == 100 + R.total_water + wet + dry
