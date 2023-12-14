from maya import cmds
from ..utils import QualityAssurance, reference


class CustomShaderTechnique(QualityAssurance):
    """
    Custom Shaders (GLSL) will be checked 
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Shader Technique"
        self._message = "{0} shader(s) set to Uber-Transparent"
        self._categories = ["Implementation"]
        self._selectable = True


        self._attributes = [
            '.technique'
        ]
        self._values = [
            "Uber"
        ]

    # ------------------------------------------------------------------------
    @property
    def defaultState(self):
        """
        :return: Default state of attributes with values
        :rtype: list
        """
        return zip(self._attributes, self._values)


    def _find(self):
        """
        :return: shaders
        :rtype: generator
        """
        glslShaders =  self.ls(type="GLSLShader")

        for glsl in glslShaders:
            for attr, value in self.defaultState:
                if not cmds.objExists(glsl + attr):
                    continue

                if cmds.getAttr(glsl + attr) != value:
                    yield glsl

    def _fix(self, glsl):
        glslShaders =  self.ls(type="GLSLShader")

        for glsl in glslShaders:
            for attr, value in self.defaultState:
                cmds.setAttr(glsl+ attr, value,type= "string")
