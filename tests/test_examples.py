import pytest
import sys

from dataclasses import dataclass as builtin_dataclass, field
from hypothesis import assume, given, HealthCheck, settings
from hypothesis.strategies import data, DataObject, floats, integers
from typing import Union

from hypothesis_dataclasses import dataclass, field_from, instances


@dataclass
class ExampleDataclass:
    """Example dataclass containing three fields."""

    i: int = field_from(integers(0, 5))

    j: float = field_from(floats(0, 1))

    k: int = field_from(integers(0, 10))

    const: int = 5

    const_2: int = field(init=False)

    def __post_init__(self):
        assume(self.i == self.k)
        self.const_2 = 6


@given(x=instances(ExampleDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_examples(x: ExampleDataclass):
    """Tests for the `ExampleDataclass`."""
    assert 0 <= x.i <= 5
    assert 0 <= x.j <= 1
    assert x.i == x.k
    assert isinstance(x.i, int)
    assert isinstance(x.j, float)
    assert isinstance(x.k, int)
    assert x.const == 5
    assert x.const_2 == 6


@given(x=instances(ExampleDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_examples_second_test_same_dataclass(x: ExampleDataclass):
    """Tests for the `ExampleDataclass`, testing the reuse of the
    dataclass and the cached strategy map.
    """
    assert 0 <= x.i <= 5
    assert 0 <= x.j <= 1
    assert x.i == x.k
    assert isinstance(x.i, int)
    assert isinstance(x.j, float)
    assert isinstance(x.k, int)


@builtin_dataclass
class BuiltinDataclass:
    """Example dataclass containing three fields."""

    i: int = field_from(integers(0, 1))

    def __post_init__(self):
        assume(self.i == 0)


@given(x=instances(BuiltinDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_builtin_dataclass_example(x: BuiltinDataclass):
    """Tests for the `BuiltinDataclass` testing compatibility with the
    builtin dataclass decorator.
    """
    assert x.i == 0


@given(data=data())
@pytest.mark.parametrize("value", (True, False, None))
@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="'kw_only' is only available in Python 3.10 and above."
)
def test_kw_only_field(value: Union[bool, None], data: DataObject):
    """Tests for the kw_only argument of `field_from`."""

    @dataclass
    class ExampleDataclassKWOnlyField:
        """Example dataclass containing a kw only field."""

        i: float = field_from(floats(0, 1), kw_only=value)

    instance = data.draw(instances(ExampleDataclassKWOnlyField))

    assert 0 <= instance.i <= 1
