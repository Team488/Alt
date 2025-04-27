def test_Field():
    from ...Units import Types
    from ..Field import Field

    assert Field.fieldHeight.getLength() == 805  
    assert Field.fieldWidth.getLength() == 1755  

    assert Field.getDefaultLengthType() == Types.Length.Cm
    assert Field.getDefaultRotationType() == Types.Rotation.Rad