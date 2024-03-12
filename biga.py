"""
# Rene R's 50% Spelt Biga

And an experiment with LP to replace spreadsheets.
"""


def water(total, hydration):
    return total * hydration / (1 + hydration)


def flour(total, hydration):
    return total / (1 + hydration)


from recipe import R

R += R.total_flour == 200
bp = R.total_flour * 0.01

R += R.spelt == 50 * bp
R += R.biga_flour == R._starter_flour + R.spelt
R += R.biga_water == 0.5 * R.biga_flour - R._starter_water


def mix(name, hydration, total=None, flour=None, water=None):
    f = f"_{name}_flour"
    w = f"_{name}_water"
    result = [
        R[name] == R[f] + R[w],
        R[w] == hydration / 100 * R[f],
    ]
    if total:
        result.append(R[name] == total)
    if flour:
        result.append(R[f] == flour)
    if water:
        result.append(R[water] == hydration * R[flour])
    return result


R += mix("starter", total=0.05 * R.spelt, hydration=100)

R += R._dough_water == 70 * bp
R += R.added_water == R._dough_water - R.biga_water - R._starter_water

R += (
    R.total_flour
    == R.biga_flour
    + R._starter_flour
    + R.potato_flakes
    + R.flaxseed_meal
    + R.bread_flour
)

R += R.potato_flakes == 3 * bp
R += R.flaxseed_meal == 2 * bp

R += R.add_ins == R.oil + R.honey + R.improver + R.salt

R += R.oil == 5 * bp
R += R.honey == 5 * bp
R += R.improver == 2 * bp
R += R.salt == 2 * bp

R += R.tdw == R.total_flour + R._dough_water + R.add_ins
