from genericpath import exists
import json
import os
import sys

try:
    import extractImages
    import extractModel
    import mssbDecompress
except:
    print("Please include extractImages.py, extractModel.py, and mssbDecompress.py in the same directory as this file")
    print("Also make sure you have pillow installed. If you don't please run")
    print("'python -m pip install pillow'")
    exit()

def main():
    err = False
    ZZZZ_file_name = "ZZZZ.dat"
    json_file_name = "CharacterModels.json"

    output_folder = "Outputs"

    if not exists(ZZZZ_file_name):
        print(f"Failed to open {ZZZZ_file_name}")
        print("Please include ZZZZ.dat in the same directory as this file")
        err = True
    if not exists(json_file_name):
        print(f"Failed to open {json_file_name}")
        print("Please include CharacterModels.json in the same directory as this file")
        err = True

    if err:
        exit()

    j = None
    with open(json_file_name, "r") as f:
        j = json.load(f)

    names = sorted([(n["Output"], n) for n in j["Decompressions"]])
    
    for i, d in enumerate(names):
        print(f"{i+1:2}: {d[0]}")
    inp = input("\nEnter number(s), or press Enter for all: ")


    to_decompress = []
    if inp == "":
        to_decompress = [d[1] for d in names]
    else:
        lines = inp.split()
        for i in lines:
            try:
                ii = int(i) -1
                if ii >= len(names) or ii < 0:
                    print(f"{ii+1} is out of bounds")
                else:
                    to_decompress.append(names[ii][1])
            except:
                print(f"Unable to parse {i}, skipping")
    
    if not exists(output_folder):
        os.mkdir(output_folder)
    failed = []
    for d in to_decompress:
        try:
            this_file = d["Output"]
            print(f"Starting write {this_file}")
            new_folder = os.path.join(output_folder, d["Output"].split(".")[0])

            if not exists(new_folder):
                os.mkdir(new_folder)

            output_file = os.path.join(new_folder, d["Output"])
            mssbDecompress.decompress(ZZZZ_file_name, output_file, d["offset"], d["size"], d["b1"], d["b2"])
            
            extractImages.export_images(output_file, new_folder)

            extractModel.export_model(output_file, new_folder, 2)
            extractModel.export_model(output_file, new_folder, 6)
            extractModel.export_model(output_file, new_folder, 8)

            print(f"Finished decompressing {this_file}\n")

        except BaseException as err:
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