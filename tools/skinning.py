from .conversions import *

class SKNHeader:
    SIZE_OF_STRUCT = 0x24

    def __init__(self, b: bytes) -> None:
        assert(len(b) == self.SIZE_OF_STRUCT)
        self.numberOf1MTXLists = int_from_bytes(b[0:][:2])
        self.numberOf2MTXLists = int_from_bytes(b[2:][:2])
        self.numberOfAccumulationLists = int_from_bytes(b[4:][:2])
        self.positionNormalQuantization = int_from_bytes(b[6:][:1])
        self.pad = int_from_bytes(b[7:][:1])
        
        self.offsetMTX1HeaderArray = int_from_bytes(b[8:][:4])
        self.offsetMTX2HeaderArray = int_from_bytes(b[12:][:4])

        self.offsetAccumulationHeaderArray = int_from_bytes(b[16:][:4])
        self.topOfMemoryToClear = int_from_bytes(b[20:][:4])
        self.memoryToClearInBytes = int_from_bytes(b[24:][:4])
        self.offsetFlushIndexArray = int_from_bytes(b[28:][:4])
        self.numberOfFlushIndices = int_from_bytes(b[32:][:4])

    def __str__(self) -> str:
        t = ""
        t += f"=={self.__class__.__name__}==\n"
        t += f"{self.numberOf1MTXLists=}\n"
        t += f"{self.numberOf2MTXLists=}\n"
        t += f"{self.numberOfAccumulationLists=}\n"
        t += f"{self.positionNormalQuantization=}\n"
        t += f"{self.pad=}\n"
        t += f"{self.offsetMTX1HeaderArray=}\n"
        t += f"{self.offsetMTX2HeaderArray=}\n"
        t += f"{self.offsetAccumulationHeaderArray=}\n"
        t += f"{self.topOfMemoryToClear=}\n"
        t += f"{self.memoryToClearInBytes=}\n"
        t += f"{self.offsetFlushIndexArray=}\n"
        t += f"{self.numberOfFlushIndices=}"
        return t
