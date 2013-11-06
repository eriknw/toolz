"""
Alternate namespece for toolz such that all functions are traced using `q`

Trace log goes to /tmp/q

See Also:
    toolz.curried
"""
import re
import toolz
import functools
from toolz.q import q as tracer

# Decorator functions for tracing

def trace(f, wrapped=None, name=None):
    if wrapped is not None:
        # trick "q"
        f = functools.update_wrapper(f, wrapped)
    elif name is not None:
        f.__name__ = name
        f.func_name = name
    return functools.update_wrapper(tracer.trace(f), f)


def traceas(wrapped):
    def inner(f):
        return trace(f, wrapped=wrapped)
    return inner


def tracewithname(name):
    def inner(f):
        return trace(f, name=name)
    return inner


# Now trace all appropriate functions from `toolz` similar to `toolz.curried`
def traceable(name, f):
    # '__module__' attribute is required for functools.update_wrapper
    return '__' not in name and callable(f) and hasattr(f, '__module__')


d = dict((name, trace(f) if traceable(name, f) else f)
         for name, f in toolz.__dict__.items())

locals().update(d)


# Now tweak certain functions for improved clarity

# add trace to `evalform_front`
@trace
def thread_first(val, *forms):
    """ Thread value through a sequence of functions/forms

    >>> def double(x): return 2*x
    >>> def inc(x):    return x + 1
    >>> thread_first(1, inc, double)
    4

    If the function expects more than one input you can specify those inputs
    in a tuple.  The value is used as the first input.

    >>> def add(x, y): return x + y
    >>> def pow(x, y): return x**y
    >>> thread_first(1, (add, 4), (pow, 2))  # pow(add(1, 4), 2)
    25

    So in general
        thread_first(x, f, (g, y, z))
    expands to
        g(f(x), y, z)

    See Also:
        thread_last
    """
    @trace
    def evalform_front(val, form):
        if callable(form):
            return form(val)
        if isinstance(form, tuple):
            fn, args = form[0], form[1:]
            args = (val,) + args
            return fn(*args)
    return reduce(evalform_front, forms, val)


# add trace to `evalform_back`
@trace
def thread_last(val, *forms):
    """ Thread value through a sequence of functions/forms

    >>> def double(x): return 2*x
    >>> def inc(x):    return x + 1
    >>> thread_last(1, inc, double)
    4

    If the function expects more than one input you can specify those inputs
    in a tuple.  The value is used as the last input.

    >>> def add(x, y): return x + y
    >>> def pow(x, y): return x**y
    >>> thread_last(1, (add, 4), (pow, 2))  # pow(2, add(4, 1))
    32

    So in general
        thread_last(x, f, (g, y, z))
    expands to
        g(y, z, f(x))

    >>> def iseven(x):
    ...     return x % 2 == 0
    >>> list(thread_last([1, 2, 3], (map, inc), (filter, iseven)))
    [2, 4]

    See Also:
        thread_first
    """
    @trace
    def evalform_back(val, form):
        if callable(form):
            return form(val)
        if isinstance(form, tuple):
            fn, args = form[0], form[1:]
            args = args + (val,)
            return fn(*args)
    return reduce(evalform_back, forms, val)


# give the memoized function the same name (instead of "memof")
@trace
def memoize(f, cache=None):
    """ Cache a function's result for speedy future evaluation

    Considerations:
        Trades memory for speed.
        Only use on pure functions.

    >>> def add(x, y):  return x + y
    >>> add = memoize(add)

    Or use as a decorator

    >>> @memoize
    ... def add(x, y):
    ...     return x + y
    """
    if cache is None:
        cache = {}

    @traceas(f)
    def memof(*args):
        try:
            in_cache = args in cache
        except TypeError:
            raise TypeError("Arguments to memoized function must be hashable")

        if in_cache:
            return cache[args]
        else:
            result = f(*args)
            cache[args] = result
            return result
    memof.__name__ = f.__name__
    memof.__doc__ = f.__doc__
    return memof


# try really hard to come up with safe function names
def _clean_name(s):
    s = re.sub('[^0-9a-zA-Z_]', '', s)
    s = re.sub('^[^a-zA-Z_]+', '', s)
    return s[:32]


def _safe_funcname(func):
    try:
        return _clean_name(func.func_name)
    except:
        try:
            return _clean_name(func.__name__)
        except:
            return _clean_name(repr(func))


# create new, meaningful name for composed functions
@trace
def compose(*funcs):
    """ Compose functions to operate in series.

    Returns a function that applies other functions in sequence.

    Functions are applied from right to left so that
    ``compose(f, g, h)(x, y)`` is the same as ``f(g(h(x, y)))``.

    If no arguments are provided, the identity function (f(x) = x) is returned.

    >>> inc = lambda i: i + 1
    >>> compose(str, inc)(3)
    '4'

    See Also:
        pipe
    """
    if not funcs:
        return identity
    if len(funcs) == 1:
        return funcs[0]
    else:
        fns = list(reversed(funcs))
        funcname = 'composed_' + '_'.join(_safe_funcname(f) for f in funcs)

        @tracewithname(funcname)
        def composed(*args, **kwargs):
            ret = fns[0](*args, **kwargs)
            for f in fns[1:]:
                ret = f(ret)
            return ret

        return composed
