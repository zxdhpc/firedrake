"""Firedrake P1 advection-diffusion demo

This demo solves the advection-diffusion equation and is advanced in time using
a theta scheme with theta = 0.5.
"""

import pytest

from firedrake import *


def adv_diff(x, quadrilateral=False):
    dt = 0.0001
    T = 0.01

    # Create mesh and define function space
    mesh = UnitSquareMesh(2 ** x, 2 ** x, quadrilateral=quadrilateral)
    V = FunctionSpace(mesh, "CG", 1)
    U = VectorFunctionSpace(mesh, "CG", 1)

    p = TrialFunction(V)
    q = TestFunction(V)
    t = Function(V)
    u = Function(U)

    diffusivity = 0.1

    M = inner(p, q) * dx
    d = dt * (diffusivity * inner(grad(p), grad(q)) - inner(u, grad(q)) * p) * dx
    a = M + 0.5 * d
    L = action(M - 0.5 * d, t)

    A = assemble(a)

    # Set initial condition:
    # A*(e^(-r^2/(4*D*T)) / (4*pi*D*T))
    # with normalisation A = 0.1, diffusivity D = 0.1
    r2 = "(pow(x[0]-(0.45+%(T)f), 2.0) + pow(x[1]-0.5, 2.0))"
    fexpr = "0.1 * (exp(-" + r2 + "/(0.4*%(T)f)) / (0.4*pi*%(T)f))"
    t.interpolate(Expression(fexpr % {'T': T}))
    u.interpolate(Expression([1.0, 0.0]))

    while T < 0.012:
        b = assemble(L)
        solve(A, t, b)
        T = T + dt

    # Analytical solution
    a = Function(V).interpolate(Expression(fexpr % {'T': T}))
    return sqrt(assemble(inner(t - a, t - a) * dx))


def run_adv_diff():
    import numpy as np
    diff = np.array([adv_diff(i) for i in range(5, 8)])
    convergence = np.log2(diff[:-1] / diff[1:])
    assert all(convergence > [1.8, 1.95])


def test_adv_diff_serial():
    run_adv_diff()


@pytest.mark.parallel
def test_adv_diff_parallel():
    run_adv_diff()


def run_adv_diff_on_quadrilaterals():
    import numpy as np
    diff = np.array([adv_diff(i, quadrilateral=True) for i in range(5, 8)])
    convergence = np.log2(diff[:-1] / diff[1:])
    assert all(convergence > [1.8, 1.95])


def test_adv_diff_on_quadrilaterals_serial():
    run_adv_diff_on_quadrilaterals()


@pytest.mark.parallel
def test_adv_diff_on_quadrilaterals_parallel():
    run_adv_diff_on_quadrilaterals()


if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))
