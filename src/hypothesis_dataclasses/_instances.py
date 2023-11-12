"""This module contains the `instances` strategy function."""

import dataclasses as _dataclasses
import functools as _functools
import hypothesis as _hypothesis
import hypothesis.strategies as _st

from dataclasses import dataclass as _dataclass, Field as _Field
from hypothesis.strategies import composite as _composite, \
    DrawFn as _DrawFn, SearchStrategy as _SearchStrategy
from typing import Callable as _Callable, Dict as _Dict, \
    Iterable as _Iterable, List as _List, Mapping as _Mapping, \
    Optional as _Optional, Sequence as _Sequence, Tuple as _Tuple, \
    Type as _Type, TypeVar as _TypeVar

try:
    from pydantic import ValidationError as _ValidationError
except ImportError:
    _PYDANTIC_AVAILABLE = False
else:
    _PYDANTIC_AVAILABLE = True

from . import _field_from
from . import _partial_instance

from ._call_once_drawn import CallOnceDrawnFunctionDescriptor \
    as _CallOnceDrawnFunctionDescriptor
from ._manual_draw import ManualDrawFunction as _ManualDrawFunction, \
    ManualDrawFunctionDescriptor as _ManualDrawFunctionDescriptor


_T = _TypeVar("_T")


def will_draw(f: _Field) -> bool:
    """Checks whether a dataclass field will be drawn. This is the case
    if the field appears in __init__ and does not have a default value.

    Args:
        f (Field): The dataclass field to check.

    Returns:
        bool: True if the dataclass field `f` will be drawn using its
            assigned strategy or the `from_type` strategy and False,
            otherwise.
    """
    return f.init and (f.default is _dataclasses.MISSING)


def drawn_fields(cls: _Type[_T]) -> _Sequence[str]:
    """Gets the names of the fields of a dataclass which are drawn
    using their strategy or the `from_type` strategy.

    Args:
        cls (type[T]): The dataclass for which to compute the drawn
            fields.

    Raises:
        TypeError: If `cls` is not a dataclass.

    Returns:
        Sequence[str]: The names of the fields that will be drawn. The
            order of the fields is as they appear in a call to
            `dataclasses.fields`.
    """
    if not _dataclasses.is_dataclass(cls):
        raise TypeError("'cls' was not a dataclass.")
    return tuple(
        f.name for f in _dataclasses.fields(cls) if will_draw(f)
    )


def _get_strategy_map(
    cls: _Type[_T]
) -> _Sequence[_Tuple[str, _SearchStrategy]]:
    """Construct a mapping from the field names to the corresponding
    hypothesis strategies from the class.

    Args:
        cls (type): The class for which to construct the mapping.

    Returns:
        dict[str, SearchStrategy]: A mapping from the dataclass field
            names to the search strategies from which the examples can
            be drawn.
    """

    def get_item(f: _Field) -> _Tuple[str, _SearchStrategy]:
        """Construct an item for the return value of the surrounding
        function.

        Args:
            f (Field): The dataclass field to process.

        Returns:
            tuple[str, SearchStrategy]: A pair of a field name and its
                corresponding `SearchStrategy`
        """
        md = f.metadata
        if (md is not None) and (_field_from.STRATEGY_METADATA_KEY in md):
            res = md[_field_from.STRATEGY_METADATA_KEY]
            if not isinstance(res, _SearchStrategy):
                # Failsafe, the key should always lead to a strategy.
                raise AssertionError(
                    f"Invalid object {res!r} found where a "
                    "SearchStrategy was expected."
                )
            st = res
        else:
            default = f.default
            if default is not _dataclasses.MISSING:
                st = _st.just(default)
            else:
                st = _st.from_type(f.type)
        return f.name, st

    all_fields = _dataclasses.fields(cls)  # type: ignore [arg-type]
    init_fields = filter(lambda f: f.init, all_fields)
    return tuple(map(get_item, init_fields))


_CallOnceDrawnFunctionFieldsSet = _Callable[
    [_partial_instance.PartialInstance],
    None
]
"""A function used as a calloncedrawn-callback with the fields set."""


_ManualDrawMapping = _Mapping[str, _ManualDrawFunction]
"""A function used as a calloncedrawn-callback with the fields set."""


