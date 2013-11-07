#          /            0               if i is 0
# fib(i) = |            1               if i is 1
#          \ fib(i - 1) + fib(i - 2)    otherwise

def fib(n):
    """ Imperative definition of Fibonacci numbers """
    a, b = 0, 1
    for i in range(n):
        a, b = b, a + b
    return b


# This is intuitive but VERY slow
from toolz.traced import trace
@trace
def fib(n):
    """ Functional definition of Fibonacci numbers """
    if n == 0 or n == 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)

fib(4)
fib(5)

# Oh wait, it's fast again
from toolz.traced import memoize
fib = memoize(fib)

fib(4)
fib(5)
