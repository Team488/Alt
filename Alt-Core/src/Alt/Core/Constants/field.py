from __future__ import annotations

from typing import Optional, cast

from ..Units import Conversions, Types


class Field:
    _instance: Optional[Field] = None

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = cls(17.55, 8.05, Types.Length.M)
        return cls._instance

    def __init__(
        self, width: float, height: float, units: Types.Length = Types.Length.CM
    ):
        self.width = width
        self.height = height
        self.units = units

    def getWidth(self, units: Types.Length = Types.Length.CM) -> float:
        result = Conversions.convertLength(
            self.width, fromType=self.units, toType=units
        )
        return cast(float, result)

    def getHeight(self, units: Types.Length = Types.Length.CM) -> float:
        result = Conversions.convertLength(
            self.height, fromType=self.units, toType=units
        )
        return cast(float, result)
