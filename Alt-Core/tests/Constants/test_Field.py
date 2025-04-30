def test_Field():
    from Alt.Core.Units import Types
    from Alt.Core.Constants.Field import Field

    assert Field.fieldHeight.getLength() == 805  
    assert Field.fieldWidth.getLength() == 1755  

    assert Field.getDefaultLengthType() == Types.Length.CM
    assert Field.getDefaultRotationType() == Types.Rotation.Rad