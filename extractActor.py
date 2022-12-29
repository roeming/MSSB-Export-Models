from tools.file_helper import *
from tools.actor import *
import open3d as o3d


file_name = "Outputs\\Dry Bones(G)\\Dry Bones(G).dat"

part = get_parts_of_file(file_name)[1]

with open(file_name, "rb") as f:
    # f.seek(part)
    
    whole_file = f.read()

file = whole_file[part:]

b = file[0:][:ACTLayout.SIZE_OF_STRUCT]

l = ACTLayout(b)
# print(str(l) + "\n")

bones = []
for i in range(l.numberOfBones):
    bone_part = file[l.pRootBone + ACTBoneLayout.SIZE_OF_STRUCT*i:][:ACTBoneLayout.SIZE_OF_STRUCT]
    new_bone = ACTBoneLayout(bone_part)

    control_part = file[new_bone.pOrientationControl:][:ACTControl.SIZE_OF_STRUCT]
    new_control = ACTControl(control_part)

    # print(str(new_bone.displayObjectID)+"\n")
    # print(str(new_control)+"\n")

    bones.append(new_bone)
    bones.append(new_control)

for b in bones:
    print(b)
    print()
# print(bones)