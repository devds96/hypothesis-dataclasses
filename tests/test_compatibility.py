from dataclasses import fields
from hypothesis import given, HealthCheck, settings
from hypothesis.strategies import integers

from hypothesis_dataclasses import dataclass, field_from, instances
from hypothesis_dataclasses._field_from import STRATEGY_METADATA_KEY


THIRD_PARTY_VALUE = "third_party_value"
"""An example value for metadata stored in the field of a dataclass
originating from a third party library."""


THIRD_PARTY_KEY = "third_party_key"
"""An example key from a third party library extending the
`field_from`."""


@dataclass
class DataclassWithThirdPartyMetadataField:
    """Example dataclass containing three fields."""

    edfield: int = field_from(
        integers(0, 5),
        metadata={THIRD_PARTY_KEY: THIRD_PARTY_VALUE}
    )
    """The test field containing extra metadata."""


@given(x=instances(DataclassWithThirdPartyMetadataField))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_third_party_metadata_key_examples(
    x: DataclassWithThirdPartyMetadataField
):
    """Tests for the `DataclassWithThirdPartyMetadataField`."""
    i = x.edfield
    assert isinstance(i, int)
    assert 0 <= i <= 5


def test_metadata_key_preserved():
    """Test that the `THIRD_PARTY_KEY` is preserved."""
    fs = fields(DataclassWithThirdPartyMetadataField)
    assert len(fs) == 1
    field = fs[0]
    metadata = field.metadata
    assert len(metadata) == 2
    assert THIRD_PARTY_KEY in metadata
    assert THIRD_PARTY_VALUE == metadata[THIRD_PARTY_KEY]
    assert STRATEGY_METADATA_KEY in metadata
