from genericpath import exists
import os
from posixpath import dirname
import struct

def main():
    file_name = input("Input file name: ")
    part_of_file = int(input("Input part of file: "))
    export_model(file_name, dirname(file_name), part_of_file)

def export_model(file_name:str, output_directory:str, part_of_file = 2):

    if not exists(file_name):
        print("File doesn't exist")
        exit()
    
    file_bytes = None
    with open(file_name, "rb") as f:
        file_bytes = f.read()

    parts_of_file = []
    offset = 0
    while True:
        p = int_from_bytes(file_bytes[offset:offset+4])
        if p == 0:
            break
        parts_of_file.append(p)
        offset += 4
    del p

    base_gpl = parts_of_file[part_of_file]
    geo_header = GeoPaletteHeader(file_bytes[base_gpl:base_gpl + GeoPaletteHeader.size_of_struct])
    geo_header.add_offset(base_gpl)
    # print(geo_header)
    # print()
    
    descriptors = [GeoDescriptor(file_bytes[geo_header.offsetToGeometryDescriptorArray + i * GeoDescriptor.size_of_struct:geo_header.offsetToGeometryDescriptorArray + (i+1) * GeoDescriptor.size_of_struct:]) for i in range(geo_header.numberOfGeometryDescriptors)]
    
    for d in descriptors:
        d.add_offset(base_gpl)
        n = ""
        n_offset = d.offsetToName
        while file_bytes[n_offset] != 0:
            n += chr(file_bytes[n_offset])
            n_offset += 1
        d.name = n
        # print(d)
    # print()
    
    for d in descriptors:
        dol_offset = d.offsetToDisplayObject
        dol = DisplayObjectLayout(file_bytes[dol_offset : dol_offset + DisplayObjectLayout.size_of_struct])
        dol.add_offset(dol_offset)
        # print(dol)
        # print()

        dop = DisplayObjectPositionHeader(file_bytes[dol.OffsetToPositionData:dol.OffsetToPositionData+DisplayObjectPositionHeader.size_of_struct])
        dop.add_offset(dol_offset)
        # print(dop)
        poss = parse_array_values(file_bytes[dop.offsetToPositionArray : dop.offsetToPositionArray + (dop.numberOfPositions * (dop.componentSize * dop.numberOfComponents))], 3, dop.componentSize, dop.componentSize*dop.numberOfComponents, dop.componentShift, dop.componentSigned)
        # print()

        doc = DisplayObjectColorHeader(file_bytes[dol.OffsetToColorData:dol.OffsetToColorData+DisplayObjectColorHeader.size_of_struct])
        doc.add_offset(dol_offset)
        # print(doc)
        # print()

        dot = []
        tex_coords = []
        for i in range(dol.numberOfTextures):
            dd = DisplayObjectTextureHeader(file_bytes[dol.OffsetToTextureData + i * DisplayObjectTextureHeader.size_of_struct: dol.OffsetToTextureData + (i + 1) * DisplayObjectTextureHeader.size_of_struct])
            dd.add_offset(dol_offset)
            n_offset = dd.offsetToTexturePaletteFileName
            n = ""
            while file_bytes[n_offset] != 0:
                n += chr(file_bytes[n_offset])
                n_offset += 1
            dd.name = n

            dot.append(dd)
            # print(dot[i])

            if i == 0:
                tex_coords = parse_array_values(file_bytes[dd.offsetToTextureCoordinateArray : dd.offsetToTextureCoordinateArray + (dd.numberOfCoordinates * (dd.componentSize * dd.numberOfComponents))], 2, dd.componentSize, dd.componentSize*dd.numberOfComponents, dd.componentShift, dd.componentSigned)
                tex_coords = [(t[0], 1.0-t[1]) for t in tex_coords]
        # print()

        doli = DisplayObjectLightingHeader(file_bytes[dol.OffsetToLightingData:dol.OffsetToLightingData+DisplayObjectLightingHeader.size_of_struct])
        doli.add_offset(dol_offset)
        # print(doli)
        norms = parse_array_values(file_bytes[doli.offsetToNormalArray : doli.offsetToNormalArray + (doli.numberOfNormals * (doli.componentSize * doli.numberOfComponents))], 3, doli.componentSize, doli.componentSize*doli.numberOfComponents, doli.componentShift, doli.componentSigned)
        # print()

        dod = DisplayObjectDisplayHeader(file_bytes[dol.OffsetToDisplayData:dol.OffsetToDisplayData+DisplayObjectDisplayHeader.size_of_struct])
        dod.add_offset(dol_offset)
        # print(dod)
        # print()

        dods = [DisplayObjectDisplayState(file_bytes[dod.offsetToDisplayStateList + i * DisplayObjectDisplayState.size_of_struct: dod.offsetToDisplayStateList + (i + 1) * DisplayObjectDisplayState.size_of_struct]) for i in range(dod.numberOfDisplayStateEntries)]
        all_draws = []
        print(d)
        texture_index = None
        for dod_i, dod in enumerate(dods):
            dod.add_offset(dol_offset)
            # print(dod)
            
            if dod.stateID == 1: # Texture
                h = hex(dod.setting)[2:]
                if len(h) == 8 and h[:4] == "1511":
                    texture_index = dod.setting & 0xff
                    print(f"loading Texture {texture_index}")
            elif dod.stateID == 2: # Vertex Description

                size_conversion = {
                0:0,
                2:1,
                3:2
                }
                all_components = [(dod.setting >> (j * 2)) & 3 for j in range(13)]
                all_sizes = [size_conversion[j] for j in all_components]
                comps = {
                    "vector_size": sum(all_sizes),
                    "pos_size": all_sizes[1],
                    "pos_offset": sum(all_sizes[:1]),
                    "norm_size": all_sizes[2],
                    "norm_offset": sum(all_sizes[:2]),
                    "uv_size": all_sizes[5],
                    "uv_offset": sum(all_sizes[:5]),
                }

            elif dod.stateID == 3: # Matrix Load
                pass
            else:
                print(f"Unknown Display Call: {dod.stateID}")
                assert(False)

            these_tris = []
            if(dod.offsetToPrimitiveList != 0):
                tris = parse_indices(file_bytes[dod.offsetToPrimitiveList : dod.offsetToPrimitiveList + dod.byteLengthPrimitiveList], **comps)
                these_tris.extend(tris)
                all_draws.append((these_tris, texture_index))


        # Write to Obj
        mtl_file = "mtl.mtl"
        glob_mtl_file = os.path.join(output_directory, mtl_file)
        
        with open(os.path.join(output_directory, d.name + ".obj"), "w") as f:
            if(exists(glob_mtl_file)):
                f.write(f"mtllib {mtl_file}\n")
            for pp in poss:
                f.write(f"v {pp[0]} {-pp[1]} {-pp[2]}\n")
            for pp in norms:
                f.write(f"vn {pp[0]} {-pp[1]} {-pp[2]}\n")
            for pp in tex_coords:
                f.write(f"vt {pp[0]} {pp[1]}\n")

            for obj_part, gg in enumerate(all_draws):
                if len(gg) <= 0:
                    continue
                f.write(f"g group{obj_part}\n")
                if gg[1] is not None:
                    f.write(f"usemtl mssbMtl.{gg[1]}\n")
                for g in gg[0]:
                    f.write("f")
                    # print(pp)
                    for ppp in g:
                        # print(ppp)
                        f.write(" ")
                        f.write(str(ppp[0]+1))
                        f.write("/")
                        if ppp[2] is not None:
                            f.write(str(ppp[2]+1))
                        f.write("/")
                        if ppp[1] is not None:
                            f.write(str(ppp[1]+1))
                        # f.write("/".join([str(x) for x in ppp]))
                    f.write("\n")
        # exit()

    # print()

