"""
# Rene R's 50% Spelt Biga

And an experiment with LP to replace spreadsheets.
"""


def water(total, hydration):
    return total * hydration / (100 + hydration)


def flour(total, hydration):
    return total * 100 / (100 + hydration)


from recipe import R, TBD

R.scale = 250  # total flour

R += R.total_flour == 100
R += R.total_water == 70

R += "Biga"

R += R.starter == 0.1 * R.spelt
R += R.water == 0.5 * R.spelt - water(R.starter, 100)
R += R.spelt == 50

R += "Dough"

R += R.total_water == R.added_water + R.water + water(R.starter, 100)

R += R.total_flour == R.sum(
    R.spelt, flour(R.starter, 100), bread_flour=TBD, potato_flakes=3, flaxseed_meal=2
)

additions = R.sum(oil=5, honey=5, improver=2, salt=2)

R += ""

R += R.total == 100 + R.total_water + additions
