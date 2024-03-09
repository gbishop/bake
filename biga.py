"""
# Rene R's 50% Spelt Biga

And an experiment with LP to replace spreadsheets.
"""


def water(total, hydration):
    return total * hydration / (1 + hydration)


def flour(total, hydration):
    return total / (1 + hydration)


from recipe import R

R += R.total_flour == 100
bp = R.total_flour * 0.01

R += R.biga_flour == 50 * bp
R += R.biga_flour == R.starter_flour + R.spelt
R += R.biga_water == 0.5 * R.biga_flour - R.starter_water

R += R.starter_water == R.starter_flour
R += R.starter_total == R.starter_water + R.starter_flour
R += R.starter_total == 0.05 * R.biga_flour

R += R.dough_water == 80 * bp
R += R.added_water == R.dough_water - R.biga_water - R.starter_water

R += (
    R.total_flour
    == R.biga_flour
    + R.starter_flour
    + R.potato_flakes
    + R.flaxseed_meal
    + R.bread_flour
)

R += R.potato_flakes == 3 * bp
R += R.flaxseed_meal == 2 * bp

R += R.add_ins == R.oil + R.honey + R.improver + R.salt + R.yeast + R.seeds

R += R.oil == 5 * bp
R += R.honey == 5 * bp
R += R.improver == 2 * bp
R += R.salt == 2 * bp
R += R.yeast == 0.3 * bp

R += R.seeds == 10 * bp

R += R.tdw == R.total_flour + R.dough_water + R.add_ins