def parse_array_values(b:bytes, component_count:int, component_width:int, struct_size:int, fixed_point:int, signed:bool)->list:
    to_return = []
    offset = 0
    while offset < len(b):
        c = []
        these_b = b[offset:offset + struct_size]
        for i in range(component_count):
            ii = int_from_bytes(these_b[i*component_width:(i+1)*component_width], signed=signed)
            f = float_from_fixedpoint(ii, fixed_point)
            c.append(f)
        to_return.append(c)        
        offset += struct_size
    return to_return

def parse_quads(l: list) -> list:
    to_return = []
    assert(len(l) % 4 == 0)
    for i in range(len(l) // 4):
        ii = i*4
        to_return.append((l[ii+0], l[ii+1], l[ii+2]))
        to_return.append((l[ii+2], l[ii+3], l[ii+0]))
    return to_return

def parse_triangles(l: list) -> list:
    to_return = []
    assert(len(l) % 3 == 0)
    for i in range(len(l) // 3):
        ii = i*3
        to_return.append((l[ii+0], l[ii+1], l[ii+2]))
    return to_return

def parse_fan(l: list) -> list:
    to_return = []
    for i in range(len(l) - 2):
        to_return.append((l[0], l[i+1], l[i+2]))
    return to_return

def parse_strip(l: list) -> list:
    to_return = []
    for i in range(len(l) - 2):
        if i%2 == 0:
            to_return.append((l[i], l[i+1], l[i+2]))
        else:
            to_return.append((l[i+2], l[i+1], l[i]))
    return to_return


def parse_indices(b: bytes, **kwargs) -> list:
    vector_size = kwargs["vector_size"]
    pos_size = kwargs["pos_size"]
    pos_offset = kwargs["pos_offset"]
    norm_size = kwargs["norm_size"]
    norm_offset = kwargs["norm_offset"]
    uv_size = kwargs["uv_size"]
    uv_offset = kwargs["uv_offset"]
    offset = 0

    faces_to_return = []
    while offset < len(b):
        command = b[offset]
        offset+=1
        
        if command == 0x61: # bp
            # print(hex(int_from_bytes(b[offset:offset+4])))
            offset+=4

            continue
        elif command == 0x00: # nop
            continue
        
        new_tris = []
        shifted_command = command >> 3
        if shifted_command in [0x10, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17]:
            assert(command & 0x7 == 0)
            count = int_from_bytes(b[offset:offset+2])
            offset += 2
            for i in range(count):
                v = b[offset: offset + vector_size]
                vertex_parts = []
                if pos_size > 0:
                    pos = int_from_bytes(v[pos_offset:pos_offset + pos_size])
                    vertex_parts.append(pos)
                
                if norm_size > 0:
                    norm = int_from_bytes(v[norm_offset:norm_offset+norm_size])
                    vertex_parts.append(norm)
                else:
                    vertex_parts.append(None)
                
                if uv_size > 0:
                    uv = int_from_bytes(v[uv_offset:uv_offset+uv_size])
                    vertex_parts.append(uv)
                else:
                    vertex_parts.append(None)

                new_tris.append(vertex_parts)
                offset += vector_size
        else:
            print(f"Unrecognized command: {hex(command)}")
            assert(False)

        if shifted_command == 0x10: # Draw Quads
            new_tris = parse_quads(new_tris)
            # new_tris = []
        elif shifted_command == 0x12: # Draw Triangles
            new_tris = parse_triangles(new_tris)
            # new_tris = []
        elif shifted_command == 0x13: # Draw Triangle Strip
            new_tris = parse_strip(new_tris)
            # new_tris = []
        elif shifted_command == 0x14: # Draw Triangle Fan
            new_tris = parse_fan(new_tris)
            # new_tris = []
        elif shifted_command == 0x15: # Draw Lines
            print("Unimplemented Draw command")
            assert(False)
        elif shifted_command == 0x16: # Draw Line Strip
            print("Unimplemented Draw command")
            assert(False)
        elif shifted_command == 0x17: # Draw Points
            print("Unimplemented Draw command")
            assert(False)
        else:
            print("Unknown Draw command")
            assert(False)

        faces_to_return.extend(new_tris)
    return faces_to_return



def float_from_fixedpoint(a:int, shift:int):
    return a / (1 << shift)

def int_from_bytes(b:bytes, signed = False):
    if type(b) == int:
        return b
    return int.from_bytes(b, "big", signed=signed)

def ints_from_bytes(*b, signed = False):
    return [int_from_bytes(s) for s in b]

class GeoPaletteHeader:
    size_of_struct = 20

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        ints = ints_from_bytes(b[0:4], b[4:8], b[8:12], b[12:16], b[16:20])
        self.versionNumber = ints[0]
        self.userDefinedDataSize = ints[1]
        self.offsetToUserDefinedData = ints[2]
        self.numberOfGeometryDescriptors = ints[3]
        self.offsetToGeometryDescriptorArray = ints[4]

    def add_offset(self, offset:int):
        if self.offsetToGeometryDescriptorArray != 0 :
            self.offsetToGeometryDescriptorArray += offset

        if self.offsetToUserDefinedData != 0:
            self.offsetToUserDefinedData += offset

    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\nVersion Number: {self.versionNumber}\nUser Defined Data Size: {self.userDefinedDataSize}\npDefined Data: {hex(self.offsetToUserDefinedData)}\nNumber Of Geometry Descriptors: {self.numberOfGeometryDescriptors}\npGeometry Descriptor Array: {hex(self.offsetToGeometryDescriptorArray)}"

class GeoDescriptor:
    size_of_struct = 8

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:8])
        self.offsetToDisplayObject = i[0]
        self.offsetToName = i[1]
        self.name = None

    def add_offset(self, offset:int):
        if self.offsetToDisplayObject != 0:
            self.offsetToDisplayObject += offset
    
        if self.offsetToName != 0:
            self.offsetToName += offset
    
    def set_name(self, name:str):
        self.name = name
    
    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\nName: {self.name}\npDisplay Object: {hex(self.offsetToDisplayObject)}\npName: {hex(self.offsetToName)}"

