"""Package with base functionality for DatasetDescriptor objects."""

from __future__ import annotations
import typing as tp
from pathlib import Path

import pandas as pd
import pydantic

from . import helpers
from . import yamlfuncs


class DescriptorBase(pydantic.BaseModel):
    """Basis for all descriptor objects."""
    id: str
    """Id (short name). Should be a valid Python variable name."""
    name: tp.Optional[str]
    """Full name. Optional (but highly recommended)"""
    parent_id: tp.Optional[str]
    """ID of parent dataset or dataset collection. Optional (and may not be
    applicable at all)."""
    description: tp.Optional[str]
    """Free-form description. Optional"""
    notes: tp.Optional[str]
    """Notes, as a single string. Optional."""

    def with_base_path(
        self,
        basepath: tp.Union[Path, str],
        make_absolute: bool = True,
        inplace: bool = False
    ) -> DescriptorBase:
        """Prefixes a root/base path to all Path objects in `self`.
        
        The path is set recursively, i.e., it also includes Path objects in
        dicts and sequences.
        
        Parameters
        ----------
        basepath : Path or str
            The path to add
        make_absolute : bool, optional
            Whether to force paths to be absolute (through `Path.absolute`)
            after the base path has been prefixed. Optional, by default True.
        inplace : bool, optional
            Whether to add the base path in the object itself. If False, the
            changes are made to a copy which is then returned. Optional, by
            default False.
        
        Returns
        -------
        DescriptorBase
            The object itself (if `inplace` is True) or a copy with the prefixed
            base path."""
        basepath = Path(basepath)
        action: tp.Callable[[Path], Path]
        if make_absolute:
            action = lambda p: (basepath / p).absolute()
        else:
            action = lambda p: basepath / p
        new_obj: DescriptorBase = helpers.recurse_by_type(
            self,
            match_type=Path,
            action=action,
            inplace=inplace
        )
        return new_obj
    ###END def DescriptorBase.with_base_path

    @classmethod
    def dict_from_yaml(
        cls,
        descriptors_file: tp.Union[Path, str],
        descriptors_key: str = 'datasets',
        parse_func: tp.Callable[[yamlfuncs._YamlDataType],
                                 yamlfuncs._YamlDataType] \
            = yamlfuncs.resolve_variables
    ) -> tp.Dict[str, DescriptorBase]:
        """Load descriptors from a YAML file.
        
        Parameters
        ----------
        descriptors_file : Path or str
            Name or Path instance of the yaml file to load from.
        descriptors_key : str, optional
            The key that the  descriptions are found under in the yaml file.
            Optional, by default `'datasets'`.
        parse_func : callable
            Function to parse the yaml file contents. Must return a data
            structure similar to what would be returned by
            `yamlfuncs.load_yaml`, and parse any dynamic variables used in the
            file. Optional, by default uses `yamlfuncs.resolve_variables`.

        Returns
        -------
        Dict of DescriptorBase instances
            A dict of descriptor instances. The keys are the IDs, prefixed with
            parent IDs (if present) followed by underscore. If parent IDs are
            not present, the IDs alone are used as keys.
        """
        _YamlDataType = yamlfuncs._YamlDataType
        with open(descriptors_file, mode='r') as f:
            data: _YamlDataType = yamlfuncs.load_yaml(f)
        data = parse_func(data)
        datasets: tp.Dict[str, DescriptorBase] = dict()
        _dataset: tp.Dict[str, tp.Any]
        _descr: DescriptorBase
        for _dataset in data[descriptors_key]:
            _descr = DescriptorBase(**_dataset)
            if _descr.parent_id is not None:
                _dataset_key: str = f'{_descr.parent_id}_{_descr.id}'
            else:
                _dataset_key: str = f'{_descr.id}'
            datasets[_dataset_key] = _descr
        return datasets
    ###END def DescriptorBase.from_yaml

###END class DescriptorBase


class DatasetDescriptorBase(DescriptorBase):
    """Basis for dataset descriptor objects."""
    raw_data_path: tp.Optional[tp.Union[Path, tp.Dict[str, Path]]]
    """Path to raw data file(s). Either a single Path instance, or a dict of
    Path instances. If a dict, the keys will be interpreted as version
    identifiers. Optional."""
    default_version: tp.Optional[str]
    """Default version of the dataset, if there are multiple versions. If
    specified, it is assumed that `raw_data_path` (if it itself is specified)
    is a dict with version ids as keys."""
    dimensions: tp.Optional[tp.Tuple[str, ...]] = ()
    """Tuple with (ordered) names of dimensions in the dataset, if supported.
    Optional, by default set to an empty tuple (but can be explicitly set to 
    None if desired, to explicitly show if the concept of dimensions is not
    relevant to the given dataset)."""
###END class DatasetDescriptorBase
