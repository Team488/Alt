from collections.abc import Iterable
from typing import Any, Union, TypeVar, Callable, Tuple
from . import Types, Measurements
from ..Constants import Field

# Type variables for better typing
NumericType = Union[float, int]
T = TypeVar('T')
ConversionFunction = Callable[[NumericType], T]


def mtoin(m: NumericType) -> float:
    """Convert meters to inches"""
    return m * 39.37


def intom(inch: NumericType) -> float:
    """Convert inches to meters"""
    return inch / 39.37


def intocm(inch: NumericType) -> float:
    """Convert inches to centimeters"""
    return inch * 2.54


def cmtoin(cm: NumericType) -> float:
    """Convert centimeters to inches"""
    return cm / 2.54


def ftocm(f: NumericType) -> float:
    """Convert feet to centimeters"""
    return f * 30.48


def cmtof(cm: NumericType) -> float:
    """Convert centimeters to feet"""
    return cm / 30.48


def ytocm(y: NumericType) -> float:
    """Convert yards to centimeters"""
    return y * 91.44


def cmtoy(cm: NumericType) -> float:
    """Convert centimeters to yards"""
    return cm / 91.44


def toint(
    value: Union[Iterable[NumericType], NumericType]
) -> Union[Tuple[int, ...], int, None]:
    """
    Convert numeric value(s) to integer
    
    Args:
        value: A single numeric value or an iterable of numeric values
        
    Returns:
        The input value(s) converted to integer, or None if conversion fails
    """
    return __convert(value, int)


def invertY(y: NumericType, lengthType : Types.Length = Types.Length.CM) -> float:
    """
    Invert the Y coordinate relative to field height
    
    Args:
        yCM: Y coordinate in units specified, or by default CM
        
    Returns:
        Inverted Y coordinate (field height - Y)
    """
    return Field.fieldHeight.getLength(lengthType) - y

def invertX(x: NumericType, lengthType : Types.Length = Types.Length.CM) -> float:
    """
    Invert the X coordinate relative to field width
    
    Args:
        xCM: X coordinate in the units specified, or by default CM
        
    Returns:
        Inverted X coordinate (field width - X)
    """
    return Field.fieldWidth.getLength(lengthType) - x


def convertLength(
    value: Union[Iterable[NumericType], NumericType],
    fromType: Types.Length,
    toType: Types.Length,
) -> Union[Tuple[float, ...], float, None]:
    """
    Convert length value(s) between different units
    
    Args:
        value: Length value(s) to convert
        fromType: Source unit type
        toType: Target unit type
        
    Returns:
        Converted value(s), or None if conversion fails
    """
    # "default case"
    if fromType == toType:
        return value

    convertLengthFunc = lambda value: Measurements.Length.convert(value, fromType, toType)
    return __convert(value, convertLengthFunc)


def convertRotation(
    value: Union[Iterable[NumericType], NumericType],
    fromType: Types.Rotation,
    toType: Types.Rotation,
) -> Union[Tuple[float, ...], float, None]:
    """
    Convert rotation value(s) between different units
    
    Args:
        value: Rotation value(s) to convert
        fromType: Source unit type (degrees or radians)
        toType: Target unit type (degrees or radians)
        
    Returns:
        Converted value(s), or None if conversion fails
    """
    convertRotFunc = lambda value: Measurements.Rotation.convert(value, fromType, toType)
    return __convert(value, convertRotFunc)


def __convert(
    value: Union[Iterable[Any], Any], 
    convertFunction: Callable[[Any], T]
) -> Union[Tuple[T, ...], T, None]:
    """
    Internal helper function to apply a conversion function to a value or iterable of values
    
    Args:
        value: Value(s) to convert
        convertFunction: Function to apply to each value
        
    Returns:
        Converted value(s), or None if conversion fails
    """
    try:
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return tuple(map(convertFunction, value))
        else:
            return convertFunction(value)
    except ValueError:
        return None
