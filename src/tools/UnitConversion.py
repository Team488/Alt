from collections.abc import Iterable
from typing import Any, Union
import tools
from tools import Units
import tools.Constants


def mtoin(m: Union[float, int]) -> float:
    return m * 39.37


def intom(inch: Union[float, int]) -> float:
    return inch / 39.37


def intocm(inch: Union[float, int]) -> float:
    return inch * 2.54


def cmtoin(cm: Union[float, int]) -> float:
    return cm / 2.54


def ftocm(f: Union[float, int]) -> float:
    return f * 30.48


def cmtof(cm: Union[float, int]) -> float:
    return cm / 30.48


def ytocm(y: Union[float, int]) -> float:
    return y * 91.44


def cmtoy(cm: Union[float, int]) -> float:
    return cm / 91.44


def toint(
    value: Union[Iterable[Union[float, int]], float]
) -> Union[tuple[int], int, None]:
    return __convert(value, int)


def invertY(yCM: Union[float, int]) -> float:
    return tools.Constants.MapConstants.fieldHeight.getCM() - yCM


def invertX(xCM: Union[float, int]) -> float:
    return tools.Constants.MapConstants.fieldWidth.getCM() - xCM


def convertLength(
    value: Union[Iterable[Union[float, int]], float],
    fromType: Units.LengthType,
    toType: Units.LengthType,
) -> Union[tuple[float], float, None]:
    convertLengthFunc = lambda value: Units.Length.convert(value, fromType, toType)
    return __convert(value, convertLengthFunc)


def convertRotation(
    value: Union[Iterable[Union[float, int]], float],
    fromType: Units.RotationType,
    toType: Units.RotationType,
) -> Union[tuple[float], float, None]:
    convertLengthFunc = lambda value: Units.Rotation.convert(value, fromType, toType)
    return __convert(value, convertLengthFunc)


def __convert(value: Any, convertFunction: Any) -> Union[tuple, Any, None]:
    try:
        if isinstance(value, Iterable):
            return tuple(map(convertFunction, value))
        else:
            return convertFunction(value)
    except ValueError:
        return None
