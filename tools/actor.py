import math
from .conversions import *

class ACTLayout:
    SIZE_OF_STRUCT = 0x20

    def __init__(self, b: bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        self.versionNumber = int_from_bytes(b[0:][:4])
        self.actorID = int_from_bytes(b[4:][:2])
        
        self.numberOfBones = int_from_bytes(b[6:][:2])
        self.pBranch = int_from_bytes(b[8:][:4])
        self.pRootBone = int_from_bytes(b[12:][:4])
        self.pFileName = int_from_bytes(b[16:][:4])
        
        self.skinFileID = int_from_bytes(b[20:][:2])
        self.pad = int_from_bytes(b[22:][:2])
        self.userDefinedDataSize = int_from_bytes(b[24:][:4])
        self.pUserData = int_from_bytes(b[28:][:4])
        

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"{self.versionNumber=}\n"
        t += f"{self.actorID=}\n"
        t += f"{self.numberOfBones=}\n"
        t += f"{self.pBranch=}\n"
        t += f"{self.pRootBone=}\n"
        t += f"{self.pFileName=}\n"
        t += f"{self.skinFileID=}\n"
        t += f"{self.pad=}\n"
        t += f"{self.userDefinedDataSize=}\n"
        t += f"{self.pUserData=}"
        return t

class ACTBoneLayout:
    SIZE_OF_STRUCT = 0x1c

    def __init__(self, b: bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        self.pOrientationControl = int_from_bytes(b[0:][:4])
        self.pPreviousSibling = int_from_bytes(b[4:][:4])
        self.pNextSibling = int_from_bytes(b[8:][:4])
        self.pParent = int_from_bytes(b[12:][:4])
        self.pChildren = int_from_bytes(b[16:][:4])

        self.displayObjectID = int_from_bytes(b[20:][:2], signed=True)
        self.boneID = int_from_bytes(b[22:][:2])

        self.inheritanceFlag = int_from_bytes(b[24:][:1])
        self.drawingPriority = int_from_bytes(b[25:][:1])
        
        self.pad = int_from_bytes(b[26:][:2])

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"{self.pOrientationControl=}\n"
        t += f"{self.pPreviousSibling=}\n"
        t += f"{self.pNextSibling=}\n"
        t += f"{self.pParent=}\n"
        t += f"{self.pChildren=}\n"
        t += f"{self.displayObjectID=}\n"
        t += f"{self.boneID=}\n"
        t += f"{self.inheritanceFlag=}\n"
        t += f"{self.drawingPriority=}\n"
        t += f"{self.pad=}"
        return t

class ACTControl:
    SIZE_OF_STRUCT = 0x34

    CTRL_NONE       = 0x00
    CTRL_SCALE      = 0x01
    CTRL_ROT_EULER  = 0x02
    CTRL_ROT_QUAT   = 0x04
    CTRL_TRANS      = 0x08
    CTRL_MTX        = 0x10

    def __init__(self, b: bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        
        self.ControlType = int_from_bytes(b[0:][:1])
        self.ControlType_Name = ACTControl.__assign_control_name__(self.ControlType)
        self.pad1 = int_from_bytes(b[1:][:3])
        assert(self.ControlType & ~0b1101 == 0)

        self.has_scale = self.ControlType & 0x1
        self.has_rotate = self.ControlType & 0x4
        self.has_transform = self.ControlType & 0x8

        self.scaleX = float_from_bytes(b[4:][:4])
        self.scaleY = float_from_bytes(b[8:][:4])
        self.scaleZ = float_from_bytes(b[12:][:4])

        self.rotateX = float_from_bytes(b[16:][:4])
        self.rotateY = float_from_bytes(b[20:][:4])
        self.rotateZ = float_from_bytes(b[24:][:4])
        self.rotateW = float_from_bytes(b[28:][:4])

        self.rotateDistance = math.sqrt(self.rotateX**2 + self.rotateY**2+self.rotateZ**2+self.rotateW**2)

        self.transformX = float_from_bytes(b[32:][:4])
        self.transformY = float_from_bytes(b[36:][:4])
        self.transformZ = float_from_bytes(b[40:][:4])

        self.pad2 = int_from_bytes(b[44:][:8])
        
    def __assign_control_name__(i:int) -> str:
        found = []

        if i & ACTControl.CTRL_NONE != 0:
            found.append("CTRL_SCALE")
        if i & ACTControl.CTRL_ROT_EULER != 0:
            found.append("CTRL_ROT_EULER")
        if i & ACTControl.CTRL_ROT_QUAT != 0:
            found.append("CTRL_ROT_QUAT")
        if i & ACTControl.CTRL_TRANS != 0:
            found.append("CTRL_TRANS")
        if i & ACTControl.CTRL_MTX != 0:
            found.append("CTRL_MTX")
        
        if len(found) == 0:
            return "CTRL_NONE"
        return " | ".join(found)


    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"{self.ControlType=}\n"
        t += f"{self.ControlType_Name=}\n"
        t += f"{self.pad1=}\n"

        t += f"{self.scaleX=}\n"
        t += f"{self.scaleY=}\n"
        t += f"{self.scaleZ=}\n"

        t += f"{self.rotateX=}\n"
        t += f"{self.rotateY=}\n"
        t += f"{self.rotateZ=}\n"
        t += f"{self.rotateW=}\n"
        t += f"{self.rotateDistance=}\n"

        t += f"{self.transformX=}\n"
        t += f"{self.transformY=}\n"
        t += f"{self.transformZ=}\n"
        t += f"{self.pad2=}"
        return t

class CTRLControl:
    SIZE_OF_STRUCT = 0x34
    