from genericpath import exists
import json
import os
import sys

from tools.conversions import *
from tools.file_helper import *

import extractImages
import extractModel
import mssbDecompress


def main():
    err = False
    ZZZZ_file_name = "ZZZZ.dat"
    ZZZZ_hash = "b0cd4f776d023df4dee52086cc3475a5285ce3be"
    json_file_name = "CharacterModels.json"
    json_extra_file_name = "foundRelFiles.json"

    output_folder = "Outputs"

    for f in [ZZZZ_file_name, json_file_name, json_extra_file_name]:
        if not exists(f):
            print(f"Failed to open {f}\nPlease include {f} in the same directory as this file")
            err = True

    with open(json_extra_file_name, "r") as f:
        extra_count = len(json.load(f)["Decompressions"])

    if exists(ZZZZ_file_name) and calculate_sha1(ZZZZ_file_name) != ZZZZ_hash:
        print(f"Your {ZZZZ_file_name} doesn't match the known hash. Please re-export your file, and try again.")
        print(f"Also, please verify the dump of your rom.")
        print(f"You can do this by opening Dolphin, right clicking on your rom -> Properties -> Verify -> Verify Integrity.")
        err = True

    if err:
        exit()

    j = None
    with open(json_file_name, "r") as f:
        j = json.load(f)

    names = sorted([(n["Output"], n) for n in j["Decompressions"]])
    for i, d in enumerate(names):
        print(f"{i+1:2}: {d[0]}")
    print(f"New: {extra_count} new files not yet documented")
    inp = input("\nEnter number(s), or press Enter for all documented entries: ")



    to_decompress = []
    if inp == "":
        to_decompress = [d[1] for d in names]
        decompression_method = regular_decompress
    else:
        lines = [c.upper() for c in inp.split()]
        if "NEW" in lines:
            print("Warning, these files are not documented, so results may vary")
            print("These files will be brute force checked for every type of entry known")
            a = input("Enter (Y/Yes) to continue: ").upper()
            if a in ["Y", "YES"]:
                with open(json_extra_file_name) as f:
                    j = json.load(f)
                    to_decompress = j["Decompressions"]
                
                decompression_method = brute_force_decompress
            else:
                exit()
        else:
            for i in lines:
                try:
                    ii = int(i) -1
                    if ii >= len(names) or ii < 0:
                        print(f"{ii+1} is out of bounds")
                    else:
                        to_decompress.append(names[ii][1])
                except:
                    print(f"Unable to parse {i}, skipping")
                
                decompression_method = regular_decompress
            

    if not exists(output_folder):
        os.mkdir(output_folder)

    decompression_method(to_decompress, output_folder)


def regular_decompress(entries, output_folder):
    to_decompress = entries
    failed = []
    for d in to_decompress:
        try:
            this_file = d["Output"]
            print(f"Starting write {this_file}")
            new_folder = os.path.join(output_folder, this_file.split(".")[0])

            output_file = os.path.join(new_folder, this_file)
            if not exists(output_file):
                decompressor = mssbDecompress.MSSBDecompressor(d["Input"], d["offset"], d["size"], d["b1"], d["b2"])
                
                decompressed_file = decompressor.decompress()
                if decompressed_file is None:
                    print(f"failed to decompress {this_file}, skipping")
                    continue
        
                if not exists(new_folder):
                    os.mkdir(new_folder)

                success = write_bytes(output_file, decompressed_file)
                del decompressed_file

                if not success:
                    print(f"failed to write {this_file}, skipping")
                    continue
                write_bytes(output_file + ".raw", decompressor.byte_reader.allBytes)
                del decompressor

            for f in d["Files"]:
                mtl_header = "{0}_".format(f["Entry"])
                if f["Type"] == "Texture":
                    extractImages.write_images(output_file, new_folder, f["Entry"], True, "{0}_".format(f["Entry"]))
                
                elif f["Type"] == "Model":
                    extractModel.export_model(output_file, new_folder, f["Entry"], "{0}_".format(f["Entry"] + 1))
            
            print(f"Finished decompressing {this_file}\n")

        except IndexError as err:
            print(f"Failed to decompress {this_file}, {err=}, skipping")
            failed.append((this_file, sys.exc_info()))

    if len(failed) > 0:
        print("Failed to complete some files:")
        for f in failed:
            print(f)
    else:
        print("Success")

def brute_force_decompress(entries, output_folder):
    to_decompress = entries
    failed = []
    for d in to_decompress:
        try:
            this_file = d["Output"]
            print(f"Starting write {this_file}")
            new_folder = os.path.join(output_folder, this_file.split(".")[0])

            output_file = os.path.join(new_folder, this_file)
            if not exists(output_file):
                decompressor = mssbDecompress.MSSBDecompressor(d["Input"], d["offset"], d["size"], d["b1"], d["b2"])
                
                decompressed_file = decompressor.decompress()
                if decompressed_file is None:
                    print(f"failed to decompress {this_file}, skipping")
                    continue
        
                if not exists(new_folder):
                    os.mkdir(new_folder)

                success = write_bytes(output_file, decompressed_file)
                del decompressed_file

                if not success:
                    print(f"failed to write {this_file}, skipping")
                    continue

                write_bytes(output_file + ".raw", decompressor.byte_reader.allBytes)
                del decompressor
            parts_of_file = get_parts_of_file(output_file)
            note_file = os.path.join(new_folder, "notes.txt")
            notes = []


            if parts_of_file != None:
                for i in range(len(parts_of_file)):        
                    try:
                        if extractImages.write_images(output_file, new_folder, i, True, image_header=f"{i}_"):
                            notes.append(f"Part {i} is a texture")
                            continue
                    except AssertionError:
                        pass

                    try:
                        extractModel.export_model(output_file, new_folder, i, mtl_header=f"{i}_")
                        notes.append(f"Part {i} is a model")
                        continue
                    except AssertionError:
                        pass

                    notes.append(f"Part {i} is unknown")
            else:
                notes.append("Not an archive")
            write_lines(note_file, notes)
            
            print(f"Finished decompressing {this_file}\n")

        except AssertionError as err:
            print(f"Failed to decompress {this_file}, {err=}, skipping")
            failed.append((this_file, sys.exc_info()))

    if len(failed) > 0:
        print("Failed to complete some files:")
        for f in failed:
            print(f)
    else:
        print("Success")

if __name__ == "__main__":
    main()
