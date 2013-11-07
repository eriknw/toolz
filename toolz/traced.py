"""
Alternate namespece for toolz such that all functions are traced using `q`

Trace log goes to /tmp/toolz

See Also:
    toolz.curried
"""
import re
import toolz
import functools
from toolz.q import q as tracer


def trace(f, wrapped=None, name=None):
    """ Trace a function's input and output; this may be used as a decorator

    By default, all trace output is written to "/tmp/toolz".  It is common to
    view the output real-time using the command `tail -f /tmp/toolz`

    >>> @trace
    ... def add(x, y):
    ...     return x + y

    >>> def mul(x, y):
    ...     return x * y
    >>> mul = trace(mul)
    """
    if wrapped is not None:
        # trick "q"
        f = functools.update_wrapper(f, wrapped)
    elif name is not None:
        f.__name__ = name
        f.func_name = name
    return functools.update_wrapper(tracer.trace(f), f)


# Trace all appropriate functions from `toolz` similar to `toolz.curried`
def traceable(name, f):
    # '__module__' attribute is required for functools.update_wrapper
    return '__' not in name and callable(f) and hasattr(f, '__module__')


d = dict((name, trace(f) if traceable(name, f) else f)
         for name, f in toolz.__dict__.items())

locals().update(d)

# Trace the functions created by `memoize` and `compose`
memoize = toolz.compose(trace, memoize)
compose = toolz.compose(trace, compose)
