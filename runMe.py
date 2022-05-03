from genericpath import exists
import json
import os
import sys

try:
    import extractImages
    import extractModel
    import mssbDecompress
except ImportError as err:
    print("Please include extractImages.py, extractModel.py, and mssbDecompress.py in the same directory as this file")
    exit()

def main():
    err = False
    ZZZZ_file_name = "ZZZZ.dat"
    json_file_name = "CharacterModels.json"
    json_extra_file_name = "DolReads.json"

    output_folder = "Outputs"

    for f in [ZZZZ_file_name, json_file_name, json_extra_file_name]:
        if not exists(f):
            print(f"Failed to open {f}\nPlease include {f} in the same directory as this file")
            err = True

    with open(json_extra_file_name, "r") as f:
        extra_count = len(json.load(f)["Decompressions"])

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

            if not exists(new_folder):
                os.mkdir(new_folder)

            output_file = os.path.join(new_folder, this_file)
            mssbDecompress.decompress(d["Input"], output_file, d["offset"], d["size"], d["b1"], d["b2"])
            for f in d["Files"]:
                if f["Type"] == "Texture":
                    extractImages.export_images(output_file, new_folder, f["Entry"])
                elif f["Type"] == "Model":
                    extractModel.export_model(output_file, new_folder, f["Entry"])
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

def brute_force_decompress(entries, output_folder):
    to_decompress = entries
    failed = []
    for d in to_decompress:
        try:
            this_file = d["Output"]
            print(f"Starting write {this_file}")
            new_folder = os.path.join(output_folder, this_file.split(".")[0])

            if not exists(new_folder):
                os.mkdir(new_folder)

            output_file = os.path.join(new_folder, this_file)
            mssbDecompress.decompress(d["Input"], output_file, d["offset"], d["size"], d["b1"], d["b2"])
            
            output_note_file = os.path.join(new_folder, "notes.txt")
            output_notes = []
            file_size = os.path.getsize(output_file)
            archive_counter = 0
            with open(output_file, "rb") as f:
                while True:
                    e = int_from_bytes(f.read(4))
                    if e == 0:
                        possible_archive = True
                        break
                    elif e < file_size:
                        archive_counter += 1
                    else:
                        possible_archive = False
                        break
            
            if possible_archive:
                output_notes.append("Possibly an archive\n")

                for i in range(archive_counter):
                    try:
                        extractModel.export_model(output_file, new_folder, i)
                        output_notes.append(f"Part {i} is a model\n")
                        continue
                    except:
                        pass
                    
                    try:
                        extractImages.export_images(output_file, new_folder, i, f"entry{i}_")
                        output_notes.append(f"Part {i} is a texture\n")
                        continue
                    except:
                        pass
                    output_notes.append(f"Part {i} is unknown\n")
                        
            else:
                output_notes.append("Not an archive\n")

            with open(output_note_file, "w") as f:
                f.writelines(output_notes)

        except AssertionError as err:
            print(f"Failed to decompress {this_file}, {err=}, skipping")
            failed.append((this_file, sys.exc_info()))

    if len(failed) > 0:
        print("Failed to complete some files:")
        for f in failed:
            print(f)
    else:
        print("Success")

def int_from_bytes(b:bytes)->int:
    return int.from_bytes(b, "big", signed=False)

if __name__ == "__main__":
    main()
