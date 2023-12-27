from maya import cmds, OpenMaya, OpenMayaAnim, mel
from ..utils import QualityAssurance, reference, skin, api


class UnusedInfluences(QualityAssurance):
    """
    Skin clusters will be checked to see if they contain unused influences.
    When fixing this error the unused influences will be removed from the skin
    cluster.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Unused Influences"
        self._urgency = 1
        self._message = "{0} skin cluster(s) contain unused influences"
        self._categories = ["Skinning"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Skin clusters with unused influences
        :rtype: generator
        """
        skinClusters = self.ls(type="skinCluster")
        skinClusters = reference.removeReferenced(skinClusters)

        for skinCluster in skinClusters:
            mesh = cmds.skinCluster(skinCluster, query=True, geometry=True)
            if not mesh:
                continue
                
            weighted = cmds.skinCluster(
                skinCluster, 
                query=True, 
                weightedInfluence=True 
            )
            influences = cmds.skinCluster(
                skinCluster, 
                query=True, 
                influence=True
            )
            
            for i in influences:
                if i not in weighted:
                    yield skinCluster
                    break

    def _fix(self, skinCluster):
        """
        :param str skinCluster:
        """
        weighted = cmds.skinCluster(
                skinCluster, 
                query=True, 
                weightedInfluence=True 
        )
        
        influences = cmds.skinCluster(
            skinCluster, 
            query=True, 
            influence=True
        )
        
        for i in influences:
            if i not in weighted:
                cmds.skinCluster(skinCluster, edit=True, removeInfluence=i)

                
class MaximumInfluences(QualityAssurance):
    """
    Skin clusters will be checked to see if they contain vertices that exceed
    the maximum influences. When fixing this error new skin weights will be 
    applied by removing and normalizing the lowest influences that are 
    exceeding the maximum amount.
    cluster.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Maximum Influences"
        self._message = "{0} skin cluster(s) exceed the maximum influences of 4"
        self._categories = ["Skinning"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Skin clusters which exceed maximum influences.
        :rtype: generator
        """
        # variables

        shapesList = cmds.ls(type="mesh",l=True)
        transformList = cmds.listRelatives(shapesList,parent=True,f=1) or []
        maxInfluence   = 4

        for transform in transformList:
            try:
                skin = mel.eval('findRelatedSkinCluster {}'.format(transform))
                skinMaxInf = cmds.skinCluster(skin, q=1, mi=1)
                if skinMaxInf > maxInfluence:
                    yield skin
            except:
                pass

     
    def _fix(self, skin):
        """
        :param str skinCluster:
        """
        shapesList = cmds.ls(type="mesh",l=True)
        transformList = cmds.listRelatives(shapesList,parent=True,f=1) or []
        maxInfluence   = 4

        for transform in transformList:
            try:
                skin = mel.eval('findRelatedSkinCluster {}'.format(transform))
                cmds.setAttr("{}.maxInfluences".format(skin))
                cmds.setAttr("{}.maxInfluences".format(skin), maxInfluence)
                cmds.setAttr("{}.maintainMaxInfluences".format(skin), True)
                cmds.setAttr("{}.normalizeWeights".format(skin), 1)
                cmds.skinPercent(skin, normalize=True)
                
                vertsCount = cmds.polyEvaluate(transform, v=True)
                for vert in range(vertsCount):
                    vertex = "{}.vtx[{}]".format(transform, vert)
                    influenceJoints = cmds.skinPercent(skin, vertex, transform=None, query=True, ignoreBelow=0.0000001)
                    while len(influenceJoints) > maxInfluence:
                        weights = sorted(cmds.skinPercent(skin, vertex, value=True, query=True, ignoreBelow=0.0000001),reverse=True)
                        for jnt in influenceJoints:
                            jointValue = cmds.skinPercent(skin, vertex, transform=jnt, query=True)
                            if jointValue == weights[-1]:
                                cmds.skinPercent(skin, vertex, transformValue=[(jnt, 0)])
                                print("removing {0} from {1}".format(jointValue, vertex))
                        influenceJoints = cmds.skinPercent(skin, vertex, transform=None, query=True, ignoreBelow=0.0000001)
            except:
                pass