_CallOnceDrawnMapping = _Mapping[
    str, _Sequence[_CallOnceDrawnFunctionFieldsSet]
]
"""A dict mapping field names to callbacks to call after the field has
been drawn."""


@_dataclass
class _Callbacks:
    """Bundles the callbacks for a class."""

    __slots__ = ("manualdraw", "calloncedrawn")

    manualdraw: _ManualDrawMapping
    """The dict mapping field names to their draw function."""

    calloncedrawn: _CallOnceDrawnMapping
    """The dict mapping field names to a sequence of callbacks to call
    after the field has been drawn."""

    @staticmethod
    def _mro_resolved_dict(cls: _Type[_T]) -> _Dict[str, object]:
        """Compute the MRO resolved dictionary of a class object.

        Args:
            cls (type[T]): The type for which to compute the dict.

        Returns:
            dict[str, object]: A dict containing the MRO-resolved
                members of `cls`.
        """
        result: _Dict[str, object] = dict()
        for t in reversed(cls.mro()):
            result.update(t.__dict__)
        return result

    @classmethod
    def get(cls, t: _Type[_T]):
        """Obtain the callbacks for a dataclass.

        Args:
            t (type[T]): The type for which to obtain the callbacks.

        Raises:
            ValueError: If a field is referenced by multiple
                `manualdraw` decorators.

        Returns:
            _Callbacks: The instance containing the callbacks.
        """

        draw_manually: _Dict[str, _ManualDrawFunction] = dict()

        def handle_manualdraw(k: str, v: object):
            """Handle a `ManualDrawFunctionDescriptor`.

            Args:
                k (str): The field name.
                v (object): The object to handle. If it is a
                    `ManualDrawFunctionDescriptor` instance, the
                    callback will be processed and added to
                    `draw_manually`.

            Raises:
                ValueError: If a field is referenced by multiple
                    `manualdraw` decorators.
            """
            if not isinstance(v, _ManualDrawFunctionDescriptor):
                return
            for field in v.fields:
                if field in draw_manually:
                    raise ValueError(
                        f"The field {field!r} is referenced by multiple "
                        "@manualdraw decorators."
                    )
                # Use getattr to trigger the descriptor (classmethod or
                # staticmethod)
                draw_manually[field] = getattr(t, k)

        drawn_callbacks: _Dict[
            str, _List[_CallOnceDrawnFunctionFieldsSet]
        ] = dict()

        draw_fields = drawn_fields(t)
        # We need to determine the position at which each field is drawn
        field_idx_map = {k: i for i, k in enumerate(draw_fields)}

        def call_after(fields: _Iterable[str]) -> str:
            """Get the name of the last drawn field after which the
            callback waiting for `fields` can be called.

            Args:
                fields (Iterable[str]): The fields the callback depends
                    on.

            Returns:
                str: The name of the last field that must have been
                    drawn so that the `calloncedrawn` decorator
                    depending on `fields` can be called.
            """
            try:
                return draw_fields[max(field_idx_map[f] for f in fields)]
            except KeyError as ke:
                raise AttributeError(
                    f"Not a valid (drawn) field of {t.__qualname__!r}."
                ) from ke

        def handle_calloncedrawn(k: str, v: object):
            """Handle a `CallOnceDrawnFunctionDescriptor`.

            Args:
                k (str): The field name.
                v (object): The object to handle. If it is a
                    `CallOnceDrawnFunctionDescriptor` instance, the
                    callback will be processed and added to
                    `drawn_callbacks`.
            """
            if not isinstance(v, _CallOnceDrawnFunctionDescriptor):
                return
            call_after_field = call_after(v.fields)

            try:
                lst = drawn_callbacks[call_after_field]
            except KeyError:
                lst = list()
                drawn_callbacks[call_after_field] = lst

            # Use getattr to trigger the descriptor
            func = getattr(t, k)
            # Apply the fields to the function call
            func_f_set = _functools.partial(func, v.fields)
            lst.append(func_f_set)

        for k, v in cls._mro_resolved_dict(t).items():
            handle_manualdraw(k, v)
            handle_calloncedrawn(k, v)

        frozen_drawn_callbacks = {
            k: tuple(v) for k, v in drawn_callbacks.items()
        }
        return cls(draw_manually, frozen_drawn_callbacks)


