
class CNTFile:

    def __init__(self, directory: bytes, name: bytes, xor_key: bytes, pointer, fsize):
        self.directory = directory
        self.name = name
        self.xor_key = xor_key
        self.pointer = pointer
        self.size = fsize
