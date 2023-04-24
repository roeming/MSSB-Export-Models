from helper_mssb_data import DataEntry, RollingDecompressor, ensure_dir, write_bytes, ArchiveDecompressor, get_parts_of_file, write_text
from os.path import join, exists
from run_extract_Texture import export_images
from run_extract_Model import export_model
from run_file_discovery import discover_files
import json, progressbar
from run_draw_pic import draw_pic

OUTPUT_FOLDER = 'outputs'
DATA_FOLDER = 'data'
ZZZZ_FILE = join(DATA_FOLDER, 'ZZZZ.dat')

UNREF_COMPR_FOLDER = join(OUTPUT_FOLDER, "Unreferenced files")
REF_COMPR_FOLDER = join(OUTPUT_FOLDER, "Referenced files")
REF_UNCOMPR_FOLDER = join(OUTPUT_FOLDER, "Raw Files")

ALL_FILES_PATH = join(OUTPUT_FOLDER, 'results.json')
FILE_NAMES_PATH = 'FileNames.json'

def interpret_bytes(b:bytearray, output_folder:str):
    parts_of_file = get_parts_of_file(b)
    output_text = f"{len(parts_of_file)} {'part' if len(parts_of_file) == 1 else 'parts'} of file.\n"

    # interpret the files as a file, not parts of a file
    any_outputs = False
    # interpret the parts of the file
    if len(parts_of_file) > 0 and parts_of_file[0] == 80_92_000: # base address is a c3 file
        parts_of_file = []
    for part in [-1] + [x for x in range(len(parts_of_file))]:
        new_out_folder = join(output_folder, f"part {part}")
        try:
            base_images = export_images(b, part)
            if len(base_images.images) > 0:
                output_text += f"Part {part} interpreted as textures.\n"
                any_outputs = True

                base_images.write_images_to_folder(new_out_folder)
                base_images.write_mtl_file(join(new_out_folder, 'mtl.mtl'), "")
        except:
            pass

        try:
            export_model(b, new_out_folder, part)
            output_text += f"Part {part} interpreted as model.\n"
            any_outputs = True
        except Exception as e:
            pass

    if any_outputs:
        write_text(output_text, join(output_folder, "notes.txt"))
    else:
        write_text(output_text + "No output types found.\n", join(output_folder, "notes.txt"))


def main():
    ensure_dir(OUTPUT_FOLDER)

    with open(ZZZZ_FILE, 'rb') as f:
        ZZZZ_DAT = f.read()
 
    if exists(ALL_FILES_PATH): 
        with open(ALL_FILES_PATH, 'r') as f:
            found_files = json.load(f)
    else:
        found_files = discover_files(ALL_FILES_PATH)
        # draw_pic(ZZZZ_FILE, ALL_FILES_PATH)

    with open(FILE_NAMES_PATH, 'r') as f:
        file_names = json.load(f)
    offset_to_name = {int(x['Location'], 16): x['Name'] for x in file_names}

    print("Interpreting referenced compressed files... (should take about 10 minutes)")
    for json_entry in progressbar.progressbar(found_files['GameReferencedCompressedFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != ZZZZ_FILE:
            continue
        
        this_file = offset_to_name.get(entry.disk_location, f'{entry.disk_location:08X}')

        this_folder = join(REF_COMPR_FOLDER, this_file)

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):
            decompressed_bytes = ArchiveDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size, entry.original_size).decompress()
            
            interpret_bytes(decompressed_bytes, this_folder)

            write_bytes(decompressed_bytes, output_file_name)
    
    mean = lambda x : sum(x) // len(x) 

    print("Interpreting unreferenced compressed files... (this will take 30-45 minutes)")
    for json_entry in progressbar.progressbar(found_files['UnreferencedCompressedFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != ZZZZ_FILE:
            continue
        
        this_file = offset_to_name.get(entry.disk_location, f'{entry.disk_location:08X}')

        this_folder = join(UNREF_COMPR_FOLDER, this_file)

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):
            decompressor = RollingDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size)
            parts_of_file = get_parts_of_file(decompressor)
            
            if len(parts_of_file) > 1:
                if len(parts_of_file) > 0 and parts_of_file[0] == 80_92_000: # base address is a c3 file
                    parts_of_file = []
                else:
                    # calculate the average size of a section, and decompress that much past the last part start
                    # hopefully should allow for faster decompressing
                    average_size = mean([parts_of_file[x+1] - parts_of_file[x] for x in range(len(parts_of_file) - 1)])
                    try:
                        decompressed_bytes = decompressor[0:parts_of_file[-1] + average_size]
                    except:
                        decompressed_bytes = decompressor
            else:
                decompressed_bytes = decompressor

            interpret_bytes(decompressed_bytes, this_folder)

            write_bytes(decompressor.outputdata, output_file_name)

        
    print("Interpreting referenced raw files...")
    for json_entry in progressbar.progressbar(found_files['GameReferencedRawFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != ZZZZ_FILE:
            continue
        
        this_file = offset_to_name.get(entry.disk_location, f'{entry.disk_location:08X}')

        this_folder = join(REF_UNCOMPR_FOLDER, this_file)

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):
            these_bytes = ZZZZ_DAT[entry.disk_location:entry.disk_location+entry.compressed_size]

            interpret_bytes(these_bytes, this_folder)

            write_bytes(these_bytes, output_file_name)

    exit()

if __name__ == "__main__": main()
