from maya import cmds
from ..utils import QualityAssurance, reference

class NoUVSell(QualityAssurance):
    """Ensure meshes have UVs"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "All mesh has UVs"
        self._message = "{0} face(s) with no UV"
        self._categories = ["UV"]
        self._selectable = True

    def _find(self):
        """
        :return: list of faces without uvs
        :rtype: generator
        """
        meshes = cmds.ls(type='mesh', long=True)
        faces = []
        for mesh in meshes:
            # Get the faces for each mesh and concatenate '.f[:]' to each face
            mesh_faces = cmds.ls(mesh + '.f[:]', flatten=True)
            faces.extend(mesh_faces)

        for face in faces:
            # Check if the face has a UV shell
            uv_shell = cmds.polyListComponentConversion(face, fromFace=True, toUV=True)
            if not uv_shell:
                yield face
                
class UVSetMap1(QualityAssurance):
    """Ensure meshes have the default UV set"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Has UV set map1"
        self._message = "{0} mesh has map1 renamed and must be fixed"
        self._categories = ["UV"]
        self._selectable = False
    # ------------------------------------------------------------------------
    def _find(self):
        """
        :return: list of meshes without map1 uv set
        :rtype: generator
        """
        meshes = cmds.ls(type='mesh', long=True)

        invalid = []
        for mesh in meshes:

            # Get existing mapping of uv sets by index
            indices = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)
            maps = cmds.polyUVSet(mesh, query=True, allUVSets=True)
            mapping = dict(zip(indices, maps))

            # Get the uv set at index zero.
            name = mapping[0]
            if name != "map1":
                yield mesh


    def _fix(self, mesh):
        """
        :param str animCurve:
        """
        print(mesh)
        # Get existing mapping of uv sets by index
        indices = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)
        maps = cmds.polyUVSet(mesh, query=True, allUVSets=True)
        mapping = dict(zip(indices, maps))

        # Ensure there is no uv set named map1 to avoid
        # a clash on renaming the "default uv set" to map1
        existing = set(maps)
        if "map1" in existing:
            print('existing')
            # Find a unique name index
            i = 2
            while True:
                name = "map{0}".format(i)
                if name not in existing:
                    break
                i += 1

            cmds.polyUVSet(mesh,
                            rename=True,
                            uvSet="map1",
                            newUVSet=name)

        # Rename the initial index to map1
        original = mapping[0]
        cmds.polyUVSet(mesh,
                        rename=True,
                        uvSet=original,
                        newUVSet="map1")

class EmptyUVSets(QualityAssurance):
    """
    Meshes will be checked to see if they have empty uv sets. When fixing the
    uv set will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Empty UV Sets"
        self._message = "{0} empty uv set(s)"
        self._categories = ["UV"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Empty UV Sets
        :rtype: generator
        """
        meshes = cmds.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            uvSets = cmds.polyUVSet(mesh, query=True, allUVSets=True)
            uvSetsIndex = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)

            for uvSet, index in zip(uvSets, uvSetsIndex):
                if index == 0:
                    continue

                if not cmds.polyEvaluate(mesh, uvcoord=True, uvSetName=uvSet):
                    yield "{0}.uvSet[{1}].uvSetName".format(mesh, index)

    def _fix(self, meshAttribute):
        """
        :param str meshAttribute:
        """
        mesh = meshAttribute.split(".")[0]
        uvSet = cmds.getAttr(meshAttribute)

        cmds.polyUVSet(mesh, edit=True, delete=True, uvSet=uvSet)


class UnusedUVSets(QualityAssurance):
    """
    Meshes will be checked to see if they have unused uv sets. When fixing the
    uv set will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Unused UV Sets"
        self._message = "{0} unused uv set(s)"
        self._categories = ["UV"]
        self._selectable = True

        self._ignoreUvSets = [
            "hairUVSet",
        ]

    # ------------------------------------------------------------------------

    @property
    def ignoreUvSets(self):
        return self._ignoreUvSets

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Empty UV Sets
        :rtype: generator
        """
        meshes = cmds.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            uvSets = cmds.polyUVSet(mesh, query=True, allUVSets=True)
            uvSetsIndex = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)

            for uvSet, index in zip(uvSets, uvSetsIndex):
                if index == 0 or uvSet in self.ignoreUvSets:
                    continue

                attr = "{0}.uvSet[{1}].uvSetName".format(mesh, index)
                if not cmds.listConnections(attr):
                    yield attr

    def _fix(self, meshAttribute):
        """
        :param str meshAttribute:
        """
        mesh = meshAttribute.split(".")[0]
        uvSet = cmds.getAttr(meshAttribute)

        cmds.polyUVSet(mesh, edit=True, delete=True, uvSet=uvSet)



