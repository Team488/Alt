from ..Units import Types, Conversions

class Field:
    def __init__(self, width : float, height : float, units : Types.Length = Types.Length.CM):
        self.width = width
        self.height = height
        self.units = units

    def getWidth(self, units: Types.Length = Types.Length.CM) -> float:
        result = Conversions.convertLength(
            self.width, fromType=self.units, toType=units
        )
        return result
    
    def getHeight(self, units: Types.Length = Types.Length.CM) -> float:
        result = Conversions.convertLength(
            self.height, fromType=self.units, toType=units
        )
        return result
