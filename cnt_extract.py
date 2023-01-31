# based on https://github.com/szymski/Rayman2Lib/blob/master/csharp_tools/Rayman2Lib/CNTFile.cs

from cnt_file import CNTFile
import os
from byte_utils import decode, xor_bytes

files = ["Vignette.cnt", "Textures.cnt"]
cnt_file_path = files[0]

output_dir = "output"

max_4B_value = 4294967295  # same as FFFFFFF in hex


with open(cnt_file_path, 'rb') as f:
    dir_count = decode(f.read(4))
    file_count = decode(f.read(4))
    signature = decode(f.read(2))
    assert signature == 257  # Check if this is a valid CNT file
    xor_key = f.read(1)
    print("Directory count:", dir_count)
    print("File count:", file_count)

    # Read directories
    print("[*] Reading directory names...")
    directories = []
    for i in range(dir_count):
        dir_name_size = decode(f.read(4))
        dir_name = b""
        for j in range(dir_name_size):
            dir_name += xor_bytes(xor_key, f.read(1))
        directories.append(dir_name)
        print("[dir]", dir_name, "id:", i)

    version = decode(f.read(1))
    print("CNT version:", version)
    print("Note: version seems to relate to file types. These vary between games.")

    test_files = []
    print("[*] Reading file data...")
    cnt_files = []
    for i in range(file_count):
        dir_index = decode(f.read(4))
        file_name_size = decode(f.read(4))

        file_name = b""
        for j in range(file_name_size):
            file_name += xor_bytes(xor_key, f.read(1))

        file_xor_key = f.read(4)
        file_checksum = decode(f.read(4))
        file_pointer = decode(f.read(4))
        file_size = decode(f.read(4))
        # print("[file]", file_name, "dir index:", dir_index)
        print(f"[file] {file_name}, dir index: {dir_index}")
        if dir_index == max_4B_value:
            dir_name = b""  # root folder
        else:
            dir_name = directories[dir_index]
        dir_name = dir_name.replace(b"\\", b"/")
        cnt_file = CNTFile(dir_name, file_name, file_xor_key, file_pointer, file_size)
        cnt_files.append(cnt_file)

        # TODO debug / search functionality
        if file_name == b'Background.gf':
            test_files.append(cnt_file)
        # if dir_name == b'gladiateur':
        #     test_files.append(cnt_file)

    print("[*] Reading files...")
    if len(test_files) == 0:
        print("[!] No files to extract!")
    for file in test_files:  # TODO change to export all files
        print(f"[file] {file.name}, size: {file.size}, XOR key: {file.xor_key}")
        f.seek(file.pointer)
        file_bytes_raw = f.read(file.size)
        file_bytes = b''
        for j in range(file.size):
            current_byte = file_bytes_raw[j].to_bytes(length=1, byteorder='little')  # python reads single bytes as ints
            current_xor_key_byte = file.xor_key[j % 4].to_bytes(length=1, byteorder='little')
            # print("[i] file bytes to xor:", current_xor_key_byte, current_byte)
            file_bytes += xor_bytes(current_xor_key_byte, current_byte)

        dir_str = file.directory.decode()
        file_name = file.name.decode()
        full_dir_path = os.path.join(output_dir, dir_str)
        file_path = os.path.join(full_dir_path, file_name)
        print(full_dir_path)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.exists(full_dir_path):
            os.makedirs(full_dir_path)
        with open(file_path, 'wb') as o:
            o.write(file_bytes)
