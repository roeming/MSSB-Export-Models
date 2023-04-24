from __future__ import annotations
from typing import NamedTuple, Union
from struct import pack, unpack, calcsize
from os.path import dirname, exists
from os import makedirs

class CompressionData(NamedTuple):
    ORIGINAL_DATA = 1
    REPETITION_DATA = 0
    flag: int = None
    data: int = None
    look_back: int = None
    length: int = None
    
    def is_original_data(self):
        return self.flag == self.ORIGINAL_DATA
    
    def is_repeated_data(self):
        return self.flag == self.REPETITION_DATA

    def __str__(self):
        if self.flag == self.ORIGINAL_DATA:
            return f"OriginalData({self.data:02x})"
        elif self.flag == self.REPETITION_DATA:
            return f"RepetitionData(look_back={self.look_back}, length={self.length})"
        else:
            return ""
        
    def __repr__(self) -> str:
        return self.__str__()

class ArchiveDecompressor:
    def __init__(self, buffer:bytearray, lookback_bit_count:int, repetition_bit_count:int, original_size:int=None) -> None:
        self.bytes_to_decompress = bytearray(buffer)
        self.lookback_bit_count = lookback_bit_count
        self.repetition_bit_count = repetition_bit_count
        self.__byte_index = 0
        self.__bit_buffer = 0
        self.__bits_in_buffer = 0
        self.original_size = original_size
    
    def __read_int(self)->int:
        if(self.__byte_index + 3 >= len(self.bytes_to_decompress)):
            raise ValueError("No more ints to read")

        value = int.from_bytes(self.bytes_to_decompress[self.__byte_index : self.__byte_index + 4], 'big')

        self.__byte_index += 4

        return value

    def __has_bits(self):
        if self.__byte_index >= len(self.bytes_to_decompress) - 1:
            return self.__bit_buffer != 0
        return True

    def __should_keep_decompressing(self, size:int):
        if self.original_size != None:
            return size < self.original_size
        return self.__has_bits()

    def __read_bits(self, bit_count:int):
        # if enough bits in buffer
        if bit_count <= self.__bits_in_buffer:
            # read the bits from the low end
            value = self.__bit_buffer & (2**bit_count - 1)
            # rotate out the bits
            self.__bit_buffer >>= bit_count
            # remove the count of those bits
            self.__bits_in_buffer -= bit_count
        else:
            # else not enough bits,
            # we need a new int
            new_buffer = self.__read_int()
            
            new_bits_needed = bit_count - self.__bits_in_buffer
            # the bits remaining in the buffer will be the high bits for the output data
            value = self.__bit_buffer << new_bits_needed

            self.__bits_in_buffer = 32 - new_bits_needed
            # the bits we're using from the new data will become the low bits of the output data
            value |= (new_buffer & (0xffffffff >> self.__bits_in_buffer))
            # rotate out the data
            self.__bit_buffer = new_buffer >> new_bits_needed

        return value
    
    def __reset_buffer(self):
        self.__byte_index = 0
        self.__bit_buffer = 0
        self.__bits_in_buffer = 0

    def is_valid_decompression(self) -> bool:
        if self.lookback_bit_count == 0 and self.repetition_bit_count == 0:
            return True
        
        self.__reset_buffer()

        written_bit_count = 0

        while self.__should_keep_decompressing(written_bit_count):
            # returns 0 or 1
            head_bit = self.__read_bits(1)
            if head_bit == 0:                
                far_back = self.__read_bits(self.lookback_bit_count)
                repetitions = self.__read_bits(self.repetition_bit_count) + 2
                if far_back >= written_bit_count:
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    return False
                written_bit_count += repetitions
            else:
                self.__read_bits(8)
                written_bit_count += 1
        return True
    
    def get_compression_instructions(self) -> list[CompressionData]:
        if self.lookback_bit_count == 0 and self.repetition_bit_count == 0:
            return []
        
        self.__reset_buffer()

        written_bit_count = 0
        instructions = []
        while self.__should_keep_decompressing(written_bit_count):
            # returns 0 or 1
            head_bit = self.__read_bits(1)
            if head_bit == 0:                
                far_back = self.__read_bits(self.lookback_bit_count)
                length = self.__read_bits(self.repetition_bit_count) + 2
                if far_back > written_bit_count:
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    raise ValueError("Invalid data, received too far lookback")

                instructions.append(CompressionData(flag=head_bit, look_back=far_back, length=length))
            else:
                instructions.append(CompressionData(flag=head_bit, data=self.__read_bits(8)))
                length = 1

            written_bit_count += length
        return instructions

    def decompress(self):
        if self.lookback_bit_count == 0 and self.repetition_bit_count == 0:
            if self.original_size != None:
                return self.bytes_to_decompress[:self.original_size]
            else:
                return bytearray()
        
        self.__reset_buffer()

        final_data = bytearray()

        while self.__should_keep_decompressing(len(final_data)):
            # returns 0 or 1
            head_bit = self.__read_bits(1)
            if head_bit == CompressionData.REPETITION_DATA:

                far_back = self.__read_bits(self.lookback_bit_count)
                
                repetitions = self.__read_bits(self.repetition_bit_count) + 2

                if far_back > len(final_data):
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    raise ValueError("Invalid data, received too far lookback")
                while repetitions != 0:
                    final_data.append(final_data[-1 - far_back])
                    repetitions -= 1
            else:
                final_data.append(self.__read_bits(8))

        return final_data

