from os.path import dirname, join, exists
from helper_vector import *
from helper_obj_file import *
from helper_c3 import *
from helper_mssb_data import *

from helper_mssb_data import get_parts_of_file, float_from_fixedpoint

def main():
    file_name = input("Input file name: ")
    part_of_file = int(input("Input part of file: "))
    export_model(file_name, dirname(file_name), part_of_file)

def export_model(file_bytes:bytearray, output_directory:str, part_of_file = 2, mtl_header:str = ""):

    parts_of_file = get_parts_of_file(file_bytes)

    base_gpl_address = parts_of_file[part_of_file]
    geo_header = GeoPaletteHeader(file_bytes, base_gpl_address)
    geo_header.add_offset(base_gpl_address)
    
    descriptors:list[GeoDescriptor] = []
    
    for i in range(geo_header.numberOfGeometryDescriptors):
        gd_offset = geo_header.offsetToGeometryDescriptorArray + i * GeoDescriptor.SIZE_OF_STRUCT
        d = GeoDescriptor(file_bytes, gd_offset)

        d.add_offset(base_gpl_address)
        MAX_NAME_LENGTH = 100
        
        d.name = get_c_str(file_bytes, d.offsetToName)

        descriptors.append(d)

        dol_offset = d.offsetToDisplayObject
        dol = DisplayObjectLayout(file_bytes, dol_offset)
        dol.add_offset(dol_offset)

        dop = DisplayObjectPositionHeader(file_bytes, dol.OffsetToPositionData)
        dop.add_offset(dol_offset)

        poss = parse_array_values(
            file_bytes[dop.offsetToPositionArray : dop.offsetToPositionArray + (dop.numberOfPositions * (dop.componentSize * dop.numberOfComponents))],
            3,
            dop.componentSize, 
            dop.componentSize * dop.numberOfComponents,
            dop.componentShift,
            dop.componentSigned,
            PositionVector
            )

        doc = DisplayObjectColorHeader(file_bytes, dol.OffsetToColorData)
        doc.add_offset(dol_offset)

        dot = []
        tex_coords = []
        for i in range(dol.numberOfTextures):
            dd = DisplayObjectTextureHeader(file_bytes, dol.OffsetToTextureData + i * DisplayObjectTextureHeader.SIZE_OF_STRUCT)
            dd.add_offset(dol_offset)

            dd.name = get_c_str(file_bytes, dd.offsetToTexturePaletteFileName)

            dot.append(dd)

            if i == 0:
                tex_coords = parse_array_values(
                    file_bytes[dd.offsetToTextureCoordinateArray:][:(dd.numberOfCoordinates * (dd.componentSize * dd.numberOfComponents))],
                    2,
                    dd.componentSize, 
                    dd.componentSize * dd.numberOfComponents,
                    dd.componentShift, 
                    dd.componentSigned,
                    TextureVector
                    )

        doli = DisplayObjectLightingHeader(file_bytes, dol.OffsetToLightingData)
        doli.add_offset(dol_offset)

        norms = parse_array_values(
            file_bytes[doli.offsetToNormalArray:][:(doli.numberOfNormals * (doli.componentSize * doli.numberOfComponents))],
            3,
            doli.componentSize, 
            doli.componentSize * doli.numberOfComponents, 
            doli.componentShift, 
            doli.componentSigned,
            NormalVector
            )

        dod = DisplayObjectDisplayHeader(file_bytes, dol.OffsetToDisplayData)
        dod.add_offset(dol_offset)

        dods = [DisplayObjectDisplayState(file_bytes, dod.offsetToDisplayStateList + i * DisplayObjectDisplayState.SIZE_OF_STRUCT) for i in range(dod.numberOfDisplayStateEntries)]
        all_draws = []
        # print(d)

        texture_index = None
        matrix_src = None
        matrix_dst = None
        for dod_i, dod in enumerate(dods):
            dod.add_offset(dol_offset)
            # print(dod)
            
            if dod.stateID == 1: # Texture
                h = hex(dod.setting)[2:]
                if len(h) == 8 and h[2:4] == "11":
                    texture_index = dod.setting & 0xff
                    # print(f"loading Texture {texture_index}")
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
                matrix_src = dod.setting >> 16
                matrix_dst = dod.setting & 0xffff
            else:
                raise ValueError(f"Unknown Display Call: {dod.stateID}")

            if(dod.offsetToPrimitiveList != 0):
                tris = parse_indices(file_bytes[dod.offsetToPrimitiveList:][:dod.byteLengthPrimitiveList], **comps)
                # these_tris.extend(tris)
                all_draws.append((tris, texture_index, [f"Using Texture {texture_index}", f"Using Matrix {matrix_src}, {matrix_dst}", f"Display Object {dod_i}"]))


        # Write to Obj
        coord_group = OBJGroup(
            positions=poss,
            textures=tex_coords,
            normals=norms,
            faces=[],
            comments=[]
            )

        draw_groups = [OBJGroup(positions=[], textures=[], normals=[], faces=gg[0], mtl=f"mssbMtl.{gg[1]}" if gg[1] != None else None, name=f"group{obj_part}", comments=gg[2]) for obj_part, gg in enumerate(all_draws)]
        
        draw_groups = [coord_group] + draw_groups

        mtl_file = join(mtl_header, "mtl.mtl")
        obj_file = OBJFile(
            groups=draw_groups, 
            mtl_file=mtl_file
            )

        # if not obj_file.assert_valid():
        #     debug = 0

        write_text(str(obj_file), join(output_directory, d.name + ".obj"))

