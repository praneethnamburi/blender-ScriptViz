import functools
import pntools as my

@my.Tracker
@my.AddMethods([my.cm.properties])
class behavior:
    def __init__(self, agent, accuracy, weight):
        self.agent = agent
        self.accuracy = accuracy
    
    def behMethod(self):
        print(self)

sausageBeh = behavior('sausage', 0.80, 312)
wafflesBeh = behavior('waffles', 0.70, 350)
barbBeh = behavior('barb', 0.70, 367)
rafikibeh = behavior('rafiki', 0.3, 392)
settabeh = behavior('setta', 0.4, 337)
ajbeh = behavior('aj', 0.6, 401)

# tmp1 = behavior.query("(agent == 'barb' and 'ar' in agent or agent == 'sausage')")
tmp1 = behavior.query()
behavior.query("k.accuracy > 0.6", keys=[])

# for more complicated queries, either use keys, or append 
behavior.query("len(agent) > 4  and accuracy >= 0.3", keys=['agent', 'accuracy'])
behavior.query("len(k.agent) > 4 and k.accuracy >= 0.3", keys=[])
a = 1