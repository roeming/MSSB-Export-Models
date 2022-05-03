
from genericpath import exists
import os
from posixpath import dirname

class MSSBByteReadBuffer:
    def __init__(self, file_name: str, offset: int) -> None:
        self.file_name = file_name
        self.offset = offset
        
        file = open(self.file_name, "rb")
        file.seek(self.offset)
        self.file_bytes = file.read()
        self.byte_offset = 0

        self.bits_in_buffer = 0
        self.buffer = 0
        self.allBytes = []
    
    def __read_new_byte__(self) ->  int:
        b = int.to_bytes(self.file_bytes[self.byte_offset], 1, "big", signed=False)
        self.byte_offset += 1

        self.allBytes.append(b)
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

    def close(self):
        del self.file_bytes

class MSSBDecompressor:

    def __init__(self, file_name: str, offset: int, size:int, b1:int, b2:int) -> None:
        self.file_name = file_name
        self.offset = offset
        self.size = size
        self.b1 = b1
        self.b2 = b2
        self.byte_reader = None

    def __init_byte_reader__(self):
        self.byte_reader = MSSBByteReadBuffer(self.file_name, self.offset)

    @staticmethod
    def byte_to_int(b: bytes) -> int:
        return int.from_bytes(b, "big", signed=False)

    def decompress(self) -> list:
        self.__init_byte_reader__()

        bytesToRead = self.size

        final_data = []

        while bytesToRead > 0:
            # returns 0 or 1
            head_bit = self.byte_reader.read_bits(1)
            if head_bit == 0:
                far_back = self.byte_reader.read_bits(self.b1)
                repetitions = self.byte_reader.read_bits(self.b2)
                repetitions += 2
                bytesToRead -= repetitions
                if far_back > len(final_data):
                    # if there is a sequence requested to be read that is before the start of the array, then stop
                    print("read %d bytes, Got weird data" % (self.size - bytesToRead))
                    return None
                while repetitions != 0:
                    data = final_data[-(far_back+1)]
                    # print(hex(data))
                    final_data.append(data)
                    repetitions -= 1
            else:
                data = self.byte_reader.read_bits(8)
                # print(hex(data))
                final_data.append(data)
                bytesToRead -= 1

        self.byte_reader.close()
        return final_data

__default_b_values__ = ("11, 4")

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
        b_values = __default_b_values__

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
    try:
        a = s.decompress()
        if a == None:
            return False
        else:
            print("Finished decompressing file, writing now.")
            with open(output_name, "wb") as f:
                for aa in a:
                    f.write(int.to_bytes(aa, 1, "big", signed=False))

        print("Completed decompressing")
        return True
    except IndexError as err:
        print(f"Failed Decompressing, {err=}")
        return False
    
if __name__ == "__main__":
    main()
