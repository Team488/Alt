from .Types import Length, Rotation

class Transform3d:
    """
    Coordinate system:

                ^ x
                |
                |
         y <----o z

    x: forwards
    y: left
    z: out of screen (up)
    """
    def __init__(self, x : float, y : float, z : float, units : Length = Length.CM):
        self.x = x
        self.y = y
        self.z = z
        self.units = units

    def add(self, other : "Transform3d") -> "Transform3d":
        return Transform3d(self.x + other.x, self.y + other.y, self.z + other.z)

    def subtract(self, other : "Transform3d") -> "Transform3d":
        return self.add(other.negate())

    def negate(self) -> "Transform3d":
        return Transform3d(-self.x, -self.y, -self.z)

class Pose3d:
    """
    Coordinate system:

                ^ x
                |
                |
         y <----o z

    x: forwards
    y: left
    z: out of screen (up)
    """
    def __init__(self, transform : Transform3d, units : Length = Length.CM):
        self.transform = transform
        self.units = units
        # TODO rotation

class Pose2d:
    """
    Coordinate system:

                ^ x
                |
                |
         y <----o 

    x: forwards
    y: left
    yaw: rotation counter clockwise from x -> y
    """
    def __init__(self, x : float, y : float, yaw : float, lengthUnit : Length = Length.CM, rotationUnit : Rotation = Rotation.Rad):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.lengthUnit = lengthUnit
        self.rotrotationUnit = rotationUnit