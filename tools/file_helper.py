import os
from .conversions import int_from_bytes
import hashlib

def write_bytes(file_name:str, b:bytes) -> bool:
    try:
        with open(file_name, "wb") as f:
            f.write(bytearray(b))
        return True
    except:
        return False

def get_file_size(file_name:str) -> int:
    return os.path.getsize(file_name)

def get_parts_of_file(file_name:str) -> list[int]:
    file_size = get_file_size(file_name)
    
    file_parts = []

    with open(file_name, "rb") as f:
    
        current_part = int_from_bytes(f.read(0x4))
    
        while current_part != 0:
            if current_part > file_size:
                return None

            file_parts.append(current_part)
            current_part = int_from_bytes(f.read(0x4))
    
    return file_parts

def calculate_sha1(file_name:str) -> str:
    sha1 = hashlib.sha1()
    with open(file_name, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def write_lines(file_name:str, s:list[str]) -> None:
    with open(file_name, "w") as f:
        f.write("\n".join(s))