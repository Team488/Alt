import struct
def getPose2dFromBytes(bytes : bytes) -> tuple[float,float,float]:
    """Returns pose 2d in form of x,y,rot. Units depend on what was packed"""
    return struct.unpack('ddd',bytes)

def getTranslation3dFromBytes(bytes : bytes) -> tuple[tuple[float,float,float],tuple[float,float,float,float]]:
    """ Returns a translation3d (x,y,z) and a rotation3d (w,x,y,z) as a tuple"""
    ret = struct.unpack('ddddddd',bytes)
    translation = ret[:3]
    rotation = ret[3:]
    return (translation, rotation)