class DisplayObjectLayout:
    size_of_struct = 0x18

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:8], b[8:12], b[12:16], b[16:20], b[20])
        self.OffsetToPositionData = i[0]
        self.OffsetToColorData = i[1]
        self.OffsetToTextureData = i[2]
        self.OffsetToLightingData = i[3]
        self.OffsetToDisplayData = i[4]
        self.numberOfTextures = i[5]
        
    def add_offset(self, offset:int) -> None:
        if self.OffsetToPositionData != 0:
            self.OffsetToPositionData += offset

        if self.OffsetToColorData != 0:
            self.OffsetToColorData += offset
        
        if self.OffsetToTextureData != 0:
            self.OffsetToTextureData += offset

        if self.OffsetToLightingData != 0:
            self.OffsetToLightingData += offset

        if self.OffsetToDisplayData != 0:
            self.OffsetToDisplayData += offset
    
    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\npPosition Data: {hex(self.OffsetToPositionData)}\npColor Data: {hex(self.OffsetToColorData)}\npTexture Data: {hex(self.OffsetToTextureData)}\npLighting Data: {hex(self.OffsetToLightingData)}\npDisplay Data: {hex(self.OffsetToDisplayData)}"

class DisplayObjectPositionHeader:
    size_of_struct = 0x8
    quantize_info={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:6], b[6], b[7])
        self.offsetToPositionArray = i[0]
        self.numberOfPositions = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.quantize_info["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.quantize_info["signed info"][self.format]

        self.numberOfComponents = i[3]

    def add_offset(self, offset:int)->None:
        if self.offsetToPositionArray != 0:
            self.offsetToPositionArray += offset
    
    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\npPositions: {hex(self.offsetToPositionArray)}\nPosition Count: {hex(self.numberOfPositions)}\nQuantize Info: {hex(self.quantizeInfo)}\nComponent Count: {self.numberOfComponents}"


class DisplayObjectColorHeader:
    size_of_struct = 0x8

    quantize_info = {
        0x0:2,
        0x1:3,
        0x2:4,
        0x3:2,
        0x4:3,
        0x5:4,
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:6], b[6], b[7])
        self.offsetToColorArray = i[0]
        self.numberOfColors = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.alpha = self.format > 2
        self.componentSize = self.quantize_info[self.format]
        self.numberOfComponents = i[3]

    def add_offset(self, offset:int)->None:
        if self.offsetToColorArray != 0:
            self.offsetToColorArray += offset

    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\npColors: {hex(self.offsetToColorArray)}\nColor Count: {self.numberOfColors}\nFormat Info: {hex(self.quantizeInfo)}\nComponent Count: {self.numberOfComponents}"

