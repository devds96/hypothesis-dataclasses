from dataclasses import asdict, dataclass as builtin_dataclass
from hypothesis import assume, given
from hypothesis.strategies import data, DataObject, integers, just
from typing import Dict, Union

from hypothesis_dataclasses import dataclass, field_from, instances


class Unset:
    """A class whose values mark an unset field."""

    INSTANCE: "Unset"

    def __repr__(self) -> str:
        return "Unset"

    def __str__(self) -> str:
        return repr(self)


Unset.INSTANCE = Unset()


bool_or_unset = Union[bool, Unset]
"""The type of a boolean or unset field."""


@builtin_dataclass(frozen=True)
class ArgumentSpec:

    repr: bool_or_unset

    eq: bool_or_unset

    order: bool_or_unset

    unsafe_hash: bool_or_unset

    frozen: bool_or_unset

    match_args: bool_or_unset

    kw_only: bool_or_unset

    slots: bool_or_unset

    weakref_slot: bool_or_unset

    def __post_init__(self):
        assume(not (self.weakref_slot is True and self.slots is not True))
        assume(not (self.order is True and self.eq is False))

    def to_dict(self) -> Dict[str, object]:
        """Convert the instance to a dict.

        Returns:
            dict[str, object]: The mapping from the argument names to
                their values.
        """
        return {
            k: v for k, v in asdict(self).items() if not isinstance(v, Unset)
        }


@given(args=instances(ArgumentSpec), data=data())
def test_dataclass_construction(args: ArgumentSpec, data: DataObject):
    """Test that dataclasses can be correctly constructed using the
    decorator.
    """

    @dataclass(**args.to_dict())  # type: ignore
    class A:
        value: bool = field_from(just(True))

    strat = instances(A)
    assert data.draw(strat).value


@builtin_dataclass(frozen=True)
class FieldArgumentSpec:

    repr: bool_or_unset

    hash: bool_or_unset

    compare: bool_or_unset

    def to_dict(self) -> Dict[str, object]:
        """Convert the instance to a dict.

        Returns:
            dict[str, object]: The mapping from the argument names to
                their values.
        """
        return {
            k: v for k, v in asdict(self).items() if not isinstance(v, Unset)
        }


@given(args=instances(FieldArgumentSpec), data=data())
def test_dataclass_construction_field_params(
    args: FieldArgumentSpec,
    data: DataObject
):
    """Test that dataclasses can be correctly constructed using the
    decorator.
    """

    @dataclass(order=True)
    class A:
        value: int = field_from(
            integers(), **args.to_dict()  # type: ignore
        )

    strat = instances(A)
    a = data.draw(strat)
    b = data.draw(strat)

    if args.compare is not False:
        if a.value > b.value:
            assert a > b
        elif a.value < b.value:
            assert b > a
        else:
            assert a == b

    if args.repr is not False:
        assert "value" in repr(a)
        assert "value" in repr(b)
