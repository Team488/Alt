from abc import abstractmethod
from .Agent import Agent
from functools import partial

class BindableAgent(Agent):
    """ When an Agent requires extra keyword arguments, the Neo class cannot just create an instance of it due to it needing arguments.
        To fix this, we use the functools partial method. You can imagine it pre-binding the args of the agent, before it gets created.
        This way, when the agent needs to be created, the arguments will be stored inside, and Neo can create an instance.
    """
    @abstractmethod
    @classmethod
    def bind(cls, *args, **kwargs) -> partial:
        """ To make it clearer what arguments an agent needs, please override this bind method and specify the same input arguments as the agents __init__
            At the moment, this is the only way to change the static method signature of bind, so people know what arguments to provide. 
            In the method body, you can just call cls.__getBindedAgent() with the input arguments.

            Example:
            ``` python
            class bindable(Agent, BindableAgent): 
                # overriding the bind method to make the static method signature clear
                @classmethod
                def bind(arg1 : str, arg2 : int, ....):
                    # you can use keyword or positional arguments, but it should match your constructor
                    return cls.__getBindedAgent(arg1, arg2=arg2, ....)

                def __init__(arg1 : str, arg2 : int, ....):
                    # same signature as above, ensures that when neo gets the bound agent, it needs no extra arguments
                    # init things....
            ```
        """
        pass

    @classmethod
    def __getBindedAgent(cls, *args, **kwargs) -> partial:
        return partial(cls, *args, **kwargs)