def _is_dataclass(cls: _Type) -> bool:
    """Checks whether a class is a dataclass. This wraps
    `dataclasses.is_dataclass` and removes the TypeGuard since
    currently causes issues with mypy.

    Args:
        cls (type[T]): The type to check.

    Returns:
        bool: Whether `cls` is a dataclass.
    """
    return _dataclasses.is_dataclass(cls)


def instances(
    cls: _Type[_T],
    *,
    disable_pydantic: _Optional[bool] = None
) -> _SearchStrategy[_T]:
    """A hypothesis strategy to construct instances of a dataclass. The
    instances will be constructed using the dataclass's __init__ method.

    Args:
        cls (type[T]): The dataclass.
        disable_pydandic (bool, optional): Whether to disable the
            conversion of pydantic `ValidationError`s to failed
            hypothesis assumptions. Defaults to False. This argument
            will be ignored if pydantic is not installed.

    Raises:
        TypeError: If `cls` is not a dataclass.
        ValueError: If no search strategy can be found for a field of
            the dataclass because no strategy is specified and no type
            annotation is given.

    Returns:
        SearchStrategy[T]: The search strategy.

    Examples:
        >>> from dataclasses import dataclass
        >>> from hypothesis.strategies import integers
        >>> from hypothesis_dataclasses import field_from, instances
        ...
        >>> @dataclass
        ... class ExampleDClass:
        ...     value: int = field_from(integers())
        ...
        >>> # We can draw examples from the strategy returned by this
        >>> # function
        >>> example_instance = instances(ExampleDClass).example()
        >>> print(isinstance(example_instance.value, int))
        True

        Note that default values assigned to fields will be interpreted
        as the only acceptable values for these fields, similar to the
        `just` strategy:
        >>> from dataclasses import dataclass
        >>> from hypothesis_dataclasses import instances
        ...
        >>> @dataclass
        ... class ExampleDClassConst:
        ...     value: int = 5
        ...
        >>> example_instance = instances(ExampleDClassConst).example()
        >>> print(example_instance.value)
        5
    """
    if not _is_dataclass(cls):
        raise TypeError("'cls' was not a dataclass.")

    smap = _get_strategy_map(cls)
    callbacks = _Callbacks.get(cls)
    man_draws = callbacks.manualdraw
    callback_map = callbacks.calloncedrawn

    def draw_instance(draw: _DrawFn) -> _Dict[str, object]:
        """Construct a dictionary for the fields of the instance and
        call the callbacks if appropriate.

        Args:
            draw (DrawFn): The hypothesis draw function.

        Returns:
            dict[str, object]: The dictionary containing the values for
                the dataclass fields (the keys).
        """

        instance_dict: _Dict[str, object] = dict()

        for field_name, strat in smap:
            try:
                manual_draw_fn = man_draws[field_name]
            except KeyError:
                value = draw(strat)
            else:
                pi = _partial_instance.PartialInstance(**instance_dict)
                value = manual_draw_fn(draw, field_name, pi)

            instance_dict[field_name] = value

            try:
                callbacks = callback_map[field_name]
            except KeyError:
                pass
            else:
                for callback in callbacks:
                    # Create a new instance for each call, since it may
                    # be modified accidentally.
                    pi = _partial_instance.PartialInstance(**instance_dict)
                    # The callbacks already have the first argument
                    # (the fields) set.
                    callback(pi)

        return instance_dict

    # We define helper functions to generate the strategy. These
    # functions capture all necessary info from this function as their
    # closure.
    if (not _PYDANTIC_AVAILABLE) or disable_pydantic:

        @_composite
        def strategy(draw: _DrawFn) -> _T:
            vmap = draw_instance(draw)
            return cls(**vmap)

    else:

        @_composite
        def strategy(draw: _DrawFn) -> _T:
            vmap = draw_instance(draw)
            try:
                return cls(**vmap)
            except _ValidationError:
                _hypothesis.assume(False)
                # Failsafe in case assume does something unexpected.
                raise AssertionError(
                    "'hypothesis.assume(False)' did not raise an "
                    "exception."
                )

    return strategy()
