from copy import deepcopy
from genericpath import exists
import json
from struct import unpack

from sklearn.multiclass import OutputCodeClassifier

def int_from_bytes(a, signed=True):
    if(isinstance(a, int)):
        return a
    return int.from_bytes(a, "big", signed=signed)

def float_from_bytes(b: bytes, unused):
    assert(len(b) == 4)
    ba = bytearray(b)
    ba.reverse()
    return unpack("f", ba)[0]

def double_from_bytes(b: bytes, unused):
    assert(len(b) == 8)
    ba = bytearray(b)
    ba.reverse()
    return unpack("d", ba)[0]

file_name = input("Input File Name: ")
if not exists(file_name):
    print("Couldn't find file.")
    exit()
with open(file_name, "r") as f:
    bs = f.read()



type = input("Type: ").lower()

signed = {
    "byte": False,
    "uchar": False,
    "char": True,
    "short": True,
    "ushort": False,
    "float": True,
    "double": True,
    "int": True,
    "uint": False,
}[type]

size = {
    "byte": 1,
    "uchar": 1,
    "char": 1,
    "short": 2,
    "ushort": 2,
    "float": 4,
    "double": 8,
    "int": 4,
    "uint": 4,
}[type]

convert = int_from_bytes
if type == "float":
    convert = float_from_bytes
elif type == "double":
    convert = double_from_bytes

bs = [int(b, 16) for b in [bs[x*2:][:2] for x in range(len(bs)//2)]]
bs = [convert(bs[x*size:][:size], signed) for x in range(len(bs)//size)]

dims = input("What are the dims: ")
dims = [int(x) for x in dims.split()]



output = bs

print(len(output))
for d in reversed(dims[1:]):
    output = [output[x*d:][:d] for x in range(len(output)//d)]
    print(len(output))

with open(file_name, "w") as f:
    # for i, ff in enumerate(output):
    #     f.write(f"{i:2}: {ff},\n")
    # # json.dump(output, f, indent=2)
    f.write(str(output))