class ArchiveCompressor:
    class CompressedBufferHelper:
        ORIGINAL_DATA = 1
        REPETITION = 0

        def __init__(self) -> None:
            self.out_values = []
            self.buffer = 0
            self.buffer_bit_count = 0

        def write_original_data(self, data:int):
            assert(data >= 0)
            assert(data < 2**8)
            
            self.add_bits(self.ORIGINAL_DATA, 1)
            self.add_bits(data, 8)
        
        def write_repetition(self, lookback:int, lookback_size:int, repetitions:int, repetitions_size:int):
            assert(lookback >= 0)
            assert(lookback < 2**lookback_size)
            
            assert(repetitions >= 0)
            assert(repetitions < 2**repetitions_size)

            self.add_bits(self.REPETITION, 1)
            self.add_bits(lookback, lookback_size)
            self.add_bits(repetitions, repetitions_size)

        def add_bits(self, value:int, bit_count:int):
            assert(value & (2**bit_count -1) == value) # make sure the bit count convers all bits with value

            if self.buffer_bit_count + bit_count <= 32:
                self.buffer |= value << self.buffer_bit_count
                self.buffer_bit_count += bit_count
                if self.buffer_bit_count == 32:
                    self.out_values.append(self.buffer)

                    self.buffer = 0
                    self.buffer_bit_count = 0
            else:
                remaining_bits = 32 - self.buffer_bit_count
                # the remaining bits will get the high bits of the value
                upper_value = value >> (bit_count - remaining_bits)
                lower_value = value & (2**(bit_count - remaining_bits) - 1)

                self.buffer |= upper_value << self.buffer_bit_count

                self.out_values.append(self.buffer)

                self.buffer = lower_value
                self.buffer_bit_count = (bit_count - remaining_bits)


        def flush(self):
                if self.buffer_bit_count > 0:
                    self.out_values.append(self.buffer)
                    self.buffer = 0
                    self.buffer_bit_count = 0
        
        def to_byte_array(self) -> bytearray:
            b = bytearray()
            for i in self.out_values:
                b.extend(i.to_bytes(4, 'big', signed=False))
            return b
        
    class SublistDefinition(NamedTuple):
        offset:int
        length:int

    def __init__(self, data:bytearray, lookback_bit_size:int, repetition_bit_size:int) -> None:
        self.data = bytearray(data)
        self.lookback_bit_size = lookback_bit_size
        self.repetition_bit_size = repetition_bit_size

        self.cached_data = {}

    # function to help get the count of the matching characters
    def __length_of_match(data:bytearray, sublist:bytearray):
        count = 0
        while count < len(sublist) and (sublist[count] == data[count]):
            count += 1
        return count

    def __largest_sublist_cachedsearch(self, sub_start: int, sub_stop: int, sliding_window_start_index: int, sliding_window_stop_index: int, look_ahead_size: int, min_sublist_size:int):
        sliding_window_size = sliding_window_stop_index - sliding_window_start_index

        sublist = self.data[sub_start:sub_stop]
        
        first_char = sublist[0]

        cached_ind_set:list = self.cached_data.get(first_char, None)
        if cached_ind_set != None:
            to_remove = []
            match_length = -1
            match_index = -1

            for cached_ind in cached_ind_set:
                if cached_ind < (sub_start - sliding_window_size):
                    to_remove.append(cached_ind)
                    continue

                len_of_match = ArchiveCompressor.__length_of_match(self.data[cached_ind:cached_ind+sub_stop-sub_start], sublist)

                if len_of_match > match_length:
                    match_length = len_of_match
                    match_index = cached_ind
                
            cached_ind_set.append(sub_start)
            for rem in to_remove:
                cached_ind_set.remove(rem)

            for sublist_index in range(1, match_length):
                char = sublist[sublist_index]
                char_ind = sub_start + sublist_index
                
                cached_ind_set = self.cached_data.get(char, None)
                if cached_ind_set == None:
                    cached_ind_set = set()
                    self.cached_data[char] = cached_ind_set

                cached_ind_set.append(char_ind)
            
            if match_length >= min_sublist_size:
                return self.SublistDefinition(match_index, match_length)
        else:
            self.cached_data[first_char] = [sub_start]

        return None
    
    def __largest_sublist_bytesearch(self, sub_start: int, sub_stop: int, sliding_window_start_index: int, sliding_window_stop_index: int, look_ahead_size: int, min_sublist_size:int) -> SublistDefinition:

        sub_start                   = max(0, sub_start)
        sliding_window_start_index  = max(0, sliding_window_start_index)

        dat_len                     = len(self.data)

        sub_stop                    = min(dat_len, sub_stop)
        sliding_window_stop_index   = min(dat_len, sliding_window_stop_index)

        sublist = self.data[sub_start:sub_stop]

        
        # -------- bytearray built-in find ----------- 2.5 seconds

        # size of sliding window | first offset that is unacceptable
        unusable_lookahead_ind = sliding_window_stop_index - sliding_window_start_index
        # cut sliding window and lookahead to search in
        sliding_window_and_lookahead = self.data[sliding_window_start_index : sliding_window_stop_index + look_ahead_size]
        # only look for sublists for sizes above min_sublist_size
        while len(sublist) >= min_sublist_size:
            # finds first instance, returns >= 0 if found, else -1
            ind = sliding_window_and_lookahead.find(sublist)
            # checks to see if any found and first instance is not in the lookahead
            if 0 <= ind < unusable_lookahead_ind:
                # return offset into large array
                return self.SublistDefinition(sliding_window_start_index + ind, len(sublist))
            # cut down list to look for smaller sublist
            sublist = sublist[:-1]
        # nothing found
        return None
        
        # -----------------------------------

    def __largest_sublist_search(self, sub_start: int, sub_stop: int, sliding_window_start_index: int, sliding_window_stop_index: int, look_ahead_size: int, min_sublist_size:int) -> SublistDefinition:

        sub_start                   = max(0, sub_start)
        sliding_window_start_index  = max(0, sliding_window_start_index)

        dat_len                     = len(self.data)

        sub_stop                    = min(dat_len, sub_stop)
        sliding_window_stop_index   = min(dat_len, sliding_window_stop_index)

        sublist = self.data[sub_start:sub_stop]
        
        # ----------------- Iterate ------------------ 30 seconds
        # max_length = len(sublist)
        # best_index = -1
        # best_length = -1

        # # walk through every index in the sliding window
        # for compare_index in range(sliding_window_start_index, sliding_window_stop_index):

        #     # check to see how many values in the sublist match at this index
        #     sub_count = 0
        #     while sub_count < max_length and self.data[compare_index + sub_count] == sublist[sub_count]:
        #         sub_count += 1
            
        #     # record it if it was better than the previous best found
        #     if sub_count > best_length:
        #         best_index = compare_index
        #         best_length = sub_count

        # # only return sublist if it meets the min sublist requirement
        # if best_length >= min_sublist_size:
        #     return self.SublistDefinition(offset=best_index, length=best_length)
        # return None
        # -----------------------------------

        # ----------------- look for first char ------ 13 seconds
        sliding_window = self.data[sliding_window_start_index:sliding_window_stop_index]

        first_char = sublist[0]
        # retrive the indices of all times the first character of the sublist exists in the sliding window
        all_first_char_inds = [ind for (ind, v) in enumerate(sliding_window) if v == first_char]


        # loop over the indices, and figure out how many characters match the sublist
        all_lengths = [(ArchiveCompressor.__length_of_match(self.data[sliding_window_start_index + ind : sliding_window_start_index + ind + len(sublist)], sublist), ind) for ind in all_first_char_inds]
        
        # if no matches are found, return None
        if len(all_lengths) == 0:
            return None

        # have to choose 1 of the found, choose the first instance of longest length
        best_length = max([x[0] for x in all_lengths])

        # if best length isn't long enough, return none
        if best_length < min_sublist_size:
            return None

        best_index = min([x[1] for x in all_lengths if x[0] == best_length])
        return self.SublistDefinition(sliding_window_start_index + best_index, best_length)
        # -----------------------------------

    def compress(self) -> bytearray:
        self.cached_data    = {}
        data_index          = 0
        look_back_size      = 2**self.lookback_bit_size
        repetitions_size    = 2**self.repetition_bit_size + 1

        buffer = self.CompressedBufferHelper()
        while data_index < len(self.data):
                        
            longest_match = self.__largest_sublist_bytesearch(
                    sub_start                   = data_index,
                    sub_stop                    = data_index + repetitions_size,
                    min_sublist_size            = 2,

                    sliding_window_start_index  = data_index - look_back_size,
                    sliding_window_stop_index   = data_index,
                    look_ahead_size             = repetitions_size,
                )

            if longest_match != None:
                #longest_match.offset is just an index into the array, we actually want to have it become a lookback from the data_index
                buffer.write_repetition(
                    lookback            = data_index - longest_match.offset - 1, 
                    repetitions         = longest_match.length - 2, 
                    lookback_size       = self.lookback_bit_size, 
                    repetitions_size    = self.repetition_bit_size,
                )
                data_index += longest_match.length
            else:
                buffer.write_original_data(self.data[data_index])
                data_index += 1
        
        buffer.flush()
        return buffer.to_byte_array()

