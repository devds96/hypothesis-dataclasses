# hypothesis-dataclasses

![Tests](https://github.com/devds96/hypothesis-dataclasses/actions/workflows/tests.yml/badge.svg)
[![Coverage](https://github.com/devds96/hypothesis-dataclasses/raw/gh-pages/coverage/coverage_badge.svg)](https://devds96.github.io/hypothesis-dataclasses/coverage/index.html)


An extension for `hypothesis` with which dataclasses can be used to
combine and define new strategies.

## Introduction
[`Hypothesis`](https://hypothesis.readthedocs.io/en/latest/#welcome-to-hypothesis)
is a Python library for writing parametrized tests in
Python. It can for example be combined with `pytest` and allows for
easily running tests with many different examples. Data is provided by
`strategies` which defined how and which data can be generated.
`Hypothesis` also has a built-in mechanism for combining strategies, the
`composite` strategy.

This package aims to extends this functionality by allowing Python
dataclasses to define composite strategies.

To this end, this module defines the `instances` hypothesis
`SearchStrategy` which accepts a dataclass as its argument. (More
precisely, this is a function returning a `SearchStrategy` object.) <br>
Additionally, it defines a `from_field` function which accepts search
strategies and returns a dataclass field. This allows fields to be
defined as being drawn from a certain strategy. Two helper functions
`drawn_fields` and `will_draw` can be used to get all the fields of a
dataclass that will be drawn and to check whether a particualar field
will be drawn.


## Examples

### 1. Basic Usage
A basic minimal example using the core functionality would look like
this:
```python
from hypothesis.strategies import floats
from hypothesis_dataclasses import dataclass, field_from, instances


@dataclass
class UnitSquarePoint:
    x1: float = field_from(floats(0, 1))
    x2: float = field_from(floats(0, 1))


example_point = instances(UnitSquarePoint).example()
print(example_point)
```
This will first define the dataclass `UnitSquarePoint` as a class with
two fields `x1` and `x2`. These are assigned the strategy `floats(0, 1)`
using `field_from`. Then, the `instances` strategy is used to generate
an example for the dataclass which is finally printed. This example will
be an instance of `UnitSquarePoint` and the fields will be drawn from
their respective strategies. In principle, this example shows how to
generate random points in the unit square [0, 1] &times; [0, 1] with
coordinates `x1` and `x2`.

A more general case would look like this:
```python
from dataclasses import dataclass
from hypothesis_dataclasses import instances


@dataclass
class Point:
    x1: float
    x2: float


example_point = instances(Point).example()
print(example_point)
```
This will generate arbitrary points with random `float` values drawn and
assigned to `x1` and `x2`. Generally, the
`hypothesis.strategies.from_type` strategy is applied to the type
annotation of fields that do not explicitly set a strategy using
`field_from`. Note that, in this case, this means that &#177;`inf`
and `nan` ("Not a Number") values may also be drawn for `x1` and `x2`.

Here, the `@hypothesis_dataclasses.dataclass` decorator has also been
replaced with the builtin `@dataclass` decorator. Currently, there is
no difference between these two decorators except that
`@hypothesis_dataclasses.dataclass` does not provide an `init` argument
and that arguments which are not available, such as `slots` in Python
versions below 3.10, will be silently ignored. <br>

Note that using the builtin `@dataclass` with `init=False` will fail
during construction of the instances. In general, a proper `__init__`
method allowing for the drawn fields to be provided as keyword arguments
must be provided.

There are a few additional caveats:
- Consequently, fields that have `init=False` set will not be drawn,
  even if they appear as constructor arguments.
- Fields that define a default value will not be drawn and will retain
  that value.


### 2. More Control over How Fields Are Drawn
In order to define dependent fields, it is possible to define
`@classmethod` or `@staticmethod` callback functions that will be called
to draw the values of certain fields:
```python
from hypothesis.strategies import DrawFn, floats
from hypothesis_dataclasses import dataclass, field_from, instances, \
    manualdraw, PartialInstance


@dataclass
class TwoFloats:
    lower_bound: float = field_from(floats(0, 1))
    value: float

    @manualdraw("value")
    @staticmethod
    def draw_value(
        draw: DrawFn, field: str, pi: PartialInstance
    ) -> float:
        return draw(floats(pi.lower_bound, 1))


example_instance = instances(TwoFloats).example()
print(example_instance)
```
In this example, a value for the field `lower_bound` is drawn from the
interval [0, 1] are drawn. Ater that, `draw_value` is called with a
hypothesis `DrawFn` followed by the field name and a `PartialInstance`
object containing the already drawn fields. Inside the function, a value
from the interval [`lower_bound`, 1] is drawn and returned. This value
will be assigned to the `value` field.

The second `str` parameter is provided for the case when multiple field
values are passed to the `@manualdraw` decorator. The function will then
be called for all of these fields and the `field` parameter specifies
which field is drawn with the current call.

Note that if `@classmethod` is used instead of `@staticmethod`, the
additional `cls` parameter would have to be added to the `draw_value`
function, just as with regular classmethods.

Furthermore, it is also possible to call `hypothesis.assume` in this
callback in order to reject the partially drawn example if necessary.
However, it is always better to provide `hypothesis` with the
constraints instead of rejecting already drawn examples, if possible.
This is why the `@manualdraw` decorator is preferrable to the validation
options presented in points [3](#3-callbacks-for-fields) and
[4](#4-pydantic-support) below.


### 3. Callbacks for Fields
It is possible to define `@classmethod` or `@staticmethod` callback
functions that will be called after the values for a certain set of
fields have been determined. This can be used to perform additional
checks on certain subsets of the dataclass fields using
`hypothesis.assume`:
```python
from hypothesis import assume
from hypothesis.strategies import floats
from hypothesis_dataclasses import calloncedrawn, dataclass, \
    field_from, instances, PartialInstance
from typing import FrozenSet


@dataclass
class UnitSquarePointNotIn11Circle:
    x1: float = field_from(floats(0, 1))
    x2: float = field_from(floats(0, 1))

    @calloncedrawn("x1", "x2")
    @staticmethod
    def validate(fields: FrozenSet[str], pi: PartialInstance):
        # Make sure the point is NOT inside the circle around (0.5, 0.5)
        # with radius 0.4. (And also not on its radius.)
        assume(((pi.x1 - 0.5) ** 2 + (pi.x2 - 0.5) ** 2) > (0.4 ** 2))


example_point = instances(UnitSquarePointNotIn11Circle).example()
print(example_point)
```
In this example, the `validate` function is called after `x1` and `x2`
have been drawn. The first parameter of type `FrozenSet[str]` contains
the fields passed to the decorator. All of these fields have values
assigned when the callback is called. In order to access them, the
partially drawn instance is provided as the second argument. Note that
there is no guarantee that the sampling of `x1` and `x2` is uniform
over [0, 1] &times; [0, 1].

Note that if `@classmethod` is used instead of `@staticmethod`, the
additional `cls` parameter would have to be added to the `validate`
function, just as with regular classmethods.

Additionally, it would have been possible to call `hypothesis.assume` in
a `__post_init__` function defined on the dataclass which will be called
after the `__init__` method has initialized the instance. However, if
the class has many fields that may be drawn, it might be possible and
more efficient to check a subset of the values even before all values
are drawn. In this case, the `@calloncedrawn` decorator is useful.
However, if possible, it is always preferrable to use `@manualdraw`,
see point [2](#2-more-control-over-how-fields-are-drawn) above.

Note that if there are multiple callbacks to be called after a certain
set of fields has been drawn, then the order in which these will be
called is undefined.


### 4. Pydantic Support
This package also has support for
[`pydantic`](https://docs.pydantic.dev/latest/): `field_validator`s can
be used to ensure that fields have certain values or that certain
fields' values have certain relations. `Pydantic` is an optional
dependency, which will normally not be automatically installed when this
package is installed, see the [installation section](#installation)
below.

An example using `pydantic` would be:
```python
from hypothesis.strategies import floats
from hypothesis_dataclasses import field_from, instances
from pydantic.dataclasses import dataclass
from pydantic import field_validator


@dataclass
class SpecialPoints:
    x1: float = field_from(floats(0, 1))
    x2: float = field_from(floats(0, 1))

    @field_validator("x1")
    def validate_x1(value: float) -> float:
        if not (0.3 < value < 0.7):
            raise ValueError
        return value


example_point = instances(SpecialPoints).example()
print(example_point)
```
Here, we restrict the set of points to points for which
0.3 &#8804; `x1` &#8804; 0.7.

Note that `pydantic` validators will be called after the `__init__`
function has constructed the instance. This means, that this method
might not always be the most performant option, for example if many
fields are drawn and only one is validated. The options listed above in
points [2](#2-more-control-over-how-fields-are-drawn) and
[3](#3-callbacks-for-fields) may be more useful in this case.

Furthermore, in order to enable `pydantic`'s `field_validators`, the
`pydantic` `@dataclass` decorator must be used instead of the bultin
decorator or the decorator provided by this package.


### 5. Inheritance
It is possible to extend existing dataclass defined strategies using
inheritance. In this case, fields defined in parent classes will be
drawn before the fields of subclasses. This also means that
`@calloncedrawn` and `@drawmanually` callbacks can be overridden by
naming the functions for the callbacks the same as the callbacks defined
in the parent class.

A simple example:
```python
from dataclasses import dataclass
from hypothesis.strategies import DrawFn, floats
from hypothesis_dataclasses import field_from, instances, manualdraw, \
    PartialInstance


@dataclass
class BaseClass:
    base_float: float = field_from(floats(0, 1))


@dataclass
class DerivedClass(BaseClass):
    derived_float: float = field_from(floats(4, 5))

    @manualdraw("base_float")
    @staticmethod
    def draw_base_float(
        draw: DrawFn, field: str, pi: PartialInstance
    ) -> float:
        return draw(floats(2, 3))


base_example = instances(BaseClass).example()
print(base_example)

derived_example = instances(DerivedClass).example()
print(derived_example)
```

As you can see when executing this example, the derived class now has
both fields defined and their values were drawn from the strategies as
expected, with `base_float` being drawn from `floats(2, 3)` for the
derived class.


### 6. More Examples
Further examples can also be found in the docstrings of:
- the `hypothesis_dataclasses` package itself (that is, the
    _\_\_init\_\_.py_ module file),
- the `instances` strategy,
- the `manualdraw` decorator,
- the `calloncedrawn` decorator

and in the unit tests in the _tests_ directory.


## Installation
The minimal supported version of Python for this package is Python 3.7.

You can install this package directly from git using pip:
```shell
pip install git+https://github.com/devds96/hypothesis-dataclasses
```

Alternatively, you can clone the git repo and run in its root directory:
```shell
pip install .
```

Both of these options will install the package without the optional
dependence `pydantic`. If this is already installed, the provided
functionality will still be available.

If you want to install the package with `pydantic` directly use
```shell
pip install git+https://github.com/devds96/hypothesis-dataclasses#egg=hypothesis-dataclasses[pydantic]
```
or
```shell
pip install .[pydantic]
```
depending on whether you install directly from github or from a local
repo. See also
[this answer](https://stackoverflow.com/a/30239714) on Stack Overflow
which explains how to install extra dependencies when installing from
git or a local repo.