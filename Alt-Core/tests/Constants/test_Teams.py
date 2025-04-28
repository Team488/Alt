def test_Teams():
    from Alt.Constants.Teams import TEAM
    # you can never be too sure
    assert TEAM.BLUE is TEAM.BLUE
    assert TEAM.RED is TEAM.RED