class RollingDecompressor():
    MAX_SIZE = 4_000_000 # 4 mb max size

    def __init__(self, buffer:bytearray, lookback_bit_count:int, repetition_bit_count:int) -> None:
        self.bytes_to_decompress = bytearray(buffer)
        self.lookback_bit_count = lookback_bit_count
        self.repetition_bit_count = repetition_bit_count
        self.__reset_buffer()
        self.outputdata = bytearray()
    
    def __read_int(self)->int:
        if(self.__byte_index + 3 >= len(self.bytes_to_decompress)):
            raise ValueError("No more ints to read")

        value = int.from_bytes(self.bytes_to_decompress[self.__byte_index : self.__byte_index + 4], 'big')

        self.__byte_index += 4

        return value

    def __len__(self):
        return 2**32-1

    def __read_bits(self, bit_count:int):
        # if enough bits in buffer
        if bit_count <= self.__bits_in_buffer:
            # read the bits from the low end
            value = self.__bit_buffer & (2**bit_count - 1)
            # rotate out the bits
            self.__bit_buffer >>= bit_count
            # remove the count of those bits
            self.__bits_in_buffer -= bit_count
        else:
            # else not enough bits,
            # we need a new int
            new_buffer = self.__read_int()
            
            new_bits_needed = bit_count - self.__bits_in_buffer
            # the bits remaining in the buffer will be the high bits for the output data
            value = self.__bit_buffer << new_bits_needed

            self.__bits_in_buffer = 32 - new_bits_needed
            # the bits we're using from the new data will become the low bits of the output data
            value |= (new_buffer & (0xffffffff >> self.__bits_in_buffer))
            # rotate out the data
            self.__bit_buffer = new_buffer >> new_bits_needed

        return value
    
    def __reset_buffer(self):
        self.__byte_index = 0
        self.__bit_buffer = 0
        self.__bits_in_buffer = 0

    def decompress(self, size:int):
        while len(self.outputdata) < size and len(self.outputdata) < RollingDecompressor.MAX_SIZE:
            # returns 0 or 1
            head_bit = self.__read_bits(1)
            if head_bit == CompressionData.REPETITION_DATA:

                far_back = self.__read_bits(self.lookback_bit_count)
                
                repetitions = self.__read_bits(self.repetition_bit_count) + 2

                if far_back > len(self.outputdata):
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    raise ValueError("Invalid data, received too far lookback")
                while repetitions != 0:
                    self.outputdata.append(self.outputdata[-1 - far_back])
                    repetitions -= 1
            else:
                self.outputdata.append(self.__read_bits(8))

        return self.outputdata
    
    class RollingDecompressorSlice:
        def __init__(self, d:RollingDecompressor, s:slice) -> None:
            # we should only get to this point if stop is not defined
            self.__rolling_decompressor = d
            self.__slice = s
        
        def __getitem__(self, key):
            if isinstance(key, int):
                assert(key >= 0)
                
                self.__rolling_decompressor.decompress(max(self.__slice.start, self.__slice.stop))
                return self.__rolling_decompressor.outputdata[self.__slice.start:self.__slice.stop:self.__slice.step][key]
            
            elif isinstance(key, slice):
                assert(key.step == None or key.step > 0)
                assert(key.start == None or key.start >= 0)
                assert(key.stop == None or key.stop >= 0)

                my_start   = self.__slice.start if self.__slice.start != None else 0
                my_step    = self.__slice.step  if self.__slice.step  != None else 1

                this_start = key.start if key.start != None else 0
                this_step  = key.step  if key.step  != None else 1

                if key.stop != None: # stop defined

                    total_start = this_start + my_start
                    total_end = total_start + max((key.stop - this_start) * my_step, 0)
                    self.__rolling_decompressor.decompress(max(total_start, total_end))

                    return self.__rolling_decompressor.outputdata[total_start : total_end : this_step * my_step]
            
                elif key.stop == None: # no stop defined
                    
                    return RollingDecompressor.RollingDecompressorSlice(self.__rolling_decompressor, slice(my_start + (this_start * this_step), None, this_step*my_step))
                
            raise ValueError(f"Unexpected key: {type(key)}: {key}")

        def __len__(self):
            return len(self.__rolling_decompressor)
                    
    def __getitem__(self, key):
        if isinstance(key, int):
            assert(key >= 0)
            
            self.decompress(key+1)
            return self.outputdata[key]

        elif isinstance(key, slice):
            assert(key.step == None or key.step > 0)
            assert(key.start == None or key.start >= 0)
            assert(key.stop == None or key.stop >= 0)

            if key.stop != None: # stop defined
                assert(key.stop >= 0)
                
                this_start = key.start if key.start != None else 0
                
                self.decompress(max(this_start, key.stop))
                return self.outputdata[this_start:key.stop:key.step] # return data between start and stop
                        
            return RollingDecompressor.RollingDecompressorSlice(self, key) # if no stop defined
        raise ValueError(f"Unexpected key: {type(key)}: {key}")
    
