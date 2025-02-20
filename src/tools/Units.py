from dataclasses import dataclass
from enum import Enum
import math
from tools import UnitConversion

class LengthType(Enum):
    """
    Enum for representing length types.
    Options:
    - CM: Centimeters
    - IN: Inches
    """
    CM = "cm"
    IN = "in"
    FT = "feet"
    M = "meter"
    YARD = "yard"

class RotationType(Enum):
    """
    Enum for representing rotation types.
    Options:
    - Deg: Degrees
    - Rad: Radians
    """
    Deg = "deg"
    Rad = "rad"

class UnitMode:
    """
    Represents a unit mode for length and rotation.
    Attributes:
    - lengthType (LengthType): The unit type for length (CM or IN).
    - rotationType (RotationType): The unit type for rotation (Deg or Rad).
    """
    def __init__(self, lengthType: LengthType, rotationType: RotationType):
        """
        Initializes a UnitMode instance.

        Args:
        - lengthType (LengthType): The desired length unit type.
        - rotationType (RotationType): The desired rotation unit type.
        """
        self.lengthType = lengthType
        self.rotationType = rotationType


@dataclass
class Length:
    """
    Represents a length with internal storage in centimeters and inches.

    Attributes:
    - __cm (float): Length in centimeters (private).
    - __in (float): Length in inches (private).
    """
    __cm: float
    __in: float

    def __init__(self):
        """
        Prevents direct instantiation of the class.
        Use static constructors like `fromCm`, `fromIn`, etc., to create instances.
        """
        raise AttributeError("Use the Static constructors to create a length")
    
    def __repr__(self):
        """
        Provides a string representation of the Length instance.
        Returns:
            str: The length in both centimeters and inches.
        """
        return f"Length: {self.__cm:.2f} Cm / {self.__in:.2f} In"

    def __eq__(self, value):
        """
        Checks equality between two Length instances based on their inch value.
        Args:
            value (Length): The other Length instance to compare with.
        Returns:
            bool: True if both instances represent the same length, False otherwise.
        """
        if isinstance(value, Length):
            return abs(self.__in - value.__in) < 1e-6
        return False

    
    @classmethod
    def fromCm(cls, centimeters: float) -> "Length":
        """
        Creates a Length instance from centimeters.
        """
        obj = cls.__new__(cls)
        obj.__cm = centimeters
        obj.__in = UnitConversion.cmtoin(centimeters)
        return obj

    @classmethod
    def fromM(cls, meters: float) -> "Length":
        """
        Creates a Length instance from meters.
        """
        obj = cls.__new__(cls)
        obj.__cm = meters * 100
        obj.__in = UnitConversion.mtoin(meters)
        return obj

    @classmethod
    def fromIn(cls, inches: float) -> "Length":
        """
        Creates a Length instance from inches.
        """
        obj = cls.__new__(cls)
        obj.__cm = UnitConversion.intocm(inches)
        obj.__in = inches
        return obj

    @classmethod
    def fromFeet(cls, feet: float) -> "Length":
        """
        Creates a Length instance from feet.
        """
        obj = cls.__new__(cls)
        obj.__cm = UnitConversion.ftocm(feet)
        obj.__in = feet * 12
        return obj

    @classmethod
    def fromYards(cls, yards: float) -> "Length":
        """
        Creates a Length instance from yards.
        """
        obj = cls.__new__(cls)
        obj.__cm = UnitConversion.ytocm(yards)
        obj.__in = yards * 36
        return obj
    
    @classmethod
    def fromLengthType(cls, length : float, lengthType: LengthType) -> "Length":
        if lengthType == LengthType.CM:
            return cls.fromCm(length)
        if lengthType == LengthType.IN:
            return cls.fromIn(length)
        if lengthType == LengthType.M:
            return cls.fromM(length)
        if lengthType == LengthType.YARD:
            return cls.fromYards(length)
        if lengthType == LengthType.FT:
            return cls.fromFeet(length)

    def getCm(self) -> float:
        """
        Returns the length in centimeters.
        """
        return self.__cm

    def getM(self) -> float:
        """
        Returns the length in meters.
        """
        return self.__cm / 100

    def getIn(self) -> float:
        """
        Returns the length in inches.
        """
        return self.__in

    def getFeet(self) -> float:
        """
        Returns the length in feet.
        """
        return self.__in / 12

    def getYards(self) -> float:
        """
        Returns the length in yards.
        """
        return self.__in / 36

    def getAsLengthType(self, lengthType: LengthType) -> float:
        """
        Returns the length in the desired unit mode.
        
        Args:
        - unitmode (UnitMode): The unit mode for length.

        Returns:
        - float: The length in the requested unit.
        """
        if lengthType == LengthType.CM:
            return self.getCm()
        if lengthType == LengthType.IN:
            return self.getIn()
        if lengthType == LengthType.M:
            return self.getIn()
        if lengthType == LengthType.YARD:
            return self.getYards()
        if lengthType == LengthType.FT:
            return self.getFeet()
    @classmethod    
    def convert(cls, value : float, fromL : LengthType, toL : LengthType) -> float:
        return cls.fromLengthType(value,fromL).getAsLengthType(toL)


@dataclass
class Rotation:
    """
    Represents a rotation with internal storage in degrees and radians.

    Attributes:
    - __deg (float): Rotation in degrees (private).
    - __rad (float): Rotation in radians (private).
    """
    __deg: float
    __rad: float

    def __init__(self):
        """
        Prevents direct instantiation of the class.
        Use static constructors like `fromDegrees` or `fromRadians` to create instances.
        """
        raise AttributeError("Use the Static constructors to create a rotation")

    def __repr__(self):
        """
        Provides a string representation of the Rotation instance.
        Returns:
            str: The rotation in both degrees and radians.
        """
        return f"Rotation: {self.__deg:.2f} Degrees / {self.__rad:.2f} Radians"

    def __eq__(self, value):
        """
        Checks equality between two Rotation instances based on their inch value.
        Args:
            value (Rotation): The other Length instance to compare with.
        Returns:
            bool: True if both instances represent the same rotation, False otherwise.
        """
        if isinstance(value, Rotation):
            return abs(self.__deg - value.__deg) < 1e-6
        return False

    
    @classmethod
    def fromDegrees(cls, degrees: float):
        """
        Creates a Rotation instance from degrees.
        """
        obj = cls.__new__(cls)
        obj.__deg = degrees
        obj.__rad = math.radians(degrees)
        return obj

    @classmethod
    def fromRadians(cls, radians: float):
        """
        Creates a Rotation instance from radians.
        """
        obj = cls.__new__(cls)
        obj.__deg = math.degrees(radians)
        obj.__rad = radians
        return obj

    def getDegrees(self) -> float:
        """
        Returns the rotation in degrees.
        """
        return self.__deg

    def getRadians(self) -> float:
        """
        Returns the rotation in radians.
        """
        return self.__rad

    def getUnitMode(self, unitMode: UnitMode):
        """
        Returns the rotation in the desired unit mode.

        Args:
        - unitMode (UnitMode): The unit mode for rotation.

        Returns:
        - float: The rotation in the requested unit.
        """
        if unitMode.rotationType == RotationType.Deg:
            return self.getDegrees()
        return self.getRadians()
