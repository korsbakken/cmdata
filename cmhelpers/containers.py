"""Module for useful container types and associated functions.

Classes
-------
FrozenDict
    A UserDict subclass that implements an immutable dictionary.
"""
import typing as tp
from collections import UserDict


class FrozenDict(UserDict):
    def __init__(
        self,
        initdict: tp.Optional[tp.Mapping] = None,
        copy_initdict: bool = True,
        **kwargs
    ):
        if initdict is None:
            initdict = dict()
        elif copy_initdict:
            initdict = dict(initdict)
        initdict |= kwargs
        self.data = initdict
    def __setitem__(self, key: tp.Hashable, item: tp.Any) -> None:
        raise AttributeError(
            'FrozenDict does not support setting or altering items.'
        )
    def __delitem__(self, key: tp.Hashable) -> None:
        raise AttributeError(
            'FrozenDict does not support deleting items.'
        )
###END class FrozenDict
