"""
┌──────────────────┬───────┬───────┬──────────────────┬────────┬─────────┐
│                  │   %   │   g   │                  │   sum  │   +bowl │
├──────────────────┼───────┼───────┼──────────────────┼────────┼─────────┤
│      total flour │ 100.0 │ 250.0 │ total flour      │        │         │
│      total water │  70.0 │ 175.0 │ total water      │        │         │
│                  │       │       │                  │        │         │
│ ──────Wet─────── │       │       │                  │        │         │
│                  │       │       │                  │        │         │
│           leaven │  20.0 │  50.0 │ leaven           │   50.0 │   770.5 │
│       warm water │  60.0 │ 150.0 │ warm water       │  200.0 │   920.5 │
│              oil │       │       │ oil              │  200.0 │   920.5 │
│            honey │       │       │ honey            │  200.0 │   920.5 │
│                  │       │       │                  │        │         │
│ ─────Flours───── │       │       │                  │        │         │
│                  │       │       │                  │        │         │
│     prairie gold │  25.0 │  62.5 │ prairie gold     │  262.5 │   983.0 │
│     bronze chief │  20.0 │  50.0 │ bronze chief     │  312.5 │  1033.0 │
│            spelt │  15.0 │  37.5 │ spelt            │  350.0 │  1070.5 │
│    potato flakes │   3.0 │   7.5 │ potato flakes    │  357.5 │  1078.0 │
│              vwg │   2.0 │   5.0 │ vwg              │  362.5 │  1083.0 │
│      bread flour │  25.0 │  62.5 │ bread flour      │  425.0 │  1145.5 │
│                  │       │       │                  │        │         │
│ ──────Dry─────── │       │       │                  │        │         │
│                  │       │       │                  │        │         │
│         improver │   0.5 │   1.2 │ improver         │  426.2 │  1146.8 │
│             salt │   2.0 │   5.0 │ salt             │  431.2 │  1151.8 │
│            yeast │   0.4 │   1.0 │ yeast            │  432.2 │  1152.8 │
│                  │       │       │                  │        │         │
│ ───Inclusion──── │       │       │                  │        │         │
│                  │       │       │                  │        │         │
│ caramelized oats │  50.0 │ 125.0 │ caramelized oats │  557.2 │  1277.8 │
│ ──────────────── │       │       │                  │        │         │
│            total │ 222.9 │ 557.2 │ total            │        │         │
└──────────────────┴───────┴───────┴──────────────────┴────────┴─────────┘

# Try Pressure Caramelized Inclusions in my usual loaf

https://modernistcuisine.com/recipes/caramelized-inclusions-with-a-pressure-cooker-or-instant-pot/

I used 100g of steel cut oats cooked with 170g of water and 2.4g of salt for 20
minutes in the instant pot. After cooling, I combined 200g of the result with
60g of butter, 40g of sugar, and 100g of water and cooked for another hour. I
refrigerated them until the next day. The result was about 350g.

This turned out OK but not worth the extra work.

22 March 2024
"""

from recipe import R, TBD, water, flour

R.scale = 250

R += R.total_flour == 100
R += R.total_water == 70

R += "Wet"

R += R.leaven == 20
R += R.total_water == water(R.leaven, 100) + R.warm_water
wet = R.sum(oil=0, honey=0)

R += "Flours"

R += 100 == R.sum(
    flour(R.leaven, 100),
    prairie_gold=25,
    bronze_chief=20,
    spelt=15,
    potato_flakes=3,
    vwg=2,
    bread_flour=TBD,
)

R += "Dry"

dry = R.sum(
    improver=0.5,
    salt=2,
    yeast=0.4,
)

R += "Inclusion"

R += R.caramelized_oats == 50

R += ""

R += R.total == 100 + R.total_water + wet + dry + R.caramelized_oats

"""
Thinking about the caramelized oats

oats = 100
water = 170
salt = 2.4

cooked = 200 / 272.4 * (oats + water + salt)

butter = 60
sugar = 40
water = 100

caramelized = 350/400 * (cooked + butter + sugar + water)
"""
