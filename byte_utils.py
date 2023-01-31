

def decode(data: bytes):
    return int.from_bytes(data, byteorder='little')


def xor_bytes(b1: bytes, b2: bytes):
    assert len(b1) == len(b2)
    return bytes(a ^ b for a, b in zip(b1, b2))


def extract_bits(_input: int, bit_count: int, offset: int):
    assert bit_count in [1, 4, 5, 6]  # available masks

    b = _input.to_bytes(1, 'little')
    mask = None
    if bit_count == 1:
        mask = int('', 2)


