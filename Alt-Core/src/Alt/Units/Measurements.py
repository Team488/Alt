import math
from dataclasses import dataclass
from Alt.Units import Types, Conversions

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

    def __init__(self) -> None:
        """
        Prevents direct instantiation of the class.
        Use static constructors like `fromCm`, `fromIn`, etc., to create instances.
        """
        raise AttributeError("Use the Static constructors to create a length")

    def __repr__(self) -> str:
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
        obj.__in = Conversions.cmtoin(centimeters)
        return obj

    @classmethod
    def fromM(cls, meters: float) -> "Length":
        """
        Creates a Length instance from meters.
        """
        obj = cls.__new__(cls)
        obj.__cm = meters * 100
        obj.__in = Conversions.mtoin(meters)
        return obj

    @classmethod
    def fromIn(cls, inches: float) -> "Length":
        """
        Creates a Length instance from inches.
        """
        obj = cls.__new__(cls)
        obj.__cm = Conversions.intocm(inches)
        obj.__in = inches
        return obj

    @classmethod
    def fromFeet(cls, feet: float) -> "Length":
        """
        Creates a Length instance from feet.
        """
        obj = cls.__new__(cls)
        obj.__cm = Conversions.ftocm(feet)
        obj.__in = feet * 12
        return obj

    @classmethod
    def fromYards(cls, yards: float) -> "Length":
        """
        Creates a Length instance from yards.
        """
        obj = cls.__new__(cls)
        obj.__cm = Conversions.ytocm(yards)
        obj.__in = yards * 36
        return obj

    @classmethod
    def fromLengthType(cls, length: float, lengthType: Types.Length) -> "Length":
        if lengthType == Types.Length.CM:
            return cls.fromCm(length)
        if lengthType == Types.Length.IN:
            return cls.fromIn(length)
        if lengthType == Types.Length.M:
            return cls.fromM(length)
        if lengthType == Types.Length.YARD:
            return cls.fromYards(length)
        if lengthType == Types.Length.FT:
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

    def getAsLengthType(self, lengthType: Types.Length) -> float:
        """
        Returns the length in the desired unit mode.

        Args:
        - unitmode (UnitMode): The unit mode for length.

        Returns:
        - float: The length in the requested unit.
        """
        if lengthType == Types.Length.CM:
            return self.getCm()
        if lengthType == Types.Length.IN:
            return self.getIn()
        if lengthType == Types.Length.M:
            return self.getM()
        if lengthType == Types.Length.YARD:
            return self.getYards()
        if lengthType == Types.Length.FT:
            return self.getFeet()

    @classmethod
    def convert(cls, value: float, fromL: Types.Length, toL: Types.Length) -> float:
        return cls.fromLengthType(value, fromL).getAsLengthType(toL)


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

    def __init__(self) -> None:
        """
        Prevents direct instantiation of the class.
        Use static constructors like `fromDegrees` or `fromRadians` to create instances.
        """
        raise AttributeError("Use the Static constructors to create a rotation")

    def __repr__(self) -> str:
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

    @classmethod
    def fromRotationType(cls, length: float, rotationType: Types.Rotation) -> "Rotation":
        if rotationType == Types.Rotation.Rad:
            return cls.fromRadians(length)
        if rotationType == Types.Rotation.Deg:
            return cls.fromDegrees(length)

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

    def getAsRotationType(self, rotationType: Types.Rotation) -> float:
        """
        Returns the length in the desired rotationType.

        Args:
        - rotationType (RotationType): The rotationType for rotation.

        Returns:
        - float: The rotation in the requested unit.
        """
        if rotationType == Types.Rotation.Rad:
            return self.getRadians()
        if rotationType == Types.Rotation.Deg:
            return self.getDegrees()

    @classmethod
    def convert(cls, value: float, fromR: Types.Rotation, toR: Types.Rotation) -> float:
        return cls.fromRotationType(value, fromR).getAsRotationType(toR)
