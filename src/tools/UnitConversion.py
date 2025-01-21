from collections.abc import Iterable 

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
    if isinstance(value,Iterable):
        return tuple(map(int,value))
    try:
        ret = int(value)
    except ValueError:
        print("Warning not able to convert to integer!")
        ret = value
    finally:
        return ret
