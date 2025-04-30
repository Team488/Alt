from enum import Enum

class Length(Enum):
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


class Rotation(Enum):
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

    def __init__(self, lengthType: Length, rotationType: Rotation) -> None:
        """
        Initializes a UnitMode instance.

        Args:
        - lengthType (LengthType): The desired length unit type.
        - rotationType (RotationType): The desired rotation unit type.
        """
        self.lengthType = lengthType
        self.rotationType = rotationType
