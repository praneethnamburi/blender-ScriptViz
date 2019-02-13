import functools
import pnTools as my

class addMethods:
    """"""
    def __init__(self, methodList):
        self.methodList = methodList
    def __call__(self, func):
        functools.update_wrapper(self, func)
        def wrapperFunc(*args, **kwargs):
            for method in self.methodList:
                setattr(func, method.__name__, method)
            funcOut = func(*args, **kwargs)
            return funcOut
        return wrapperFunc

@my.Tracker
@addMethods([my.cm.properties])
class behavior:
    def __init__(self, agent, accuracy):
        self.agent = agent
        self.accuracy = accuracy
    
    def behMethod(self):
        print(self)

sausageBeh = behavior('sausage', 0.80)
wafflesBeh = behavior('waffles', 0.70)
barbBeh = behavior('barb', 0.70)