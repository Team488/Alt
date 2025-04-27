def test_get_proxy_requests():
    from functools import partial
    from ...Core.Agents import Agent
    from ..AgentConstants import ProxyType

    class TestAgent(Agent):
        @classmethod
        def requestProxies():
            super().addProxyRequest("test1", ProxyType.STREAM)
            super().addProxyRequest("test1", ProxyType.LOG)
            super().addProxyRequest("test2", ProxyType.LOG)
            super().addProxyRequest("test3", ProxyType.LOG)

    partialTestAgent = partial(TestAgent)

    assert ProxyType.getProxyRequests(TestAgent) == {"test1": ProxyType.LOG, "test2": ProxyType.LOG, "test3" : ProxyType.LOG}
    assert ProxyType.getProxyRequests(partialTestAgent) == {"test1": ProxyType.LOG, "test2": ProxyType.LOG, "test3" : ProxyType.LOG}
