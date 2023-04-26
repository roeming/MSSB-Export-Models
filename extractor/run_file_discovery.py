from os.path import exists, dirname, join
from os import makedirs
from helper_mssb_data import DataEntry, FileCache, FingerPrintSearcher, MultipleRanges, ArchiveDecompressor, ensure_dir, write_text, write_bytes
import json, progressbar
from helper_file_system import *

file_cache = FileCache()

for file in [US_AAAA_FILE, US_ZZZZ_FILE, US_MAIN_FILE]:
    if not exists(file):
        print(f"{file} does not exist. Please supply this file to continue.")

if any([not exists(file) for file in [US_AAAA_FILE, US_ZZZZ_FILE, US_MAIN_FILE]]):
    exit()

KNOWN_AAAA_FILES:list[DataEntry] = [
    DataEntry.from_dict({
        "Input": US_AAAA_FILE,
        "Output": join(OUTPUT_FOLDER, '800.rel'),
        "lookbackBitSize": 0xb,
        "repetitionBitSize": 0x4,
        "size": 0x1027E4,
        "offset": 0x800,
        "compressedSize": 0x5A818,
        "compressionFlag": 0x4,
    }),
    DataEntry.from_dict({
        "Input": US_AAAA_FILE,
        "Output": join(OUTPUT_FOLDER, '5b800.rel'),
        "lookbackBitSize": 0xb,
        "repetitionBitSize": 0x4,
        "size": 0x2220F8,
        "offset": 0x5B800,
        "compressedSize": 0xF4450,
        "compressionFlag": 0x4,
    }),
    DataEntry.from_dict({
        "Input": US_AAAA_FILE,
        "Output": join(OUTPUT_FOLDER, '150000.rel'),
        "lookbackBitSize": 0xb,
        "repetitionBitSize": 0x4,
        "size": 0x5912C,
        "offset": 0x150000,
        "compressedSize": 0x271C0,
        "compressionFlag": 0x4,
    })
]

KNOWN_RAW_MOVIES = [
    DataEntry.from_dict({
        "Input": US_ZZZZ_FILE,
        "Output": "movie1.HVQM4",
        "lookbackBitSize": 0,
        "repetitionBitSize": 0,
        "size": 0X5233458,
        "offset": 0X12000,
        "compressedSize": 0X5233458,
        "compressionFlag": 0,
    }),
    DataEntry.from_dict({
        "Input": US_ZZZZ_FILE,
        "Output": "movie2.HVQM4",
        "lookbackBitSize": 0,
        "repetitionBitSize": 0,
        "size": 0X33452C,
        "offset": 0X5245800,
        "compressedSize": 0X33452C,
        "compressionFlag": 0,
    }),
    DataEntry.from_dict({
        "Input": US_ZZZZ_FILE,
        "Output": "movie3.HVQM4",
        "lookbackBitSize": 0,
        "repetitionBitSize": 0,
        "size": 0X1700804,
        "offset": 0X557A000,
        "compressedSize": 0X1700804,
        "compressionFlag": 0,
    })
]

KNOWN_COMPRESSED_FILES = [
    DataEntry.from_dict({
        "Input": US_ZZZZ_FILE,
        "lookbackBitSize": 0xe,
        "repetitionBitSize": 5,
        "size": 0x3e1a0,
        "offset": 0x08e77000,
        "compressedSize": 0x143ec,
        "compressionFlag": 0,
    })
]

def discover_US_files():
    return discover_files(US_MAIN_FILE, US_AAAA_FILE, US_ZZZZ_FILE, US_OUTPUT_FOLDER, KNOWN_RAW_MOVIES, KNOWN_AAAA_FILES + KNOWN_COMPRESSED_FILES, US_RESULTS_FILE)

def discover_JP_files():
    return discover_files(JP_MAIN_FILE, JP_AAAA_FILE, JP_ZZZZ_FILE, JP_OUTPUT_FOLDER, [], [], JP_RESULTS_FILE)

def discover_EU_files():
    return discover_files(EU_MAIN_FILE, EU_AAAA_FILE, EU_ZZZZ_FILE, EU_OUTPUT_FOLDER, [], [], EU_RESULTS_FILE)

def discover_beta_files():
    return discover_files(BETA_MAIN_FILE, BETA_AAAA_FILE, BETA_ZZZZ_FILE, BETA_OUTPUT_FOLDER, [], [], BETA_RESULTS_FILE)


