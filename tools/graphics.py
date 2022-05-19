from dataclasses import dataclass
import typing

from .conversions import *

class GeoPaletteHeader:
    SIZE_OF_STRUCT = 20

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        ints = ints_from_bytes(b[0:4], b[4:8], b[8:12], b[12:16], b[16:20])
        self.versionNumber = ints[0]
        self.userDefinedDataSize = ints[1]
        self.offsetToUserDefinedData = ints[2]
        self.numberOfGeometryDescriptors = ints[3]
        self.offsetToGeometryDescriptorArray = ints[4]

    def add_offset(self, offset:int):
        if self.offsetToGeometryDescriptorArray != 0 :
            self.offsetToGeometryDescriptorArray += offset

        if self.offsetToUserDefinedData != 0:
            self.offsetToUserDefinedData += offset

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"Version Number: {self.versionNumber}\n"
        t += f"User Defined Data Size: {self.userDefinedDataSize}\n"
        t += f"pDefined Data: {hex(self.offsetToUserDefinedData)}\n"
        t += f"Number Of Geometry Descriptors: {self.numberOfGeometryDescriptors}\n"
        t += f"pGeometry Descriptor Array: {hex(self.offsetToGeometryDescriptorArray)}"

        return t

class GeoDescriptor:
    SIZE_OF_STRUCT = 8

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:8])
        self.offsetToDisplayObject = i[0]
        self.offsetToName = i[1]
        self.name = None

    def add_offset(self, offset:int):
        if self.offsetToDisplayObject != 0:
            self.offsetToDisplayObject += offset
    
        if self.offsetToName != 0:
            self.offsetToName += offset
    
    def set_name(self, name:str):
        self.name = name
    
    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"Name: {self.name}\n"
        t += f"pDisplay Object: {hex(self.offsetToDisplayObject)}\n"
        t += f"pName: {hex(self.offsetToName)}"
        
        return t

class DisplayObjectLayout:
    SIZE_OF_STRUCT = 0x18

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:8], b[8:12], b[12:16], b[16:20], b[20])
        self.OffsetToPositionData = i[0]
        self.OffsetToColorData = i[1]
        self.OffsetToTextureData = i[2]
        self.OffsetToLightingData = i[3]
        self.OffsetToDisplayData = i[4]
        self.numberOfTextures = i[5]
        
    def add_offset(self, offset:int) -> None:
        if self.OffsetToPositionData != 0:
            self.OffsetToPositionData += offset

        if self.OffsetToColorData != 0:
            self.OffsetToColorData += offset
        
        if self.OffsetToTextureData != 0:
            self.OffsetToTextureData += offset

        if self.OffsetToLightingData != 0:
            self.OffsetToLightingData += offset

        if self.OffsetToDisplayData != 0:
            self.OffsetToDisplayData += offset
    
    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"pPosition Data: {hex(self.OffsetToPositionData)}\n"
        t += f"pColor Data: {hex(self.OffsetToColorData)}\n"
        t += f"pTexture Data: {hex(self.OffsetToTextureData)}\n"
        t += f"pLighting Data: {hex(self.OffsetToLightingData)}\n"
        t += f"pDisplay Data: {hex(self.OffsetToDisplayData)}"
        return t

class DisplayObjectPositionHeader:
    SIZE_OF_STRUCT = 0x8
    QUANTIZE_INFO={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:6], b[6], b[7])
        self.offsetToPositionArray = i[0]
        self.numberOfPositions = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]

        self.numberOfComponents = i[3]

    def add_offset(self, offset:int)->None:
        if self.offsetToPositionArray != 0:
            self.offsetToPositionArray += offset
    
    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"pPositions: {hex(self.offsetToPositionArray)}\n"
        t += f"Position Count: {hex(self.numberOfPositions)}\n"
        t += f"Quantize Info: {hex(self.quantizeInfo)}\n"
        t += f"Component Count: {self.numberOfComponents}"

        return t


