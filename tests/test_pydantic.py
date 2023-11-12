import pytest

from hypothesis import given, HealthCheck, settings
from hypothesis.strategies import data, DataObject, integers

from hypothesis_dataclasses import field_from, instances

try:
    import pydantic as _  # type: ignore # noqa: F401
except ImportError:
    PYDANTIC_UNAVAILABLE = True

    # We still have to create dataclasses because instances() requires
    # it. Otherwise the tests would fail before they start when this
    # module is run.
    from dataclasses import dataclass

    # The field_validator will always accept the field name and
    # therefore must return an inner decorator.
    def field_validator(*_, **__):  # noqa: F811

        def inner(*_, **__):
            pass

        return inner

else:
    PYDANTIC_UNAVAILABLE = False

    from pydantic import field_validator
    from pydantic.dataclasses import dataclass  # type: ignore [no-redef]


@dataclass
class PydanticDataclass:
    """Example dataclass containing three fields."""

    i: int = field_from(integers(0, 1))

    @field_validator('i')
    @staticmethod
    def validate_i(value: int) -> int:
        if value == 0:
            raise ValueError
        return value


@given(x=instances(PydanticDataclass))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
@pytest.mark.skipif(PYDANTIC_UNAVAILABLE, reason="Test requires pydantic.")
def test_pydantic_example(x: PydanticDataclass):
    """Tests for the `PydanticDataclass` testing the pydantic
    validator.
    """
    assert x.i == 1


@dataclass
class PydanticDataclassNeverValid:
    """Example pydantic dataclass which is never valid."""

    i: int = field_from(integers())

    @field_validator('i')
    @staticmethod
    def validate_i(value: int):
        raise ValueError("test")


@given(data=data())
@pytest.mark.skipif(PYDANTIC_UNAVAILABLE, reason="Test requires pydantic.")
def test_pydantic_disabled_exception_passed_through(data: DataObject):
    """Test that validation errors are passed through directly if
    pydantic is disabled.
    """

    with pytest.raises(ValueError, match="test"):
        data.draw(instances(
            PydanticDataclassNeverValid, disable_pydantic=True
        ))
