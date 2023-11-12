import pytest
import sys
import warnings

from dataclasses import asdict
from hypothesis import assume, given, HealthCheck, settings
from hypothesis.strategies import data, DataObject, integers
from hypothesis.errors import HypothesisDeprecationWarning, \
    NonInteractiveExampleWarning
from typing import FrozenSet, Union

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

from hypothesis_dataclasses import calloncedrawn, dataclass, field_from, \
    instances, PartialInstance


def test_calloncedrawn_examples():
    """Tests an example for @calloncedrawn."""

    num_calls = 0
    num_calls_2 = 0

    @dataclass
    class ExampleDataclass:
        """Example dataclass containing three fields."""

        i: int = field_from(integers(0, 1))

        j: int = field_from(integers(0, 1))

        k: int = field_from(integers(0, 1))

        ll: int = field_from(integers(0, 10))

        mm: int = field_from(integers(0, 10))

        num_calls: int = 0

        @calloncedrawn('i', 'j', 'k', 'j')
        @staticmethod
        def called_after_ijk(fields: FrozenSet[str], pi: PartialInstance):
            j = pi.j
            assume(pi.i == j)
            assume(j != pi.k)
            assert 'i' in fields
            assert 'j' in fields
            assert 'k' in fields
            assert len(fields) == 3
            assert hasattr(pi, 'i')
            assert hasattr(pi, 'i')
            assert hasattr(pi, 'k')
            assert not hasattr(pi, "ll")
            assert not hasattr(pi, "mm")
            nonlocal num_calls
            num_calls += 1

        @calloncedrawn("ll")
        @classmethod
        def call_after_ll(cls, fields: FrozenSet[str], pi: PartialInstance):
            assume(pi.ll > 5)
            assert cls is ExampleDataclass
            assert "ll" in fields
            assert len(fields) == 1
            assert hasattr(pi, 'i')
            assert hasattr(pi, 'i')
            assert hasattr(pi, 'k')
            assert hasattr(pi, "ll")
            assert not hasattr(pi, "mm")
            nonlocal num_calls_2
            num_calls_2 += 1

    for _ in range(10):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=NonInteractiveExampleWarning
            )
            x = instances(ExampleDataclass).example()
        j = x.j
        assert isinstance(j, int)
        assert x.i == j
        assert j != x.k
        assert isinstance(x.i, int)
        assert isinstance(x.k, int)
        assert isinstance(x.ll, int)
        assert isinstance(x.mm, int)
        assert x.ll > 5

        xpi = asdict(x)
        del xpi["mm"]

        nc2 = num_calls_2
        with warnings.catch_warnings():
            # Suppress "Using `assume` outside a property-based test is
            # deprecated"
            warnings.filterwarnings(
                "ignore",
                category=HypothesisDeprecationWarning
            )
            ExampleDataclass.call_after_ll(
                frozenset(["ll"]),
                PartialInstance(**xpi)
            )
        assert (nc2 + 1) == num_calls_2

        del xpi["ll"]
        nc = num_calls
        with warnings.catch_warnings():
            # Suppress "Using `assume` outside a property-based test is
            # deprecated"
            warnings.filterwarnings(
                "ignore",
                category=HypothesisDeprecationWarning
            )
            ExampleDataclass.called_after_ijk(
                frozenset(['i', 'j', 'k', 'j']),
                PartialInstance(**xpi)
            )
        assert (nc + 1) == num_calls

    assert num_calls > 0
    assert num_calls_2 > 0


def test_wrapped_instance_method_raises():
    """Test that instance methods wrapped in @calloncedrawn lead to an
    exception.
    """
    msg = ".*not a staticmethod or a classmethod.*"
    with pytest.raises(TypeError, match=msg):
        @dataclass
        class _:

            j: float

            @calloncedrawn('j')
            def draw_j(self, _, __, ___):
                raise AssertionError