class DisplayObjectColorHeader:
    SIZE_OF_STRUCT = 0x8

    QUANTIZE_INFO = {
        0x0:2,
        0x1:3,
        0x2:4,
        0x3:2,
        0x4:3,
        0x5:4,
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:6], b[6], b[7])
        self.offsetToColorArray = i[0]
        self.numberOfColors = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.alpha = self.format > 2
        self.componentSize = self.QUANTIZE_INFO[self.format]
        self.numberOfComponents = i[3]

    def add_offset(self, offset:int)->None:
        if self.offsetToColorArray != 0:
            self.offsetToColorArray += offset

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"pColors: {hex(self.offsetToColorArray)}\n"
        t += f"Color Count: {self.numberOfColors}\n"
        t += f"Format Info: {hex(self.quantizeInfo)}\n"
        t += f"Component Count: {self.numberOfComponents}"

        return t

class DisplayObjectTextureHeader:
    SIZE_OF_STRUCT = 0x10

    QUANTIZE_INFO={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:6], b[6:7], b[7:8], b[8:12])
        self.offsetToTextureCoordinateArray = i[0]
        self.numberOfCoordinates = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]

        self.numberOfComponents = i[3]
        self.offsetToTexturePaletteFileName = i[4]

        self.name = None

    def add_offset(self, offset:int)->None:
        if self.offsetToTextureCoordinateArray != 0:
            self.offsetToTextureCoordinateArray += offset
        
        if self.offsetToTexturePaletteFileName != 0:
            self.offsetToTexturePaletteFileName += offset

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"Name: {self.name}\n"
        t += f"pName: {hex(self.offsetToTexturePaletteFileName)}\n"
        t += f"pTexture Coords: {hex(self.offsetToTextureCoordinateArray)}\n"
        t += f"Coord Count: {self.numberOfCoordinates}\n"
        t += f"Format Info: {hex(self.quantizeInfo)}\n"
        t += f"Component Count: {self.numberOfComponents}"

        return t


class DisplayObjectLightingHeader:
    SIZE_OF_STRUCT = 0xc

    QUANTIZE_INFO={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:6], b[6:7], b[7:8])
        self.offsetToNormalArray = i[0]
        self.numberOfNormals = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]

        self.numberOfComponents = i[3]
        ba = bytearray(b[8:12])
        ba.reverse()
        self.ambientBrightness = float_from_bytes(ba)

    def add_offset(self, offset:int)->None:
        if self.offsetToNormalArray != 0:
            self.offsetToNormalArray += offset

    def __str__(self) -> str: 
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"pNormals: {hex(self.offsetToNormalArray)}\n"
        t += f"Normal Count: {self.numberOfNormals}\n"
        t += f"Format Info: {hex(self.quantizeInfo)}\n"
        t += f"Component Count: {self.numberOfComponents}\n"
        t += f"Ambient Brightness: {self.ambientBrightness}"
        return t


class DisplayObjectDisplayHeader:
    SIZE_OF_STRUCT = 0xc

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0:4], b[4:8], b[8:10])
        self.offsetToPrimitiveBank = i[0]
        self.offsetToDisplayStateList = i[1]
        self.numberOfDisplayStateEntries = i[2]
    
    def add_offset(self, offset:int)->None:
        if self.offsetToPrimitiveBank != 0:
            self.offsetToPrimitiveBank += offset
        
        if self.offsetToDisplayStateList != 0:
            self.offsetToDisplayStateList += offset
    
    def __str__(self) -> str: 
        t= ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"pPrimitive Bank: {hex(self.offsetToPrimitiveBank)}\n"
        t += f"pDisplay States: {hex(self.offsetToDisplayStateList)}\n"
        t += f"Display State Count: {self.numberOfDisplayStateEntries}"
        return t

        
