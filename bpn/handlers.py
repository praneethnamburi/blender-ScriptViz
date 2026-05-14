"""
Event handlers and broadcasting using blinker's signal.

Relocated from ``pntools/__init__.py`` (2026-05-14). bpn is the only real
consumer of these helpers, so the home is here. See
``plans/20260514_pntools_handler_retirement.md`` in pn-specs for the
migration log.
"""
import inspect
import weakref

import blinker


class Handler:
    """
    Event handlers based on blinker's signal.
    Currently, handlers can be defined on:
    1) Class functions - act on all members of a class
    2) Bound methods - act on a specific class member
    3) Class property - act on all members of a class when a property is set
    4) Object property - act on a specific class member when its property is set
    A receiver function can be attached either before, or after for each of these categories.
    Therefore, there are 8 types of handlers in total.
    thing = (class, object)
    attr = (function, property)
    mode = (pre, post)
    """
    def __init__(self, thing, attr, mode='post', sig=None):
        assert isinstance(attr, str)
        assert hasattr(thing, attr)
        assert mode in ('pre', 'post')
        self._thing = weakref.ref(thing)
        self.attr = attr
        self.mode = mode
        if sig is None:
            self.signal = blinker.base.signal
        else: # providing signal from a specific namespace will leave blinker's default namespace free for other apps
            assert isinstance(sig.__self__, blinker.base.Namespace)
            self.signal = sig
        assert self.attr_cat in ('property', 'function')
        if self.attr_cat == 'property':
            assert getattr(self.thing_class, self.attr).fset is not None

    thing = property(lambda s: s._thing())
    thing_is_class = property(lambda s: inspect.isclass(s.thing))
    thing_class = property(lambda s: s.thing if s.thing_is_class else type(s.thing))
    attr_cat = property(lambda s: type(getattr(s.thing_class, s.attr)).__name__)
    mod_name = property(lambda s: s.thing.__module__ if s.thing_is_class else type(s.thing).__module__)
    cls_id = property(lambda s: s.mode + '-' + s.mod_name + '-' + s.thing_class.__name__ + '-' + s.attr_name)
    @property
    def attr_name(self):
        """Name of the attribute. If it is a property, it must have a setter to support a handler."""
        if self.attr_cat == 'function':
            return self.attr
        return self.attr + '.fset'
    @property
    def instance_name(self):
        """Name of the instance"""
        if self.thing_is_class:
            return ''
        return self.thing.name if hasattr(self.thing, 'name') else hex(id(self.thing))
    @property
    def id(self):
        """This is the broadcasted signal."""
        if self.thing_is_class:
            return self.cls_id
        return self.cls_id + '(' + self.instance_name + ')'

    def id2dict(self):
        """Handler ID as a dictionary"""
        return handler_id2dict(self.id)

    def broadcast(self):
        """Tweak thing's attr to broadcast a signal either before or after execution."""
        if self.attr_cat == 'function':
            setattr(self.thing, self.attr, self._broadcast_function())
        if self.attr_cat == 'property': # only the class property can broadcast!
            # Remember that either all instances broadcast a property, or none of them do.
            # The strategy for object specific handlers is to filter at the receiver.
            setattr(self.thing_class, self.attr, self._broadcast_property())

    def add_receiver(self, receiver_func):
        """
        Add a receiver function to the handler.
        A receiver function should have the same signature as defining a function in a class:
        def receiver_fun(self):
            pass
        """
        assert type(receiver_func).__name__ in ('function', 'method')
        r_desc = self.receiver_descriptor(receiver_func)
        if r_desc not in [r for r in self.receivers if r[1] != '<lambda>']:
            self.signal(self.id).connect(receiver_func)
        else:
            print('Receiver with description '+str(r_desc)+' already connected. No action taken.')

    def get_receivers(self):
        """Return the receivers (weakref list)"""
        return self.signal(self.id).receivers

    def delete_receivers(self):
        """Delete all receivers for a signal."""
        self.signal(self.id).receivers = {}

    @property #**
    def channels(self):
        """Broadcasting channels (if any)"""
        if self.attr_cat == 'function':
            func = getattr(self.thing, self.attr)
            if hasattr(func, '__broadcast__'):
                return func.__broadcast__
            return None
        if self.attr_cat == 'property':
            p = getattr(self.thing_class, self.attr)
            if hasattr(p.fset, '__broadcast__'):
                return p.fset.__broadcast__
            return None

    @property #**
    def receivers(self):
        """
        Descriptions for current receiver functions.
        ('function'/'method(obj_id)', __qualname__, __module__)
        """
        return [self.receiver_descriptor(r()) for r in list(self.get_receivers().values())]

    def __eq__(self, other):
        return self.channels == other.channels and self.receivers == other.receivers

    def __str__(self):
        return object.__repr__(self)

    def __repr__(self):
        return self.__module__ + "." + self.__class__.__name__ + ': ' + self.id + '\nChannels: ' + str(self.channels) + '\nReceivers: ' + str(self.receivers)

    @staticmethod
    def receiver_descriptor(r):
        """Tuple description of a signal's receiver function"""
        f_type = type(r).__name__
        if f_type == 'method':
            bound_obj = r.__self__
            bound_obj_id = bound_obj.name if hasattr(bound_obj, 'name') else hex(id(bound_obj))
            return (f_type+'('+ bound_obj_id +')', r.__qualname__, r.__module__)
        return (f_type, r.__qualname__, r.__module__)

    def _broadcast_function(self):
        """
        modifies self.thing's attribute to broadcast
        """
        func = getattr(self.thing, self.attr)
        func_type = type(func).__name__
        signal_name = self.id

        if hasattr(func, '__broadcast__'): # already broadcasting
            assert func.__broadcast__ == signal_name
            return func

        if func_type == 'method': # 'unbounded'
            meth = func
            func = getattr(meth.__self__.__class__, meth.__name__)

        def _new_func_pre(s, *args, **kwargs):
            if bool(self.signal(signal_name).receivers):
                self.signal(signal_name).send(s) # signal is sent BEFORE the object is modified
            f_out = func(s, *args, **kwargs)
            return f_out
        def _new_func_post(s, *args, **kwargs):
            f_out = func(s, *args, **kwargs)
            if bool(self.signal(signal_name).receivers):
                self.signal(signal_name).send(s) # signal is sent AFTER the object is modified
            return f_out

        _new_func = _new_func_pre if self.mode == 'pre' else _new_func_post
        _new_func.__name__ = func.__name__
        _new_func.__qualname__ = func.__qualname__
        _new_func.__module__ = func.__module__
        _new_func.__broadcast__ = signal_name

        if func_type == 'method': # bind the function to the object
            return _new_func.__get__(meth.__self__)

        return _new_func

    def _broadcast_property(self):
        """
        Creates a new property with a modified setter.
        Adds a broadcasting signal to the setter of property p.
        """
        p = getattr(self.thing_class, self.attr)
        signal_name = self.cls_id
        assert isinstance(p, property)

        if hasattr(p.fset, '__broadcast__'):
            if signal_name in p.fset.__broadcast__:
                return p # no need to modify the property

        def _new_fset_pre(x, s): # x is the object whose property is being modified (self)
            # broadcast signal for all members
            if bool(self.signal(signal_name).receivers):
                self.signal(signal_name).send(x)
            # member-specific broadcast
            instance_name = x.name if hasattr(x, 'name') else hex(id(x))
            new_signal_name = signal_name+'('+instance_name+')'
            if bool(self.signal(new_signal_name).receivers):
                self.signal(new_signal_name).send(x) # signal is sent AFTER the object is modified
            f_out = p.fset(x, s)
            return f_out
        def _new_fset_post(x, s): # x is the object whose property is being modified (self)
            f_out = p.fset(x, s)
            # broadcast signal for all members
            if bool(self.signal(signal_name).receivers):
                self.signal(signal_name).send(x)
            # member-specific broadcast
            instance_name = x.name if hasattr(x, 'name') else hex(id(x))
            new_signal_name = signal_name+'('+instance_name+')'
            if bool(self.signal(new_signal_name).receivers):
                self.signal(new_signal_name).send(x) # signal is sent AFTER the object is modified
            return f_out

        _new_fset = _new_fset_pre if self.mode == 'pre' else _new_fset_post
        _new_fset.__name__ = p.fset.__name__
        _new_fset.__qualname__ = p.fset.__qualname__
        _new_fset.__module__ = p.fset.__module__
        if hasattr(p.fset, '__broadcast__'):
            _new_fset.__broadcast__ = p.fset.__broadcast__
        else:
            _new_fset.__broadcast__ = []
        _new_fset.__broadcast__ += [signal_name] # this is the signal name for the class
        return property(p.fget, _new_fset)

