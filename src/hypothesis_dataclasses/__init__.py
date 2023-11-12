"""This module aims to extend the built in `from_type` strategy of
hypothesis by providing control over the strategies from which
individual fields of a dataclass are drawn.

Examples:
>>> from dataclasses import dataclass
>>> from hypothesis.strategies import integers, text
...
>>> @dataclass
... class ExampleDClass:
...     index: int = field_from(integers(0, 10))
...     value: str = field_from(text())
...
>>> # We can draw examples from the strategy returned by this
>>> # function
>>> example_instance = instances(ExampleDClass).example()
>>> # Note that the actual values of the index and value fields
>>> # may be different on each run.
>>> print(isinstance(example_instance.index, int))
True
>>> print(0 <= example_instance.index <= 10)
True
>>> print(isinstance(example_instance.value, str))
True

It is also possible to rely on `from_type` to automatically resolve the
types of the dataclass fields. However, then it is not possible to for
example define the range from which integers are drawn:
>>> from dataclasses import dataclass
...
>>> @dataclass
... class ExampleDClassAuto:
...     int_value: int
...     str_value: str
...     float_value: float
...
>>> example_instance = instances(ExampleDClassAuto).example()
>>> print(isinstance(example_instance.int_value, int))
True
>>> print(isinstance(example_instance.str_value, str))
True
>>> print(isinstance(example_instance.float_value, float))
True

It is also possible to use the __post_init__ method and pydantic for
more control over the values of the dataclass fields. See the unit tests
for examples, in particular `test_examples.py` and `test_pydantic.py`.
"""

__all__ = [
    "dataclass",
    "field_from",
    "manualdraw",
    "PartialInstance",
    "drawn_fields", "instances", "will_draw",
    "calloncedrawn"
]

__author__ = "devds96"
__email__ = "src.devds96@gmail.com"
__license__ = "MIT"
__version__ = "0.1.0"


from ._dataclass import dataclass
from ._field_from import field_from
from ._manual_draw import manualdraw
from ._partial_instance import PartialInstance
from ._instances import drawn_fields, instances, will_draw
from ._call_once_drawn import calloncedrawn
