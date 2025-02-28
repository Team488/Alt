from tools.Units import Length, Rotation


def test_length_creation() -> None:
    l1 = Length.fromCm(10)
    l2 = Length.fromFeet(l1.getFeet())
    assert l1 == l2

    l3 = Length.fromCm(0.000001)
    l4 = Length.fromYards(l3.getYards())
    assert l3 == l4


def test_rotation_creation() -> None:
    l1 = Rotation.fromDegrees(180)
    l2 = Rotation.fromRadians(l1.getRadians())
    assert l1 == l2

    l3 = Rotation.fromDegrees(0.000001)
    l4 = Rotation.fromRadians(l3.getRadians())
    assert l3 == l4
