# Baking formulas with relations

This is a hack. I wrote it because I was sick of fooling with
spreadsheets. Programming is more fun than spreadsheets!

I'm currently using the `*.bake` files for my recipes.

A bake file might look like this:
```
starter:
  ap_flour
  water
  hydration = 100%

leaven:
  starter
  bread_flour = 5 * starter
  cold_water
  extra = -20g
  hydration = 100%

grain:
  prairie_gold
  hard_red
  barley = 5%
  spelt = 5%
  buckwheat = 5%

dry:
  grain
  vwg = 3%
  potato_flakes = 5%
  flaxseed_meal = 5%
  yeast = 0.5%
  salt = 1.8%

wet:
  cold_water
  old_dough = 100g
  ascorbic_acid_1p = 50ppm * 100 * grain
  leaven = 40%
  olive_oil = 5%
  honey = 5%
  yogurt = 5%

dough:
  wet
  dry
  hydration = 70%
  old_dough = 0 - wet.old_dough # forgot to remove it
  total_flour = 500g # 9 inch

```

And produce a table like this:

```
┌─────────┬─────────┬──────────────────┬───────┬────────┬────────┐
│   part  │  grams  │    ingredient    │   %   │ flour  │ water  │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ starter │   20.0  │                  │   4.0 │  10.0  │  10.0  │
│         │   10.0  │ ap_flour         │   2.0 │  10.0  │        │
│         │   10.0  │ water            │   2.0 │        │  10.0  │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ leaven  │  200    │                  │  40.0 │ 110    │ 110    │
│         │   20.0  │ starter          │   4.0 │  10.0  │  10.0  │
│         │  100    │ bread_flour      │  20.0 │ 100    │        │
│         │  100    │ cold_water       │  20.0 │        │ 100    │
│         │  -20.0  │ extra            │  -4.0 │        │        │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ grain   │  350    │                  │  70.0 │ 350    │        │
│         │  137    │ prairie_gold     │  27.5 │ 137    │        │
│         │  138    │ hard_red         │  27.5 │ 138    │        │
│         │   25.0  │ barley           │   5.0 │  25.0  │        │
│         │   25.0  │ spelt            │   5.0 │  25.0  │        │
│         │   25.0  │ buckwheat        │   5.0 │  25.0  │        │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ dry     │  427    │                  │  85.3 │ 390    │ -50.0  │
│         │  350    │ grain            │  70.0 │ 350    │        │
│         │   15.0  │ vwg              │   3.0 │  15.0  │        │
│         │   25.0  │ potato_flakes    │   5.0 │        │ -50.0  │
│         │   25.0  │ flaxseed_meal    │   5.0 │  25.0  │        │
│         │    2.50 │ yeast            │   0.5 │        │        │
│         │    9.0  │ salt             │   1.8 │        │        │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ wet     │  640    │                  │ 127.9 │ 110    │ 400    │
│         │  263    │ cold_water       │  52.6 │        │ 263    │
│         │  100    │ old_dough        │  20.0 │        │        │
│         │    1.75 │ ascorbic_acid_1p │   0.3 │        │   1.75 │
│         │  200    │ leaven           │  40.0 │ 110    │ 110    │
│         │   25.0  │ olive_oil        │   5.0 │        │        │
│         │   25.0  │ honey            │   5.0 │        │   4.25 │
│         │   25.0  │ yogurt           │   5.0 │        │  21.0  │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│ dough   │  966    │                  │ 193.2 │ 500    │ 350    │
│         │  640    │ wet              │ 127.9 │ 110    │ 400    │
│         │  427    │ dry              │  85.3 │ 390    │ -50.0  │
│         │ -100    │ old_dough        │ -20.0 │        │        │
│         │         │ hydration        │  70.0 │        │        │
├─────────┼─────────┼──────────────────┼───────┼────────┼────────┤
│         │   78.3  │ protein          │   8.9 │        │        │
│         │   49.9  │ fiber            │   5.7 │        │        │
│         │   46.8  │ fat              │   5.3 │        │        │
│         │  388    │ carbs            │  44.2 │        │        │
│         │ 2288    │ calories         │ 260.2 │        │        │
└─────────┴─────────┴──────────────────┴───────┴────────┴────────┘
```

You can specify values in grams (suffix g) or baker's percent (suffix %). You
can mix them in the same recipe.

See the recipes folder for examples.