def handler_id2dict(k):
    """
    Turn a handler ID into meaningful parts
    A handler id is a string that has the following construction:
    mode-module-class-attribute(instance)
    """
    k_dict = {}
    stg1 = k.split('(')
    k_dict['instance'] = stg1[-1].rstrip(')') if len(stg1) == 2 else ''
    stg2 = stg1[0].split('-')
    assert len(stg2) == 4
    k_dict['mode'], k_dict['module'], k_dict['class'], stg3 = stg2
    k_dict['attr'] = stg3.replace('.fset', '')
    return k_dict

def add_handler(thing, attr, receiver_func, mode='post', sig=None):
    """
    One-liner access to setting up a broadcaster and receiver.

    Example:
        s1 = new.sphere('sph1')
        # s1.frame is a property, and fire fun whenever s1.frame is set
        add_handler(s1, 'frame', fun, mode='pre')
        # Fire fun when the frame attribute of any instance of core.Object is set
        add_handler(core.Object, 'frame', fun, mode='post')
        # s1.translate is a method, and fire fun whenever s1.translate is invoked!
        add_handler(s1, 'translate', core.Object.show_frame, mode='post')
    """
    h = Handler(thing, attr, mode, sig)
    h.broadcast()
    h.add_receiver(receiver_func)
    return h

# BroadcastProperties is useful for modifying classes when defining them
class BroadcastProperties:
    """
    Enables properties in a class to have event handlers. This
    manipulation 'replaces' a property in a class with a new property
    object.

    Takes a class, and makes chosen properties setter emit a signal on
    every change. Use it as a decorator on classes to broadcast some/all
    property changes. Receiver receives the object after it is changed.

    Example: see tests.test_broadcasting2()

    Usage: (Don't chain with the same property. Chaining below is OK)
        @handlers.BroadcastProperties('loc', mode='pre')
        @handlers.BroadcastProperties('frame', mode='post')
        class Object(Thing):
            frame = property(...)
            loc = property(...)
    """
    def __init__(self, p_names='ALL', mode='post'):
        assert isinstance(p_names, (str, list, tuple))
        assert mode in ('pre', 'post')
        self.p_names = p_names
        self.mode = mode
    def __call__(self, src_class):
        if isinstance(self.p_names, str) and self.p_names == 'ALL':
            src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property)}
        else:
            src_properties = {p_name : p for p_name, p in src_class.__dict__.items() if isinstance(p, property) and p_name in self.p_names}
        for p_name, p in src_properties.items():
            if p.fset is not None:
                h = Handler(src_class, p_name, self.mode)
                h.broadcast()
        return src_class
