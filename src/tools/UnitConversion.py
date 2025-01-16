from collections.abc import Iterable 
import math
def degtorad(deg):
    return deg*math.pi/180

def radtodeg(rad):
    return rad*180/math.pi

def mtoin(m):
    return m*39.37

def intom(inch):
    return inch/39.37

def toint(value):
    if isinstance(value,Iterable):
        return tuple(map(int,value))
    try:
        ret = int(value)
    except ValueError:
        print("Warning not able to convert to integer!")
        ret = value
    finally:
        return ret
