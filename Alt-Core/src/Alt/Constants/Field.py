from enum import Enum
from ..Units import Types, Conversions

class Field(Enum):
    @staticmethod
    def getDefaultLengthType():
        return Types.Length.CM

    @staticmethod
    def getDefaultRotationType():
        return Types.Rotation.Deg

    fieldWidth = 1755  # 54' 3" in cm
    fieldHeight = 805  # 26' 3" in cm

    def _getCM(self) -> float:
        return self.value

    def getLength(self, lengthType: Types.Length = Types.Length.CM) -> float:
        result = Conversions.convertLength(
            self._getCM(), fromType=self.getDefaultLengthType(), toType=lengthType
        )
        return result
