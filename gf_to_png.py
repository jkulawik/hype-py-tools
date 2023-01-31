from byte_utils import *

from PIL import Image
import sys
import os


def read_gf_file(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        montreal_engine_version = decode(f.read(1))  # unlike in Rayman, Hype files use 1 byte here instead of 4
        assert montreal_engine_version == 1  # seems to be the case with all files in Hype
        width = decode(f.read(4))
        height = decode(f.read(4))

        channel_count = decode(f.read(1))  # possibly could be mipmap count?
        repeat_byte_marker = f.read(1)

        palette_color_num = decode(f.read(2))
        palette_bytes_per_color = decode(f.read(1))
        unknown_1 = f.read(3)  # can be some data but is often just 0s
        unknown_2 = f.read(4)  # appears to always be either all 0s or all Fs
        print("Unknown values:")
        print(unknown_1)
        print(unknown_2)

        pixel_count = decode(f.read(4))
        montreal_encoding = decode(f.read(1))
        encoding_types = {
            5: "0",  # uses 1 channel and a palette; others use channel 0 for BG and channel 1 for RA data
            10: "565",
            11: "1555",
            12: "4444"
        }  # there might exist unknown encodings
        assert montreal_encoding in encoding_types  # probably better to throw exception

        palette = None
        if palette_bytes_per_color != 0 and palette_color_num != 0:
            print(f"Palette: {palette_color_num} colors, {palette_bytes_per_color} bytes each")
            palette = f.read(palette_bytes_per_color * palette_color_num)

        is_transparent = (montreal_encoding != 5) or (palette_bytes_per_color == 4)

        channel_size_px = width * height
        print("Pixel count:", pixel_count)
        channels = []

        print("Image data: size =", width, "x", height, "channel count =",
              channel_count, "encoding:", encoding_types[montreal_encoding])

        for j in range(channel_count):
            channel = []
            current_pixel = 0
            print('Reading channel', j)

            # TODO it appears that all channel data should be stored in a single array, in a way which bypasses mipmaps

            while current_pixel < pixel_count:
                color_value = f.read(1)
                if color_value == repeat_byte_marker:
                    actual_color_value = decode(f.read(1))
                    repeat_count = decode(f.read(1))
                    for i in range(repeat_count):
                        channel.append(actual_color_value)
                        current_pixel += 1
                else:
                    channel.append(decode(color_value))
                    current_pixel += 1
            channels.append(channel)

        if f.tell() < file_size:
            print("[!] File not fully read!")

        # FIXME the channels sometimes come out too big (because mipmaps?)
        print("Channel 0 size:", len(channels[0]))
        print("Correct channel size:", channel_size_px)
        # print(channels[0])

        implemented_types = [5, 10, 11, 12]
        if montreal_encoding in implemented_types:  # TODO change to encoding_types
            new_data = []
            if montreal_encoding == 5:  # palette
                assert palette is not None and channel_count == 1
                for pixel_value in channels[0]:
                    # They values are 'byte int' which work as ints really, but PIL whines about it, hence casting them
                    a = 255
                    r = int(palette[pixel_value * palette_bytes_per_color + 2])
                    g = int(palette[pixel_value * palette_bytes_per_color + 1])
                    b = int(palette[pixel_value * palette_bytes_per_color + 0])
                    if is_transparent:
                        a = int(palette[pixel_value * palette_bytes_per_color + 3])
                    new_pixel = (r, g, b, a)
                    new_data.append(new_pixel)
                    # print(new_pixel)
            else:
                assert len(channels) == 2
                for i in range(pixel_count):
                    max_int = int('11111111', 2)
                    # assert bg_data < max_int and ar_data < max_int  # might be redundant

                    byte1 = channels[0][i].to_bytes(1, 'little')
                    byte2 = channels[1][i].to_bytes(1, 'little')
                    data = int.from_bytes(byte1+byte2, 'little')
                    # print(bin(data))

                    a, r, g, b = 255, 0, 0, 0

                    if montreal_encoding == 10:  # 565
                        b = data & int('00000000' + '00011111', 2)
                        g = (data & int('00000111' + '11100000', 2)) >> 5
                        r = (data & int('11111000' + '00000000', 2)) >> 11

                        b = int(b/31*255)
                        g = int(g/63*255)
                        r = int(r/31*255)
                    elif montreal_encoding == 11:  # 1555
                        b = data & int('00000000'+'00011111', 2)
                        g = (data & int('00000011'+'11100000', 2)) >> 5
                        r = (data & int('01111100'+'00000000', 2)) >> 10
                        a = (data & int('10000000'+'00000000', 2)) >> 15

                        b = int(b/31*255)
                        g = int(g/31*255)
                        r = int(r/31*255)
                        a = int(a*255)
                    elif montreal_encoding == 12:  # 4444
                        b = data & int('00000000' + '00001111', 2)
                        g = (data & int('00000000' + '11110000', 2)) >> 4
                        r = (data & int('00001111' + '00000000', 2)) >> 8
                        a = (data & int('11110000' + '00000000', 2)) >> 12

                        b = int(b / 15 * 255)
                        g = int(g / 15 * 255)
                        r = int(r / 15 * 255)
                        a = int(a / 15 * 255)

                    new_pixel = (r, g, b, a)
                    # print(new_pixel)
                    new_data.append(new_pixel)

            img = Image.new('RGBA', (width, height))
            img.putdata(new_data[:channel_size_px])  # FIXME channel size bypass
            img.show()
        else:
            print("[!] Unknown encoding! Displaying channels in black and white")
            for channel in channels:
                img = Image.new('L', (width, height*2))
                img.putdata(channel)  # FIXME channel size bypass
                img.show()


if len(sys.argv) > 1:
    for arg in sys.argv[1:]:
        read_gf_file(arg)
else:
    # gf_file_path = 'output/books_nz.gf'  # palette
    gf_file_path = 'output/menu_princ.gf'  # 565
    # gf_file_path = 'output/dragon.gf'  # 4444
    # gf_file_path = 'output/FixTex/Inventor/Magics/feu.gf'  # 4444
    # gf_file_path = 'output/hypestatue/ha01a_nz.gf'  # 1555
    # gf_file_path = 'output/Zatila/pc07_1.gf'  # 565
    # gf_file_path = 'output/hypestatue/ha02.gf'  # 565
    gf_file_path = 'output/INVENTOR/Background.gf'  # 565
    read_gf_file(gf_file_path)
