from maya import cmds
from ..utils import QualityAssurance, reference


class NoShadingGroup(QualityAssurance):
    """
    Meshes will be checked to see if they have a shading group attached.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "No Shading Group Assignment"
        self._message = "{0} mesh(es) are not connected to any shading group"
        self._categories = ["Shaders"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes without shading group attachment
        :rtype: generator
        """
        meshes = self.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            shadingGroups = cmds.listConnections(mesh, type="shadingEngine")
            if not shadingGroups:
                yield mesh


class InitialShadingGroup(QualityAssurance):
    """
    Meshes will be checked to see if they have the default shading group
    attached.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Initial Shading Group Assignment"
        self._message = "{0} object(s) are connected to the initial shading group"
        self._categories = ["Shaders"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes without shading group attachment
        :rtype: generator
        """
        shadingGroups = cmds.ls(type="shadingEngine")

        if "initialShadingGroup" not in shadingGroups:
            return

        connections = cmds.sets("initialShadingGroup", query=True) or []
        if not connections:
            return

        connections = cmds.ls(connections, l=True)
        for connection in connections:
            yield connection


