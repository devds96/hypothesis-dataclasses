import pytest
import sys

from hypothesis import given, HealthCheck, settings
from hypothesis.strategies import data, DataObject, DrawFn, floats, \
    integers
from typing import Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from hypothesis_dataclasses import dataclass, field_from, instances, \
    manualdraw, PartialInstance


@dataclass
class ManualDrawExampleDataclass:
    """Example dataclass containing three fields."""

    i: int = field_from(integers(0, 5))

    j: float  # type: ignore [misc]

    k: int  # type: ignore [misc]

    @manualdraw('j')
    @staticmethod
    def draw_j(draw: DrawFn, field: str, others: PartialInstance) -> float:
        assert field == 'j'
        assert hasattr(others, 'i')
        return draw(floats(-1, 0))

    @manualdraw('k')
    @classmethod
    def draw_k(cls, draw: DrawFn, field: str, others: PartialInstance) -> int:
        assert field == 'k'
        assert hasattr(others, 'i')
        assert hasattr(others, 'j')
        return draw(integers(0, 1))


@given(x=instances(ManualDrawExampleDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_manualdraw_example(x: ManualDrawExampleDataclass):
    """Tests for the `ExampleDataclass`."""
    assert 0 <= x.i <= 5
    assert -1 <= x.j <= 0
    assert x.k in (0, 1)
    assert isinstance(x.i, int)
    assert isinstance(x.j, float)
    assert isinstance(x.k, int)


@given(data=data())
def test_field_refd_multiple_times_raises(data: DataObject):
    """Test that a field referenced in multiple @manualdraw functions
    leads to an exception.
    """

    @dataclass
    class C:

        j: float

        @manualdraw('j')
        @staticmethod
        def draw_j(_, __, ___):
            raise AssertionError

        @manualdraw('j')
        @staticmethod
        def draw_j_2(_, __, ___):
            raise AssertionError

    with pytest.raises(ValueError, match=".*referenced by multiple.*"):
        data.draw(instances(C))


def test_wrapped_instance_method_raises():
    """Test that instance methods wrapped in @manualdraw lead to an
    exception.
    """
    msg = ".*not a staticmethod or a classmethod.*"
    with pytest.raises(TypeError, match=msg):
        @dataclass
        class _:

            j: float

            @manualdraw('j')
            def draw_j(self, _, __, ___):
                raise AssertionError


@pytest.mark.parametrize("which", ("more", "less"))
@pytest.mark.parametrize("decorator", (classmethod, staticmethod))
def test_wrapped_invalid_number_of_arguments(
    which: Literal["more", "less"],
    decorator: Union[classmethod, staticmethod]
):
    """Test that the functions decorated with @manualdraw must have the
    correct number of arguments.
    """
    if decorator == staticmethod:
        exp_nparam = 3
        if which == "less":
            nparam = 0
        elif which == "more":
            nparam = 4
        else:
            raise AssertionError
    elif decorator == classmethod:
        exp_nparam = 4
        if which == "less":
            nparam = 1
        elif which == "more":
            nparam = 5
        else:
            raise AssertionError
    else:
        raise AssertionError

    msg = f".*Expected {exp_nparam}, got {nparam}.*"
    with pytest.raises(TypeError, match=msg):

        @dataclass
        class _:

            j: float

            if decorator == classmethod:

                if which == "more":

                    def _draw(cls, _, __, ___, ____):
                        raise AssertionError

                elif which == "less":

                    def _draw(cls):  # type: ignore [misc]
                        raise AssertionError

            elif decorator == staticmethod:

                if which == "more":

                    def _draw(_, __, ___, ____):  # type: ignore [misc]
                        raise AssertionError

                elif which == "less":

                    def _draw():  # type: ignore [misc]
                        raise AssertionError

            func = decorator(_draw)  # type: ignore [operator]
            draw_j = manualdraw('j')(func)


def test_incorrectly_applied_decorator_raises():
    """Test that an exception is raised if the decorator is applied
    directly, without specifying the field name.
    """
    with pytest.raises(RuntimeError, match=".*not a str.*"):
        @dataclass
        class _:

            @manualdraw
            @classmethod
            def draw(cls, _, __, ___):
                raise AssertionError


@dataclass
class ManualDrawMultipleSameFunctionExampleDataclass:
    """Example dataclass containing three fields."""

    i: int = field_from(integers(0, 5))

    j: float  # type: ignore [misc]

    k: int  # type: ignore [misc]

    @manualdraw('j', 'k')
    @staticmethod
    def draw_jk(draw: DrawFn, field: str, others: PartialInstance) -> float:
        if field == 'j':
            assert hasattr(others, 'i')
            return draw(floats(-1, 0))
        elif field == 'k':
            assert hasattr(others, 'i')
            assert hasattr(others, 'j')
            return draw(integers(0, 1))
        raise AssertionError


@given(x=instances(ManualDrawMultipleSameFunctionExampleDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_draw_multiple_fields_same_function(
    x: ManualDrawMultipleSameFunctionExampleDataclass
):
    """Test that multiple fields can be correcly drawn using the same
    decorated function.
    """
    assert 0 <= x.i <= 5
    assert -1 <= x.j <= 0
    assert x.k in (0, 1)
    assert isinstance(x.i, int)
    assert isinstance(x.j, float)
    assert isinstance(x.k, int)


@dataclass
class Base:
    """Defines a base class for testing the @manualdraw decorator.
    """

    base_k: int

    base_k2: int = field_from(integers(0, 1))

    @manualdraw("base_k")
    @staticmethod
    def draw_base_k(draw: DrawFn, field: str, pi: PartialInstance) -> int:
        assert field == "base_k"
        return draw(integers(0, 1))


@dataclass
class DerivedNoOverride(Base):
    """Defines a derived class for testing the @manualdraw decorator.
    This class does not override the draw callback but instead defines
    and additional callback not present in the parent class.
    """

    derived_k: int  # type: ignore [misc]

    @manualdraw("derived_k")
    @staticmethod
    def draw_derived_k(draw: DrawFn, field: str, pi: PartialInstance) -> int:
        assert field == "derived_k"
        assert hasattr(pi, "base_k")
        return draw(integers(1, 2))

    @manualdraw("base_k2")
    @staticmethod
    def draw_derived_k2(draw: DrawFn, field: str, pi: PartialInstance) -> int:
        assert field == "base_k2"
        assert hasattr(pi, "base_k")
        assert not hasattr(pi, "derived_k")
        return draw(integers(2, 3))


@given(instance=instances(DerivedNoOverride))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_manualdraw_inheritance_no_override(instance: DerivedNoOverride):
    """Test that inheritance is compatible with the `manualdraw`
    decorator.
    """
    assert instance.base_k in (0, 1)
    assert instance.derived_k in (1, 2)
    assert instance.base_k2 in (2, 3)


@dataclass
class DerivedWithOverride(Base):
    """Defines a derived class for testing the @manualdraw decorator.
    This class overrides the parent class's draw callback.
    """

    derived_k: int = field_from(integers(0, 1))

    @manualdraw("base_k")
    @staticmethod
    def draw_base_k(draw: DrawFn, field: str, pi: PartialInstance) -> int:
        assert field == "base_k"
        return draw(integers(3, 4))


@given(instance=instances(DerivedWithOverride))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_manualdraw_inheritance_with_override(instance: DerivedWithOverride):
    """Test that inheritance is compatible with the `manualdraw`
    decorator and that it is possible to override the draw callbacks in
    derived classes.
    """
    assert instance.base_k in (3, 4)
    assert instance.derived_k in (0, 1)
