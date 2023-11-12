"""This module provides a basic descriptor class which is used by the
`manualdraw` and `calloncedrawn` decorators.
"""

import inspect as _inspect

from typing import Callable as _Callable, ClassVar as _ClassVar


class SCFuncDescriptor:
    """A descriptor wrapping a staticmethod or classmethod."""

    __slots__ = ("func",)

    _nparam_classmethod: _ClassVar[int] = -1
    """The number of expected parameters if the descriptor is applied to
    a classmethod."""

    _nparam_staticmethod: _ClassVar[int] = -1
    """The number of expected parameters if the descriptor is applied to
    a staticmethod."""

    def __init_subclass__(cls):
        for fname in ("_nparam_classmethod", "_nparam_staticmethod"):
            if getattr(cls, fname) != -1:
                continue
            raise AssertionError(
                f"The subclass {cls.__qualname__!r} does not override "
                f"the {fname!r} field."
            )

    def __init__(self, func: _Callable):
        if isinstance(func, classmethod):
            exp_nparam = self._nparam_classmethod
        elif isinstance(func, staticmethod):
            exp_nparam = self._nparam_staticmethod
        else:
            raise TypeError(
                "The wrapped function was not a staticmethod or a "
                "classmethod."
            )
        sig = _inspect.signature(func.__func__)
        nparam = len(sig.parameters)
        if nparam != exp_nparam:
            raise TypeError(
                "The wrapped function does not have the expected "
                f"number of parameters. Expected {exp_nparam}, got "
                f"{nparam}."
            )
        self.func: _Callable = func

    def __get__(self, obj, objtype):
        # We dont want to actually change anything about the function
        # itself.
        return self.func.__get__(obj, objtype)
