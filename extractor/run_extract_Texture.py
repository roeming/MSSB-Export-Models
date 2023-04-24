from os.path import dirname, join, basename

from helper_texture import *
from helper_mssb_data import get_parts_of_file, ensure_dir, write_text

try:
    from PIL.Image import Image
except:
    print("Make sure you have pillow installed. If you don't please run")
    print("\'python -m pip install -r requirements.txt\'")
    input("Press Enter To continue...")
    exit()


def main():
    input_file = input("Input file name: ")
    file_part = int(input("Input file part: "))
    output_folder = dirname(input_file)

    export_images(input_file, output_folder, file_part)

def get_all_tpl_headers(b:bytes) -> list[TPLTextureHeader]:
    image_count = int.from_bytes(b[:2], 'big', signed=False)

    image_headers = []

    for i in range(image_count):
        image_headers.append(TPLTextureHeader.from_bytes(b, 4 + TPLTextureHeader.SIZE_OF_STRUCT * i))
    return image_headers

def unimplemented_format(err:str):
    raise ValueError(f"Parsing texture format \"{err}\" is not implemented.")

TEXTURE_PARSE_FUNCTIONS = {
    "I4":     (lambda a, b: unimplemented_format("I4")),
    "I8":     (lambda a, b: unimplemented_format("I8")),
    "IA4":    (lambda a, b: unimplemented_format("IA4")),
    "RGB565": (lambda a, b: unimplemented_format("RGB565")),
    "RGB5A3": (lambda a, b: unimplemented_format("RGB5A3")),
    "RGBA32": (lambda a, b: unimplemented_format("RGBA32")),
    "C4":     (lambda a, b: TPLFileC4.parse_source(a, b)),
    "C8":     (lambda a, b: TPLFileC8.parse_source(a, b)),
    "C14X2":  (lambda a, b: unimplemented_format("C14X2")),
    "CMPR":   (lambda a, b: TPLFileCMPR.parse_source(a, b)),
}

def write_images(filename:str, output_dir:str, part_of_file:int, write_mtl:bool = False, image_header:str = "") -> bool:
    images = export_images(filename, part_of_file)
    try:
        image_files = []
        for i, (img, img_format) in enumerate(images):
            if img is None:
                continue
            img:Image

            img_file = join(output_dir, image_header+f"{i}.png")
            ensure_dir(dirname(img_file))

            image_files.append(img_file)
            img.save(img_file)

        mtl_file = [(f"mssbMtl.{ii}", i_name) for ii, i_name in enumerate(image_files)]
        if write_mtl:
            return write_mtl_file(join(output_dir, image_header+"mtl.mtl"), mtl_file)
        return True
    except IndexError:
        return False


def export_images(file_bytes:bytearray, part_of_file:int) -> ExtractedTextureCollection:
    parts = get_parts_of_file(file_bytes)
    if part_of_file >= len(parts):
        return ExtractedTextureCollection([])

    if part_of_file < 0:
        lines = file_bytes[::]
    else:
        lines = file_bytes[parts[part_of_file]:]
    
    headers = get_all_tpl_headers(lines)
    images = []
    for header in headers:
        if not header.is_valid():
            continue
        
        image = TEXTURE_PARSE_FUNCTIONS[VALID_IMAGE_FORMATS[header.format]](lines, header)
        
        images.append(ExtractedTexture(image, VALID_IMAGE_FORMATS[header.format]))
    return ExtractedTextureCollection(images)

def write_mtl_file(file_name:str, mtls:list[tuple[str, str]], cut_at_base_folder:bool=True) -> bool:
    mtl_file = ""
    for name, path in mtls:
        if cut_at_base_folder:
            path = basename(path)
        else:
            path = path.replace("\\", "\\\\")

        mtl_file += f"newmtl {name}\n"
        mtl_file += f"map_kd {path}\n"
        mtl_file += "\n"

    write_text(mtl_file, file_name)

    return True

if __name__ == "__main__":
    main()
