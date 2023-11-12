"""This module contains the `field_from` helper class used for the field
definitions.
"""

import dataclasses as _dataclasses
import functools as _functools
import sys as _sys
import warnings as _warnings

from hypothesis.strategies import SearchStrategy as _SearchStrategy
from typing import Any as _Any, Mapping as _Mapping, \
    Optional as _Optional, TypeVar as _TypeVar


_T = _TypeVar("_T")


STRATEGY_METADATA_KEY = object()
"""The object used as the key int the `metadata` mapping of the
dataclass fields to identify the strategy associated with the field."""


def field_from(
    st: _SearchStrategy[_T],
    *,
    repr: _Optional[bool] = None,
    hash: _Optional[bool] = None,
    compare: _Optional[bool] = None,
    metadata: _Optional[_Mapping[_Any, _Any]] = None,
    # 3.10
    kw_only: _Optional[bool] = None
) -> _T:
    """Provides a `SearchStrategy` for a dataclass field.

    Args:
        st (SearchStrategy[_T]): The `SearchStrategy` used by hypothesis
            to provide values of the field.
        repr (bool, optional): Whether to include the field in the repr.
            Defaults to True.
        hash (bool, optional): Whether to include the field in the hash.
            Defaults to True.
        compare (bool, optional): Whether to include the field in
            comparisons. Defaults to True.
        metadata (Mapping[Any, Any], optional): Additional metadata to
            attach to the field. If the metadata key for the strategies
            used by this module already appears in this mapping, a
            warning is issued and the value is overwritten by the
            provided strategy.
        kw_only (bool, optional): Whether to make the field a
            keyword-only parameter to __init__. Defaults to False. This
            argument will be ignored below Python version 3.10.

    Returns:
        T: Returns the corresponding dataclass field. The type
            annotation signals the correct type associated with the
            field (inferred from `st`) to allow proper type checking.
    """

    if metadata is not None:
        if STRATEGY_METADATA_KEY in metadata:
            _warnings.warn(
                "The '_STRATEGY_METADATA_KEY' was already found in the "
                "provided metadata mapping. This will be overwritten."
            )
        md = dict(metadata)
        md[STRATEGY_METADATA_KEY] = st
    else:
        md = {STRATEGY_METADATA_KEY: st}

    field = _dataclasses.field

    if _sys.version_info >= (3, 10):
        if kw_only is None:
            kw_only = False
        field = _functools.partial(  # type: ignore [assignment]
            field, kw_only=kw_only
        )

    if repr is None:
        repr = True
    if hash is None:
        hash = True
    if compare is None:
        compare = True

    return field(repr=repr, hash=hash, compare=compare, metadata=md)
