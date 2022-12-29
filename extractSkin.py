from tools.file_helper import *
from tools.skinning import *

file_name = "Outputs\\Mario\\Mario.dat"

part = get_parts_of_file(file_name)[3]

with open(file_name, "rb") as f:
    f.seek(part)
    
    file = f.read()