@pytest.mark.parametrize("which", ("more", "less"))
@pytest.mark.parametrize("decorator", (classmethod, staticmethod))
def test_wrapped_invalid_number_of_arguments(
    which: Literal["more", "less"],
    decorator: Union[classmethod, staticmethod]
):
    """Test that the functions decorated with @calloncedrawn must have
    the correct number of arguments.
    """
    if decorator == staticmethod:
        exp_nparam = 2
        if which == "less":
            nparam = 0
        elif which == "more":
            nparam = 4
        else:
            raise AssertionError
    elif decorator == classmethod:
        exp_nparam = 3
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

                    def _drawn(cls, _, __, ___, ____):
                        raise AssertionError

                elif which == "less":

                    def _drawn(cls):  # type: ignore [misc]
                        raise AssertionError

            elif decorator == staticmethod:

                if which == "more":

                    def _drawn(_, __, ___, ____):  # type: ignore [misc]
                        raise AssertionError

                elif which == "less":

                    def _drawn():  # type: ignore [misc]
                        raise AssertionError

            func = decorator(_drawn)  # type: ignore [operator]
            draw_j = calloncedrawn('j')(func)


def test_incorrectly_applied_decorator_raises():
    """Test that an exception is raised if the decorator is applied
    directly, without specifying the field name.
    """
    with pytest.raises(RuntimeError, match=".*not a str.*"):
        @dataclass
        class _:

            @calloncedrawn
            @classmethod
            def drawn(cls, _, __, ___):
                raise AssertionError


INVALID_FIELD_MESSAGE_RE = r"Not a valid \(drawn\) field.*"


@given(data=data())
def test_invalid_field_name_non_existent(data: DataObject):
    """Test that an exception is raised if a non-existing field is
    specified at the decorator.
    """
    @dataclass
    class A:

        @calloncedrawn('k')
        @staticmethod
        def drawn(_, __):
            raise AssertionError

    with pytest.raises(AttributeError, match=INVALID_FIELD_MESSAGE_RE):
        data.draw(instances(A))


@given(data=data())
def test_invalid_field_name_non_drawn(data: DataObject):
    """Test that an exception is raised if a non-drawn field is
    specified at the decorator.
    """
    @dataclass
    class A:

        k: int = 5

        @calloncedrawn('k')
        @staticmethod
        def drawn(_, __):
            raise AssertionError

    with pytest.raises(AttributeError, match=INVALID_FIELD_MESSAGE_RE):
        data.draw(instances(A))


@dataclass
class Base:
    """Defines a base class for testing the @calloncedrawn decorator."""

    base_k: int = field_from(integers(0, 1))

    @calloncedrawn("base_k")
    @staticmethod
    def base_k_drawn(_, pi: PartialInstance):
        assume(pi.base_k == 0)


@dataclass
class DerivedNoOverride(Base):
    """Defines a derived class for testing the @calloncedrawn decorator.
    This class does not override the callback.
    """

    derived_k: int = field_from(integers(0, 1))

    @calloncedrawn("derived_k")
    @staticmethod
    def derived_k_drawn(_, pi: PartialInstance):
        assert hasattr(pi, "base_k")
        assert pi.base_k == 0
        assume(pi.derived_k == 1)


@given(instance=instances(DerivedNoOverride))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_calloncedrawn_inheritance_no_override(instance: DerivedNoOverride):
    """Test that inheritance is compatible with the `calloncedrawn`
    decorator.
    """
    assert instance.base_k == 0
    assert instance.derived_k == 1


@dataclass
class DerivedWithOverride(Base):
    """Defines a derived class for testing the @calloncedrawn decorator.
    This class overrides the parent class's callback.
    """

    derived_k: int = field_from(integers(0, 1))

    @calloncedrawn("derived_k")
    @staticmethod
    def derived_k_drawn(_, pi: PartialInstance):
        assert hasattr(pi, "base_k")
        assert pi.base_k == 1
        assume(pi.derived_k == 1)

    @calloncedrawn("base_k")
    @staticmethod
    def base_k_drawn(_, pi: PartialInstance):
        assume(pi.base_k == 1)


@given(instance=instances(DerivedWithOverride))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_calloncedrawn_inheritance_with_override(
    instance: DerivedWithOverride
):
    """Test that inheritance is compatible with the `calloncedrawn`
    decorator and that it is possible to override the callbacks in
    derived classes.
    """
    assert instance.base_k == 1
    assert instance.derived_k == 1
