"""This module contains the `dataclass` decorator."""

import dataclasses as _dataclasses
import functools as _functools
import sys as _sys

from typing import Callable as _Callable, Optional as _Optional, \
    overload as _overload, Type as _Type, TypeVar as _TypeVar

if _sys.version_info < (3, 11):
    from typing_extensions import dataclass_transform as _dataclass_transform
else:
    from typing import dataclass_transform as _dataclass_transform


_T = _TypeVar("_T")


@_dataclass_transform()
@_overload
def dataclass(
    cls: None = None,
    *,
    repr: _Optional[bool] = None,
    eq: _Optional[bool] = None,
    order: _Optional[bool] = None,
    unsafe_hash: _Optional[bool] = None,
    frozen: _Optional[bool] = None,
    # 3.10
    match_args: _Optional[bool] = None,
    kw_only: _Optional[bool] = None,
    slots: _Optional[bool] = None,
    # 3.11
    weakref_slot: _Optional[bool] = None
) -> _Callable[[_Type[_T]], _Type[_T]]:
    pass


@_dataclass_transform()
@_overload
def dataclass(
    cls: _Type[_T],
    *,
    repr: _Optional[bool] = None,
    eq: _Optional[bool] = None,
    order: _Optional[bool] = None,
    unsafe_hash: _Optional[bool] = None,
    frozen: _Optional[bool] = None,
    # 3.10
    match_args: _Optional[bool] = None,
    kw_only: _Optional[bool] = None,
    slots: _Optional[bool] = None,
    # 3.11
    weakref_slot: _Optional[bool] = None
) -> _Type[_T]:
    pass


@_dataclass_transform()
def dataclass(
    cls: _Optional[_Type] = None,
    *,
    repr: _Optional[bool] = None,
    eq: _Optional[bool] = None,
    order: _Optional[bool] = None,
    unsafe_hash: _Optional[bool] = None,
    frozen: _Optional[bool] = None,
    # 3.10
    match_args: _Optional[bool] = None,
    kw_only: _Optional[bool] = None,
    slots: _Optional[bool] = None,
    # 3.11
    weakref_slot: _Optional[bool] = None
):
    """Create a dataclass. See also the documentation of the same
    parameters of the builtin `dataclass` function. This function should
    be used as a decorator.
    Currently, this decorator does nothing that is absoluteley necessary
    and it is possible to use the bultin or pydantic @dataclass
    decorators instead. In the future, this decorator might be used to
    allow for additional configuration.

    Args:
        cls (type, optional): The class to transform into a dataclass.
            This is normally not passed directly if this function is
            used as a decorator on the class.
        repr (bool, optional): Whether to add the dataclass __repr__ to
            the class. Defaults to True.
        eq (bool, optional): Whether to defind __eq__ for the class.
            Defaults to True.
        order (bool, optional): Whether to defined the ordering methods
            such as __lt__ and __gt__ for the dataclass. Defaults to
            False.
        unsafe_hash (bool, optional): Whether to add a __hash__
            functions even when this is unsafe. Defaults to False.
        frozen (bool, optional): Whether to make the instances of the
            dataclass frozen. Defaults to False.
        match_args (bool, optional): Whether to generate the
            __match_args__ on the class. Defaults to True. This argument
            will be ignored below Python 3.10.
        kw_only (bool, optional): Whether to mark all fields of the
            dataclass as keyword-only. Defaults to False. This argument
            will be ignored below Python 3.10.
        slots (bool, optional): Whether to make the dataclass a
            __slots__ dataclass. Defaults to False. This argument will
            be ignored below Python 3.10.
        weakref_slot (bool, optional): Whether to add a __weakref__ slot
            to make instances weakref-able. Defaults to False. If True,
            `slots` must also be True. This argument will
            be ignored below Python 3.11.
    """
    if repr is None:
        repr = True
    if eq is None:
        eq = True
    if order is None:
        order = False
    if unsafe_hash is None:
        unsafe_hash = False
    if frozen is None:
        frozen = False
    if match_args is None:
        match_args = True
    if kw_only is None:
        kw_only = False
    if slots is None:
        slots = False
    if weakref_slot is None:
        weakref_slot = False

    base = _functools.partial(
        _dataclasses.dataclass,
        repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash,
        frozen=frozen
    )

    if _sys.version_info >= (3, 10):
        base = _functools.partial(
            base, match_args=match_args, kw_only=kw_only, slots=slots
        )

    if _sys.version_info >= (3, 11):
        base = _functools.partial(
            base, weakref_slot=weakref_slot
        )

    def setup(t: _Type):
        # It is important to cache the return value of the call and
        # never cls itself since a new type might be constructed, for
        # example when slots is True.
        dc = base(t)
        if not isinstance(dc, type):
            # Failsafe in case a function is returned instead of a type.
            # This would hint at incorrect use of the decorator.
            raise AssertionError(
                "Expected dataclass function to return a type."
            )
        return dc

    if cls is None:
        return setup
    return setup(cls)
