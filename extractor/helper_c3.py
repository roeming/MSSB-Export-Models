from __future__ import annotations

from helper_mssb_data import DataBytesInterpreter

class GeoPaletteHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IIIII'

    def __init__(self, b:bytes, offset:int) -> None:
        
        self.versionNumber, \
        self.userDefinedDataSize, \
        self.offsetToUserDefinedData, \
        self.numberOfGeometryDescriptors, \
        self.offsetToGeometryDescriptorArray, \
        = self.parse_bytes(b, offset)

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

class GeoDescriptor(DataBytesInterpreter):
    DATA_FORMAT = '>II'

    def __init__(self, b:bytes, offset:int) -> None:

        self.offsetToDisplayObject, \
        self.offsetToName, \
        = self.parse_bytes(b, offset)

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

class DisplayObjectLayout(DataBytesInterpreter):
    DATA_FORMAT = '>IIIIIBxxx'

    def __init__(self, b:bytes, offset:int) -> None:

        self.OffsetToPositionData, \
        self.OffsetToColorData, \
        self.OffsetToTextureData, \
        self.OffsetToLightingData, \
        self.OffsetToDisplayData, \
        self.numberOfTextures, \
        = self.parse_bytes(b, offset)
        
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

class DisplayObjectPositionHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IHBB'

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

    def __init__(self, b:bytes, offset) -> None:

        self.offsetToPositionArray, \
        self.numberOfPositions, \
        self.quantizeInfo, \
        self.numberOfComponents, \
        = self.parse_bytes(b, offset)
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]


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


class DisplayObjectColorHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IHBB'

    QUANTIZE_INFO = {
        0x0:2,
        0x1:3,
        0x2:4,
        0x3:2,
        0x4:3,
        0x5:4,
    }

    def __init__(self, b:bytes, offset:int) -> None:

        self.offsetToColorArray, \
        self.numberOfColors, \
        self.quantizeInfo, \
        self.numberOfComponents, \
        = self.parse_bytes(b, offset)
        
        self.format = self.quantizeInfo >> 4
        self.alpha = self.format > 2
        self.componentSize = self.QUANTIZE_INFO[self.format]

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

class DisplayObjectTextureHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IHBBII'

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

    def __init__(self, b:bytes, offset:int) -> None:

        self.offsetToTextureCoordinateArray, \
        self.numberOfCoordinates, \
        self.quantizeInfo, \
        self.numberOfComponents, \
        self.offsetToTexturePaletteFileName, \
        self.offsetToPalettePointer, \
        = self.parse_bytes(b, offset)
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]

        self.name = None

    def add_offset(self, offset:int)->None:
        if self.offsetToTextureCoordinateArray != 0:
            self.offsetToTextureCoordinateArray += offset
        
        if self.offsetToTexturePaletteFileName != 0:
            self.offsetToTexturePaletteFileName += offset
        
        if self.offsetToPalettePointer != 0:
            self.offsetToPalettePointer += offset

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

class DisplayObjectDisplayHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IIHxx'

    def __init__(self, b:bytes, offset:int) -> None:

        self.offsetToPrimitiveBank, \
        self.offsetToDisplayStateList, \
        self.numberOfDisplayStateEntries, \
        = self.parse_bytes(b, offset)
    
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


class DisplayObjectLightingHeader(DataBytesInterpreter):
    DATA_FORMAT = '>IHBBf'

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

    def __init__(self, b:bytes, offset:int) -> None:

        self.offsetToNormalArray, \
        self.numberOfNormals, \
        self.quantizeInfo, \
        self.numberOfComponents, \
        self.ambientBrightness, \
        = self.parse_bytes(b, offset)
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.QUANTIZE_INFO["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.QUANTIZE_INFO["signed info"][self.format]


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


class DisplayObjectDisplayState(DataBytesInterpreter):
    DATA_FORMAT = '>BxxxIII'
    
    def __init__(self, b:bytes, offset:int) -> None:

        self.stateID, \
        self.setting, \
        self.offsetToPrimitiveList, \
        self.byteLengthPrimitiveList, \
        = self.parse_bytes(b, offset)
    
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

