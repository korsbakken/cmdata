"""Functionality for accessing YAML files with labels.

Contains the class LabelfileManager, which holds paths to yaml files, and
provides the `get_label_map` function to obtain `LabelMap` instances, and the
`labelsets` property that contains avilable label sets in each yaml file."""

import typing as tp
from pathlib import Path
from collections import UserDict

import pandas as pd

from . import LabelMap
from . import helpers


class FrozenDict(UserDict):
    def __init__(self, initdict: dict = None, **kwargs):
        if initdict is None:
            initdict = dict()
        initdict |= kwargs
        self.data = initdict.copy()
    def __setitem__(self, key: tp.Hashable, item: tp.Any) -> None:
        raise AttributeError(
            'FrozenDict does not support setting or altering items.'
        )
    def __delitem__(self, key: tp.Hashable) -> None:
        raise AttributeError(
            'FrozenDict does not support deleting items.'
        )
###END class FrozenDict


class LabelfileManager:

###END class LabelfileManager
