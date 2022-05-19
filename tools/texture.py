from dataclasses import dataclass

CMPR_BLOCK_SIZE = 8

VALID_IMAGE_FORMATS = {
    0: "I4",
    1: "I8",
    2: "IA4",
    3: "IA8",
    4: "RGB565",
    5: "RGB5A3",
    6: "RGBA32",
    8: "C4",
    9: "C8",
    0xa: "C14X2",
    0xe: "CMPR"
}

@dataclass
class TPLTextureHeader:
    address:int
    height:int
    width:int
    format:int
    palette:int
    palette_format:int

    def __str__(self) -> str:
        t = ""
        format = VALID_IMAGE_FORMATS.get(self.format, hex(self.format))
        t += f"format: {format}\n"
        t += f"width: {self.width}\n"  
        t += f"height: {self.height}"
        return t

