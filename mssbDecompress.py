
from genericpath import exists

file_cache = {}

class MSSBByteReadBuffer:
    def __init__(self, file_name: str, offset: int) -> None:
        self.file_name = file_name
        self.offset = offset
        
        if file_name not in file_cache:
            file = open(self.file_name, "rb")
            file_cache[self.file_name] = file.read()
            file.close()
            del file
        
        # self.file_bytes = file_cache[self.file_name][self.offset:]
        
        self.byte_offset = self.offset

        self.bits_in_buffer = 0
        self.buffer = 0
        self.allBytes = bytearray()
    
    def __read_new_byte__(self) ->  int:
        new_byte = file_cache[self.file_name][self.byte_offset]
        self.allBytes.append(new_byte)

        b = int.to_bytes(new_byte, 1, "big", signed=False)
        self.byte_offset += 1

        return int.from_bytes(b, "big", signed = False) 

    def read_bits(self, num: int) -> bytes:
        
        if self.bits_in_buffer == 0:
            self.buffer |= self.__read_new_byte__()
            self.buffer <<= 8

            self.buffer |= self.__read_new_byte__()
            self.buffer <<= 8

            self.buffer |= self.__read_new_byte__()
            self.buffer <<= 8

            self.buffer |= self.__read_new_byte__()
            self.bits_in_buffer = 32
        

        bit = 0
        if self.bits_in_buffer >= num:
        
            bit = self.buffer & (0xffffffff >> (32 - num))
            self.buffer >>= num
            self.bits_in_buffer -= num
        else:
            bitsNeededToRead = num - self.bits_in_buffer
            uVar4 = self.buffer << bitsNeededToRead
            nextData = 0

            nextData |= self.__read_new_byte__()
            nextData <<= 8

            nextData |= self.__read_new_byte__()
            nextData <<= 8

            nextData |= self.__read_new_byte__()
            nextData <<= 8

            nextData |= self.__read_new_byte__()
            
            self.bits_in_buffer = 32 - bitsNeededToRead
            
            uVar4 |= nextData & (0xffffffff >> self.bits_in_buffer)

            bit = uVar4

            self.buffer = nextData >> bitsNeededToRead
        return bit

    def remaining_bytes(self)->int:
        return len(file_cache[self.file_name]) - self.byte_offset

    def close(self):
        pass
        # del self.file_bytes


class MSSBDecompressor:

    def __init__(self, file_name: str, offset: int, size:int, b1:int, b2:int) -> None:
        self.file_name = file_name
        self.offset = offset
        self.size = size
        self.b1 = b1
        self.b2 = b2
        self.byte_reader = None
        self.final_data = bytearray()

    def __init_byte_reader__(self):
        self.byte_reader = MSSBByteReadBuffer(self.file_name, self.offset)

    @staticmethod
    def byte_to_int(b: bytes) -> int:
        return int.from_bytes(b, "big", signed=False)

    def decompress(self) -> list:
        self.__init_byte_reader__()

        bytesToRead = self.size

        if self.byte_reader.remaining_bytes() < bytesToRead:
            return None

        self.final_data = bytearray()

        while bytesToRead > 0:
            # returns 0 or 1
            
            head_bit = self.byte_reader.read_bits(1)
            if head_bit == 0:
                far_back = self.byte_reader.read_bits(self.b1)
                repetitions = self.byte_reader.read_bits(self.b2)
                repetitions += 2
                bytesToRead -= repetitions
                if far_back >= len(self.final_data) or len(self.final_data) == 0:
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    # print("read %d bytes, Got weird data" % (self.size - bytesToRead))
                    return None
                while repetitions != 0:
                    data = self.final_data[-(far_back+1)]
                    self.final_data.append(data)
                    repetitions -= 1
            else:
                data = self.byte_reader.read_bits(8)
                self.final_data.append(data)
                bytesToRead -= 1

        self.byte_reader.close()
        return self.final_data

__DEFAULT_B_VALUES__ = ("11, 4")

def hex_if_possible(num:str)->int:
    if "0x" in num:
        return int(num, 16)
    return int(num)

def main():
    file_name = input("Enter the name of the data file you're decompressing: ")
    output_name = input("Enter the destination file name: ")
    
    if not exists(file_name):
        print("File does not exist")
        return
    
    offset = input("Enter the offset for the file you're decompressing (use 0x for hex): ")
    offset = hex_if_possible(offset)

    size = input("Enter the size of the decompressed file (not the compressed data size) (use 0x for hex): ")
    size = hex_if_possible(size)

    b_values = input("Enter the compression constants (enter nothing to use the default 11,4 values) (use 0x for hex): ")

    if len(b_values) == 0 or b_values.isspace():
        b_values = __DEFAULT_B_VALUES__

    b1 = None
    b2 = None
    b_split = None
    try:
        if "," in b_values:
            b_split = b_values.split(",")
        else:
            b_split = b_values.split(" ")
        
        b1 = hex_if_possible(b_split[0])       
        b2 = hex_if_possible(b_split[1])
    except:   
        print("Failed to read compression constants.")
        return

    decompress(file_name, output_name, offset, size, b1, b2)

def decompress(file_name:str, output_name:str, offset:int, size:int, b1:int, b2:int, skip_if_exists = True) -> bool:
    if skip_if_exists and exists(output_name):
        print("Decompressed file already exists, skipping...")
        return True
    s = MSSBDecompressor(file_name, offset, size, b1, b2)
#    try:
    a = s.decompress()
    if a == None:
        return False
    else:
        print("Finished decompressing file, writing now.")
        with open(output_name, "wb") as f:
            f.write(a)

    print("Completed decompressing")
    return True
    
if __name__ == "__main__":
    main()
