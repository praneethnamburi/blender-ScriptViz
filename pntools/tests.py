"""
Run tests on pntools
"""

import os
import sys
import numpy as np

from blinker import signal

DEV_ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
if DEV_ROOT not in sys.path:
    sys.path.append(DEV_ROOT)

import pntools as pn

def test_broadcasting():
    """Expected output: I 2 received 6"""
    def broadcast_properties(src_class):
        src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property)}
        for p_name, p in src_properties.items():
            if p.fset is not None:
                setattr(src_class, p_name, pn.broadcast_property(p, pn.handler_id(src_class, p_name, 'post'), 'post'))
        return src_class

    @broadcast_properties
    class DummyClass:
        def __init__(self, some_number):
            self.number = some_number
    
        @property
        def num(self):
            return self.number

        @num.setter
        def num(self, new_number):
            self.number = new_number

    s = signal(pn.handler_id(DummyClass, 'num', 'post'))
    @s.connect
    def receiver2(some_thing):
        print('I 2 received '+str(some_thing.number))

    a = DummyClass(3)

    a.num = 6

    s.disconnect(receiver2)
    a.num = 7


def test_broadcasting2():
    """
    Basic test for the BroadcastProperties class
    Expected output:
    Number before change : 3
    Number after change : 5
    """
    @pn.BroadcastProperties('ALL', 'post')
    @pn.BroadcastProperties('ALL', 'pre')
    class MClass:
        def __init__(self, number):
            self._number = number

        @property
        def num(self):
            return self._number
        
        @num.setter
        def num(self, new_number):
            self._number = new_number

    def fire_before_change(self):
        print('Number before change : ' + str(self.num))

    def fire_after_change(self):
        print('Number after change : ' + str(self.num))
    
    signal(pn.handler_id(MClass, 'num', 'pre')).connect(fire_before_change)
    signal(pn.handler_id(MClass, 'num', 'post')).connect(fire_after_change)

    x = MClass(3)
    x.num = 5


def testTracker():
    """
    Also demonstrates how to use the tracker
    Expected output:
        Testing pntools.Tracker:
        []
        [<class '__main__.testTracker.<locals>.testClass'>]
        [<class '__main__.testTracker.<locals>.testClass'>, <class '__main__.testTracker.<locals>.testClass2'>]
        [<__main__.testTracker.<locals>.testClass object at 0x00000226323621D0>, <__main__.testTracker.<locals>.testClass object at 0x0000022632362208>]
        []
        2
        12
        <pntools.Tracker object at 0x000002263234D240> <class '__main__.testTracker.<locals>.testClass'>
        <pntools.Tracker object at 0x0000022632362198> <class '__main__.testTracker.<locals>.testClass2'>
        [101, 102, 103]
        sausage accuracy:  0.8  waffles accuracy:  0.7
        mean, std of accuracy:  (0.7333333333333334, 0.047140452079103216)
        sausage is the best Monkey!
        0.8
        barb
        0.015269871000000101
    Note that the memory locations and execution time (last number) will be different in your printout.
    """
    #pylint: disable=protected-access, no-member
    print('Testing pntools.Tracker:')
    print(pn.Tracker._tracked)

    @pn.Tracker
    class testClass:
        def __init__(self, myAttr):
            self.attr = myAttr

    tmp1 = testClass(11)
    tmp2 = testClass(12)
    tmp3 = testClass(13)

    del testClass[tmp1] #pylint: disable=unsupported-delete-operation
    del tmp1

    print(pn.Tracker._tracked)

    @pn.Tracker
    class testClass2:
        def __init__(self, myAttr):
            self.attr2 = myAttr

    print(pn.Tracker._tracked)
    
    print(testClass.all) 
    print(testClass2.all)
    print(testClass.n)
    print(tmp2.attr)
    
    # test if wrapper was updated
    import inspect
    print(testClass, inspect.unwrap(testClass))
    print(testClass2, inspect.unwrap(testClass2))

    # extend the tracker to do operations on all objects created by that class!
    # for example, group statistics of all images
    # Just don't override the __new__, __init__ or __call__ methods
    class extendedTracker(pn.Tracker):
        """"""
        def extMethod(self):
            print([k.attr for k in self.all])
    
    @extendedTracker
    class extClass: 
        def __init__(self, myAttr):
            self.attr = myAttr

    ext1 = extClass(101)
    ext2 = extClass(102)
    ext3 = extClass(103)
    extClass.extMethod()

    class behaviorMetrics(pn.Tracker):
        @property
        def accuracy(self):
            allAcc = [k.accuracy for k in self.all]
            return (np.mean(allAcc), np.std(allAcc))
        def sophieSays(self):
            bestAgent = self.all[np.argmax([k.accuracy for k in self.all])].agent
            print(bestAgent, 'is the best Monkey!')

    @behaviorMetrics
    class behavior:
        def __init__(self, agent, accuracy):
            self.agent = agent
            self.accuracy = accuracy
    
    sausageBeh = behavior('sausage', 0.80)
    wafflesBeh = behavior('waffles', 0.70)
    barbBeh = behavior('barb', 0.70)
    
    print('sausage accuracy: ', sausageBeh.accuracy, ' waffles accuracy: ', wafflesBeh.accuracy)
    print('mean, std of accuracy: ', behavior.accuracy)
    behavior.sophieSays()
    print(behavior.dictAccess('agent')['sausage'].accuracy) # what is sausage's accuracy?
    print(behavior.dictAccess('accuracy')[0.7].agent) # who had an accuracy of 0.7?

def testTrackerQuery():
    """
    Debug and monitor the res variable to check if results are as expected.
    Expected output:
        Testing pntools.Tracker.query and pntools.AddMethods
        ('accuracy', <class 'float'>, ())
        ('agent', <class 'str'>, ())
        ('properties', <class 'method'>, ())
        ('weight', <class 'int'>, ())
        testTrackerQuery finished.
        0.00497705599999998
    # Note that the last number (execution time) can be different.
    """
    print('Testing pntools.Tracker.query and pntools.AddMethods')

    @pn.Tracker
    @pn.AddMethods([pn.properties])
    class behavior:
        def __init__(self, agent, accuracy, weight):
            self.agent = agent
            self.accuracy = accuracy
            self.weight = weight

    behavior('sausage', 0.80, 312)
    behavior('waffles', 0.70, 350)
    behavior('barb', 0.70, 367)
    behavior('rafiki', 0.3, 392)
    behavior('setta', 0.4, 337)
    behavior('aj', 0.6, 401)

    # pylint: disable=no-member #pylint won't catch all functionality added through decorators
    res = behavior.query("(agent == 'barb' and 'ar' in agent or agent == 'sausage')")

    # for complicated queries with methods (e.g. len), either use keys, or prefix k. to all the keys
    res = behavior.query("len(agent) > 4  and accuracy >= 0.3", keys=['agent', 'accuracy'])
    res[0].properties() # testing pn.AddMethods
    res = behavior.query("len(k.agent) > 4 and k.accuracy >= 0.3", keys=[])
    print('testTrackerQuery finished.')

if __name__ == '__main__':
    pn.Time(testTracker)()
    pn.Time(testTrackerQuery)()