def parse_array_values(b:bytes, component_count:int, component_width:int, struct_size:int, fixed_point:int, signed:bool, cls=None)->list:
    to_return = []
    offset = 0
    while offset < len(b):
        c = []
        these_b = b[offset:][:struct_size]
        for i in range(component_count):
            ii = int.from_bytes(these_b[i*component_width:][:component_width], 'big', signed=signed)
            f = float_from_fixedpoint(ii, fixed_point)
            c.append(f)
        to_return.append(c)        
        offset += struct_size
    if cls == None:
        return to_return
    else:
        return [cls(*x) for x in to_return]

def parse_quads(l: list, cls=None) -> list:
    to_return = []
    assert(len(l) % 4 == 0)
    for i in range(len(l) // 4):
        ii = i*4
        to_return.append((l[ii+0], l[ii+1], l[ii+2]))
        to_return.append((l[ii+2], l[ii+3], l[ii+0]))
    if cls == None:
        return to_return
    else:
        return [cls(*x) for x in to_return]

def parse_triangles(l: list, cls=None) -> list:
    to_return = []
    assert(len(l) % 3 == 0)
    for i in range(len(l) // 3):
        ii = i*3
        to_return.append((l[ii+0], l[ii+1], l[ii+2]))
    if cls == None:
        return to_return
    else:
        return [cls(*x) for x in to_return]

def parse_fan(l: list, cls=None) -> list:
    to_return = []
    for i in range(len(l) - 2):
        to_return.append((l[0], l[i+1], l[i+2]))
    if cls == None:
        return to_return
    else:
        return [cls(*x) for x in to_return]

def parse_strip(l: list, cls=None) -> list:
    to_return = []
    for i in range(len(l) - 2):
        if i%2 == 0:
            to_return.append((l[i], l[i+1], l[i+2]))
        else:
            to_return.append((l[i+2], l[i+1], l[i]))
    if cls == None:
        return to_return
    else:
        return [cls(*x) for x in to_return]

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
            count = int.from_bytes(b[offset:][:2], 'big')
            offset += 2
            for i in range(count):
                v = b[offset:][:vector_size]
                vertex_parts = []
                if pos_size > 0:
                    pos = int.from_bytes(v[pos_offset:][:pos_size], 'big')
                else:
                    pos = None
                
                if norm_size > 0:
                    norm = int.from_bytes(v[norm_offset:][:norm_size], 'big')
                else:
                    norm = None
                
                if uv_size > 0:
                    uv = int.from_bytes(v[uv_offset:][:uv_size], 'big')
                else:
                    uv = None

                new_tris.append(OBJIndices(
                    position_coordinate=OBJIndex(pos),
                    normal_coordinate=OBJIndex(norm),
                    texture_coordinate=OBJIndex(uv)
                ))
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
    
    return [OBJFace(face) for face in faces_to_return]

if __name__ == "__main__":
    main()
