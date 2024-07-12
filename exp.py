# coding: utf-8
from sympy import symbols, nonlinsolve
import numpy as np
import scipy
import time

# equations for both percent and grams

fp, wp, sp, fg, wg, sg, tdw, tdp, eg, ep = symbols("fp wp sp fg wg sg tdw eg ep tdp")

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
    tdp * fg - tdw,
]

v = (fp, fg, wp, wg, sp, sg, ep, eg, tdw, tdp)

s = nonlinsolve(e, v)

print("s1", s)

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


def func(
    x,  # current solution estimate
    m,  # linear terms
    n,  # terms scaled by total flour
    c,  # constant terms
    ti,  # index of the total flour
):
    lv = np.dot(m, x)
    nv = np.dot(n, x) * x[ti]
    return lv + nv + c


t0 = time.time()
opt = scipy.optimize.least_squares(func, x0, args=(m, n, c, 1))
print("m1", time.time() - t0)
print(opt)

# mixed grams and percent

e2 = [
    fp - 1,
    fg - 500,
    wp - 0.7,
    sp - 0.02,
    ep - 50 / fg,
    tdp - fp - wp - sp - ep,
]

v2 = (fp, fg, wp, sp, ep, tdp)

s2 = nonlinsolve(e2, v2)

print("s2", s2)

x0 = np.array([50, 100, 50, 50, 50, 200])
m = np.zeros([6, 6])
n = np.zeros(6)
c = np.zeros(6)

m[0, 0] = 1
c[0] = -100
m[1, 1] = 1
c[1] = -500
m[2, 2] = 1
c[2] = -70
m[3, 3] = 1
c[3] = -2
m[4, 4] = 1
n[4] = -50
m[5, 5] = 1
m[5, 0] = -1
m[5, 2] = -1
m[5, 3] = -1
m[5, 4] = -1


def func2(
    x,  # current solution estimate
    m,  # linear terms
    n,  # terms scaled by total flour
    c,  # constant terms
    ti,  # index of the total flour
):
    lv = np.dot(m, x)
    nv = 100 * n / x[ti]
    return lv + nv + c


t0 = time.time()
opt = scipy.optimize.least_squares(func2, x0, args=(m, n, c, 1))
print(time.time() - t0)
print(opt)

# specify grams for everything

e3 = [
    fp - 1,
    fg - 500,
    wp - 350 / fg,
    sp - 10 / fg,
    ep - 50 / fg,
    tdp - fp - wp - sp - ep,
]

s3 = nonlinsolve(e3, v2)

print("s3", s3)

x0 = np.array([50, 100, 50, 50, 50, 200])
x0 = np.ones(6)
m = np.zeros([6, 6])
n = np.zeros(6)
c = np.zeros(6)

m[0, 0] = 1
c[0] = -100
m[1, 1] = 1
c[1] = -500
m[2, 2] = 1
n[2] = -350
m[3, 3] = 1
n[3] = -10
m[4, 4] = 1
n[4] = -50
m[5, 5] = 1
m[5, 0] = -1
m[5, 2] = -1
m[5, 3] = -1
m[5, 4] = -1

t0 = time.time()
opt = scipy.optimize.least_squares(func2, x0, args=(m, n, c, 1))
print(time.time() - t0)
print(opt)

# specify TDW instead of fg
e4 = [
    fp - 1,
    tdp - 910 / fg,
    wp - 0.7,
    sp - 0.02,
    ep - 50 / fg,
    tdp - fp - wp - sp - ep,
]

v4 = (fp, fg, wp, sp, ep, tdp)

s4 = nonlinsolve(e4, v4)

print("s4", s4)

x0 = np.array([100, 100, 50, 50, 50, 200])
m = np.zeros([6, 6])
n = np.zeros(6)
c = np.zeros(6)

m[0, 0] = 1
c[0] = -100
m[1, 5] = 1
n[1] = -910
m[2, 2] = 1
c[2] = -70
m[3, 3] = 1
c[3] = -2
m[4, 4] = 1
n[4] = -50
m[5, 5] = 1
m[5, 0] = -1
m[5, 2] = -1
m[5, 3] = -1
m[5, 4] = -1

t0 = time.time()
opt = scipy.optimize.least_squares(func2, x0, args=(m, n, c, 1))
print(time.time() - t0)
print(opt)

# how about a gram focused solution

f1, f2 = symbols("f1 f2")

e5 = [
    fg - f1 - f2,
    f2 - 0.2 * fg,
    tdw - 910,
    wg - 0.7 * fg,
    sg - 0.02 * fg,
    eg - 50,
    tdw - f1 - f2 - wg - sg - eg,
]

v5 = (fg, f1, f2, wg, sg, eg, tdw)

s5 = nonlinsolve(e5, v5)

print("s5", s5)

x0 = np.ones(7) * 100.0
m = np.zeros([7, 7])
n = np.zeros(7)
c = np.zeros(7)

m[0, 0] = 1
m[0, 1] = -1
m[0, 2] = -1
m[1, 2] = 1
n[1] = -20
m[2, 6] = 1
c[2] = -910
m[3, 3] = 1
n[3] = -70
m[4, 4] = 1
n[4] = -2
m[5, 5] = 1
c[5] = -50
m[6, 6] = 1
m[6, 1] = -1
m[6, 2] = -1
m[6, 3] = -1
m[6, 4] = -1
m[6, 5] = -1


def func3(
    x,  # current solution estimate
    m,  # linear terms
    n,  # terms scaled by total flour
    c,  # constant terms
    ti,  # index of the total flour
):
    lv = np.dot(m, x)
    nv = n * x[ti] / 100
    return lv + nv + c


t0 = time.time()
opt = scipy.optimize.least_squares(func3, x0, args=(m, n, c, 0))
print(time.time() - t0)
print(opt)


# how does it break when over constrained

f1, f2 = symbols("f1 f2")

e5 = [
    fg - f1 - f2,
    f2 - 0.2 * fg,
    tdw - 910,
    wg - 0.7 * fg,
    sg - 0.02 * fg,
    eg - 50,
    tdw - f1 - f2 - wg - sg - eg,
    f1 - 400,  # this is an error
]

v5 = (fg, f1, f2, wg, sg, eg, tdw)

s5 = nonlinsolve(e5, v5)

print("s5", s5)

x0 = np.ones(7) * 100.0
m = np.zeros([8, 7])
n = np.zeros(8)
c = np.zeros(8)

m[0, 0] = 1
m[0, 1] = -1
m[0, 2] = -1
m[1, 2] = 1
n[1] = -20
m[2, 6] = 1
c[2] = -910
m[3, 3] = 1
n[3] = -70
m[4, 4] = 1
n[4] = -2
m[5, 5] = 1
c[5] = -50
m[6, 6] = 1
m[6, 1] = -1
m[6, 2] = -1
m[6, 3] = -1
m[6, 4] = -1
m[6, 5] = -1
m[7, 1] = 1
c[7] = -300


t0 = time.time()
opt = scipy.optimize.least_squares(func3, x0, args=(m, n, c, 0))
print(time.time() - t0)
print(opt)
