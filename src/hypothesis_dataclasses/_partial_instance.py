"""This module defines the `PartialInstance`."""

from types import SimpleNamespace as _SimpleNamespace


class PartialInstance(_SimpleNamespace):
    """A partially drawn instance. Fields of the full instance may or
    may not be defined on this class. `hasattr` can for example be used
    to check for present fields.
    """
    pass