class DataBytesInterpreter:
    @classmethod
    @property
    def SIZE_OF_STRUCT(cls):
        return calcsize(cls.DATA_FORMAT)

    @classmethod
    def parse_bytes_static(cls, all_bytes:bytearray, offset:int, format_str:str):
        struct_size = calcsize(format_str)
        these_bytes = all_bytes[offset:offset+struct_size]

        if len(these_bytes) != struct_size:
            raise ValueError(f'Ran out of bytes to interpret in {cls.__class__.__name__}, needed {cls.SIZE_OF_STRUCT}, received {len(these_bytes)}')

        return unpack(format_str, these_bytes)

    def parse_bytes(self, all_bytes:bytearray, offset:int):
        return self.parse_bytes_static(all_bytes, offset, self.DATA_FORMAT)
        
class DataEntry(DataBytesInterpreter):
    DATA_FORMAT = ">xxBBIII"

    @property
    def footer_size(self):
        base = 0x800
        size = self.disk_location + self.compressed_size
        size %= base
        if size == 0:
            footer = 0
        else:
            footer = base - size
        
        return footer

    def __init__(self, b: bytearray, offset:int, file="") -> None:

        self.file = file
        self.repetition_bit_size,\
        self.lookback_bit_size,\
        self.original_size,\
        self.disk_location,\
        self.compressed_size =\
        self.parse_bytes(b, offset)

        self.compression_flag = self.original_size >> 28

        self.original_size &= 0xf_ff_ff_ff

        self.output_name = f"{self.file} {self.lookback_bit_size:02x}{self.repetition_bit_size:02x} {self.disk_location:08x}.dat"
        
        self.reset_output_name()

    def reset_output_name(self):
        self.output_name = f"{self.file} {self.lookback_bit_size:02x}{self.repetition_bit_size:02x} {self.disk_location:08x}.dat"

    def __str__(self) -> str:
        s = ""
        s += f'File:            {self.file}\n'
        s += f'Output Name:     {self.output_name}\n'
        s += f'Lookback bits:   0x{self.lookback_bit_size:02x}\n'
        s += f'Repetition bits: 0x{self.repetition_bit_size:02x}\n'
        s += f'Original Size:   0x{self.original_size:x}\n'
        s += f'Disk Location:   0x{self.disk_location:08x}\n'
        s += f'Compressed Size: 0x{self.compressed_size:x}\n'
        s += f'Compressed Flag: {self.compression_flag}\n'
        s += f'Footer Size:     0x{self.footer_size:x}'

        return s
    
    def to_dict(self)->dict:
        return {
            "Input": self.file,
            "Output": self.output_name,
            "lookbackBitSize": self.lookback_bit_size,
            "repetitionBitSize": self.repetition_bit_size,
            "size": self.original_size,
            "offset": self.disk_location,
            "compressedSize": self.compressed_size,
            "compressionFlag": self.compression_flag,
            "footerSize": self.footer_size
        }
    
    def from_dict(d:dict) -> DataEntry:
        data = DataEntry(
            pack(
                DataEntry.DATA_FORMAT, 
                d["repetitionBitSize"], 
                d["lookbackBitSize"], 
                d["size"] | (d["compressionFlag"] << 28), 
                d["offset"], 
                d["compressedSize"]
            ),
            0,
            d["Input"]
        )

        if "Output" in d:
            data.output_name = d["Output"]
        return data
    
    def to_range(self):
        return range(self.disk_location, self.disk_location + self.compressed_size + self.footer_size)

    def __hash__(self) -> int:
        return hash((self.file, self.lookback_bit_size, self.repetition_bit_size, self.original_size, self.disk_location, self.compressed_size, self.compression_flag, self.footer_size))
    
    def equals_besides_filename(self, __o: object):
        if not isinstance(__o, DataEntry):
            return False
        
        return self.lookback_bit_size == __o.lookback_bit_size and self.repetition_bit_size == __o.repetition_bit_size and self.original_size == __o.original_size and self.disk_location == __o.disk_location and self.compressed_size == __o.compressed_size and self.compression_flag == __o.compression_flag and self.footer_size == __o.footer_size

    def __eq__(self, __o: object) -> bool:
        return self.equals_besides_filename(__o) and  self.file == __o.file
    
    def __lt__(self, __o: object):
        if not isinstance(__o, DataEntry):
            return False
        return self.disk_location < __o.disk_location