def discover_files(this_main: str, this_aaaa: str, this_zzzz: str, this_output_folder: str, this_verified_raw_files:list[DataEntry], this_verified_compressed_files:list[DataEntry], output_file: str):
    if any([not exists(x) for x in [this_zzzz, this_aaaa, this_main]]):
        return

    ensure_dir(this_output_folder)

    this_zzzz_dat = file_cache.get_file_bytes(this_zzzz)
    this_aaaa_dat = file_cache.get_file_bytes(this_aaaa)
    this_main_dol = file_cache.get_file_bytes(this_main)

    b1 = 11
    b2 = 4
    size = 200    

    unverified_aaaa_decompressions = []
    print(f'Doing brute force decompression check ({b1} {b2})...')
    for i in progressbar.progressbar(range(0, len(this_aaaa_dat), 0x800)):
        if ArchiveDecompressor(this_aaaa_dat[i : i + 2*size], b1, b2, size).is_valid_decompression():
            unverified_aaaa_decompressions.append(DataEntry.from_dict({
                "Input": this_aaaa,
                "lookbackBitSize": b1,
                "repetitionBitSize": b2,
                "size": 0,
                "offset": i,
                "compressedSize": 0,
                "compressionFlag": 0,
            }))

    main_search_results = FingerPrintSearcher(this_main_dol, this_aaaa).search_compression(b1, b2)
    
    rels = []
    list_found_main_entries = list(main_search_results)
    for entry in unverified_aaaa_decompressions:
        matching_offsets = [x for x in list_found_main_entries if x.disk_location == entry.disk_location]

        assert(len(matching_offsets) in [0, 1])

        if len(matching_offsets) > 0:
            for r in matching_offsets:
                r: DataEntry
                if is_decompression_valid(r):
                    rels.append(r)

    rels_to_search = [this_main]
    for rel in rels:
        rel_output_path = join(this_output_folder, f'{rel.disk_location:x}.rel')
        rels_to_search.append(rel_output_path)

        if not exists(rel_output_path):
            write_bytes(decompress(rel), rel_output_path)
    
    main_search_results: set[DataEntry] = set()
    found_raw_entries:set[DataEntry] = set()

    # start mapping out all files
    verified_entries:list[DataEntry] = list()
    verified_entries.extend(this_verified_compressed_files)

    verified_raw_entries:list[DataEntry] = list()
    verified_raw_entries.extend(this_verified_raw_files)

    # accumulate all entries that look like a decompression fingerprint
    print("Searching rels...")
    for rel in progressbar.progressbar(rels_to_search):
        searcher = FingerPrintSearcher(file_cache.get_file_bytes(rel), this_zzzz)
        main_search_results.update(searcher.search_compression(11, 4))
        found_raw_entries.update(searcher.search_uncompressed())

    list_entries = list(main_search_results)
    list_entries.sort(key=lambda x: x.disk_location)
    # remove ones that look like the aaaa.dat files
    for rel in rels:
        rel: DataEntry

        list_entries = [x for x in list_entries if not rel.equals_besides_filename(x)]

    list_raw_entries = list(found_raw_entries)
    list_raw_entries.sort(key=lambda x: x.disk_location)

    # start mapping file    
    file_mapping = MultipleRanges()

    for known_file in this_verified_raw_files:
        known_file: DataEntry

        verified_raw_entries.append(known_file)
        file_mapping.add_range(known_file.to_range())

    # check new entries
    print('Checking found compressed data...')
    for new_entry in progressbar.progressbar(list_entries):
        new_entry:DataEntry
        entry_range = new_entry.to_range()

        if is_decompression_valid(new_entry):
            new_entry.output_name = join(OUTPUT_FOLDER, "cmp " + new_entry.output_name.strip(US_ZZZZ_FILE))
            verified_entries.append(new_entry)
            file_mapping.add_range(entry_range)
    
    unverified_aaaa_decompressions:list[DataEntry] = list()

    formats_to_search = [(11,4,200)]
    for b1, b2, size in formats_to_search:
        print(f'Doing brute force decompression check ({b1} {b2})...')
        for i in progressbar.progressbar(range(0, len(this_zzzz_dat), 0x800)):
            if i in file_mapping:
                continue
            if ArchiveDecompressor(this_zzzz_dat[i:i+2*size], b1, b2, size).is_valid_decompression():
                unverified_aaaa_decompressions.append(DataEntry.from_dict({
                    "Input": this_zzzz,
                    "Output": join(this_output_folder, f"cmp unverified {i:x}.dat"),
                    "lookbackBitSize": b1,
                    "repetitionBitSize": b2,
                    "size": 0,
                    "offset": i,
                    "compressedSize": 0,
                    "compressionFlag": 0,
                }))
                file_mapping.add_range(range(i, i+size))

    print('Checking found raw data...')
    for new_entry in progressbar.progressbar(list_raw_entries):
        
        new_entry:DataEntry
        entry_range = new_entry.to_range()
        # if the proposed range overlaps with previous entries, skip
        if file_mapping.does_overlap(entry_range):
            continue

        # if is_decompression_valid(new_entry):
        new_entry.output_name = join(this_output_folder, "raw " + new_entry.output_name.strip(this_zzzz))
        verified_raw_entries.append(new_entry)
        file_mapping.add_range(new_entry.to_range())

    output = {
        'GameReferencedCompressedFiles': [x.to_dict() for x in verified_entries],
        'GameReferencedRawFiles': [x.to_dict() for x in verified_raw_entries],
        'UnreferencedCompressedFiles': [x.to_dict() for x in unverified_aaaa_decompressions],
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    return output

# def discover_files_(output_file: str):

#     # make a list of all the files to search
#     rels_to_search = [US_MAIN_FILE]
#     for rel in KNOWN_AAAA_FILES:
#         rel_output_path = join(OUTPUT_FOLDER, f'{rel.disk_location:x}.rel')
#         rels_to_search.append(rel_output_path)

#         if not exists(rel_output_path):
#             write_bytes(decompress(rel), rel_output_path)
    
#     all_found_entries: set[DataEntry] = set()
#     found_raw_entries:set[DataEntry] = set()

#     # start mapping out all files
#     verified_entries:list[DataEntry] = list()
#     verified_entries.extend(KNOWN_AAAA_FILES + KNOWN_COMPRESSED_FILES)

#     verified_raw_entries:list[DataEntry] = list()

#     # accumulate all entries that look like a decompression fingerprint
#     print("Searching rels...")
#     for rel in progressbar.progressbar(rels_to_search):
#         searcher = FingerPrintSearcher(file_cache.get_file_bytes(rel), US_ZZZZ_FILE)
#         all_found_entries.update(searcher.search_compression(11, 4))
#         found_raw_entries.update(searcher.search_uncompressed())

#     list_entries = list(all_found_entries)
#     list_entries.sort(key=lambda x: x.disk_location)
#     # remove ones that look like the aaaa.dat files
#     for rel in KNOWN_AAAA_FILES:
#         list_entries = [x for x in list_entries if not rel.equals_besides_filename(x)]

#     list_raw_entries = list(found_raw_entries)
#     list_raw_entries.sort(key=lambda x: x.disk_location)

#     # start mapping file    
#     file_mapping = MultipleRanges()
#     # add known movies because they're so big, they can eliminate any weird files
#     for known_file in KNOWN_RAW_MOVIES:
#         verified_raw_entries.append(known_file)
#         file_mapping.add_range(known_file.to_range())
    
#     # check new entries
#     print('Checking found compressed data...')
#     for new_entry in progressbar.progressbar(list_entries):
#         new_entry:DataEntry
#         entry_range = new_entry.to_range()
#         # can ignore the movie files
#         # if file_mapping.does_overlap(entry_range):
#         #     continue

#         if is_decompression_valid(new_entry):
#             new_entry.output_name = join(OUTPUT_FOLDER, "cmp " + new_entry.output_name.strip(US_ZZZZ_FILE))
#             verified_entries.append(new_entry)
#             file_mapping.add_range(entry_range)
    
#     unverified_decompressions:list[DataEntry] = list()
#     zzzz_dat = file_cache.get_file_bytes(US_ZZZZ_FILE)
#     formats_to_search = [(11,4,200)]
#     for b1, b2, size in formats_to_search:
#         print(f'Doing brute force decompression check ({b1} {b2})...')
#         for i in progressbar.progressbar(range(0, len(zzzz_dat), 0x800)):
#             if i in file_mapping:
#                 continue
#             if ArchiveDecompressor(zzzz_dat[i:i+2*size], b1, b2, size).is_valid_decompression():
#                 unverified_decompressions.append(DataEntry.from_dict({
#                     "Input": US_ZZZZ_FILE,
#                     "Output": f"cmp unverified {i:x}.dat",
#                     "lookbackBitSize": b1,
#                     "repetitionBitSize": b2,
#                     "size": 0,
#                     "offset": i,
#                     "compressedSize": 0,
#                     "compressionFlag": 0,
#                 }))
#                 file_mapping.add_range(range(i, i+size))

#     print('Checking found raw data...')
#     for new_entry in progressbar.progressbar(list_raw_entries):
        
#         new_entry:DataEntry
#         entry_range = new_entry.to_range()
#         # if the proposed range overlaps with previous entries, skip
#         if file_mapping.does_overlap(entry_range):
#             continue

#         # if is_decompression_valid(new_entry):
#         new_entry.output_name = join(OUTPUT_FOLDER, "raw " + new_entry.output_name.strip(US_ZZZZ_FILE))
#         verified_raw_entries.append(new_entry)
#         file_mapping.add_range(new_entry.to_range())

#     output = {
#         'GameReferencedCompressedFiles': [x.to_dict() for x in verified_entries],
#         'GameReferencedRawFiles': [x.to_dict() for x in verified_raw_entries],
#         'UnreferencedCompressedFiles': [x.to_dict() for x in unverified_decompressions],
#     }
    
#     with open(output_file, "w") as f:
#         json.dump(output, f, indent=2)
    
#     return output


def is_decompression_valid(d: DataEntry) -> bool:
    byte_data = file_cache.get_file_bytes(d.file)[d.disk_location : d.disk_location+d.compressed_size]
    return ArchiveDecompressor(byte_data, d.lookback_bit_size, d.repetition_bit_size).is_valid_decompression()


def decompress(d: DataEntry) -> bytearray:
    byte_data = file_cache.get_file_bytes(d.file)[d.disk_location : d.disk_location+d.compressed_size]
    return ArchiveDecompressor(byte_data, d.lookback_bit_size, d.repetition_bit_size).decompress()
