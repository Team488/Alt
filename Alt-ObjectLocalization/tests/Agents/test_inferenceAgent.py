from Alt.Core.TestUtils import AgentTests

def test_inferenceAgent():
    from Alt.ObjectLocalization.Agents.InferenceAgent import InferenceAgent
    from Alt.Cameras.Captures.FakeCapture import FakeCamera

    # TODO make mock inferennce backend...

    # agent = InferenceAgent.bind(FakeCamera())