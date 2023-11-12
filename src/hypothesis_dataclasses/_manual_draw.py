"""This module implements the `manualdraw` decorator."""

import functools as _functools

from hypothesis.strategies import DrawFn as _DrawFn
from typing import Any as _Any, Callable as _Callable, \
    ClassVar as _ClassVar, FrozenSet as _FrozenSet, Set as _Set, \
    TypeVar as _TypeVar

from ._partial_instance import PartialInstance as _PartialInstance
from ._scfunc_descriptor import SCFuncDescriptor as _SCFuncDescriptor


_T = _TypeVar("_T")


ManualDrawFunction = _Callable[[_DrawFn, str, _PartialInstance], _Any]
"""Defines the signature of a function wrapped by @manualdraw."""


class ManualDrawFunctionDescriptor(_SCFuncDescriptor):
    """A descriptor marking a function for a manual draw."""

    __slots__ = ("fields",)

    def __init__(self, fields: _Set[str], func: _Callable):
        """Construct a new `ManualDrawFunctionDescriptor`.

        Args:
            fields (Set[str]): The fields for which to call the
                function to draw the fields' values.
            func (Callable): The function to call. Must be wrapped in
                @staticmethod or @classmethod.
        """
        super().__init__(func)
        self.fields: _FrozenSet[str] = frozenset(fields)

    _nparam_classmethod: _ClassVar[int] = 4
    """The number of expected parameters if the descriptor is applied to
    a classmethod."""

    _nparam_staticmethod: _ClassVar[int] = 3
    """The number of expected parameters if the descriptor is applied to
    a staticmethod."""


def manualdraw(field: str, *fields: str) -> _Callable[[_T], _T]:
    """A decorator for functions that perform manual draws for fields.
    The function should have the signature
    `f(DrawFn, str, PartialInstance)` and must be a staticmethod or
    classmethod (in which case there must be an additional argument in
    the first position for the class). The first argument passed to it
    will be the hypothesis draw function, the second argument will be
    the name of the field for which to perform the draw and the third
    argument will be a `PartialInstance` containing the values of the
    fields that have already been drawn. This is useful for dependent
    fields, where the value of one field might depend on several
    previously drawn fields. Additionally, it is also possible to use
    these functions to reject the example using `hypothesis.assume`.

    Args:
        field(s) (str): The field(s) for which to perform the draw.
            Duplicates will be removed.

    Raises:
        RuntimeError: If no fields are provided and this function is
            applied directly to the function to decorate without
            parentheses.
        TypeError: If the decorated function is not a static or class
            function.

    Examples:
        >>> from dataclasses import dataclass
        >>> from hypothesis.strategies import DrawFn, integers
        >>> from hypothesis_dataclasses import instances, manualdraw, \
                PartialInstance
        ...
        >>> @dataclass
        ... class ExampleDClass:
        ...     value: int
        ...
        ...     @manualdraw("value")
        ...     @staticmethod
        ...     def draw_value(
        ...         draw: DrawFn, field: str, pi: PartialInstance
        ...     ) -> int:
        ...         return draw(integers(0, 5))
        ...
        >>> example_instance = instances(ExampleDClass).example()
        >>> print(isinstance(example_instance.value, int))
        True
        >>> print(0 <= example_instance.value <= 5)
        True

        Another example using `hypothesis.assume` to reject an example
        from the draw function:
        >>> from dataclasses import dataclass
        >>> from hypothesis import assume
        >>> from hypothesis.strategies import booleans, DrawFn, integers
        >>> from hypothesis_dataclasses import field_from, instances, \
                manualdraw, PartialInstance
        ...
        >>> @dataclass
        ... class ExampleDCRejecting:
        ...     reject: bool = field_from(booleans())
        ...     value: int
        ...
        ...     @manualdraw("value")
        ...     @staticmethod
        ...     def draw_value(
        ...         draw: DrawFn, field: str, others: PartialInstance
        ...     ) -> int:
        ...         assume(not others.reject)
        ...         return draw(integers())
        ...
        >>> example_instance = instances(ExampleDCRejecting).example()
        >>> print(not example_instance.reject)
        True
        >>> print(isinstance(example_instance.value, int))
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
        ManualDrawFunctionDescriptor, field_set
    )
