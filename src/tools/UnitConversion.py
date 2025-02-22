from collections.abc import Iterable
from typing import Any
import tools
from tools import Units
import tools.Constants

def mtoin(m):
    return m*39.37

def intom(inch):
    return inch/39.37

def intocm(inch):
    return inch*2.54

def cmtoin(cm):
    return cm/2.54

def ftocm(f):
    return f*30.48

def cmtof(cm):
    return cm/30.48

def ytocm(y):
    return y * 91.44

def cmtoy(cm):
    return cm / 91.44


def toint(value):
    return __convert(value,int)

def invertY(yCM):
    return tools.Constants.MapConstants.fieldHeight.getCM()-yCM

def invertX(xCM):
    return tools.Constants.MapConstants.fieldWidth.getCM()-xCM

def convertLength(value, fromType : Units.LengthType, toType : Units.LengthType):
    convertLengthFunc = lambda value : Units.Length.convert(value,fromType,toType)
    return __convert(value,convertLengthFunc)

def convertRotation(value, fromType : Units.RotationType, toType : Units.RotationType):
    convertLengthFunc = lambda value : Units.Rotation.convert(value,fromType,toType)
    return __convert(value,convertLengthFunc)
    

def __convert(value : Any, convertFunction : Any):
    try:
        if isinstance(value,Iterable):
            return tuple(map(convertFunction,value))
        else:
            return convertFunction(value)
    except ValueError:
        return None