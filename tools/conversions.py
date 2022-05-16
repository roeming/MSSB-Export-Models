from struct import unpack

def int_from_bytes(b:bytes, signed = False):
    if type(b) == int:
        return b
    return int.from_bytes(b, "big", signed=signed)

def ints_from_bytes(*b, signed = False):
    return [int_from_bytes(s) for s in b]

def float_from_fixedpoint(a:int, shift:int):
    return a / (1 << shift)

def float_from_bytes(b: bytes):
    return unpack("f", b)[0]