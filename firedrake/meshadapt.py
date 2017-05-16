from __future__ import absolute_import, print_function, division

import numpy as np

from firedrake.mesh import Mesh
import firedrake.dmplex as dmplex


__all__ = ['adapt']




class AAdaptation(object):

    """
    Object that performs anisotropic mesh adaptation
    """

    def __init__(self, mesh, metric):
        """
        """
        self.mesh = mesh
        self.metric = metric
        self.meshnew = None


    def adapt(self):
        """
        """
        self.meshnew = adapt(self.mesh, self.metric)



    def transfer_solution(self, f, fnew):
        """
        """
        if self.newmesh == None:
            raise("Cannot transfer solution before generating adapted mesh")
        #TODO many checks
        fnew.dat.data[:] = f.at(meshnew.coordinates.dat.data)



def adapt(mesh, metric):
    """ Adapt the mesh to a prescribed metric field.

    :arg mesh: the base mesh to adapt
    :arg metric: a metric tensor field (a Function of a TensorFunctionSpace)

    :return: a new mesh adapted to the metric
    """
    dim = mesh._topological_dimension
    entity_dofs = np.zeros(dim+1, dtype=np.int32)
    entity_dofs[0] = mesh.geometric_dimension()
    coordSection = mesh._plex.createSection([1], entity_dofs, perm=mesh.topology._plex_renumbering)
    dmCoords = mesh.topology._plex.getCoordinateDM()
    dmCoords.setDefaultSection(coordSection)

    with mesh.coordinates.dat.vec_ro as coords:
        mesh.topology._plex.setCoordinatesLocal(coords)
    with metric.dat.vec as vec:
        dmplex.reorder_metric(mesh.topology._plex, vec, coordSection)
    with metric.dat.vec_ro as vec:
        newplex = mesh.topology._plex.adapt(vec, "boundary_ids")

    newmesh = Mesh(newplex)

    return newmesh