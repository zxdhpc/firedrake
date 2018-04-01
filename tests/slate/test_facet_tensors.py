import pytest
import numpy as np
from firedrake import *


@pytest.fixture(scope='module', params=[False, True])
def mesh(request):
    m = UnitSquareMesh(2, 2, quadrilateral=request.param)
    return m


def test_facet_interior_jump(mesh):
    DG = VectorFunctionSpace(mesh, "DG", 1)
    n = FacetNormal(mesh)
    u = TestFunction(DG)

    x, y = SpatialCoordinate(mesh)
    f = project(as_vector([x, y]), DG)

    form = jump(f[0]*f[1]*u, n=n)*dS

    A = assemble(Tensor(form)).dat.data
    ref = assemble(form).dat.data

    assert np.allclose(A, ref, rtol=1e-14)


def test_facet_interior_avg(mesh):
    DG = FunctionSpace(mesh, "DG", 1)
    u = TestFunction(DG)

    x, y = SpatialCoordinate(mesh)
    f = interpolate(x + y, DG)

    form = avg(f * u)*dS

    A = assemble(Tensor(form)).dat.data
    ref = assemble(form).dat.data

    assert np.allclose(A, ref, rtol=1e-14)


def test_facet_exterior(mesh):
    DG = VectorFunctionSpace(mesh, "DG", 1)
    n = FacetNormal(mesh)
    u = TestFunction(DG)

    x, y = SpatialCoordinate(mesh)
    f = project(as_vector([x, y]), DG)

    form = dot(f[0]*f[1]*u, n)*ds

    A = assemble(Tensor(form)).dat.data
    ref = assemble(form).dat.data

    assert np.allclose(A, ref, rtol=1e-14)


if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))
