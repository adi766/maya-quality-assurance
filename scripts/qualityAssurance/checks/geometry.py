from maya import cmds, OpenMaya
from ..utils import QualityAssurance, reference


class EmptyMesh(QualityAssurance):
    """
    Find meshes that have no vertices and are considered to be empty. When
    fixing this error the meshes will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Empty Mesh"
        self._message = "{0} mesh(es) are empty"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Empty meshes
        :rtype: generator
        """
        meshes = self.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            if not cmds.polyEvaluate(mesh, v=True):
                yield mesh

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        cmds.delete(mesh)


class EmptyMesh(QualityAssurance):
    """
    Find meshes that have non-manifold edges and/or faces.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Non Manifold Geometry"
        self._message = "{0} non-manifold edges or faces"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Empty meshes
        :rtype: generator
        """
        meshes = self.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            nmEdges = cmds.polyInfo(mesh, nonManifoldEdges=True) or []
            nmVertices = cmds.polyInfo(mesh, nonManifoldVertices=True) or []

            for error in nmEdges + nmVertices:
                yield error

class OverlappingFaces(QualityAssurance):
    """
    Find meshes that have overlapping faces. When fixing this error the
    overlapping faces will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Overlapping Faces"
        self._message = "{0} mesh(es) with overlapping face(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Overlapping faces
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()

        # get mesh iterator
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        # iterate meshes
        while not meshIter.isDone():
            # variables
            faces = []
            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            # ignore references
            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            # iterate faces
            faceIter = OpenMaya.MItMeshPolygon(dagNode)

            # variable
            allPoints = []
            allIndices = []

            print('mesh---------------', path)
            # loop faces
            while not faceIter.isDone():
                # get world space positions
                points = OpenMaya.MPointArray()
                faceIter.getPoints(points, OpenMaya.MSpace.kWorld)

                # sort points
                points = [
                    #sorted(
                    [
                        round(points[i][0], 5),
                        round(points[i][1], 5),
                        round(points[i][2], 5)
                    ]
                    #)
                    for i in range(points.length())
                ]

                # store points and indices
                allPoints.append(str(sorted(points)))
                allIndices.append(faceIter.index())

                faceIter.next()
            meshIter.next()

            # find matching faces
            seen = set()
            for i, p in zip(allIndices, allPoints):
                if p not in seen:
                    seen.add(p)
                    continue

                faces.append("{0}.f[{1}]".format(path, i))

            if not faces:
                continue

            yield faces

    def _fix(self, faces):
        """
        :param list faces:
        """
        cmds.delete(faces)


class ConcaveFaces(QualityAssurance):
    """
    Finds concave faces.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Concave Faces"
        self._message = "{0} objects with concave face(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Concave faces
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        while not meshIter.isDone():
            concave_faces = []

            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            mesh_fn = OpenMaya.MFnMesh(dagNode)

            num_polygons = mesh_fn.numPolygons()
            for face_index in range(num_polygons):
                if not mesh_fn.isPolygonConvex(face_index):
                    concave_faces.append("{0}.f[{1}]".format(path, face_index))

            meshIter.next()

            if not concave_faces:
                continue

            yield concave_faces

class ZeroEdgeLength(QualityAssurance):
    """
    Find edges no length.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Zero Edge Length"
        self._message = "{0} zero length edge(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Zero length edges
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()
        edgeLength = OpenMaya.MScriptUtil()
        edgeLengthPntr = edgeLength.asDoublePtr()

        # get mesh iterator
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        # iterate meshes
        while not meshIter.isDone():
            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            # ignore references
            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            # iterate edges
            edgeIter = OpenMaya.MItMeshEdge(dagNode)
            while not edgeIter.isDone():
                # get edge length
                edgeIter.getLength(edgeLengthPntr, OpenMaya.MSpace.kWorld)
                if edgeLength.getDouble(edgeLengthPntr) < 0.00001:
                    index = edgeIter.index()
                    yield "{0}.e[{1}]".format(path, index)

                edgeIter.next()
            meshIter.next()


class ZeroAreaFaces(QualityAssurance):
    """
    Find faces that have no surface area.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Zero Area Faces"
        self._message = "{0} zero area face(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Zero area faces
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()
        faceArea = OpenMaya.MScriptUtil()
        faceAreaPntr = faceArea.asDoublePtr()

        # get mesh iterator
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        # iterate meshes
        while not meshIter.isDone():
            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            # ignore references
            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            # iterate faces
            faceIter = OpenMaya.MItMeshPolygon(dagNode)
            while not faceIter.isDone():
                # get face area
                faceIter.getArea(faceAreaPntr, OpenMaya.MSpace.kWorld)
                if faceArea.getDouble(faceAreaPntr) < 0.00001:
                    index = faceIter.index()
                    yield "{0}.f[{1}]".format(path, index)

                faceIter.next()
            meshIter.next()



