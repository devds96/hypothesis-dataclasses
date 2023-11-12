import pytest

from hypothesis.strategies import integers
from hypothesis_dataclasses import dataclass, field_from, instances

from hypothesis_dataclasses._field_from import STRATEGY_METADATA_KEY


def test_not_a_dataclass_raises():
    """Test that an exception is raised if the class provided to
    `instances` is not a dataclass.
    """

    class A:
        pass

    with pytest.raises(TypeError, match=".*not a dataclass.*"):
        instances(A)


def test_metadata_key_provided_warns():
    """Tets that a warning is issued if the metadata key appears in the
    provided metadata.
    """

    with pytest.warns(UserWarning):

        @dataclass
        class A:
            i: int = field_from(
                integers(), metadata={STRATEGY_METADATA_KEY: None}
            )
