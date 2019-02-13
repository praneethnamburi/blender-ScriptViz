import functools
import pntools as my

@my.Tracker
@my.AddMethods([my.cm.properties])
class behavior:
    def __init__(self, agent, accuracy):
        self.agent = agent
        self.accuracy = accuracy
    
    def behMethod(self):
        print(self)

sausageBeh = behavior('sausage', 0.80)
wafflesBeh = behavior('waffles', 0.70)
barbBeh = behavior('barb', 0.70)