"""Functionality for accessing YAML files with labels.

Contains the class LabelfileManager, which holds paths to yaml files, and
provides the `get_label_map` function to obtain `LabelMap` instances, and the
`labelsets` property that contains avilable label sets in each yaml file."""

import typing as tp
from pathlib import Path

import pandas as pd

from . import LabelMap
from . import helpers

FrozenDict: type = helpers.containers.FrozenDict


class LabelfileManager:
    """Stores locations of label YAML files, and provides label mappings.
    
    Attributes
    ----------
    yamlfiles : FrozenDict
        Dictionary of file identifiers (strings) and paths to corresponding YAML
        files.
    labelsets : FrozenDict
        Dict with file indentifiers as keys (same as in `yamlfiles`) and list of
        labelsets for each file as values.

    Methods
    -------
    get_label_map(file: str, labelset: str) -> LabelMap
        Returns a LabelMap instance for the given file and label set
    """

    __slots__ = ('_yamlfiles_root', 'yamlfiles', 'labelsets')
    _yamlfiles_root: Path
    yamlfiles: tp.Mapping[str, Path]
    labelsets: tp.Mapping[str, tp.List[str]]

    def __init__(
        self,
        yamlfiles_root: Path,
        yamlfiles: tp.Mapping[str, Path]
    ):
        """
        Parameters
        ----------
        yamlfiles_root : Path
            The root directory holding the YAML files
        yamlfiles : dict
            Dictionary or mapping with file ids (strings) as keys and Path
            instances for the corresponding label files (relative to
            `yamlfiles_root`.
        """
        self._yamlfiles_root = yamlfiles_root
        self.yamlfiles = FrozenDict(
            {
                _file_id: yamlfiles_root / _file_path
                for _file_id, _file_path in yamlfiles.items()
            }
        )
        self.labelsets = FrozenDict(self.read_labelsets())
    ###END def LabelfileManager.__init__

    def read_labelsets(self) -> tp.Mapping[str, tp.List[tp.Hashable]]:
        return {
            _key: list(helpers.yaml_utils.read_yaml(_file).keys())
            for _key, _file in self.yamlfiles.items()
        }
    ###END def LabelfileManager.read_labelsets

    def get_label_map(
        self,
        file_id: str,
        labelset: str
    ) -> LabelMap:
        """Get a `LabelMap` instance for the desired label set.
        
        Parameters
        ----------
        file_id : str
            File identifier to get labels from. Valid values are any of the keys in
            the instance attribute `self.yamlfiles` (a dict).
        labelset : str
            The name of the label set to get from `file_id`. Valid values are listed
            in `self.labelsets[file_id]`.

        Returns
        -------
        LabelMap
        """
        return LabelMap.from_yaml(
            yamlfile=self.yamlfiles[file_id],
            key=labelset
        )
    ###END def LabelfileManager.get_label_map

###END class LabelfileManager
