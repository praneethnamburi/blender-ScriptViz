import functools
import numpy as np
import pntools as my

def testTracker():
    """
    Also demonstrates how to use the tracker
    Expected output:
        Testing pntools.Tracker:
        []
        [<class '__main__.testTracker.<locals>.testClass'>]
        [<class '__main__.testTracker.<locals>.testClass'>, <class '__main__.testTracker.<locals>.testClass2'>]
        [<list of two testClass objects>]
        []
        2
        12
        <pntools.Tracker object at 0x0000022C51F41710> <class '__main__.testTracker.<locals>.testClass'>
        <pntools.Tracker object at 0x0000022C51F9CEB8> <class '__main__.testTracker.<locals>.testClass2'>
        [101, 102, 103]
        monkey1 accuracy:  0.9  monkey2 accuracy:  0.7
        mean, std of accuracy:  (0.8, 0.10000000000000003)
        sausage is the best Monkey!
        0.8
        barb
    Note that the memory locations will be different in your printout.
    """
    #pylint: disable=protected-access, no-member
    print('Testing pntools.Tracker:')
    print(my.Tracker.tracked)

    @my.Tracker
    class testClass:
        def __init__(self, myAttr):
            self.attr = myAttr

    tmp1 = testClass(11)
    tmp2 = testClass(12)
    tmp3 = testClass(13)

    del testClass[tmp1] #pylint: disable=unsupported-delete-operation
    del tmp1

    print(my.Tracker.tracked)

    @my.Tracker
    class testClass2:
        def __init__(self, myAttr):
            self.attr2 = myAttr

    print(my.Tracker.tracked)
    
    print(testClass._all) 
    print(testClass2._all)
    print(testClass._nInst)
    print(tmp2.attr)
    
    # test if wrapper was updated
    import inspect
    print(testClass, inspect.unwrap(testClass))
    print(testClass2, inspect.unwrap(testClass2))

    # extend the tracker to do operations on all objects created by that class!
    # for example, group statistics of all images
    # Just don't override the __new__, __init__ or __call__ methods
    class extendedTracker(my.Tracker):
        """"""
        def extMethod(self):
            print([k.attr for k in self._all])
    
    @extendedTracker
    class extClass: 
        def __init__(self, myAttr):
            self.attr = myAttr

    ext1 = extClass(101)
    ext2 = extClass(102)
    ext3 = extClass(103)
    extClass.extMethod()

    class behaviorMetrics(my.Tracker):
        @property
        def accuracy(self):
            allAcc = [k.accuracy for k in self._all]
            return (np.mean(allAcc), np.std(allAcc))
        def sophieSays(self):
            bestAgent = self._all[np.argmax([k.accuracy for k in self._all])].agent
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
        ('accuracy', <class 'float'>, ())
        ('agent', <class 'str'>, ())
        ('behMethod', <class 'method'>, ())
        ('properties', <class 'method'>, ())
        ('weight', <class 'int'>, ())
    """
    print('Testing pntools.Tracker.query and pntools.AddMethods')

    @my.Tracker
    @my.AddMethods([my.cm.properties])
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
    res[0].properties() # testing my.AddMethods
    res = behavior.query("len(k.agent) > 4 and k.accuracy >= 0.3", keys=[])
    print('testTrackerQuery finished.')

if __name__ == '__main__':
    testTracker()
    testTrackerQuery()
