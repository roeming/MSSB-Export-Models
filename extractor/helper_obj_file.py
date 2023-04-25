from dataclasses import dataclass
import typing
from helper_vector import *

class PositionVector(Vector3):
    def __str__(self) -> str:
        return f"v {self.X} {-self.Y} {-self.Z}" 

class TextureVector(Vector2):
    def __str__(self) -> str:
        return f"vt {self.U} {-self.V}" 

class NormalVector(Vector3):
    def __str__(self) -> str:
        return f"vn {self.X} {-self.Y} {-self.Z}" 
    
@dataclass
class OBJIndex:
    ind: 'typing.Any'=None

    def __str__(self) -> str:
        return f"{self.ind+1}" if self.ind != None else ""

@dataclass
class OBJIndices:
    position_coordinate: OBJIndex = None
    texture_coordinate: OBJIndex = None
    normal_coordinate: OBJIndex = None

    def __str__(self) -> str:
        return "/".join(str(x) for x in [self.position_coordinate, self.texture_coordinate, self.normal_coordinate] if x != None)

        
@dataclass
class OBJFace:
    obj_indices:list[OBJIndices]

    def __str__(self) -> str:
        return "f " + " ".join(str(x) for x in self.obj_indices)

@dataclass
class OBJGroup:
    positions: list[PositionVector]
    textures: list[TextureVector]
    normals: list[NormalVector]

    faces: list[OBJFace]
    comments:list[str]

    mtl:"typing.any" = None
    name:"typing.any" = None
    def __str__(self) -> str:
        t = ""

        if self.name != None:
            t += f"g {self.name}\n"
    
        if self.mtl != None:
            t += f"usemtl {self.mtl}\n"

        if self.comments is not None:
            for c in self.comments:
                t += f"# {c}\n"

        for p in self.positions:
            t += f"{p}\n"
        for p in self.normals:
            t += f"{p}\n"
        for p in self.textures:
            t += f"{p}\n"
        for p in self.faces:
            t += f"{p}\n"

        return t

@dataclass        
class OBJFile:
    groups:list[OBJGroup]
    mtl_file:str = None

    def __str__(self) -> str:
        t = ""

        if self.mtl_file != None:
            mtl = self.mtl_file.replace("\\", "\\\\")
            t+= f"mtllib {self.mtl_file}\n"
        
        for mtl in self.groups:
            t += f"{mtl}\n"
        
        return t
    
    def assert_valid(self):
        poss = []
        uvs = []
        norms = []
        for g in self.groups:
            if g.positions != None:
                poss.extend(g.positions)
            if g.normals != None:
                norms.extend(g.positions)
            if g.textures != None:
                uvs.extend(g.positions)
        
            for f in g.faces:
                for o in f.obj_indices:

                    if o.position_coordinate.ind != None and o.position_coordinate.ind >= len(poss):
                        return False
                                            
                    if o.normal_coordinate.ind != None and o.normal_coordinate.ind >= len(norms):
                        return False

                    if o.texture_coordinate.ind != None and o.texture_coordinate.ind >= len(uvs):
                        return False
        return True
    