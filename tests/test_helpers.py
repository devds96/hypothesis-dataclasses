import pytest

from dataclasses import dataclass, field, fields
from hypothesis.strategies import floats

from hypothesis_dataclasses import drawn_fields, field_from, will_draw


class ExampleDCNoDataclass:
    """Base class of the example dataclass. This class itself is not
    one, which will be used in one of the exception tests.
    """

    d_i: int

    d_j: float = field_from(floats())

    n_k: str = "abc"

    n_l: object = field(init=False)


@dataclass
class ExampleDC(ExampleDCNoDataclass):
    """The example dataclass to test the helper methods."""
    pass


def test_will_draw_example():
    """Test that the `will_draw` helper returns correct values using an
    example.
    """
    for f in fields(ExampleDC):
        name = f.name
        if name.startswith('d'):
            assert will_draw(f)
        elif name.startswith('n'):
            assert not will_draw(f)
        else:
            raise AssertionError


def test_drawn_fields_example():
    """Test that the `drawn_fields` helper returns the correct
    fields.
    """
    df = drawn_fields(ExampleDC)
    df_known = [f for f in fields(ExampleDC) if f.name.startswith('n')]
    assert len(df) == len(df_known)


def test_drawn_fields_raises_no_dataclass():
    """Test that the `drawn_fields` helper raises an exception if the
    provided type is not a dataclass.
    """
    with pytest.raises(TypeError, match=".*not a dataclass.*"):
        drawn_fields(ExampleDCNoDataclass)
