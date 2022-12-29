from struct import unpack

def int_from_bytes(b:bytes, signed = False):
    if type(b) == int:
        return b
    return int.from_bytes(b, "big", signed=signed)

def bytes_from_int(i:int, signed = False, size = -1):
    if size < 0:
        byte_length, extra_bits = (i.bit_length // 8, i.bit_length % 8)
        if extra_bits > 0:
            byte_length += 1
    else:
        byte_length = size

    return i.to_bytes(i.bit_length, byteorder="big", signed=signed)

def ints_from_bytes(*b, signed = False):
    return [int_from_bytes(s, signed=signed) for s in b]

def float_from_fixedpoint(a:int, shift:int):
    return a / (1 << shift)

def float_from_bytes(b: bytes):
    ba = bytearray(b)
    ba.reverse()
    return unpack("f", ba)[0]

def sublist(list, offset:int, count:int):
    return list[offset:][:count]

def c_string_from_bytes(b:bytes) -> str:
    t = ""
    i = 0
    while b[i] != 0:
        t+= chr(b[i])
        i += 1
    return t
