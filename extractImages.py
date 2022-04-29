from genericpath import exists
import os
from os.path import dirname, join
from PIL import Image

def main():
    input_file = input("Input file name: ")
    output_folder = dirname(input_file)

    export_images(input_file, output_folder)

def export_images(input_file:str, output_dir:str):

    if not exists(input_file):
        print("File doesn't exist")
        exit()
    if not exists(output_dir):
        os.mkdir(output_dir)

    with open(input_file, "rb") as f:
        file_offset = int_from_bytes(f.read(4))
        f.seek(file_offset)
        image_count = int_from_bytes(f.read(2))
        
        # extra bytes
        f.read(2)

        for i in range(image_count):
            f.seek(file_offset + 4 + 0x20*i)
            header = texture_header_from_bytes(f.read(0x20))
            try:
                assert(header["format"] in [0xe, 0x8])
                assert(header["width"] % 4 == 0)
                assert(header["height"] % 4 == 0)
            except:
                print("File header failed check")
                format = hex(header["format"])
                width = header["width"]
                height = header["height"]
                print(f"format: {format}")
                print(f"width: {width}")
                print(f"height: {height}")
                assert(False)

            f.seek(header["address"] + file_offset)

            width, height = (header["width"], header["height"])

            image = Image.new("RGBA", (width, height))

            if header["format"] == 0xe:
                blocks_to_read = (width//4) * (height//4) * 8
                image_data = f.read(blocks_to_read)
                for t in range(height):
                    for s in range(width):
                        p = get_pixel_cmpr(image_data, s, t, width)
                        image.putpixel((s,t), p)
            elif header["format"] == 0x8:
                header["palette"] = header["palette"] + file_offset 

                blocks_to_read = (width//4) * (height//4) * 8
                image_data = f.read(blocks_to_read)

                f.seek(header["palette"])
                byt = f.read(0x20)
                palette = [int_from_bytes(byt[i*2:i*2+2]) for i in range(0x10)]

                for t in range(height):
                    for s in range(width):
                        p = get_pixel_c4(image_data, s, t, width, palette)
                        image.putpixel((s,t), p)
            else:
                assert("Unhandled file extension")
                
            image.save(join(output_dir, f"{i}.png"))

    with open(join(output_dir, "mtl.mtl"), "w") as mtl:
        for i in range(image_count):
            new_image = join(output_dir, f"{i}.png")
            new_image = new_image.replace("\\", "\\\\")
            mtl.write(f"newmtl mssbMtl.{i}\n")
            mtl.write(f"map_Kd {new_image}\n")
            mtl.write("\n")


def int_from_bytes(a:bytes, signed = False)->int:
    return int.from_bytes(a, "big", signed = signed)

def tuple_from_R5G6B5(a:bytes) -> str:
    i = int_from_bytes(a)
    return ((i >> 11) << 3, ((i >> 5) & 0b111111) << 2, (i & 0b11111) << 3)


def RGB5A3_to_tuple(a:int):
    return (((a >> 10) & 0x1f) << 3, ((a >> 5) & 0x1f) << 3, (a & 0x1f) << 3, 255)
    if a & 0x80:
        return ((a >> 8) & 0xf, (a >> 4) & 0xf, a & 0xf, (a >> 12) & 0x7)
    else:
        return ((a >> 10) & 0x1f, (a >> 5) & 0x1f, a & 0x1f, 255)

def texture_header_from_bytes(a:bytes) -> dict[str: str]:
    ret = {}
    ret["address"] = int_from_bytes(a[:4])
    ret["height"] = int_from_bytes(a[8:10])
    ret["width"] = int_from_bytes(a[10:12])
    ret["format"] = int_from_bytes(a[20:24])
    ret["palette"] = int_from_bytes(a[4:8])
    return ret
    
def dxt_blend(v1, v2):
    return ((v1 * 3 + v2 * 5) >> 3)

# function taken from dolphin source code
def get_pixel_cmpr(src:bytes, s:int, t:int, width:int):
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

    c1 = tuple_from_R5G6B5(dxt_block[0:2])
    c2 = tuple_from_R5G6B5(dxt_block[2:4])

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
        return (dxt_blend(c2[0], c1[0]), dxt_blend(c2[1], c1[1]), dxt_blend(c2[2], c1[2]), 255)
    elif color_select in [3]:
        return (dxt_blend(c1[0], c2[0]), dxt_blend(c1[1], c2[1]), dxt_blend(c1[2], c2[2]), 255)
    elif color_select in [6]:
        return ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2, 255)
    elif color_select in [7]:
        return ((c1[0] + c2[0]) // 2, (c1[1] + c2[1]) // 2, (c1[2] + c2[2]) // 2, 0)
    else:
        return (0,0,0,0)

def get_pixel_c4(src:bytes, s:int, t:int, width:int, palette):
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
    return RGB5A3_to_tuple(palette[val])

if __name__ == "__main__":
    main()
