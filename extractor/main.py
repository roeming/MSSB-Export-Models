from helper_mssb_data import DataEntry, RollingDecompressor, ensure_dir, write_bytes, ArchiveDecompressor, get_parts_of_file, write_text
from os.path import join, exists
from os import rename
from run_extract_Texture import export_images
from run_extract_Model import export_model
from run_file_discovery import discover_US_files, discover_beta_files, discover_JP_files, discover_EU_files
import json, progressbar
from run_draw_pic import draw_pic
from helper_file_system import *

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

def interpret_US():
    print('Looking at US files...')
    return interpret_version(US_OUTPUT_FOLDER, US_RESULTS_FILE, US_ZZZZ_FILE, discover_US_files, US_CUSTOM_FILENAMES)
def interpret_JP():
    print('Looking at JP files...')
    return interpret_version(JP_OUTPUT_FOLDER, JP_RESULTS_FILE, JP_ZZZZ_FILE, discover_JP_files, JP_CUSTOM_FILENAMES)
def interpret_EU():
    print('Looking at EU files...')
    return interpret_version(EU_OUTPUT_FOLDER, EU_RESULTS_FILE, EU_ZZZZ_FILE, discover_EU_files, EU_CUSTOM_FILENAMES)
def interpret_BETA():
    print('Looking at Beta files...')
    return interpret_version(BETA_OUTPUT_FOLDER, BETA_RESULTS_FILE, BETA_ZZZZ_FILE, discover_beta_files, BETA_CUSTOM_FILENAMES)

def main():
    interpret_US()
    interpret_JP()
    interpret_EU()
    interpret_BETA()

def interpret_version(output_folder:str, results_path:str, zzzz_file:str, discovery_method, file_name_path:str):
    REFERENCED_FOLDER = join(output_folder, 'Referenced files')
    UNREFERENCED_FOLDER = join(output_folder, 'Unreferenced files')
    RAW_FOLDER = join(output_folder, 'Raw files')
    ADGCFORMS_FOLDER = join(output_folder, 'AdGCForms')

    if not exists(zzzz_file):
        return

    ensure_dir(output_folder)

    with open(zzzz_file, 'rb') as f:
        ZZZZ_DAT = f.read()
 
    if exists(results_path): 
        with open(results_path, 'r') as f:
            found_files = json.load(f)
    else:
        found_files = discovery_method()
        draw_pic(zzzz_file, results_path, join(output_folder, "results.png"))
        
    if exists(file_name_path):
        with open(file_name_path, 'r') as f:
            file_names = json.load(f)
        offset_to_name = {int(x['Location'], 16): x['Name'] for x in file_names}
    else:
        offset_to_name = {}

    print("Interpreting referenced compressed files... (should take about 10 minutes)")
    for json_entry in progressbar.progressbar(found_files['GameReferencedCompressedFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != zzzz_file:
            continue
        
        this_file = f'{entry.disk_location:08X}'
        this_folder = join(REFERENCED_FOLDER, this_file)

        renamed_file = offset_to_name.get(entry.disk_location, None)
        if renamed_file != None:
            renamed_folder = join(REFERENCED_FOLDER, renamed_file)

            if exists(this_folder) and not exists(renamed_folder):
                rename(this_folder, renamed_folder)
            
            this_folder = renamed_folder
            this_file = renamed_file

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):
            this_data = ZZZZ_DAT[entry.disk_location : entry.disk_location + entry.compressed_size]
            if len(this_data) == entry.compressed_size:
                decompressed_bytes = ArchiveDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size, entry.original_size).decompress()
                
                interpret_bytes(decompressed_bytes, this_folder)

                write_bytes(decompressed_bytes, output_file_name)
    
    mean = lambda x : sum(x) // len(x) 

    print("Interpreting unreferenced compressed files... (this will take 30-45 minutes)")
    for json_entry in progressbar.progressbar(found_files['UnreferencedCompressedFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != zzzz_file:
            continue
        
        this_file = f'{entry.disk_location:08X}'
        this_folder = join(UNREFERENCED_FOLDER, this_file)

        renamed_file = offset_to_name.get(entry.disk_location, None)
        if renamed_file != None:
            renamed_folder = join(UNREFERENCED_FOLDER, renamed_file)

            if exists(this_folder) and not exists(renamed_folder):
                rename(this_folder, renamed_folder)
            
            this_folder = renamed_folder
            this_file = renamed_file

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

    print("Interpreting AdGCForms files...")
    for json_entry in progressbar.progressbar(found_files['AdGCForms']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != zzzz_file:
            continue
        
        this_file = f'{entry.disk_location:08X}'
        this_folder = join(ADGCFORMS_FOLDER, this_file)

        renamed_file = offset_to_name.get(entry.disk_location, None)
        if renamed_file != None:
            renamed_folder = join(ADGCFORMS_FOLDER, renamed_file)

            if exists(this_folder) and not exists(renamed_folder):
                rename(this_folder, renamed_folder)
            
            this_folder = renamed_folder
            this_file = renamed_file

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):

            if entry.compression_flag == 0:
                these_bytes = ZZZZ_DAT[entry.disk_location : entry.disk_location + entry.original_size]
            else:
                these_bytes = ArchiveDecompressor(ZZZZ_DAT[entry.disk_location:], entry.lookback_bit_size, entry.repetition_bit_size, entry.original_size).decompress()

            interpret_bytes(these_bytes, this_folder)

            write_bytes(these_bytes, output_file_name)

    print("Interpreting referenced raw files...")
    for json_entry in progressbar.progressbar(found_files['GameReferencedRawFiles']):
        entry = DataEntry.from_dict(json_entry)
        if entry.file != zzzz_file:
            continue
        
        this_file = f'{entry.disk_location:08X}'
        this_folder = join(RAW_FOLDER, this_file)

        renamed_file = offset_to_name.get(entry.disk_location, None)

        if renamed_file != None:
            renamed_folder = join(RAW_FOLDER, renamed_file)

            if exists(this_folder) and not exists(renamed_folder):
                rename(this_folder, renamed_folder)
            
            this_folder = renamed_folder
            this_file = renamed_file

        output_file_name = join(this_folder, this_file) + ".dat"

        if not exists(output_file_name):
            these_bytes = ZZZZ_DAT[entry.disk_location:entry.disk_location+entry.compressed_size]

            interpret_bytes(these_bytes, this_folder)

            write_bytes(these_bytes, output_file_name)


if __name__ == "__main__": main()
