from genericpath import exists
import os

def main():
    file_name = input("input file name: ")
    if not exists(file_name):
        print("File doesn't exist")
        exit()

    with open(file_name, "rb") as f:
        addresses = []

        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        
        f.seek(0,0)

        while True:
            a = int.from_bytes(f.read(4), "big", signed=False)
            print(a)
            if a == 0:
                break
            addresses.append(a)
        

        addresses.sort()

        for i in range(len(addresses)):
            f.seek(0,0) 
            start = addresses[i]
            f.seek(start, 0)

            end = file_size
            if i+1 < len(addresses):
                end = addresses[i+1]

            num_bytes = end - start

            with open(file_name + f".{i}.tpl", "wb") as ff:
                ff.write(f.read(num_bytes)) 



            


if __name__ == "__main__":
    main()    