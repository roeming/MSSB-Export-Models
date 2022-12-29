from genericpath import exists
import json
import os
import progressbar
from mssbDecompress import MSSBDecompressor
from tools.file_helper import write_bytes
from tools.conversions import int_from_bytes

# ALIGNMENT = 0X800
ALIGNMENT = 0X20

j = {
    "Decompressions":[]
}

TEMPLATE = {
            "Input": "ZZZZ.dat",
            "Output": "DK.dat",
            "b1": 11,
            "b2": 4,
            "size": 0,
            "offset": 0,
            "d4": 0,
            "Files": []
        }

files = ["main.dol"]

OUTPUT_FOLDER = "Outputs\\FoundFiles"

output_file_name = os.path.join(OUTPUT_FOLDER, "{0} found files.json")

if not os.path.exists(OUTPUT_FOLDER):
    os.mkdir(OUTPUT_FOLDER)

COMPRESSED_FILES = ["aaaa.dat", "ZZZZ.dat"]

FINGERPRINT_LENGTH = 0x10

FINGERPRINT = b"\x00\x00\x04\x0b\x40"

REL_FILE = "aaaa.dat"

uncompressed_files = dict()

all_found_files = []

i = 0
while i < len(files):
    ff = files[i]
    ff_path = ff
    ff_base = os.path.basename(ff)

    final_json_name = output_file_name.format(ff_base)
    if exists(final_json_name) and False:
        with open(final_json_name, "r") as f:
            j = json.load(f)
        
        for jj in j["Decompressions"]:
            if jj["Input"] == REL_FILE and jj["Output"] not in files:
                files.append(os.path.join(OUTPUT_FOLDER, jj["Output"]))
        
        print(f"Skipping {ff_base}...")
        i += 1
        continue
    
    print(f"Reading {ff_base}...")
    new_files = {}
    with open(ff_path, "rb") as f:
        file_data = f.read()
    
    for b in progressbar.progressbar(range(len(file_data) - FINGERPRINT_LENGTH)):
        bb = file_data[b:b+FINGERPRINT_LENGTH]

        if bb[:5] == FINGERPRINT:
            for data_file in COMPRESSED_FILES:
                t = {
                "Input": data_file,
                "b1": bb[3],
                "b2": bb[2],
                "size": int_from_bytes(bb[4:8]) & 0xfffffff,
                "offset": int_from_bytes(bb[8:12]),
                "d4": int_from_bytes(bb[12:16]),
                "Files": []
                }
                t["Output"] = "{0}-{1}-{2}.dat".format(t["Input"].split(".")[0], hex(t["offset"]), hex(t["size"]))
            
                k = t["Output"]

                if k not in uncompressed_files and k not in new_files:
                    decompressor = MSSBDecompressor(t["Input"], t["offset"], t["size"], t["b1"], t["b2"])
                    dat = decompressor.decompress()
                    if dat == None:
                        new_files[k] = None
                        uncompressed_files[k] = None
                    else:
                        new_files[k] = t #06cf8800
                        uncompressed_files[k] = t

                        if t["Input"] == REL_FILE :
                            output_file = os.path.join(OUTPUT_FOLDER, t["Output"])
                            if output_file not in files:
                                write_bytes(output_file, dat)
                                files.append(output_file)

    decompr = {
        "Decompressions":[]
    }

    for v in new_files.values():
        if v != None:
            decompr["Decompressions"].append(v)

    print(len(decompr["Decompressions"]))

    with open(final_json_name, "w") as f:
        json.dump(decompr, f)

    i += 1