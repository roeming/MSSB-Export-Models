import mssbDecompress
for o in range(0x0eb1d5a8, 0x0eb1d7ff, 4):
    for i, ii in [(4, 11), (5, 10)]:
            mssbDecompress.decompress("ZZZZ.dat", f"test_decompress/{hex(o)}_{i}_{ii}.txt", o, 100, i, ii)