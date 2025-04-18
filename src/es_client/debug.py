"""Module for tiered debugging with a global TieredDebug instance.

This module defines a global `debug` instance of `TieredDebug` and a `begin_end`
decorator to log function call boundaries at specified debug levels. Copy this
file into your project to enable project-wide debugging. Import `debug` and `begin_end`
in any module with `from .debug import debug, begin_end`.
"""

import typing as t
from functools import wraps
from tiered_debug import TieredDebug, DebugLevel

DEFAULT_BEGIN: DebugLevel = 2
"""Default debug level for begin message in begin_end decorator."""

DEFAULT_END: DebugLevel = 3
"""Default debug level for end message in begin_end decorator."""

debug = TieredDebug()
"""Global TieredDebug instance for project-wide debugging."""


def begin_end(
    begin: t.Optional[DebugLevel] = DEFAULT_BEGIN,
    end: t.Optional[DebugLevel] = DEFAULT_END,
    debug_obj: t.Optional[TieredDebug] = None,
    stklvl: t.Optional[int] = None,
) -> t.Callable:
    """Decorator to log the beginning and end of a function call.

    Logs the start and end of a function at the specified debug levels using the
    provided or global `debug` instance. If `begin` or `end` is invalid (not 1-5),
    logs an error and uses default levels (2 for begin, 3 for end). The stack level
    defaults to one level beyond the global `debug.stacklevel` to report the caller's
    context.

    :param begin: Debug level (1-5) for the begin message. Defaults to 2.
    :type begin: Optional[DebugLevel]
    :param end: Debug level (1-5) for the end message. Defaults to 3.
    :type end: Optional[DebugLevel]
    :param debug_obj: TieredDebug instance to use for logging. Defaults to global
        `debug`.
    :type debug_obj: Optional[TieredDebug]
    :param stklvl: Stack level for caller reporting. Defaults to debug.stacklevel + 1.
    :type stklvl: Optional[int]
    :return: Decorated function.
    :rtype: Callable
    """
    if debug_obj is None:
        debug_obj = globals()["debug"]

    effective_begin = begin
    effective_end = end

    if begin not in (1, 2, 3, 4, 5):
        debug_obj.logger.error(
            f"Invalid begin level: {begin}. Using default: {DEFAULT_BEGIN}"
        )
        effective_begin = DEFAULT_BEGIN
    if end not in (1, 2, 3, 4, 5):
        debug_obj.logger.error(
            f"Invalid end level: {end}. Using default: {DEFAULT_END}"
        )
        effective_end = DEFAULT_END

    mmap = {
        1: debug_obj.lv1,
        2: debug_obj.lv2,
        3: debug_obj.lv3,
        4: debug_obj.lv4,
        5: debug_obj.lv5,
    }

    def decorator(func: t.Callable) -> t.Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            common = f"CALL: {func.__name__}()"
            effective_stklvl = (
                stklvl if stklvl is not None else debug_obj.stacklevel + 1
            )
            mmap[effective_begin](f"BEGIN {common}", stklvl=effective_stklvl)
            result = func(*args, **kwargs)
            mmap[effective_end](f"END {common}", stklvl=effective_stklvl)
            return result

        return wrapper

    return decorator
