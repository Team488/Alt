import struct
def getPose2dFromBytes(bytes) -> tuple[float,float,float]:
    return struct.unpack('ddd',bytes)