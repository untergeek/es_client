"""Tiered Debugging module"""

import typing as t
from functools import wraps
from tiered_debug import TieredDebug

debug = TieredDebug()


def begin_end(begin: t.Optional[int] = 2, end: t.Optional[int] = 3) -> t.Callable:
    """Decorator to log the beginning and end of a function.

    This decorator will log the beginning and end of a function call at the
    specified levels, defaulting to 2 for the beginning and 3 for the ending.

    :return: The decorated function.
    :rtype: Callable
    """
    mmap = {
        1: debug.lv1,
        2: debug.lv2,
        3: debug.lv3,
        4: debug.lv4,
        5: debug.lv5,
    }

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            common = f"CALL: {func.__name__}()"
            mmap[begin](f"BEGIN {common}", stklvl=debug.stacklevel + 1)
            result = func(*args, **kwargs)
            mmap[end](f"END {common}", stklvl=debug.stacklevel + 1)
            return result

        return wrapper

    return decorator
