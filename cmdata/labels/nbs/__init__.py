"""Label definitions and mappings for China NBS statistics."""
import typing as tp
from pathlib import Path
from collections import UserDict

import pandas as pd

from .. import LabelMap
from .. import helpers


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

_yamlfiles_root: Path = Path(__file__).parent

_yamlfiles_relative_paths: tp.Dict[str, Path] = {
    'monthly_stats': 'nbs_monthly_labels.yaml'
}

yamlfiles: tp.Dict[str, Path] = FrozenDict(
    {_key: _yamlfiles_root / _filename
     for _key, _filename in _yamlfiles_relative_paths.items()}
)
"""Dict with paths to label definitions for different NBS datasets."""

labelsets: FrozenDict = FrozenDict(
    # {_key: list(_yamldict.keys()) for _key, _yamldict in helpers.yaml_utils.read_yaml(yamlfiles.items())}
    {_key: list(helpers.yaml_utils.read_yaml(_file).keys())
     for _key, _file in yamlfiles.items()}
)
"""Label set identifiers in each NBS label definition file."""

def get_label_map(file: str, labelset: str) -> LabelMap:
    """Get a `LabelMap` instance with NBS labels.
    
    Parameters
    ----------
    file : str
        File identifier to get labels from. Valid values are any of the keys in
        the module attribute `yamlfiles` (a dict).
    labelset : str
        The name of the label set to get from `file`. Valid values are listed
        in `labelsets[file]`.

    Returns
    -------
    LabelMap
    """
    return LabelMap.from_yaml(
        yamlfile=yamlfiles[file],
        key=labelset
    )
###END def get_label_map
