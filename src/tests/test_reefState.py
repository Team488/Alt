from reefTracking.ReefState import ReefState
from tools.Constants import TEAM
def test_querying_highest():
    state = ReefState()
    state.addObservation(11,4,1)
    
    # team independent
    assert state.getHighestSlot()[:2] == (11,4)
    assert state.getHighestSlot()[2] >= 0.5

    # as this is a red tag, the result should be the same
    assert state.getHighestSlot(team=TEAM.RED)[:2] == (11,4)
    assert state.getHighestSlot(team=TEAM.RED)[2] >= 0.5

    # blue should be NONE
    assert state.getHighestSlot(team=TEAM.BLUE) == None



def test_invalid_input():
    state = ReefState()
    state.addObservation(1000,1000,1000)
    assert state.getHighestSlot() == None
