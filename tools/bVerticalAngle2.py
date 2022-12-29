angle_bytes =  [ 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x64, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x64, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x65, 0x00, 0x00, 0x00, 0x66, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5e, 0x00, 0x00, 0x00, 0x5f, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66, 0x00, 0x00, 0x00, 0x67, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x11, 0x11, 0x10, 0x01, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x55, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66, 0x00, 0x00, 0x00, 0x67, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x64, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5f, 0x00, 0x00, 0x00, 0x64, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x68, 0x00, 0x00, 0x00, 0x69, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x00, 0x3c, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46, 0x00, 0x00, 0x00, 0x4b, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x57, 0x00, 0x00, 0x00, 0x5a, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x46, 0x00, 0x00, 0x00, 0x46, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x50, 0x00, 0x00, 0x00, 0x55, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x69, 0x00, 0x00, 0x00, 0x6e, 0x00, 0x11, 0x11, 0x10, 0x00, 0x11, 0x11, 0x10, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x32, 0x00, 0x00, 0x00, 0x32, 0x00, 0x11, 0x01, 0x10, 0x00, 0x11, 0x01, 0x10, 0x00, 0x00, 0x00, 0x00 ]
def int_from_bytes(a):
    return int.from_bytes(a, "big", signed=True)

values = [int_from_bytes(angle_bytes[x*4:][:4]) for x in range(len(angle_bytes)//4)]

formatted_values = [values[x*5:][:5] for x in range(19)]

enums = [(0x0	, "SourSlap"),
         (0x1	, "NiceSlap"),
         (0x2	, "PerfectSlap"),
         (0x3	, "SourCharge"),
         (0x4	, "NiceCharge"),
         (0x5	, "PerfectCharge"),
         (0x6	, "SourChangeUpSlap"),
         (0x7	, "NiceChangeUpSlap"),
         (0x8	, "PerfectChangeUpSlap"),
         (0x9	, "SourChangeUpCharge"),
         (0xa	, "NiceChangeUpCharge"),
         (0xb	, "PerfectChangeUpCharge"),
         (0xc	, "PerfectPitchSourSlap"),
         (0xd	, "PerfectPitchNiceSlap"),
         (0xe	, "PerfectPitchPerfectSlap"),
         (0xf	, "PerfectPitchSourCharge"),
         (0x10  , "PerfectPitchNiceCharge"),
         (0x11  , "PerfectPitchPerfectCharge")]
for i, i_str in enums:
    for upDown, upDown_str in [(0, "Neutral"), (1, "Up"), (2, "Down")]:
        these_values = formatted_values[i]
        print(f"{i_str}, {upDown_str}: {these_values}")
        for ox, ox_str in [(3, "0x7a=False"),(2, "0x7a=True ")]:
            iVar5 = 0

            uVar4 = these_values[ox]
            uVar6 = these_values[4]
            uVar5 = uVar4 & 0xf000000        
            if (uVar5 == 0):
                uVar16 = uVar4 & 0xf
                if (uVar16 != 0):
                    iVar5 = 2
                    if (uVar16 == 2):
                        if (upDown == 2):
                            iVar5 = 0
                            uVar6 = 2
                    elif ((uVar16 == 3) and (upDown == 1)):
                        iVar5 = 0
                        uVar6 = 2
            else:
                iVar5 = 1
                if (uVar5 == 0x2000000):
                    if (upDown == 2):
                        iVar5 = 0
                        uVar6 = 2
                elif ((uVar5 == 0x3000000) and (upDown == 1)):
                    iVar5 = 0
                    uVar6 = 2
            if (iVar5 == 0):
                if ((uVar4 & 0x1e0) == 0):
                    # local_28 = 0
                    print("Zeroes Range0")
                if ((uVar4 & 0xf0) == 0):
                    # local_27 = 0
                    print("Zeroes Range1")
                if ((uVar4 & 0x78) == 0):
                    # local_26 = 0
                    print("Zeroes Range2")
                if ((uVar4 & 0x3c) == 0):
                    # local_25 = 0
                    print("Zeroes Range3")
                if ((uVar4 & 0x1e) == 0):
                    # local_24 = 0
                    print("Zeroes Range4")
                if (upDown == 2):
                    local_24 += local_28
                    local_28 = 0
                    pass
                elif (upDown == 1):
                    cVar2 = local_24 + local_28
                    local_24 = 0
                    local_28 = local_25 + cVar2
                    local_25 = 0
                    pass

            print(f"{iVar5=}, {uVar6=}")
            print()
