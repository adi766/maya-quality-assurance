import os
from maya import cmds
from ..utils import QualityAssurance, reference





class Lambert1connections(QualityAssurance):
    """
    Checks if any nodes is connected to the initialShadingGroup (lambert1)
    Fixing will delete the node(s)
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "lambert1 has no incoming texture"
        self._message = "{0} texture node(s) connected to lambert1"
        self._categories = ["Textures"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: lambert1 incoming connections
        :rtype: generator
        """
        incoming_connections = cmds.listConnections('lambert1', destination=False, source=True)

        if incoming_connections:
            for connection in incoming_connections:
                yield connection

    def _fix(self, fileNode):
        """
        :param str fileNode:
        """
        incoming_connections = cmds.listConnections('lambert1', destination=False, source=True)

        if incoming_connections:
            for connection in incoming_connections:
                cmds.delete(connection)


class NonExistingTextures(QualityAssurance):
    """
    Check if there exist any texture that do not exist!
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Non Existing Textures"
        self._urgency = 1
        self._message = "{0} file(s) contain a link to a not existing texture"
        self._categories = ["Textures"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Textures that dont exist
        :rtype: generator
        """
        fileNodes = self.ls(type="file")
        for fileNode in fileNodes:
            path = cmds.getAttr("{0}.fileTextureName".format(fileNode))
            if not os.path.exists(path):
                yield fileNode