class DisplayObjectDisplayState:
    SIZE_OF_STRUCT = 0x10
    
    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        i = ints_from_bytes(b[0], b[4:8], b[8:12], b[12:16])
        self.stateID = i[0]
        self.setting = i[1]
        self.offsetToPrimitiveList = i[2]
        self.byteLengthPrimitiveList = i[3]
    
    def add_offset(self, offset:int)->None:
        if self.offsetToPrimitiveList != 0:
            self.offsetToPrimitiveList += offset
    
    def __str__(self) -> str: 
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"State ID: {self.stateID}\n"
        t += f"Setting: {hex(self.setting)}\n"
        t += f"pPrimitive List: {hex(self.offsetToPrimitiveList)}\n"
        t += f"Primitive Byte Count: {self.byteLengthPrimitiveList}"
        
        return t

@dataclass
class Vector3:
    X:float
    Y:float
    Z:float
    
    def __str__(self) -> str:
        return f"{self.X} {self.Y} {self.Z}"

    def __getitem__(self, key):
        return [self.X, self.Y, self.Z][key]

@dataclass
class Vector2:
    U:float
    V:float

    def __str__(self) -> str:
        return f"{self.U} {self.V}"
    
    def __getitem__(self, key):
        return [self.U, self.V][key]

class PositionVector(Vector3):
    def __str__(self) -> str:
        return f"v {self.X} {-self.Y} {-self.Z}" 

class TextureVector(Vector2):
    def __str__(self) -> str:
        return f"vt {self.U} {-self.V}" 

class NormalVector(Vector3):
    def __str__(self) -> str:
        return f"vn {self.X} {-self.Y} {-self.Z}" 

@dataclass
class OBJIndex:
    ind: 'typing.Any'=None

    def __str__(self) -> str:
        return f"{self.ind+1}" if self.ind != None else ""

@dataclass
class OBJIndices:
    position_coordinate:OBJIndex=OBJIndex(None)
    texture_coordinate:OBJIndex=OBJIndex(None)
    normal_coordinate:OBJIndex=OBJIndex(None)

    def __str__(self) -> str:
        return "/".join(str(x) for x in [self.position_coordinate, self.texture_coordinate, self.normal_coordinate] if x != None)

        
@dataclass
class OBJFace:
    obj_indices:list[OBJIndices]

    def __str__(self) -> str:
        return "f " + " ".join(str(x) for x in self.obj_indices)

@dataclass
class OBJGroup:
    positions: list[PositionVector]
    textures: list[TextureVector]
    normals: list[NormalVector]

    faces: list[OBJFace]

    mtl:"typing.any" = None
    name:"typing.any" = None

    def __str__(self) -> str:
        t = ""

        if self.name != None:
            t += f"g {self.name}\n"
    
        if self.mtl != None:
            t += f"usemtl {self.mtl}\n"

        for p in self.positions:
            t += f"{p}\n"
        for p in self.normals:
            t += f"{p}\n"
        for p in self.textures:
            t += f"{p}\n"
        for p in self.faces:
            t += f"{p}\n"

        return t

@dataclass        
class OBJFile:
    groups:list[OBJGroup]
    mtl_file:"typing.any" = None

    def __str__(self) -> str:
        t = ""

        if self.mtl_file != None:
            mtl = self.mtl_file.replace("\\", "\\\\")
            t+= f"mtllib {self.mtl_file}\n"
        
        for mtl in self.groups:
            t += f"{mtl}\n"
        
        return t
    
    def assert_valid(self):
        poss = []
        uvs = []
        norms = []
        try:
            for g in self.groups:
                if g.positions != None:
                    poss.extend(g.positions)
                if g.normals != None:
                    norms.extend(g.positions)
                if g.textures != None:
                    uvs.extend(g.positions)
            
                for f in g.faces:
                    for o in f.obj_indices:

                        if o.position_coordinate.ind != None:
                            assert(o.position_coordinate.ind < len(poss))
                        
                        if o.normal_coordinate.ind != None:
                            assert(o.normal_coordinate.ind < len(norms))

                        if o.texture_coordinate.ind != None:
                            assert(o.texture_coordinate.ind < len(uvs))
            return True
        except AssertionError:
            return False