class FileCache:
    def __init__(self) -> None:
        self.__byte_cache__ = {}
    
    def __load_file(self, file_name:str):
        assert(file_name not in self.__byte_cache__)

        with open(file_name, "rb") as f:
            self.__byte_cache__[file_name] = f.read()

    def get_file_bytes(self, file_name:str)->bytes:
        if file_name not in self.__byte_cache__:
            self.__load_file(file_name)

        return self.__byte_cache__[file_name]
    
class MultipleRanges:
    def __init__(self) -> None:
        self.__ranges:list[range] = []

    def __overlap(r1:range, r2:range):
        return (
            # if one of the start/stops exists in the other
            (r2.start in r1 or r2.stop in r1) or
            (r1.start in r2 or r1.stop in r2))
    
    def __overlap_or_touch(r1:range, r2:range):
        return (
            # if they overlap on an edge
            r1.start == r2.stop or 
            r2.start == r1.stop or
            MultipleRanges.__overlap(r1, r2))
    
    def __combine_range(r1:range, r2:range)->range:
        if MultipleRanges.__overlap_or_touch(r1, r2):
            all_points = [r1.start, r2.start, r1.stop, r2.stop]
            # if the overlap, just take the max and mins
            return range(min(all_points), max(all_points))
        return None

    def does_overlap(self, r:range):
        return any([MultipleRanges.__overlap(x, r) for x in self.__ranges])

    def add_range(self, r:range):

        overlapping_indices = [i for i, this_range in enumerate(self.__ranges) if MultipleRanges.__overlap_or_touch(r, this_range)]

        if len(overlapping_indices) == 0:
            self.__ranges.append(r)
        else:
            # indices should be next to eachother
            new_range = range(r.start, r.stop)
            for ind in overlapping_indices:
                new_range = MultipleRanges.__combine_range(new_range, self.__ranges[ind])
                assert(new_range != None)

            to_remove_ind = min(overlapping_indices)
            to_remove_count = len(overlapping_indices)
            for _ in range(to_remove_count):
                self.__ranges.pop(to_remove_ind)
            
            self.__ranges.append(new_range)

        self.__ranges.sort(key=lambda x: x.start)

    def __str__(self) -> str:
        return f"{self.__ranges}"
    
    def __repr__(self) -> str:
        return self.__str__()

    def remove_range(self, r:range):
        new_ranges = []

        for old_range in self.__ranges:
            if (old_range.start >= r.start and 
                old_range.stop <= r.stop): # complete overlap, remove
                pass
            elif (old_range.start <= r.start and
                   old_range.stop >= r.start and 
                   old_range.stop <= r.stop): # overlap top
                new_ranges.append(range(old_range.start, r.start))
            elif (old_range.stop >= r.stop and
                   old_range.start >= r.start and 
                   old_range.start <= r.stop): # overlap bottom
                new_ranges.append(range(r.stop, old_range.stop))
            elif (r.start >= old_range.start and 
                  r.stop <= old_range.stop): # overlap middle
                new_ranges.append(range(old_range.start, r.start))
                new_ranges.append(range(r.stop, old_range.stop))            

        self.__ranges = new_ranges

        self.__ranges.sort(key=lambda x: x.start)
    
    def __contains__(self, value):
        # binary search
        max_ind = len(self.__ranges)
        min_ind = 0
        ind = max_ind // 2
        while True:
            this_range = self.__ranges[ind]
            
            if value in this_range:
                return True
            
            if ind == min_ind or ind == len(self.__ranges) - 1:
                return False
            
            if value < this_range.start:
                max_ind = ind
                ind = (ind + min_ind) // 2
            elif value > this_range.stop:
                min_ind = ind
                ind = (ind + max_ind) // 2
            elif value == this_range.stop:
                return False
            
