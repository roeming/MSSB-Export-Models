from PIL import Image
import json, math
from helper_mssb_data import DataEntry, MultipleRanges, dirname, ensure_dir
import progressbar

def draw_pic(zzzz_path:str, results_path:str, output_path="found.png"):
    with open(results_path, 'r') as f:
        results = json.load(f)

    with open(zzzz_path, 'rb') as f:
        data_length = len(f.read())

    square_size = math.sqrt(data_length//0x800)

    if int(square_size) != square_size:
        square_size = int(square_size) + 1
    else:
        square_size = int(square_size)

    referencedCompressedRanges = MultipleRanges()
    for entry_json in results['GameReferencedCompressedFiles']:
        referencedCompressedRanges.add_range(DataEntry.from_dict(entry_json).to_range())

    referencedUncompressedRanges = MultipleRanges()
    for entry_json in results['GameReferencedRawFiles']:
        referencedUncompressedRanges.add_range(DataEntry.from_dict(entry_json).to_range())

    unreferencedCompressedRanges= MultipleRanges()
    for entry_json in results['UnreferencedCompressedFiles']:
        entry = DataEntry.from_dict(entry_json)
        unreferencedCompressedRanges.add_range(range(entry.disk_location, entry.disk_location+100))

    img = Image.new('RGB', (square_size, square_size), (0,0,0))

    WHITE_PIXEL  = (255, 255, 255)
    CYAN_PIXEL   = (0,255,255)
    ORANGE_PIXEL = (255, 191, 0)
    RED_PIXEL    = (255, 0, 0)
    print('Drawing ZZZZ picture...')
    for i, address in progressbar.progressbar([x for x in enumerate(range(0, data_length, 0x800))]):
        
        if   address in referencedCompressedRanges:     pix = CYAN_PIXEL
        elif address in referencedUncompressedRanges:   pix = ORANGE_PIXEL
        elif address in unreferencedCompressedRanges:   pix = RED_PIXEL
        else:                                           pix = WHITE_PIXEL
        
        img.putpixel((i % square_size, i // square_size), pix)
    
    ensure_dir(dirname(output_path))

    img.save(output_path)