class DisplayObjectTextureHeader:
    size_of_struct = 0x10

    quantize_info={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:6], b[6:7], b[7:8], b[8:12])
        self.offsetToTextureCoordinateArray = i[0]
        self.numberOfCoordinates = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.quantize_info["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.quantize_info["signed info"][self.format]

        self.numberOfComponents = i[3]
        self.offsetToTexturePaletteFileName = i[4]

        self.name = None

    def add_offset(self, offset:int)->None:
        if self.offsetToTextureCoordinateArray != 0:
            self.offsetToTextureCoordinateArray += offset
        
        if self.offsetToTexturePaletteFileName != 0:
            self.offsetToTexturePaletteFileName += offset

    def __str__(self) -> str:
        return f"=={self.__class__.__name__}==\nName: {self.name}\npName: {hex(self.offsetToTexturePaletteFileName)}\npTexture Coords: {hex(self.offsetToTextureCoordinateArray)}\nCoord Count: {self.numberOfCoordinates}\nFormat Info: {hex(self.quantizeInfo)}\nComponent Count: {self.numberOfComponents}"


class DisplayObjectLightingHeader:
    size_of_struct = 0xc
    quantize_info={
        "size info":{
            0x1:4,
            0x2:2,
            0x3:2,
            0x4:1,
            0x5:1
        },
        "signed info":{
            0x1:True,
            0x2:False,
            0x3:True,
            0x4:False,
            0x5:True
        }
    }

    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:6], b[6:7], b[7:8])
        self.offsetToNormalArray = i[0]
        self.numberOfNormals = i[1]
        self.quantizeInfo = i[2]
        
        self.format = self.quantizeInfo >> 4
        self.componentSize = self.quantize_info["size info"][self.format]
        self.componentShift = self.quantizeInfo & 0xf
        self.componentSigned = self.quantize_info["signed info"][self.format]

        self.numberOfComponents = i[3]
        ba = bytearray(b[8:12])
        ba.reverse()
        self.ambientBrightness = struct.unpack("f", ba)[0]

    def add_offset(self, offset:int)->None:
        if self.offsetToNormalArray != 0:
            self.offsetToNormalArray += offset

    def __str__(self) -> str: 
        return f"=={self.__class__.__name__}==\npNormals: {hex(self.offsetToNormalArray)}\nNormal Count: {self.numberOfNormals}\nFormat Info: {hex(self.quantizeInfo)}\nComponent Count: {self.numberOfComponents}\nAmbient Brightness: {self.ambientBrightness}"