class FingerPrintSearcher:
    def __init__(self, b:bytearray, file_name:str) -> None:
        self.data = b
        self.file_name = file_name

    def search_compression(self, lookback:int, repetitions:int) -> set[DataEntry]:
        to_find = ((repetitions << 8) | lookback).to_bytes(4, 'big')
        d = self.data
        
        found = set()

        ind = d.find(to_find)
        while ind > 0 and len(d) >= DataEntry.SIZE_OF_STRUCT:
            entry = DataEntry(d, ind, self.file_name)            
            # for now it has to be a mult of 2048 bytes, and not 0
            if entry.disk_location % 0x800 == 0 and entry.disk_location != 0:
                found.add(entry)
            
            d = d[ind + len(to_find):]
            ind = d.find(to_find)
        
        return found

    def search_uncompressed(self) -> set[DataEntry]:
        epsilon = 3
        to_find = (0).to_bytes(4, 'big')
        d = self.data
        found = set()

        ind = d.find(to_find)
        while ind >= 0 and len(d[ind:]) >= DataEntry.SIZE_OF_STRUCT:
            entry = DataEntry(d, ind, self.file_name)
            
            # for now it has to be a mult of 2048 bytes, and not 0
            if entry.disk_location % 0x800 == 0 and entry.disk_location != 0:
                # compressed size and entry size should be close to same size, but not 0
                if entry.compressed_size > 0 and entry.original_size > 0 and abs(entry.compressed_size - entry.original_size) <= epsilon:
                    found.add(entry)
            
            d = d[ind + 1:]
            ind = d.find(to_find)
        return found

def get_parts_of_file(file_bytes:bytearray):
    found_inds = []

    i = 0
    while True:
        new_ind = int.from_bytes(file_bytes[i:i+4], 'big')
        i += 4
        
        if new_ind == 0:
            break

        if len(found_inds) != 0 and new_ind <= found_inds[-1]:
            break

        found_inds.append(new_ind)

    return found_inds

def float_from_fixedpoint(a:int, shift:int):
    return a / (1 << shift)

def ensure_dir(path:str):
    if not (path == '' or path in "\\/" or exists(path)):
        makedirs(path)

def write_text(s:str, file_path:str):
    write_bytes(s.encode(), file_path)

def write_bytes(b:bytes, file_path:str):
    ensure_dir(dirname(file_path))
    with open(file_path, "wb") as f:
        f.write(b)

def get_c_str(b: bytes, offset: int, max_length: Union[int, None] = 100):
    s = ""
    n_offset = offset
    while b[n_offset] != 0:
        s += chr(b[n_offset])

        if max_length != None and len(s) >= max_length:
            break

        n_offset += 1

    return s
