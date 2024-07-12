# coding: utf-8
from sympy import *
import numpy as np
import scipy
import time

fp, wp, sp, fg, wg, sg, tdw, eg, ep = symbols("fp wp sp fg wg sg tdw eg ep")

e = [
    fp - 1,
    fg - 500,
    wp - 0.7,
    wp * fg - wg,
    sp - 0.02,
    sp * fg - sg,
    ep * fg - eg,
    eg - 50,
    tdw - fg - wg - sg - eg,
]

v = (fp, fg, wp, wg, sp, sg, ep, eg, tdw)

s = solve(e, v, dict=True)


def func(
    x,  # current solution estimate
    m,  # linear terms
    n,  # terms scaled by total flour
    c,  # constant terms
    ti,  # index of the total flour
):
    lv = np.dot(m, x)
    nv = x[ti] * np.dot(n, x)
    return lv + nv + c


x0 = np.array([50, 100, 50, 100, 50, 100, 50, 100, 100])
m = np.zeros([9, 9])
c = np.zeros(9)
n = np.zeros([9, 9])

# fp = 100
m[0, 0] = 1
c[0] = -100
# fg = 500
m[1, 1] = 1
c[1] = -500
# wp = 70%
m[2, 2] = 1
c[2] = -70
# wg = wp * fg
m[3, 3] = 1
n[3, 2] = -0.01
# sp = 2
m[4, 4] = 1
c[4] = -2
# sg = sp * fg
m[5, 5] = 1
n[5, 4] = -0.01
# eg = ep * fg
m[6, 7] = 1
n[6, 6] = -0.01
# eg = 50,
m[7, 7] = 1
c[7] = -50
# tdw - fg - wg - sg - eg,
m[8, 8] = 1
m[8, 1] = -1
m[8, 3] = -1
m[8, 5] = -1
m[8, 7] = -1

t0 = time.time()
opt = scipy.optimize.least_squares(func, x0, args=(m, n, c, 1))
print(time.time() - t0)
print(opt)
