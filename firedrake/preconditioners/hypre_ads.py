from firedrake.preconditioners.base import PCBase
from firedrake.petsc import PETSc
from firedrake.functionspace import FunctionSpace
from firedrake.ufl_expr import TestFunction
from firedrake.interpolation import Interpolator
from firedrake.dmhooks import get_function_space
from ufl import grad, curl

__all__ = ("HypreADS",)


class HypreADS(PCBase):
    def initialize(self, obj):
        A, P = obj.getOperators()
        prefix = obj.getOptionsPrefix()
        V = get_function_space(obj.getDM())
        mesh = V.mesh()

        family = str(V.ufl_element().family())
        degree = V.ufl_element().degree()
        if family != 'Raviart-Thomas' or degree != 1:
            raise ValueError("Hypre ADS requires lowest order RT elements! (not %s of degree %d)" % (family, degree))

        P1 = FunctionSpace(mesh, "Lagrange", 1)
        NC1 = FunctionSpace(mesh, "N1curl", 1)
        # DiscreteGradient
        G = Interpolator(grad(TestFunction(P1)), NC1).callable().handle
        # DiscreteCurl
        C = Interpolator(curl(TestFunction(NC1)), V).callable().handle

        pc = PETSc.PC().create(comm=obj.comm)
        pc.incrementTabLevel(1, parent=obj)
        pc.setOptionsPrefix(prefix + "hypre_ads_")
        pc.setOperators(A, P)

        pc.setType('hypre')
        pc.setHYPREType('ads')
        pc.setHYPREDiscreteGradient(G)
        pc.setHYPREDiscreteCurl(C)
        pc.setCoordinates(mesh.coordinates.dat.data_ro)

        pc.setUp()
        self.pc = pc

    def apply(self, pc, x, y):
        self.pc.apply(x, y)

    def applyTranspose(self, pc, x, y):
        self.pc.applyTranspose(x, y)

    def view(self, pc, viewer=None):
        super(HypreADS, self).view(pc, viewer)
        if hasattr(self, "pc"):
            viewer.printfASCII("PC to apply inverse\n")
            self.pc.view(viewer)

    def update(self, pc):
        self.pc.setUp()