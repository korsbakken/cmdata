"""Module for retrieving maps and mapping between labels."""
from __future__ import annotations
import typing as tp
from pathlib import Path

import pandas as pd
import numpy as np
import ruamel.yaml as yaml


class LabelMap:
    """Class used to map between different versions of labels.
    
    The class stores label versions in an internal `pandas.DataFrame`, indexed
    by standardized label codes, and with each possible version of the label in
    separate columns. A copy of the DataFrame can be through the `get_df`
    method, which makes a (shallow) copy to reduce the risk of external
    changes being made. The original DataFrame can be accessed through the
    attribute `_df`, though this should obviously be used with caution.
    
    Label definitions are read from yaml files using the `from_yaml` class
    method.
    """

    __slots__ = ('_df')
    _df: pd.DataFrame

    def __init__(
        self,
        defdict: tp.Dict[tp.Hashable, tp.Any],
        orient: tp.Literal['index', 'columns'] = 'columns',
        values_dtype: tp.Union[str, type, np.dtype] = 'category',
        index_dtype: tp.Union[str, type, np.dtype] = 'category'
    ):
        """Initializes an instance with definitions from a dictionary.
        
        Parameters
        ----------
        defdict : dict
            Dictionary with label codes as keys and dicts with equal lengths and
            the same keys as values. Will be converted into an internal
            DataFrame using `pandas.DataFrame.from_dict.
        orient : `'index'` or `'columns'`, optional
            Orientation of `defdict`. Same as in `pandas.DataFrame.from_dict`.
            Optional, by default `'columns'`.
        values_dtype : str, type, or numpy.dtype
            dtype to use for the values columns in the internal DataFrame.
            Opitional, by default `'category'`.
        index_dtype : str, type, or numpy.dtype
            dtype to use for the index in the internal DataFrame. Opitional, by
            default `'category'`.
        """
        self._df: pd.DataFrame = pd.DataFrame.from_dict(
            data=defdict,
            orient=orient,
            dtype=values_dtype
        )
        self._df.index = self._df.index.astype(index_dtype)
    ###END def LabelMap.__init__

    def get_df(
        self,
        deep: bool = False
    ) -> pd.DataFrame:
        """Returns a copy of the internal DataFrame. Shallow by default.
        
        Parameters
        ----------
        deep : bool, optional
            Whether to make a deep copy (copy values, not just of the DataFrame
            object itself). Optional, False by default.
        """
        return self._df.copy(deep=deep)
    ###END def LabelMap.get_df

    @classmethod
    def from_yaml(
        cls,
        yamlfile: tp.Union[str, Path],
        key: tp.Union[tp.Hashable, tp.Sequence[tp.Hashable]] = None,
        orient: tp.Literal['index', 'columns'] = 'columns'
    ) -> LabelMap:
        """Constructs a `LabelMap` instance from a YAML file definition.
        
        Parameters
        ----------
        yamlfile : str or Path
            YAML file to read from
        key : hashable, or sequence of hashable, optional
            Key(s) for item to read the definitions from in the YAML file. The
            method will use the key to retrieve an item from the dict returned
            when reading the YAML file, and process that item rather than
            processing from the root of the YAML file. If `key` is a list,
            the elements will be used to get the item from a nested dict. Note
            that in order to get nested items, `keys` must not be a hashable
            container, so you should provide a `list`, not a `tuple` or other
            immutable container, or `key` may be interpreted as just a single-
            level key.
        orient : `'index'` or `'columns'`
            Orientation to read the YAML file dictionary into a DataFrame.
            Works like the `orient` parameter of `pandas.DataFrame.from_dict`.
            Optional, by default `'columns'`.

        Returns
        -------
        LabelMap
        """
        _def: tp.Dict[tp.Hashable, tp.Any] = yaml.load(yamlfile)
        if key:
            if isinstance(key, tp.Hashable):
                _def = _def[key]
            else:
                for _key in key:
                    _def = _def[_key]
        return cls(_def, orient=orient)
    ###END def classmethod LabelMap.from_yaml

###END class LabelMap