class DisplayObjectDisplayHeader:
    size_of_struct = 0xc
    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0:4], b[4:8], b[8:10])
        self.offsetToPrimitiveBank = i[0]
        self.offsetToDisplayStateList = i[1]
        self.numberOfDisplayStateEntries = i[2]
    
    def add_offset(self, offset:int)->None:
        if self.offsetToPrimitiveBank != 0:
            self.offsetToPrimitiveBank += offset
        
        if self.offsetToDisplayStateList != 0:
            self.offsetToDisplayStateList += offset
    
    def __str__(self) -> str: 
        return f"=={self.__class__.__name__}==\npPrimitive Bank: {hex(self.offsetToPrimitiveBank)}\npDisplay States: {hex(self.offsetToDisplayStateList)}\nDisplay State Count: {self.numberOfDisplayStateEntries}"

        
class DisplayObjectDisplayState:
    size_of_struct = 0x10
    def __init__(self, b:bytes) -> None:
        assert(len(b) == self.size_of_struct)
        i = ints_from_bytes(b[0], b[4:8], b[8:12], b[12:16])
        self.stateID = i[0]
        self.setting = i[1]
        self.offsetToPrimitiveList = i[2]
        self.byteLengthPrimitiveList = i[3]
    
    def add_offset(self, offset:int)->None:
        if self.offsetToPrimitiveList != 0:
            self.offsetToPrimitiveList += offset
    
    def __str__(self) -> str: 
        return f"=={self.__class__.__name__}==\nState ID: {self.stateID}\nSetting: {hex(self.setting)}\npPrimitive List: {hex(self.offsetToPrimitiveList)}\nPrimitive Byte Count: {self.byteLengthPrimitiveList}"

if __name__ == "__main__":
    main()
