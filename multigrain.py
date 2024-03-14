"""
# My usual loaf

And an experiment with LP to replace spreadsheets.
"""

from recipe import R, TBD, water, flour

R += R.total_flour == 100
R += R.total_water == 70

R += "Liquid"

R += R.starter == 20
R += R.total_water == water(R.starter, 100) + R.warm_water

R += "Grains"

R += 100 == R.sum(
    flour(R.starter, 100),
    prairie_gold=60,
    bronze_chief=20,
    spelt=15,
    rye=5,
    oats=5,
    potato_flakes=3,
    flaxseed_meal=2,
    bread_flour=TBD,
)

R += "Additions"

R += R.sum(
    oil=5,
    honey=5,
    improver=2,
    salt=2,
    yeast=0.4,
    nuts=15,
)
