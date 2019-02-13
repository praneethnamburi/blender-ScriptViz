# def tracker(inCls):
#     inCls._nInst = 0
#     inCls._all = []
#     def new(cls, *args, **kwargs):
#         print("new")
#         cls._nInst += 1
#         return super().__new__(cls, *args, **kwargs)
#     inCls.__new__ = new
#     # class trackedClass(inCls):
#     #     def __new__(cls, *args, **kwargs):
#     #         print("new")
#     #         inCls._nInst += 1
#     #         return super().__new__(cls, *args, **kwargs)
#     return inCls

import functools
class trackerDecorator(object):
    """"""
    def __new__(cls, *args, **kwargs):
        cls._nInst = 0
        cls._all = []
        return super().__new__(cls)
    def __init__(self, clsToTrack):
        self.clsToTrack = clsToTrack
        functools.update_wrapper(self, clsToTrack)
    def __call__(self, *args, **kwargs):
        self._nInst += 1
        funcOut = self.clsToTrack(*args, **kwargs)
        return funcOut


class trackerCls(object):
    _nInst = 0
    _all = []
    def __new__(cls, *args, **kwargs):
        cls._nInst += 1
        return super().__new__(cls)
    def __init__(self):
        self.__class__._all.append(self)
        self._inst = self.__class__._nInst
    @classmethod
    def delete(cls, obj):
        cls._nInst -= 1
        cls._all.remove(obj)

@trackerDecorator
class testClass(object):
    def __init__(self, myAttr):
        self.attr = myAttr
        super().__init__()


tmp1 = testClass(11)
tmp2 = testClass(12)
tmp3 = testClass(13)

testClass.delete(tmp2)
print(testClass._nInst)