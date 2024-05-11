"""
┌────────────────┬───────┬───────┬────────────────┬────────┬─────────┐
│                │   %   │   g   │                │   sum  │   +bowl │
├────────────────┼───────┼───────┼────────────────┼────────┼─────────┤
│         soaker │  35.1 │ 175.8 │ soaker         │  175.8 │   900.9 │
│        polenta │  10.0 │  50.0 │ polenta        │  225.8 │   950.9 │
│  boiling water │  25.0 │ 125.0 │ boiling water  │  350.8 │  1075.8 │
│ diastatic malt │   0.1 │   0.8 │ diastatic malt │  351.5 │  1076.6 │
│        starter │   1.4 │   7.1 │ starter        │  358.6 │  1083.7 │
│    starter rye │   0.7 │   3.6 │ starter rye    │  362.2 │  1087.3 │
│  starter water │   0.7 │   3.6 │ starter water  │  365.8 │  1090.9 │
│         sponge │  30.0 │ 150.0 │ sponge         │  515.8 │  1240.9 │
│     sponge rye │  14.3 │  71.4 │ sponge rye     │  587.2 │  1312.3 │
│     warm water │  14.3 │  71.4 │ warm water     │  658.6 │  1383.7 │
│            dry │  75.0 │ 375.0 │ dry            │ 1033.6 │  1758.7 │
│   prairie gold │  50.0 │ 250.0 │ prairie gold   │ 1283.6 │  2008.7 │
│   bronze chief │  25.0 │ 125.0 │ bronze chief   │ 1408.6 │  2133.7 │
│            wet │ 120.2 │ 600.8 │ wet            │ 2009.4 │  2734.5 │
│          water │  55.0 │ 275.0 │ water          │ 2284.4 │  3009.5 │
└────────────────┴───────┴───────┴────────────────┴────────┴─────────┘

# stuff
"""

from recipe import R

R += R.soaker == R.polenta + R.boiling_water + R.diastatic_malt
R += R.boiling_water == 2.5 * R.polenta
R += R.diastatic_malt == 0.015 * R.polenta

R += R.starter == R.starter_rye + R.starter_water
R += R.starter_rye == R.starter_water

R += R.sponge == R.sponge_rye + R.starter + R.warm_water
R += R.starter == 0.1 * R.sponge_rye
R += R.warm_water == R.sponge_rye + R.starter_rye - R.starter_water

R += R.dry == R.prairie_gold + R.bronze_chief
R += R.bronze_chief == 0.5 * R.prairie_gold

R += R.wet == R.water + R.soaker + R.sponge
R += R.polenta == 10
R += R.sponge == 30

R += 100 == R.polenta + R.starter_rye + R.sponge_rye + R.prairie_gold + R.bronze_chief
R += 70 == R.water + R.warm_water + R.starter_water
