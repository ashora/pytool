"""
This module contains items that are "missing" from the Python standard library,
that do miscelleneous things.
"""
import inspect
import functools


def get_name(frame):
    """ Gets the name of the passed frame.

        :warning: It's very important to delete a stack frame after you're done
               using it, as it can cause circular references that prevents
               garbage collection.

        :param frame: Stack frame to inspect.
        :returns: Name of the frame in the form *module.class.method*.

    """
    module = inspect.getmodule(frame)

    name = frame.f_code.co_name
    if frame.f_code.co_varnames:
        # Does this method belong to a class?
        try:
            varname = frame.f_code.co_varnames[0]
            # The class or instance should be the first argument,
            # unless it was otherwise munged by a decorator or is a
            # @staticmethod
            maybe_cls = frame.f_locals[varname]

            # Get the actual method, if it exists on the class
            maybe_func = getattr(maybe_cls, frame.f_code.co_name)

            # If we have self, or a classmethod, we need the class name
            if (varname == 'self' or maybe_func.im_self == maybe_cls):
                cls_name = (getattr(maybe_cls, '__name__', None)
                        or getattr(getattr(maybe_cls, '__class__', None),
                            '__name__', None))

                if cls_name:
                    name =  "%s.%s" % (cls_name, name)
                    module = maybe_cls.__module__
        except (KeyError, AttributeError):
            # Probably not a class method, so fuck it
            pass

    if module:
        if not isinstance(module, basestring):
            module = module.__name__
        if name != '<module>':
            return "%s.%s" % (module, name)
        else:
            return module
    else:
        return name


def classproperty(func):
    """
    Makes a @classmethod-style property (since @property only works on
    instances).

    ::

        from pytool.lang import classproperty

        class MyClass(object):
            _attr = 'Hello World'

            @classproperty
            def attr(cls):
                return cls._attr

        MyClass.attr # 'Hello World'
        MyClass().attr # Still 'Hello World'

    """
    def __get__(self, instance, owner):
        return func(owner)

    return type(func.__name__, (object,), {
        '__get__':__get__,
        '__module__':func.__module__,
        '__doc__':func.__doc__,
        })()


def singleton(klass):
    """ Wraps a class to create a singleton version of it.

        :param klass: Class to decorate

        Example usage::

            # Make a class directly behave as a singleton
            @singleton
            class Test(object):
                pass

            # Make an imported class behave as a singleton
            Test = singleton(Test)

    """
    cls_dict = {'_singleton': None}

    # Mirror original class
    cls_name = klass.__name__
    for attr in functools.WRAPPER_ASSIGNMENTS:
        cls_dict[attr] = getattr(klass, attr)

    # Make new method that controls singleton behavior
    def __new__(cls, *args, **kwargs):
        if not cls._singleton:
            cls._singleton = klass(*args, **kwargs)
        return cls._singleton

    # Add new method to singleton class dict
    cls_dict['__new__'] = __new__

    # Build and return new class
    return type(cls_name, (object,), cls_dict)


class _UNSETMeta(type):
    def __nonzero__(cls):
        return False

    def __len__(cls):
        return 0

    def __eq__(cls, other):
        if cls is other:
            return True
        if not other:
            return True
        return False

    def __iter__(cls):
        return cls

    def next(cls):
        raise StopIteration()

    def __repr__(cls):
        return 'UNSET'


class UNSET(object):
    """ Special class that evaluates to bool(False), but can be distinctly
        identified as seperate from None or False. This class can and should be
        used without instantiation.

        ::

            >>> from pytool.lang import UNSET
            >>> bool(UNSET)
            False
            >>> UNSET() is UNSET
            True
            >>> UNSET
            <class 'pytool.lang.UNSET'>
            >>> if {}.get('example', UNSET) is UNSET:
            ...     print "Key is missing."
            ...     
            Key is missing.
            >>> len(UNSET)
            0
            >>> list(UNSET)
            []
            >>> UNSET
            UNSET

    """
    __metaclass__ = _UNSETMeta

    def __new__(cls):
        return cls

