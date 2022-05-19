from genericpath import exists
import os
from os.path import dirname, join

from cv2 import FastFeatureDetector

from tools.texture import *
from tools.conversions import *
from tools.file_helper import *
from tools.colors import *

try:
    from PIL import Image
except:
    print("Make sure you have pillow installed. If you don't please run")
    print("'python -m pip install-r requirements.txt'")
    input("Press Enter To continue...")
    exit()

def main():
    input_file = input("Input file name: ")
    file_part = int(input("Input file part: "))
    output_folder = dirname(input_file)

    export_images(input_file, output_folder, file_part)

def get_all_tpl_headers(b:bytes) -> list[TPLTextureHeader]:
    image_count = int_from_bytes(b[:2], signed=False)

    image_headers = []

    for i in range(image_count):
        image_headers.append(get_tpl_header_from_bytes(b[4 + 0x20 * i:][:0x20]))
    return image_headers

def validate_tpl_header(header: TPLTextureHeader) -> bool:
    return header.format in VALID_IMAGE_FORMATS and header.width % 4 == 0 and header.height % 4 == 0


TEXTURE_PARSE_FUNCTIONS = {
    0x1: (lambda a, b: None),  # I4
    0x2: (lambda a, b: None),  # I8
    0x3: (lambda a, b: None),  # IA4
    0x4: (lambda a, b: None),  # RGB565
    0x5: (lambda a, b: None),  # RGB5A3
    0x6: (lambda a, b: None),  # RGBA32
    0x8: (lambda a, b: TPLFileC4.parse_source(a, b)),  # C4
    0x9: (lambda a, b: None),  # C8
    0xa: (lambda a, b: None),  # C14X2
    0xe: (lambda a, b: TPLFileCMPR.parse_source(a, b)),  # CMPRs
}

def write_images(filename:str, output_dir:str, part_of_file:int, write_mtl:bool = False) -> bool:
    try:
        images = export_images(filename, part_of_file)

        image_files = []
        for i, (img, img_format) in enumerate(images):
            if img is None:
                continue

            img_file = os.path.join(output_dir, f"{i}.png")
            image_files.append(img_file)
            img.save(img_file)

        mtl_file = [(f"mssbMtl.{ii}", i_name) for ii, i_name in enumerate(image_files)]
        if write_mtl:
            return write_mtl_file(os.path.join(output_dir, "mtl.mtl"), mtl_file)
        return True
    except:
        return False

def export_images(filename:str, part_of_file:int) -> list[tuple[Image.Image, str]]:
    parts = get_parts_of_file(filename)
    if part_of_file >= len(parts):
        return None

    with open(filename, "rb") as f:
        if part_of_file < 0:
            lines = f.read()
        else:
            f.seek(parts[part_of_file])
            lines = f.read()
    
    headers = get_all_tpl_headers(lines)
    images = []
    for header in headers:
        if not validate_tpl_header(header):
            continue
        
        image = TEXTURE_PARSE_FUNCTIONS[header.format](lines, header)
        
        images.append((image, VALID_IMAGE_FORMATS[header.format]))
    return images

def write_mtl_file(file_name:str, mtls:list[tuple[str, str]], cut_at_base_folder:bool=True) -> bool:
    try:
        with open(file_name, "w") as f:
            for name, path in mtls:
                if cut_at_base_folder:
                    path = os.path.basename(path)
                else:
                    path = path.replace("\\", "\\\\")
    
                f.write(f"newmtl {name}\n")
                f.write(f"map_kd {path}\n")
                f.write("\n")
        return True
    except:
        return False

def get_tpl_header_from_bytes(a:bytes) -> TPLTextureHeader:
    ret = TPLTextureHeader(
        address=int_from_bytes(a[:4]),
        height=int_from_bytes(a[8:10]),
        width=int_from_bytes(a[10:12]),
        format=int_from_bytes(a[20:24]),
        palette=int_from_bytes(a[4:8]),
        palette_format=a[0x1a]
    )
    return ret

if __name__ == "__main__":
    main()
