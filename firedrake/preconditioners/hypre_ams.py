from firedrake.preconditioners.base import PCBase
from firedrake.petsc import PETSc
from firedrake.functionspace import FunctionSpace
from firedrake.constant import Constant
from firedrake.ufl_expr import TestFunction
from firedrake.interpolation import Interpolator
from firedrake.projection import project
from firedrake.dmhooks import get_function_space
from firedrake.utils import complex_mode
from firedrake_citations import Citations
from ufl import grad

__all__ = ("HypreAMS",)


class HypreAMS(PCBase):
    def initialize(self, obj):
        if complex_mode:
            raise NotImplementedError("HypreAMS preconditioner not yet implemented in complex mode")

        Citations().register("Kolev2009")
        A, P = obj.getOperators()
        prefix = obj.getOptionsPrefix()
        V = get_function_space(obj.getDM())
        mesh = V.mesh()

        family = str(V.ufl_element().family())
        degree = V.ufl_element().degree()
        if family != 'Nedelec 1st kind H(curl)' or degree != 1:
            raise ValueError("Hypre AMS requires lowest order Nedelec elements! (not %s of degree %d)" % (family, degree))

        P1 = FunctionSpace(mesh, "Lagrange", 1)
        G = Interpolator(grad(TestFunction(P1)), V).callable().handle

        pc = PETSc.PC().create(comm=obj.comm)
        pc.incrementTabLevel(1, parent=obj)
        pc.setOptionsPrefix(prefix + "hypre_ams_")
        pc.setOperators(A, P)

        pc.setType('hypre')
        pc.setHYPREType('ams')
        pc.setHYPREDiscreteGradient(G)
        zero_beta = PETSc.Options(prefix).getBool("pc_hypre_ams_zero_beta_poisson", default=False)
        if zero_beta:
            pc.setHYPRESetBetaPoissonMatrix(None)

        # Build constants basis for the Nedelec space
        cvecs = []
        for i in range(mesh.cell_dimension()):
            direction = [1.0 if i == j else 0.0 for j in range(mesh.cell_dimension())]
            c = project(Constant(direction), V)
            with c.vector().dat.vec_ro as cvec:
                cvecs.append(cvec)
        pc.setHYPRESetEdgeConstantVectors(*cvecs)
        pc.setUp()

        self.pc = pc

    def apply(self, pc, x, y):
        self.pc.apply(x, y)

    def applyTranspose(self, pc, x, y):
        self.pc.applyTranspose(x, y)

    def view(self, pc, viewer=None):
        super(HypreAMS, self).view(pc, viewer)
        if hasattr(self, "pc"):
            viewer.printfASCII("PC to apply inverse\n")
            self.pc.view(viewer)

    def update(self, pc):
        self.pc.setUp()
