from PIL import Image
from tools.texture import TPLTextureHeader
from .conversions import *

class TPLColor:
    @classmethod
    def from_bytes(cls, b:bytes):
        cls.from_int(int_from_bytes(b))
        return cls

    @classmethod
    def to_bytes(cls) -> bytes:
        return bytes_from_int(cls.to_int(), size=cls.SIZE)
    
    @classmethod
    def has_alpha(cls) -> bool:
        return len(cls.data) == 4

class TPLColorIA8(TPLColor):
    SIZE = 1

    @classmethod
    def from_int(cls, i: int):
        first_part = (i >> 8) & 0xff
        second_part = (i) & 0xff
        
        cls.data = (second_part, second_part, second_part, first_part)
        
        return cls
    
    @classmethod
    def to_int(cls) -> int:
        return (cls.data[3] << 8) | (cls.data[0])

class TPLColorR5G6B5(TPLColor):
    SIZE = 2

    @classmethod
    def from_int(cls, i:int):
        cls.data = ((i >> 11) << 3, ((i >> 5) & 0b111111) << 2, (i & 0b11111) << 3)
        return cls
    
    @classmethod
    def to_int(cls) -> int:
        return ((cls.data[0] >> 3) << 11) | ((cls.data[1] >> 2) << 5) | (cls.data[2] >> 3)

class TPLColorRGB5A3(TPLColor):
    SIZE = 2
    
    @classmethod
    def from_int(cls, a:int):
        if a & 0x8000 != 0: # default 255 alpha
            cls.data = (((a >> 10) & 0b11111) << 3, ((a >> 5) & 0b11111) << 3, (a & 0b11111) << 3, 0xff)
        else: # has alpha bits
            cls.data = ((a >> 8) & 0b1111) << 4, ((a >> 4) & 0b1111) << 4, (a & 0b1111) << 4, (((a >> 12) & 0b1111) << 5)
        return cls

    @classmethod
    def to_int(cls) -> int:
        if cls.data[3] == 255:
            return 0x8000 | cls.data[0] << 7 | cls.data[1] << 2 | cls.data[2] >> 3
        else:
            return cls.data[0] << 4 | cls.data[1] | cls.data[2] >> 4 | cls.data[3] << 7


class TPLFileC4:
    @staticmethod
    def get_pixel(src:bytes, s:int, t:int, width:int, palette):
        sBlk = s >> 3
        tBlk = t >> 3
        widthBlks = (width >> 3)
        base = (tBlk * widthBlks + sBlk) << 5
        blkS = s & 7
        blkT = t & 7
        blkOff = (blkT << 3) + blkS

        rs = 0 if (blkOff & 1) else 4
        offset = base + (blkOff >> 1)

        val = ((src[offset]) >> rs) & 0xF
        # print(val)
        # val = (val << 4) & val
        return palette[val]
    
    @staticmethod
    def parse_source(source:bytes, header: TPLTextureHeader) -> Image.Image:
        width, height = (header.width, header.height)
        blocks_to_read = (width//4) * (height//4) * 8
        image_data = source[header.address:][:blocks_to_read]

        byt = source[header.palette:][:0x20]
        palette = [int_from_bytes(byt[i*2:i*2+2]) for i in range(0x10)]

        if header.palette_format == 0: # IA8
            func = TPLColorIA8
            pixel_format = "RGBA"
        elif header.palette_format == 1: # RGB565
            func = TPLColorR5G6B5
            pixel_format = "RGB"
        elif header.palette_format == 2: # RGB5A3
            func = TPLColorRGB5A3
            pixel_format = "RGBA"
        else:
            assert(False)

        palette = [func.from_int(x).data for x in palette]

        image = Image.new(pixel_format, (width, height))

        for t in range(height):
            for s in range(width):
                p = TPLFileC4.get_pixel(image_data, s, t, width, palette)
                image.putpixel((s,t), p)
        
        return image


class TPLFileCMPR:
    @staticmethod
    def dxt_blend(v1, v2):
        return ((v1 * 3 + v2 * 5) >> 3)

    @staticmethod
    def parse_source(source:bytes, header: TPLTextureHeader) -> Image.Image:
        width, height = (header.width, header.height)
        blocks_to_read = (width//4) * (height//4) * 8

        image_data = source[header.address:][:blocks_to_read]
        image = Image.new("RGBA", (width, height))

        for t in range(height):
            for s in range(width):
                p = TPLFileCMPR.get_pixel(image_data, s, t, width)
                image.putpixel((s,t), p)
        return image


    @staticmethod
    def get_pixel(src:bytes, s:int, t:int, width:int):
        sDxt = s >> 2
        tDxt = t >> 2
        
        sBlock = sDxt >> 1
        tBlock = tDxt >> 1
        width_blocks = (width >> 3)
        base = (tBlock * width_blocks + sBlock) << 2
        blockS = sDxt & 1
        blockT = tDxt & 1
        block_offset = (blockT << 1) + blockS
        
        offset = (base + block_offset) << 3

        dxt_block = src[offset:offset+8]

        c1 = TPLColorR5G6B5().from_bytes(dxt_block[0:2]).data
        c2 = TPLColorR5G6B5().from_bytes(dxt_block[2:4]).data

        ss = s & 3
        tt = t & 3

        color_select = dxt_block[4:][tt]
        rs = 6 - (ss << 1)

        color_select = (color_select >> rs) & 3

        color_select |= 0 if c1 > c2 else 4

        if color_select in [0,4]:
            return (c1[0], c1[1], c1[2], 255)
        elif color_select in [1,5]:
            return (c2[0], c2[1], c2[2], 255)
        elif color_select in [2]:
            return (TPLFileCMPR.dxt_blend(c2[0], c1[0]), TPLFileCMPR.dxt_blend(c2[1], c1[1]), TPLFileCMPR.dxt_blend(c2[2], c1[2]), 255)
        elif color_select in [3]:
            return (TPLFileCMPR.dxt_blend(c1[0], c2[0]), TPLFileCMPR.dxt_blend(c1[1], c2[1]), TPLFileCMPR.dxt_blend(c1[2], c2[2]), 255)
        elif color_select in [6]:
            return ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2, 255)
        elif color_select in [7]:
            return ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2, 0)
        else:
            return (0,0,0,0)