class NGonFaces(QualityAssurance):
    """
    Find meshes that have n-gon faces. When fixing this error the n-gon faces
    will be triangulated.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "N-Gon Faces"
        self._urgency = 1
        self._message = "{0} mesh(es) with n-gon face(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: N-Gon faces
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()

        # get mesh iterator
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        # iterate meshes
        while not meshIter.isDone():
            faces = []

            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            # ignore references
            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            # iterate faces
            faceIter = OpenMaya.MItMeshPolygon(dagNode)

            # loop faces
            while not faceIter.isDone():
                if faceIter.polygonVertexCount() > 4:
                    index = faceIter.index()
                    faces.append("{0}.f[{1}]".format(path, index))

                faceIter.next()
            meshIter.next()

            # if no error faces continue
            if not faces:
                continue

            yield faces

    def _fix(self, faces):
        """
        :param list faces:
        """
        cmds.polyTriangulate(faces, ch=False)


class LaminaFaces(QualityAssurance):
    """
    Find meshes that have lamina faces.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Lamina Faces"
        self._message = "{0} lamina face(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Lamina faces
        :rtype: generator
        """
        meshes = self.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            laminaFaces = cmds.polyInfo(mesh, laminaFaces=True) or []
            for error in laminaFaces:
                yield error

class DeleteColorSets(QualityAssurance):
    """
    Meshes will be checked if they have color set(s).
    When fixing this will delete all the color sets.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "No Color Sets"
        self._message = "{0} mesh(es) contain color sets"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes with Color Sets
        :rtype: generator
        """

        transforms = self.ls(transforms=True, l=True)

        for mesh in transforms:
            if len(cmds.polyColorSet( mesh, q=True, acs=True ) or []) > 0:
                yield mesh

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        cmds.polyColorSet(mesh, acs=True, d=True)

class LockedNormals(QualityAssurance):
    """
    Find meshes that have locked normals. When fixing this error the normals
    will be unlocked. Make sure that this is what you really want, CAD files
    in general have locked normals, these normals are needed to present the
    mesh properly.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Locked Normals"
        self._urgency = 1
        self._message = "{0} mesh(es) have locked normals"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Locked normals
        :rtype: generator
        """
        meshes = self.ls(type="mesh", noIntermediate=True, l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            normals = cmds.polyNormalPerVertex(
                "{0}.vtx[*]".format(mesh),
                query=True,
                freezeNormal=True
            )

            if True in normals:
                yield mesh


class BorderEdges(QualityAssurance):
    """
    Finds border edges, this is not an issue,  but sometimes certain
    edges needs to be mearged.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Border Edges"
        self._urgency = 0
        self._message = "{0} border edge(s)"
        self._categories = ["Geometry"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Border edges
        :rtype: generator
        """
        # variables
        obj = OpenMaya.MObject()

        # get mesh iterator
        meshIter = self.lsApi(nodeType=OpenMaya.MFn.kMesh)

        # iterate meshes
        while not meshIter.isDone():
            meshIter.getDependNode(obj)
            dagNode = OpenMaya.MDagPath.getAPathTo(obj)
            path = dagNode.fullPathName()

            # ignore references
            if cmds.referenceQuery(path, inr=True):
                meshIter.next()
                continue

            # iterate edges
            edgeIter = OpenMaya.MItMeshEdge(dagNode)
            while not edgeIter.isDone():
                # check if edge is a boundary edge
                if edgeIter.onBoundary():
                    index = edgeIter.index()
                    yield "{0}.e[{1}]".format(path, index)

                edgeIter.next()
            meshIter.next()