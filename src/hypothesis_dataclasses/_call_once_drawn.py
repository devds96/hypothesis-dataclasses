"""This module implements the `calloncedrawn` decorator."""

import functools as _functools

from typing import Callable as _Callable, ClassVar as _ClassVar, \
    FrozenSet as _FrozenSet, Set as _Set, TypeVar as _TypeVar

from ._scfunc_descriptor import SCFuncDescriptor as _SCFuncDescriptor


_T = _TypeVar("_T")


class CallOnceDrawnFunctionDescriptor(_SCFuncDescriptor):
    """A descriptor marking a function to be called after certain fields
    have been drawn.
    """

    __slots__ = ("fields",)

    def __init__(self, fields: _Set[str], func: _Callable):
        """Construct a new `CallOnceDrawnFunctionDescriptor`.

        Args:
            fields (Set[str]): The fields for which to call the function
                after they have been drawn.
            func (Callable): The function to call. Must be wrapped in
                @staticmethod or @classmethod.
        """
        super().__init__(func)
        self.fields: _FrozenSet[str] = frozenset(fields)

    _nparam_classmethod: _ClassVar[int] = 3
    """The number of expected parameters if the descriptor is applied to
    a classmethod."""

    _nparam_staticmethod: _ClassVar[int] = 2
    """The number of expected parameters if the descriptor is applied to
    a staticmethod."""


def calloncedrawn(field: str, *fields: str) -> _Callable[[_T], _T]:
    """A decorator for functions that should be called once a certain
    set of fields has been drawn. The function should have the signature
    `f(frozenset[str], PartialInstance)` and must be a staticmethod or
    classmethod (in which case there must be an additional argument in
    the first position for the class). The first argument will be the
    fields passed to this decorator and the second argument will be the
    partially constructed instance in which these fields have already
    been set. This is useful for rejecting partially drawn examples
    using `hypothesis.assume`.

    Args:
        field(s) (str): The field(s) for which this function should be
            called, after they all have been drawn. Duplicates will be
            removed.

    Raises:
        RuntimeError: If no fields are provided and this function is
            applied directly to the function to decorate without
            parentheses.
        TypeError: If the decorated function is not a static or class
            function.

    Example:
        >>> from dataclasses import dataclass
        >>> from hypothesis_dataclasses import calloncedrawn, \
                instances, PartialInstance
        >>> from hypothesis import assume
        >>> from hypothesis.strategies import DrawFn, integers
        >>> from typing import FrozenSet
        ...
        >>> @dataclass
        ... class ExampleDClass:
        ...     i: int
        ...     j: int
        ...
        ...     @calloncedrawn('i', 'j')
        ...     @staticmethod
        ...     def draw_value(
        ...         fields: FrozenSet[str], pi: PartialInstance
        ...     ) -> int:
        ...         assume(pi.i == pi.j)
        ...
        >>> example_instance = instances(ExampleDClass).example()
        >>> isinstance(example_instance.i, int)
        True
        >>> example_instance.i == example_instance.j
        True
    """

    if not isinstance(field, str):
        raise RuntimeError(
            "'field' was not a str. Perhaps you forgot to specify the "
            "field name?"
        )

    field_set = set(fields)
    field_set.add(field)
    return _functools.partial(  # type: ignore
        CallOnceDrawnFunctionDescriptor, field_set
    )
